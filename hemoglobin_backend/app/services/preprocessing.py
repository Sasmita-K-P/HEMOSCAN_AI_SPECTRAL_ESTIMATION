"""
Image preprocessing pipeline with fairness considerations.
"""
import cv2
import numpy as np
from PIL import Image
from typing import Tuple, Optional
from sklearn.cluster import KMeans
from app.schemas import PreprocessingReport
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def center_crop_and_resize(image: np.ndarray, target_size: int) -> np.ndarray:
    """
    Center crop to square and resize to target size.
    
    Args:
        image: Input image array (H, W, C)
        target_size: Target dimension for square output
        
    Returns:
        Resized square image
    """
    h, w = image.shape[:2]
    
    # Crop to square
    if h > w:
        start = (h - w) // 2
        image = image[start:start+w, :, :]
    elif w > h:
        start = (w - h) // 2
        image = image[:, start:start+h, :]
    
    # Resize
    resized = cv2.resize(image, (target_size, target_size), interpolation=cv2.INTER_LANCZOS4)
    
    logger.debug(f"Cropped and resized to {target_size}x{target_size}")
    return resized


def apply_white_balance(image: np.ndarray) -> np.ndarray:
    """
    Apply gray-world white balance correction.
    
    Args:
        image: Input BGR image
        
    Returns:
        White-balanced image
    """
    result = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    avg_a = np.average(result[:, :, 1])
    avg_b = np.average(result[:, :, 2])
    
    result[:, :, 1] = result[:, :, 1] - ((avg_a - 128) * (result[:, :, 0] / 255.0) * 1.1)
    result[:, :, 2] = result[:, :, 2] - ((avg_b - 128) * (result[:, :, 0] / 255.0) * 1.1)
    
    result = cv2.cvtColor(result, cv2.COLOR_LAB2BGR)
    logger.debug("Applied white balance correction")
    return result


def apply_clahe(image: np.ndarray) -> np.ndarray:
    """
    Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) on L channel.
    
    Args:
        image: Input BGR image
        
    Returns:
        CLAHE-enhanced image
    """
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    
    enhanced = cv2.merge([l, a, b])
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    
    logger.debug("Applied CLAHE enhancement")
    return enhanced


def detect_glare(image: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Detect specular highlights/glare using HSV thresholding.
    
    Args:
        image: Input BGR image
        
    Returns:
        Tuple of (glare_mask, coverage_fraction)
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # High value, low saturation indicates glare
    lower = np.array([0, 0, 200])
    upper = np.array([180, 50, 255])
    
    glare_mask = cv2.inRange(hsv, lower, upper)
    coverage = np.sum(glare_mask > 0) / glare_mask.size
    
    logger.debug(f"Glare detection: {coverage:.3f} coverage")
    return glare_mask, float(coverage)


def inpaint_glare(image: np.ndarray, glare_mask: np.ndarray) -> np.ndarray:
    """
    Inpaint glare regions using Telea algorithm.
    
    Args:
        image: Input BGR image
        glare_mask: Binary mask of glare regions
        
    Returns:
        Inpainted image
    """
    if np.sum(glare_mask) == 0:
        return image
    
    inpainted = cv2.inpaint(image, glare_mask, 3, cv2.INPAINT_TELEA)
    logger.debug("Inpainted glare regions")
    return inpainted


def estimate_skin_tone(image: np.ndarray, mask: Optional[np.ndarray] = None) -> Tuple[int, np.ndarray]:
    """
    Estimate skin tone cluster using LAB color space.
    
    Args:
        image: Input BGR image
        mask: Optional mask for skin regions (if None, uses whole image)
        
    Returns:
        Tuple of (cluster_id, lab_mean)
    """
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    
    if mask is not None:
        pixels = lab[mask > 0]
    else:
        # Sample from border regions (likely skin around nail)
        h, w = lab.shape[:2]
        border_width = w // 10
        border_mask = np.zeros((h, w), dtype=bool)
        border_mask[:, :border_width] = True
        border_mask[:, -border_width:] = True
        border_mask[:border_width, :] = True
        border_mask[-border_width:, :] = True
        pixels = lab[border_mask]
    
    if len(pixels) < 100:
        pixels = lab.reshape(-1, 3)
    
    # Cluster into 5 tone groups (very light to very dark)
    kmeans = KMeans(n_clusters=5, random_state=settings.random_seed, n_init=10)
    kmeans.fit(pixels)
    
    # Determine cluster based on L* value
    lab_mean = np.mean(pixels, axis=0)
    cluster_id = int(kmeans.predict([lab_mean])[0])
    
    logger.debug(f"Skin tone cluster: {cluster_id}, LAB mean: {lab_mean}")
    return cluster_id, lab_mean


def apply_tone_normalization(image: np.ndarray, tone_cluster: int, lab_mean: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Apply fairness-aware tone normalization.
    
    Args:
        image: Input BGR image
        tone_cluster: Skin tone cluster ID
        lab_mean: Mean LAB values
        
    Returns:
        Tuple of (normalized_image, scaling_factor)
    """
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB).astype(np.float32)
    
    # Target L* value (mid-range)
    target_L = 180.0
    current_L = lab_mean[0]
    
    # Compute scaling factor (avoid over-correction)
    scaling_factor = target_L / (current_L + 1e-6)
    scaling_factor = np.clip(scaling_factor, 0.7, 1.3)
    
    # Apply to L channel only
    lab[:, :, 0] = np.clip(lab[:, :, 0] * scaling_factor, 0, 255)
    
    normalized = cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2BGR)
    
    logger.debug(f"Applied tone normalization: factor={scaling_factor:.3f}")
    return normalized, float(scaling_factor)


def preprocess_image(pil_image: Image.Image, save_path: Optional[str] = None) -> Tuple[np.ndarray, PreprocessingReport]:
    """
    Complete preprocessing pipeline.
    
    Args:
        pil_image: Input PIL image
        save_path: Optional path to save preprocessed image
        
    Returns:
        Tuple of (preprocessed_array, preprocessing_report)
    """
    # Convert to BGR for OpenCV
    image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    
    # 1. Geometric standardization
    image = center_crop_and_resize(image, settings.target_size)
    
    # 2. White balance
    image = apply_white_balance(image)
    
    # 3. Glare detection and handling
    glare_mask, glare_coverage = detect_glare(image)
    if glare_coverage > 0.01:  # Inpaint if >1% glare
        image = inpaint_glare(image, glare_mask)
    
    # 4. Skin tone estimation
    tone_cluster, lab_mean = estimate_skin_tone(image)
    
    # 5. Tone normalization for fairness
    image, scaling_factor = apply_tone_normalization(image, tone_cluster, lab_mean)
    
    # 6. CLAHE enhancement
    image = apply_clahe(image)
    
    # Save if requested
    if save_path:
        cv2.imwrite(save_path, image)
        logger.info(f"Saved preprocessed image to {save_path}")
    
    # Create report
    report = PreprocessingReport(
        tone_cluster=tone_cluster,
        lab_mean=lab_mean.tolist(),
        scaling_factor=scaling_factor,
        glare_mask_coverage=glare_coverage
    )
    
    logger.info(f"Preprocessing complete: tone_cluster={tone_cluster}, glare={glare_coverage:.3f}")
    
    # Convert back to RGB
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    return image_rgb, report
