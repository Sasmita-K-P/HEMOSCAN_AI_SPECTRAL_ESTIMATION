"""
Mock GradCAM generator for visualization when trained model is not available.
Creates realistic-looking heatmaps based on color analysis.
"""
import numpy as np
import cv2
from typing import Tuple
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def generate_mock_gradcam_heatmap(roi_image: np.ndarray, features: dict) -> np.ndarray:
    """
    Generate a mock GradCAM-style heatmap based on color and vascular features.
    
    This creates a realistic visualization showing which regions of the nail bed
    are most important for the prediction, based on:
    - Red channel intensity (blood oxygenation)
    - Color saturation (vascular visibility)
    - Lightness variation (nail bed vs background)
    
    Args:
        roi_image: ROI image (H, W, 3), RGB, 0-255
        features: Feature dictionary with color and vascular data
        
    Returns:
        Heatmap array (H, W), values 0-1
    """
    try:
        # Convert to different color spaces for analysis
        hsv = cv2.cvtColor(roi_image, cv2.COLOR_RGB2HSV)
        lab = cv2.cvtColor(roi_image, cv2.COLOR_RGB2LAB)
        
        # Extract channels
        h, s, v = cv2.split(hsv)
        l, a, b = cv2.split(lab)
        r, g, blue = cv2.split(roi_image)
        
        # Normalize to 0-1
        s_norm = s.astype(np.float32) / 255.0
        v_norm = v.astype(np.float32) / 255.0
        r_norm = r.astype(np.float32) / 255.0
        l_norm = l.astype(np.float32) / 255.0
        
        # Create importance map based on multiple factors
        
        # Factor 1: Red channel (blood oxygenation indicator)
        # Higher red = more important
        red_importance = r_norm
        
        # Factor 2: Saturation (vascular visibility)
        # Higher saturation = more important
        sat_importance = s_norm
        
        # Factor 3: Inverse lightness (darker = more blood = more important)
        # Lower L* = more important
        dark_importance = 1.0 - (l_norm / 255.0)
        
        # Factor 4: Red/Green ratio
        rg_ratio = np.divide(r_norm, g.astype(np.float32) / 255.0 + 1e-6)
        rg_importance = np.clip(rg_ratio / 2.0, 0, 1)
        
        # Combine factors with weights matching the mock prediction formula
        heatmap = (
            red_importance * 0.5 +      # Red channel weight
            sat_importance * 0.3 +       # Saturation weight
            dark_importance * 0.45 +     # Darkness (inverse L*) weight
            rg_importance * 0.32         # R/G ratio weight
        )
        
        # Normalize to 0-1
        heatmap = heatmap / heatmap.max() if heatmap.max() > 0 else heatmap
        
        # Apply Gaussian blur for smoother visualization
        heatmap = cv2.GaussianBlur(heatmap, (15, 15), 0)
        
        # Create a center-focused mask (nail bed is typically in center)
        height, width = heatmap.shape
        y, x = np.ogrid[:height, :width]
        center_y, center_x = height // 2, width // 2
        
        # Distance from center
        dist_from_center = np.sqrt((x - center_x)**2 + (y - center_y)**2)
        max_dist = np.sqrt(center_x**2 + center_y**2)
        center_mask = 1.0 - (dist_from_center / max_dist)
        center_mask = np.clip(center_mask, 0.3, 1.0)  # Don't completely zero out edges
        
        # Apply center focus
        heatmap = heatmap * center_mask
        
        # Enhance contrast
        heatmap = np.power(heatmap, 0.8)  # Gamma correction
        
        # Final normalization
        heatmap = (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min() + 1e-6)
        
        logger.info(f"Generated mock GradCAM heatmap (shape: {heatmap.shape}, range: {heatmap.min():.3f}-{heatmap.max():.3f})")
        return heatmap
        
    except Exception as e:
        logger.error(f"Error generating mock GradCAM: {e}")
        # Return a simple center-focused heatmap as fallback
        height, width = roi_image.shape[:2]
        y, x = np.ogrid[:height, :width]
        center_y, center_x = height // 2, width // 2
        heatmap = np.exp(-((x - center_x)**2 + (y - center_y)**2) / (2 * (min(height, width) / 4)**2))
        return heatmap
