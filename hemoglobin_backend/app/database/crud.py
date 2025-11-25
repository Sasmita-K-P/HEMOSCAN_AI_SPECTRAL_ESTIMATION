"""
Database CRUD operations.
"""
from sqlalchemy.orm import Session
from typing import Optional
from app.database.models import ScanRecord
from app.schemas import ScanResponse
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def create_scan_record(db: Session, scan_data: ScanResponse) -> ScanRecord:
    """
    Create a new scan record in database.
    
    Args:
        db: Database session
        scan_data: Scan response data
        
    Returns:
        Created ScanRecord
    """
    record = ScanRecord(
        scan_id=scan_data.scan_id,
        timestamp=scan_data.timestamp,
        qc_pass=scan_data.quality.quality_pass,
        qc_sharpness=scan_data.quality.sharpness,
        qc_brightness=scan_data.quality.brightness,
        qc_contrast=scan_data.quality.contrast,
        tone_cluster=scan_data.preprocessing.tone_cluster if scan_data.preprocessing else None,
        glare_coverage=scan_data.preprocessing.glare_mask_coverage if scan_data.preprocessing else None,
        hb_value=scan_data.prediction.hb_g_per_dl if scan_data.prediction else None,
        hb_ci_lower=scan_data.prediction.hb_ci_95[0] if scan_data.prediction and scan_data.prediction.hb_ci_95 else None,
        hb_ci_upper=scan_data.prediction.hb_ci_95[1] if scan_data.prediction and scan_data.prediction.hb_ci_95 else None,
        uncertainty=scan_data.prediction.uncertainty if scan_data.prediction else None,
        anemia_stage=scan_data.prediction.anemia_stage.value if scan_data.prediction and scan_data.prediction.anemia_stage else None,
        risk_score=scan_data.prediction.risk_score if scan_data.prediction else None,
        model_version=f"unet_{scan_data.version.unet}_hb_{scan_data.version.hb_model}",
        response_data=scan_data.dict()
    )
    
    db.add(record)
    db.commit()
    db.refresh(record)
    
    logger.info(f"Created scan record: {scan_data.scan_id}")
    return record


def get_scan_record(db: Session, scan_id: str) -> Optional[ScanRecord]:
    """
    Retrieve scan record by ID.
    
    Args:
        db: Database session
        scan_id: Scan ID
        
    Returns:
        ScanRecord if found, None otherwise
    """
    record = db.query(ScanRecord).filter(ScanRecord.scan_id == scan_id).first()
    
    if record:
        logger.info(f"Retrieved scan record: {scan_id}")
    else:
        logger.warning(f"Scan record not found: {scan_id}")
    
    return record
