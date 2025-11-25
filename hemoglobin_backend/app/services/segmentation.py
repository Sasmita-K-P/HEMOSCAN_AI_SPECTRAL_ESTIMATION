"""
Nail-bed segmentation service with mask post-processing and ROI extraction.
"""
import cv2
import numpy as np
from typing import Tuple, Optional
from pathlib import Path
from app.models.unet import get_unet_model
from app.schemas import SegmentationReport
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def threshold_mask(mask: np.ndarray, threshold: float = 0.5) -> np.ndarray:
    """
    Binarize predicted mask.
    
    Args:
        mask: Predicted mask (H, W) with values 0-1
        threshold: Binarization threshold
        
    Returns:
        Binary mask (H, W) with values 0 or 255
    """
    binary_mask = (mask > threshold).astype(np.uint8) * 255
    return binary_mask


def clean_mask(mask: np.ndarray) -> np.ndarray:
    """
    Clean mask using morphological operations and component analysis.
    
    Args:
        mask: Binary mask (H, W), values 0 or 255
        
    Returns:
        Cleaned binary mask
    """
    # Morphological opening (remove small noise)
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_open)
    
    # Keep only largest connected component
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
    
    if num_labels > 1:
        # Find largest component (excluding background)
        largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
        mask = (labels == largest_label).astype(np.uint8) * 255
    
    # Morphological closing (smooth edges)
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close)
    
    logger.debug("Cleaned segmentation mask")
    return mask


def extract_roi(image: np.ndarray, mask: np.ndarray, padding: int = 10) -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
    """
    Extract ROI based on mask bounding box.
    
    Args:
        image: Original image (H, W, 3)
        mask: Binary mask (H, W)
        padding: Pixels to extend beyond mask
        
    Returns:
        Tuple of (roi_image, bbox) where bbox is (x, y, w, h)
    """
    # Find bounding box
    coords = cv2.findNonZero(mask)
    if coords is None:
        logger.warning("No mask found, using center crop")
        h, w = image.shape[:2]
        size = min(h, w) // 2
        x, y = w // 2 - size // 2, h // 2 - size // 2
        return image[y:y+size, x:x+size], (x, y, size, size)
    
    x, y, w, h = cv2.boundingRect(coords)
    
    # Add padding
    x = max(0, x - padding)
    y = max(0, y - padding)
    w = min(image.shape[1] - x, w + 2 * padding)
    h = min(image.shape[0] - y, h + 2 * padding)
    
    roi = image[y:y+h, x:x+w]
    
    logger.debug(f"Extracted ROI: bbox=({x}, {y}, {w}, {h})")
    return roi, (x, y, w, h)


def resize_roi(roi: np.ndarray, target_size: int) -> np.ndarray:
    """
    Resize ROI to target size, maintaining aspect ratio with padding.
    
    Args:
        roi: ROI image
        target_size: Target dimension
        
    Returns:
        Resized ROI (target_size, target_size, 3)
    """
    h, w = roi.shape[:2]
    
    # Compute scaling to fit within target_size
    scale = target_size / max(h, w)
    new_h, new_w = int(h * scale), int(w * scale)
    
    resized = cv2.resize(roi, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
    
    # Pad to square
    pad_h = (target_size - new_h) // 2
    pad_w = (target_size - new_w) // 2
    
    padded = cv2.copyMakeBorder(
        resized,
        pad_h, target_size - new_h - pad_h,
        pad_w, target_size - new_w - pad_w,
        cv2.BORDER_CONSTANT,
        value=[0, 0, 0]
    )
    
    return padded


def generate_pseudo_mask(image: np.ndarray) -> np.ndarray:
    """
    Generate pseudo mask using classical CV (for training when labels unavailable).
    
    Args:
        image: Preprocessed image (H, W, 3), RGB
        
    Returns:
        Pseudo binary mask (H, W)
    """
    # Convert to HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    
    # Nail beds typically have low saturation and mid-high value
    lower = np.array([0, 0, 80])
    upper = np.array([180, 80, 255])
    
    mask = cv2.inRange(hsv, lower, upper)
    
    # Find largest contour in center region
    h, w = mask.shape
    center_mask = np.zeros_like(mask)
    center_mask[h//4:3*h//4, w//4:3*w//4] = 255
    mask = cv2.bitwise_and(mask, center_mask)
    
    # Clean
    mask = clean_mask(mask)
    
    logger.debug("Generated pseudo mask")
    return mask


def segment_nail_bed(
    image: np.ndarray,
    save_dir: Optional[Path] = None,
    scan_id: Optional[str] = None
) -> Tuple[np.ndarray, np.ndarray, SegmentationReport]:
    """
    Complete nail-bed segmentation pipeline.
    
    Args:
        image: Preprocessed image (H, W, 3), RGB, 0-255
        save_dir: Optional directory to save outputs
        scan_id: Scan ID for file naming
        
    Returns:
        Tuple of (roi_image, mask, segmentation_report)
    """
    # Get UNet model
    unet = get_unet_model()
    
    # Predict mask
    mask_pred = unet.predict(image)
    
    # Threshold and clean
    mask_binary = threshold_mask(mask_pred, threshold=0.5)
    mask_clean = clean_mask(mask_binary)
    
    # Estimate IOU (using mask coverage as proxy)
    coverage = np.sum(mask_clean > 0) / mask_clean.size
    iou_estimate = min(coverage * 2, 0.95)  # Heuristic
    
    # Extract ROI
    roi, bbox = extract_roi(image, mask_clean, padding=10)
    roi_resized = resize_roi(roi, settings.roi_size)
    
    # Save outputs
    mask_path = ""
    roi_path = ""
    
    if save_dir and scan_id:
        save_dir.mkdir(parents=True, exist_ok=True)
        
        mask_path = str(save_dir / f"{scan_id}_mask.png")
        cv2.imwrite(mask_path, mask_clean)
        
        roi_path = str(save_dir / f"{scan_id}_roi.png")
        roi_bgr = cv2.cvtColor(roi_resized, cv2.COLOR_RGB2BGR)
        cv2.imwrite(roi_path, roi_bgr)
        
        logger.info(f"Saved segmentation outputs: {mask_path}, {roi_path}")
    
    # Create report
    report = SegmentationReport(
        iou_estimate=float(iou_estimate),
        mask_path=mask_path,
        roi_path=roi_path
    )
    
    logger.info(f"Segmentation complete: IOU={iou_estimate:.3f}, ROI shape={roi_resized.shape}")
    
    return roi_resized, mask_clean, report
