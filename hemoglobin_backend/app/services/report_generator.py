"""
Clinical report generation service (PDF).
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
from pathlib import Path
from typing import Optional
import base64
from io import BytesIO
from app.schemas import ScanResponse
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def create_clinical_report(
    scan_data: ScanResponse,
    output_path: Path
) -> Path:
    """
    Generate clinical PDF report.
    
    Args:
        scan_data: Complete scan response data
        output_path: Path to save PDF
        
    Returns:
        Path to generated PDF
    """
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=10,
        spaceBefore=12
    )
    
    # Title
    elements.append(Paragraph("Hemoglobin Estimation Report", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Scan Information
    elements.append(Paragraph("Scan Information", heading_style))
    scan_info_data = [
        ['Scan ID:', scan_data.scan_id],
        ['Timestamp:', scan_data.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')],
        ['Model Version:', f"UNet {scan_data.version.unet}, Hb {scan_data.version.hb_model}"]
    ]
    scan_info_table = Table(scan_info_data, colWidths=[2*inch, 4*inch])
    scan_info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#555555')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(scan_info_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Quality Control
    elements.append(Paragraph("Image Quality Assessment", heading_style))
    qc = scan_data.quality
    qc_status = "✓ PASS" if qc.quality_pass else "✗ FAIL"
    qc_color = colors.green if qc.quality_pass else colors.red
    
    qc_data = [
        ['Status:', qc_status],
        ['Sharpness:', f"{qc.sharpness:.2f}"],
        ['Brightness:', f"{qc.brightness:.2f}"],
        ['Contrast:', f"{qc.contrast:.2f}"]
    ]
    qc_table = Table(qc_data, colWidths=[2*inch, 4*inch])
    qc_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#555555')),
        ('TEXTCOLOR', (1, 0), (1, 0), qc_color),
        ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
    ]))
    elements.append(qc_table)
    
    if not qc.quality_pass:
        elements.append(Spacer(1, 0.1*inch))
        for reason in qc.fail_reasons:
            elements.append(Paragraph(f"• {reason}", styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Add disclaimer and stop here
        elements.append(Paragraph("⚠ Disclaimer", heading_style))
        disclaimer_text = (
            "Image quality assessment failed. No prediction was generated. "
            "Please retake the image following the guidance above."
        )
        elements.append(Paragraph(disclaimer_text, styles['Normal']))
        
        doc.build(elements)
        logger.info(f"Generated QC failure report: {output_path}")
        return output_path
    
    elements.append(Spacer(1, 0.2*inch))
    
    # Prediction Results
    if scan_data.prediction and scan_data.prediction.hb_g_per_dl is not None:
        elements.append(Paragraph("Hemoglobin Estimation", heading_style))
        
        pred = scan_data.prediction
        pred_data = [
            ['Hemoglobin (Hb):', f"{pred.hb_g_per_dl:.2f} g/dL"],
            ['95% CI:', f"[{pred.hb_ci_95[0]:.2f}, {pred.hb_ci_95[1]:.2f}] g/dL"],
            ['Anemia Stage:', pred.anemia_stage.value.upper()],
            ['Risk Score:', f"{pred.risk_score:.2%}"],
            ['Uncertainty:', f"{pred.uncertainty:.3f}"]
        ]
        
        pred_table = Table(pred_data, colWidths=[2*inch, 4*inch])
        pred_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#555555')),
            ('FONTNAME', (1, 0), (1, 2), 'Helvetica-Bold'),
            ('FONTSIZE', (1, 0), (1, 0), 12),
        ]))
        elements.append(pred_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Explainability
        if scan_data.explainability and scan_data.explainability.top_features:
            elements.append(Paragraph("Key Contributing Factors", heading_style))
            
            for feat in scan_data.explainability.top_features[:3]:
                impact = "↑ increases" if feat.shap_value > 0 else "↓ decreases"
                elements.append(
                    Paragraph(
                        f"• <b>{feat.name}</b>: {impact} Hb (impact: {abs(feat.shap_value):.3f})",
                        styles['Normal']
                    )
                )
            elements.append(Spacer(1, 0.2*inch))
    
    elif scan_data.prediction and scan_data.prediction.uncertainty_flag:
        elements.append(Paragraph("Prediction Status", heading_style))
        elements.append(Paragraph(
            f"⚠ {scan_data.prediction.message}",
            styles['Normal']
        ))
        elements.append(Spacer(1, 0.2*inch))
    
    # Disclaimer
    elements.append(Paragraph("⚠ Medical Disclaimer", heading_style))
    disclaimer_text = (
        "<b>This is not a standalone diagnostic tool.</b> "
        "The hemoglobin estimate provided by this system is for screening purposes only "
        "and should not replace laboratory testing. Clinical decisions should be made by "
        "qualified healthcare professionals based on comprehensive patient assessment. "
        "If anemia is suspected, please confirm with a complete blood count (CBC) test."
    )
    elements.append(Paragraph(disclaimer_text, styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    logger.info(f"Generated clinical report: {output_path}")
    
    return output_path
