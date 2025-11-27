"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class AnemiaStage(str, Enum):
    """WHO anemia classification stages."""
    NORMAL = "normal"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class QualityReport(BaseModel):
    """Image quality control report."""
    sharpness: float = Field(..., description="Laplacian variance (higher = sharper)")
    brightness: float = Field(..., description="Mean grayscale value (0-255)")
    contrast: float = Field(..., description="Local contrast measure")
    motion_blur_score: float = Field(..., description="Motion blur indicator")
    quality_pass: bool = Field(..., description="Whether image passed QC")
    fail_reasons: List[str] = Field(default_factory=list, description="Reasons for QC failure")


class PreprocessingReport(BaseModel):
    """Preprocessing and fairness report."""
    tone_cluster: int = Field(..., description="Skin tone cluster ID (0-4)")
    lab_mean: List[float] = Field(..., description="Mean LAB values [L, a, b]")
    scaling_factor: float = Field(..., description="Fairness scaling factor applied")
    glare_mask_coverage: float = Field(..., description="Fraction of pixels with glare (0-1)")
    original_image_base64: Optional[str] = Field(None, description="Base64 encoded original image")
    preprocessed_image_base64: Optional[str] = Field(None, description="Base64 encoded preprocessed image")


class SegmentationReport(BaseModel):
    """Nail-bed segmentation report."""
    iou_estimate: float = Field(..., description="Estimated IOU score")
    mask_path: str = Field(..., description="Path to saved mask image")
    roi_path: str = Field(..., description="Path to extracted ROI image")
    roi_image_base64: Optional[str] = Field(None, description="Base64 encoded ROI nail bed image")


class ColorFeatures(BaseModel):
    """Color-based features."""
    mean_L: float
    mean_a: float
    mean_b: float
    mean_R: float
    mean_G: float
    mean_B: float
    std_L: float
    std_a: float
    std_b: float
    ratio_R_G: float
    ratio_R_B: float
    ratio_a_L: float


class TextureFeatures(BaseModel):
    """Texture-based features."""
    glcm_contrast: float
    glcm_homogeneity: float
    glcm_energy: float
    glcm_entropy: float
    lbp_uniformity: float
    fft_highfreq_power: float


class VascularFeatures(BaseModel):
    """Vascularity-based features."""
    vessel_density: float = Field(..., description="Fraction of vessel pixels")
    mean_thickness: float = Field(..., description="Average vessel thickness in pixels")
    orientation_entropy: float = Field(..., description="Vessel orientation diversity")


class Features(BaseModel):
    """Complete feature set."""
    color: ColorFeatures
    texture: TextureFeatures
    vascular: VascularFeatures


class Prediction(BaseModel):
    """Hemoglobin prediction with uncertainty."""
    hb_g_per_dl: Optional[float] = Field(None, description="Predicted hemoglobin (g/dL)")
    hb_ci_95: Optional[List[float]] = Field(None, description="95% confidence interval [lower, upper]")
    uncertainty: float = Field(..., description="Prediction uncertainty score")
    anemia_stage: Optional[AnemiaStage] = Field(None, description="Anemia classification")
    risk_score: Optional[float] = Field(None, description="Anemia risk probability (0-1)")
    uncertainty_flag: Optional[str] = Field(None, description="Warning if uncertainty too high")
    message: Optional[str] = Field(None, description="Human-readable message")


class FeatureImportance(BaseModel):
    """Feature importance from SHAP analysis."""
    name: str = Field(..., description="Feature name")
    value: float = Field(..., description="Feature value")
    importance: float = Field(..., description="Importance score (0-1)")
    contribution: float = Field(..., description="Contribution percentage")


class Explainability(BaseModel):
    """Explainability outputs."""
    gradcam_nail_overlay: Optional[str] = Field(None, description="Base64-encoded Grad-CAM overlay")
    top_features: List[FeatureImportance] = Field(default_factory=list, description="Top contributing features")
    feature_importance_plot: Optional[str] = Field(None, description="Base64-encoded feature importance visualization")
    interpretation: Optional[str] = Field(None, description="Human-readable interpretation")
    method: Optional[str] = Field(None, description="Explainability method used")


class VersionInfo(BaseModel):
    """Model version information."""
    preprocess: str = "1.0.0"
    unet: str = "1.0.0"
    hb_model: str = "1.0.0"


class ScanResponse(BaseModel):
    """Complete scan analysis response."""
    scan_id: str = Field(..., description="Unique scan identifier (UUID)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    quality: QualityReport
    preprocessing: Optional[PreprocessingReport] = None
    segmentation: Optional[SegmentationReport] = None
    features: Optional[Features] = None
    prediction: Optional[Prediction] = None
    explainability: Optional[Explainability] = None
    version: VersionInfo = Field(default_factory=VersionInfo)


class ScanRequest(BaseModel):
    """Optional metadata for scan request."""
    device_model: Optional[str] = None
    exposure: Optional[float] = None
    user_id: Optional[str] = None
    measurement_id: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    scan_id: Optional[str] = None
