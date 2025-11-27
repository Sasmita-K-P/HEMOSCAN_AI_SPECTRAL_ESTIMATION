"""
API routes for scan endpoints.
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
from PIL import Image
import io
import time
import base64
from datetime import datetime

from app.schemas import ScanResponse, ScanRequest, ErrorResponse
from app.database.models import get_db
from app.database.crud import create_scan_record, get_scan_record
from app.services.validation import validate_upload, ValidationError
from app.services.quality_control import assess_quality
from app.services.preprocessing import preprocess_image
from app.services.segmentation import segment_nail_bed
from app.services.feature_extraction import extract_all_features
from app.services.prediction import predict_hemoglobin
from app.services.explainability import generate_explainability
from app.services.report_generator import create_clinical_report
from app.utils.security import generate_scan_id
from app.utils.monitoring import (
    scan_requests_total,
    scan_duration_seconds,
    qc_failures_total,
    prediction_uncertainty,
    drift_detector
)
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["scans"])


@router.post("/scan", response_model=ScanResponse)
async def create_scan(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and analyze nail-bed image for hemoglobin estimation.
    
    Args:
        file: Uploaded image file (JPEG/PNG)
        db: Database session
        
    Returns:
        Complete scan analysis results
    """
    start_time = time.time()
    scan_id = generate_scan_id()
    
    logger.info(f"Processing scan: {scan_id}, filename: {file.filename}")
    
    try:
        # Read file
        file_bytes = await file.read()
        
        # Validation
        with scan_duration_seconds.labels(stage='validation').time():
            pil_image, hand_info = validate_upload(file_bytes, file.filename)
            logger.info(f"Hand detection: {hand_info}")
        
        # Quality Control
        with scan_duration_seconds.labels(stage='quality_control').time():
            qc_report = assess_quality(pil_image)
        
        # If QC fails, return early
        if not qc_report.quality_pass:
            for reason in qc_report.fail_reasons:
                qc_failures_total.labels(reason=reason[:50]).inc()
            
            scan_response = ScanResponse(
                scan_id=scan_id,
                quality=qc_report
            )
            
            # Save to database
            create_scan_record(db, scan_response)
            
            scan_requests_total.labels(status='qc_failed').inc()
            logger.warning(f"QC failed for scan {scan_id}")
            return scan_response
        
        # Preprocessing
        with scan_duration_seconds.labels(stage='preprocessing').time():
            # Save original
            original_path = settings.upload_dir / f"{scan_id}_original.jpg"
            pil_image.save(original_path)
            
            # Encode original image as base64
            original_buffer = io.BytesIO()
            pil_image.save(original_buffer, format='JPEG')
            original_base64 = base64.b64encode(original_buffer.getvalue()).decode('utf-8')
            
            # Preprocess
            preprocessed_path = settings.processed_dir / f"{scan_id}_preprocessed.jpg"
            preprocessed_image, preprocessing_report = preprocess_image(
                pil_image,
                save_path=str(preprocessed_path)
            )
            
            # Encode preprocessed image as base64
            preprocessed_buffer = io.BytesIO()
            Image.fromarray(preprocessed_image).save(preprocessed_buffer, format='JPEG')
            preprocessed_base64 = base64.b64encode(preprocessed_buffer.getvalue()).decode('utf-8')
        
        # Segmentation
        with scan_duration_seconds.labels(stage='segmentation').time():
            roi_image, mask, segmentation_report = segment_nail_bed(
                preprocessed_image,
                save_dir=settings.processed_dir,
                scan_id=scan_id
            )
            
            # Encode ROI image as base64
            roi_buffer = io.BytesIO()
            Image.fromarray(roi_image).save(roi_buffer, format='JPEG')
            roi_base64 = base64.b64encode(roi_buffer.getvalue()).decode('utf-8')
        
        # Feature Extraction
        with scan_duration_seconds.labels(stage='feature_extraction').time():
            features = extract_all_features(roi_image, mask)
        
        # Update drift detector
        feature_dict = {
            'mean_L': features.color.mean_L,
            'ratio_R_G': features.color.ratio_R_G,
            'vessel_density': features.vascular.vessel_density
        }
        drift_detector.update(feature_dict)
        
        # Prediction
        with scan_duration_seconds.labels(stage='prediction').time():
            prediction = predict_hemoglobin(roi_image, features.dict())
        
        # Record uncertainty
        prediction_uncertainty.observe(prediction.uncertainty)
        
        # Explainability (only if prediction succeeded)
        explainability = None
        if prediction.hb_g_per_dl is not None:
            with scan_duration_seconds.labels(stage='explainability').time():
                explainability = generate_explainability(
                    roi_image,
                    features.dict(),
                    prediction.hb_g_per_dl
                )
        
        # Add base64 images to reports
        preprocessing_report.original_image_base64 = f"data:image/jpeg;base64,{original_base64}"
        preprocessing_report.preprocessed_image_base64 = f"data:image/jpeg;base64,{preprocessed_base64}"
        segmentation_report.roi_image_base64 = f"data:image/jpeg;base64,{roi_base64}"
        
        # Create response
        scan_response = ScanResponse(
            scan_id=scan_id,
            quality=qc_report,
            preprocessing=preprocessing_report,
            segmentation=segmentation_report,
            features=features,
            prediction=prediction,
            explainability=explainability
        )
        
        # Save to database
        create_scan_record(db, scan_response)
        
        # Metrics
        status = 'success' if prediction.hb_g_per_dl is not None else 'high_uncertainty'
        scan_requests_total.labels(status=status).inc()
        
        duration = time.time() - start_time
        logger.info(f"Scan {scan_id} completed in {duration:.2f}s")
        
        return scan_response
        
    except ValidationError as e:
        scan_requests_total.labels(status='validation_error').inc()
        logger.error(f"Validation error for scan {scan_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        scan_requests_total.labels(status='error').inc()
        logger.error(f"Error processing scan {scan_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/scan/{scan_id}", response_model=ScanResponse)
async def get_scan(scan_id: str, db: Session = Depends(get_db)):
    """
    Retrieve scan results by ID.
    
    Args:
        scan_id: Scan identifier
        db: Database session
        
    Returns:
        Scan analysis results
    """
    record = get_scan_record(db, scan_id)
    
    if not record:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")
    
    # Reconstruct response from stored JSON
    scan_response = ScanResponse(**record.response_data)
    
    logger.info(f"Retrieved scan: {scan_id}")
    return scan_response


@router.get("/report/{scan_id}")
async def get_report(scan_id: str, db: Session = Depends(get_db)):
    """
    Generate and download clinical PDF report.
    
    Args:
        scan_id: Scan identifier
        db: Database session
        
    Returns:
        PDF file download
    """
    # Get scan data
    record = get_scan_record(db, scan_id)
    
    if not record:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")
    
    scan_response = ScanResponse(**record.response_data)
    
    # Generate report
    report_path = settings.processed_dir / f"{scan_id}_report.pdf"
    
    try:
        create_clinical_report(scan_response, report_path)
        
        logger.info(f"Generated report for scan: {scan_id}")
        
        return FileResponse(
            path=str(report_path),
            media_type='application/pdf',
            filename=f"hemoglobin_report_{scan_id}.pdf"
        )
        
    except Exception as e:
        logger.error(f"Error generating report for {scan_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app_version
    }
