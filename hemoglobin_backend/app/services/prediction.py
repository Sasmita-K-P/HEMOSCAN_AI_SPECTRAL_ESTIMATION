"""
Prediction service with anemia classification and uncertainty handling.
"""
import numpy as np
from typing import Optional
from app.models.hb_predictor import get_hb_model
from app.schemas import Prediction, AnemiaStage
from app.config import settings
from app.utils.logger import setup_logger
from scipy import stats

logger = setup_logger(__name__)


def classify_anemia(hb_value: float) -> AnemiaStage:
    """
    Classify anemia stage based on WHO guidelines.
    
    Args:
        hb_value: Hemoglobin value in g/dL
        
    Returns:
        AnemiaStage enum
    """
    if hb_value >= settings.anemia_threshold_normal:
        return AnemiaStage.NORMAL
    elif hb_value >= settings.anemia_threshold_mild:
        return AnemiaStage.MILD
    elif hb_value >= settings.anemia_threshold_moderate:
        return AnemiaStage.MODERATE
    else:
        return AnemiaStage.SEVERE


def compute_confidence_interval(
    mean: float,
    std: float,
    confidence: float = 0.95
) -> tuple[float, float]:
    """
    Compute confidence interval for prediction.
    
    Args:
        mean: Predicted mean value
        std: Standard deviation
        confidence: Confidence level (default 0.95)
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    z_score = stats.norm.ppf((1 + confidence) / 2)
    margin = z_score * std
    
    lower = max(0.0, mean - margin)  # Hb can't be negative
    upper = min(20.0, mean + margin)  # Reasonable upper limit
    
    return float(lower), float(upper)


def predict_hemoglobin(
    roi_image: np.ndarray,
    features: dict
) -> Prediction:
    """
    Complete hemoglobin prediction pipeline.
    
    Args:
        roi_image: ROI image (H, W, 3), RGB, 0-255
        features: Extracted features (as dict)
        
    Returns:
        Prediction object with Hb estimate, CI, anemia stage, and uncertainty
    """
    # Get model
    hb_model = get_hb_model()
    
    # Predict with uncertainty
    hb_mean, hb_std, uncertainty, anemia_probs = hb_model.predict_with_uncertainty(
        roi_image,
        features
    )
    
    # Check uncertainty threshold
    if uncertainty > settings.uncertainty_threshold:
        logger.warning(
            f"High uncertainty detected: {uncertainty:.3f} > {settings.uncertainty_threshold}"
        )
        return Prediction(
            hb_g_per_dl=None,
            hb_ci_95=None,
            uncertainty=uncertainty,
            anemia_stage=None,
            risk_score=None,
            uncertainty_flag="RETAKE_OR_LAB_CONFIRM",
            message=(
                f"Model is not confident (uncertainty: {uncertainty:.2f}). "
                "Please retake the image with better quality or confirm with a lab test."
            )
        )
    
    # Compute confidence interval
    ci_lower, ci_upper = compute_confidence_interval(
        hb_mean,
        hb_std,
        confidence=settings.confidence_level
    )
    
    # Classify anemia
    anemia_stage = classify_anemia(hb_mean)
    
    # Risk score (probability of anemia - any stage)
    risk_score = float(1.0 - anemia_probs[0])  # 1 - P(normal)
    
    prediction = Prediction(
        hb_g_per_dl=hb_mean,
        hb_ci_95=[ci_lower, ci_upper],
        uncertainty=uncertainty,
        anemia_stage=anemia_stage,
        risk_score=risk_score,
        uncertainty_flag=None,
        message=None
    )
    
    logger.info(
        f"Prediction complete: Hb={hb_mean:.2f} g/dL [{ci_lower:.2f}, {ci_upper:.2f}], "
        f"stage={anemia_stage.value}, risk={risk_score:.3f}"
    )
    
    return prediction
