"""
Nail polish detection service.
Detects if nails are painted to ensure accurate hemoglobin estimation.
"""
import numpy as np
import cv2
from PIL import Image
import io
from typing import Dict, Tuple
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class NailPolishDetectionError(Exception):
    """Exception raised when nail polish is detected."""
    pass


def detect_nail_polish(file_bytes: bytes, hand_info: dict) -> Dict:
    """
    Detect if nails are painted by analyzing color characteristics.
    
    Args:
        file_bytes: Raw image bytes
        hand_info: Hand detection info (currently not used, but available for future enhancement)
        
    Returns:
        Detection result dict with:
        - is_painted: bool - Whether nail polish is detected
        - confidence: float - Confidence score (0-1)
        - reason: str - Reason for detection
        - metrics: dict - Detailed metrics
        
    Raises:
        NailPolishDetectionError: If nails appear to be painted
    """
    try:
        # Load image
        img = Image.open(io.BytesIO(file_bytes))
        img_array = np.array(img.convert('RGB'))
        
        # Convert to HSV color space for better color analysis
        hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
        
        # Analyze the central region (where fingertips typically are)
        # This is a simplified approach - in production, you'd use hand_info to locate exact fingertips
        height, width = hsv.shape[:2]
        center_y_start = int(height * 0.3)
        center_y_end = int(height * 0.7)
        center_x_start = int(width * 0.3)
        center_x_end = int(width * 0.7)
        
        roi = hsv[center_y_start:center_y_end, center_x_start:center_x_end]
        
        # Extract HSV channels
        h_channel = roi[:, :, 0]  # Hue (0-179 in OpenCV)
        s_channel = roi[:, :, 1]  # Saturation (0-255)
        v_channel = roi[:, :, 2]  # Value/Brightness (0-255)
        
        # Normalize to 0-1 range
        s_norm = s_channel / 255.0
        v_norm = v_channel / 255.0
        
        # Calculate metrics
        mean_saturation = float(np.mean(s_norm))
        mean_value = float(np.mean(v_norm))
        std_saturation = float(np.std(s_norm))
        
        # Calculate hue distribution
        # Natural nails are typically in red/pink range (0-30° or 330-360°)
        # In OpenCV, hue is 0-179 (half of 0-360)
        h_normalized = h_channel / 179.0 * 360.0  # Convert to 0-360 degrees
        
        # Count pixels in biological hue range (red/pink: 0-30° or 330-360°)
        biological_hue_mask = ((h_normalized >= 0) & (h_normalized <= 30)) | \
                             ((h_normalized >= 330) & (h_normalized <= 360))
        biological_hue_ratio = float(np.sum(biological_hue_mask) / biological_hue_mask.size)
        
        # Detection logic
        is_painted = False
        reasons = []
        confidence = 0.0
        
        # Threshold 1: High saturation (bright colors)
        if mean_saturation > 0.4:
            is_painted = True
            reasons.append(f"high saturation ({mean_saturation:.2f})")
            confidence = max(confidence, mean_saturation)
        
        # Threshold 2: Very low saturation with high uniformity (could be dark polish)
        if mean_saturation < 0.15 and std_saturation < 0.05 and mean_value < 0.3:
            is_painted = True
            reasons.append(f"dark uniform color (V={mean_value:.2f})")
            confidence = max(confidence, 0.7)
        
        # Threshold 3: Non-biological hue (not red/pink)
        if mean_saturation > 0.25 and biological_hue_ratio < 0.3:
            is_painted = True
            reasons.append(f"non-biological hue (bio_ratio={biological_hue_ratio:.2f})")
            confidence = max(confidence, 0.8)
        
        # Threshold 4: Very bright/neon colors
        if mean_value > 0.85 and mean_saturation > 0.5:
            is_painted = True
            reasons.append(f"bright neon color (V={mean_value:.2f}, S={mean_saturation:.2f})")
            confidence = max(confidence, 0.9)
        
        # Threshold 5: Very uniform high saturation (typical of polish)
        if mean_saturation > 0.35 and std_saturation < 0.08:
            is_painted = True
            reasons.append(f"uniform high saturation (std={std_saturation:.2f})")
            confidence = max(confidence, 0.75)
        
        result = {
            'is_painted': is_painted,
            'confidence': confidence,
            'reason': ', '.join(reasons) if reasons else 'natural nails detected',
            'metrics': {
                'mean_saturation': mean_saturation,
                'std_saturation': std_saturation,
                'mean_value': mean_value,
                'biological_hue_ratio': biological_hue_ratio
            }
        }
        
        if is_painted:
            logger.warning(f"Nail polish detected: {result['reason']}")
        else:
            logger.info(f"Natural nails detected (S={mean_saturation:.2f}, V={mean_value:.2f})")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in nail polish detection: {e}")
        # Return a safe default - assume natural nails if detection fails
        return {
            'is_painted': False,
            'confidence': 0.0,
            'reason': f'detection failed: {str(e)}',
            'metrics': {}
        }
