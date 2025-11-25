"""
Image quality control metrics and assessment.
"""
import cv2
import numpy as np
from typing import Tuple, List
from PIL import Image
from app.schemas import QualityReport
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def compute_sharpness(image: np.ndarray) -> float:
    """
    Compute image sharpness using Laplacian variance.
    Higher values indicate sharper images.
    
    Args:
        image: Grayscale image array
        
    Returns:
        Sharpness score
    """
    laplacian = cv2.Laplacian(image, cv2.CV_64F)
    variance = laplacian.var()
    return float(variance)


def compute_brightness(image: np.ndarray) -> float:
    """
    Compute global brightness as mean grayscale value.
    
    Args:
        image: Grayscale image array
        
    Returns:
        Brightness score (0-255)
    """
    return float(np.mean(image))


def compute_contrast(image: np.ndarray) -> float:
    """
    Compute local contrast using standard deviation of Laplacian.
    
    Args:
        image: Grayscale image array
        
    Returns:
        Contrast score
    """
    laplacian = cv2.Laplacian(image, cv2.CV_64F)
    std = np.std(laplacian)
    return float(std)


def detect_motion_blur(image: np.ndarray) -> float:
    """
    Detect motion blur using directional variance.
    Lower values indicate more blur.
    
    Args:
        image: Grayscale image array
        
    Returns:
        Motion blur score (higher = less blur)
    """
    # Compute FFT
    f_transform = np.fft.fft2(image)
    f_shift = np.fft.fftshift(f_transform)
    magnitude = np.abs(f_shift)
    
    # High frequency content indicates less blur
    h, w = magnitude.shape
    center_h, center_w = h // 2, w // 2
    radius = min(h, w) // 4
    
    # Create mask for high frequencies (outer region)
    y, x = np.ogrid[:h, :w]
    mask = ((x - center_w)**2 + (y - center_h)**2) > radius**2
    
    high_freq_energy = np.mean(magnitude[mask])
    return float(high_freq_energy)


def assess_quality(pil_image: Image.Image) -> QualityReport:
    """
    Perform complete quality control assessment.
    
    Args:
        pil_image: PIL Image object
        
    Returns:
        QualityReport with metrics and pass/fail decision
    """
    # Convert to grayscale numpy array
    gray = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2GRAY)
    
    # Compute metrics
    sharpness = compute_sharpness(gray)
    brightness = compute_brightness(gray)
    contrast = compute_contrast(gray)
    motion_blur_score = detect_motion_blur(gray)
    
    # Determine pass/fail
    fail_reasons = []
    
    if sharpness < settings.qc_min_sharpness:
        fail_reasons.append(
            f"Image too blurry (sharpness: {sharpness:.1f}, minimum: {settings.qc_min_sharpness}). "
            "Please retake with steady hand and ensure focus."
        )
    
    if brightness < settings.qc_min_brightness:
        fail_reasons.append(
            f"Image too dark (brightness: {brightness:.1f}, minimum: {settings.qc_min_brightness}). "
            "Please retake in better lighting."
        )
    elif brightness > settings.qc_max_brightness:
        fail_reasons.append(
            f"Image too bright/overexposed (brightness: {brightness:.1f}, maximum: {settings.qc_max_brightness}). "
            "Please reduce lighting or adjust camera exposure."
        )
    
    if contrast < settings.qc_min_contrast:
        fail_reasons.append(
            f"Image has low contrast (contrast: {contrast:.1f}, minimum: {settings.qc_min_contrast}). "
            "Please ensure good lighting and avoid shadows."
        )
    
    quality_pass = len(fail_reasons) == 0
    
    report = QualityReport(
        sharpness=sharpness,
        brightness=brightness,
        contrast=contrast,
        motion_blur_score=motion_blur_score,
        quality_pass=quality_pass,
        fail_reasons=fail_reasons
    )
    
    logger.info(
        f"QC Assessment: pass={quality_pass}, sharpness={sharpness:.2f}, "
        f"brightness={brightness:.2f}, contrast={contrast:.2f}"
    )
    
    return report


def check_saturation(pil_image: Image.Image) -> bool:
    """
    Check if image has saturated regions (clipped highlights/shadows).
    
    Args:
        pil_image: PIL Image object
        
    Returns:
        True if image has significant saturation
    """
    arr = np.array(pil_image)
    
    # Check for clipped highlights (>95% of pixels near 255)
    highlight_ratio = np.mean(arr > 250)
    
    # Check for clipped shadows (>95% of pixels near 0)
    shadow_ratio = np.mean(arr < 5)
    
    is_saturated = highlight_ratio > 0.05 or shadow_ratio > 0.05
    
    if is_saturated:
        logger.warning(
            f"Image saturation detected: highlights={highlight_ratio:.3f}, shadows={shadow_ratio:.3f}"
        )
    
    return is_saturated
