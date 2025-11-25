"""
Hand detection service for validating uploaded images contain hands/fingers.
"""
import cv2
import numpy as np
import mediapipe as mp
from typing import Tuple, Dict, Optional
from PIL import Image
import io
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands_detector = mp_hands.Hands(
    static_image_mode=True,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)


class HandDetectionError(Exception):
    """Custom exception for hand detection failures."""
    pass


def detect_hand_mediapipe(image: np.ndarray) -> Tuple[bool, float, Dict]:
    """
    Detect hands using MediaPipe Hands.
    
    Args:
        image: Input image (RGB format, numpy array)
        
    Returns:
        Tuple of (hand_detected, confidence, detection_info)
    """
    try:
        # Process image with MediaPipe
        results = hands_detector.process(image)
        
        if results.multi_hand_landmarks:
            num_hands = len(results.multi_hand_landmarks)
            
            # Get confidence from handedness
            confidences = []
            if results.multi_handedness:
                for hand_info in results.multi_handedness:
                    confidences.append(hand_info.classification[0].score)
            
            avg_confidence = np.mean(confidences) if confidences else 0.7
            
            detection_info = {
                'num_hands': num_hands,
                'confidence': float(avg_confidence),
                'landmarks_detected': True,
                'method': 'mediapipe'
            }
            
            logger.info(f"Hand detected: {num_hands} hand(s), confidence: {avg_confidence:.3f}")
            return True, float(avg_confidence), detection_info
        else:
            detection_info = {
                'num_hands': 0,
                'confidence': 0.0,
                'landmarks_detected': False,
                'method': 'mediapipe'
            }
            logger.warning("No hands detected in image")
            return False, 0.0, detection_info
            
    except Exception as e:
        logger.error(f"MediaPipe hand detection failed: {e}")
        # Fall back to skin detection
        return detect_skin_fallback(image)


def detect_skin_fallback(image: np.ndarray) -> Tuple[bool, float, Dict]:
    """
    Fallback skin detection using color space analysis.
    
    Args:
        image: Input image (RGB format)
        
    Returns:
        Tuple of (skin_detected, confidence, detection_info)
    """
    try:
        # Convert to different color spaces
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        ycrcb = cv2.cvtColor(image, cv2.COLOR_RGB2YCrCb)
        
        # HSV skin detection (works for various skin tones)
        lower_hsv = np.array([0, 20, 70], dtype=np.uint8)
        upper_hsv = np.array([20, 255, 255], dtype=np.uint8)
        mask_hsv = cv2.inRange(hsv, lower_hsv, upper_hsv)
        
        # YCrCb skin detection (more robust)
        lower_ycrcb = np.array([0, 133, 77], dtype=np.uint8)
        upper_ycrcb = np.array([255, 173, 127], dtype=np.uint8)
        mask_ycrcb = cv2.inRange(ycrcb, lower_ycrcb, upper_ycrcb)
        
        # Combine masks
        skin_mask = cv2.bitwise_or(mask_hsv, mask_ycrcb)
        
        # Calculate skin percentage
        skin_pixels = np.sum(skin_mask > 0)
        total_pixels = skin_mask.size
        skin_percentage = skin_pixels / total_pixels
        
        # Require at least 15% skin pixels
        is_skin_detected = skin_percentage > 0.15
        
        detection_info = {
            'num_hands': 1 if is_skin_detected else 0,
            'confidence': float(skin_percentage),
            'skin_percentage': float(skin_percentage),
            'landmarks_detected': False,
            'method': 'skin_detection_fallback'
        }
        
        logger.info(f"Skin detection: {skin_percentage:.3f} skin coverage, detected: {is_skin_detected}")
        return is_skin_detected, float(skin_percentage), detection_info
        
    except Exception as e:
        logger.error(f"Skin detection failed: {e}")
        return False, 0.0, {'error': str(e), 'method': 'failed'}


def validate_hand_in_image(file_bytes: bytes) -> Dict:
    """
    Validate that the uploaded image contains a hand.
    
    Args:
        file_bytes: Raw image bytes
        
    Returns:
        Detection info dictionary
        
    Raises:
        HandDetectionError: If no hand is detected
    """
    try:
        # Convert bytes to PIL Image
        pil_image = Image.open(io.BytesIO(file_bytes))
        
        # Convert to RGB numpy array
        image_rgb = np.array(pil_image.convert('RGB'))
        
        # Detect hand
        hand_detected, confidence, detection_info = detect_hand_mediapipe(image_rgb)
        
        if not hand_detected:
            raise HandDetectionError(
                "No hand detected in the image. Please upload a clear image showing your hand or fingers. "
                "Ensure good lighting and that your hand is clearly visible."
            )
        
        # Warn if confidence is low
        if confidence < 0.6:
            logger.warning(f"Low confidence hand detection: {confidence:.3f}")
            detection_info['warning'] = "Hand detected but with low confidence. Image quality may affect results."
        
        # Warn if multiple hands
        if detection_info.get('num_hands', 0) > 1:
            logger.warning(f"Multiple hands detected: {detection_info['num_hands']}")
            detection_info['warning'] = "Multiple hands detected. Using the first detected hand for analysis."
        
        logger.info(f"Hand validation passed: {detection_info}")
        return detection_info
        
    except HandDetectionError:
        raise
    except Exception as e:
        logger.error(f"Hand validation error: {e}")
        raise HandDetectionError(
            f"Failed to validate image: {str(e)}. Please ensure you're uploading a valid image file."
        )


def check_finger_visibility(image: np.ndarray, landmarks) -> bool:
    """
    Check if fingertips are visible (for nail bed analysis).
    
    Args:
        image: Input image
        landmarks: MediaPipe hand landmarks
        
    Returns:
        True if fingertips are visible
    """
    # MediaPipe landmark indices for fingertips
    fingertip_indices = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky
    
    if not landmarks:
        return False
    
    # Check if at least 3 fingertips are detected
    visible_tips = 0
    for tip_idx in fingertip_indices:
        if tip_idx < len(landmarks.landmark):
            landmark = landmarks.landmark[tip_idx]
            # Check if landmark is within image bounds and visible
            if 0 <= landmark.x <= 1 and 0 <= landmark.y <= 1 and landmark.visibility > 0.5:
                visible_tips += 1
    
    return visible_tips >= 3


def get_hand_region_bbox(image: np.ndarray, landmarks) -> Optional[Tuple[int, int, int, int]]:
    """
    Get bounding box of hand region from landmarks.
    
    Args:
        image: Input image
        landmarks: MediaPipe hand landmarks
        
    Returns:
        Tuple of (x, y, w, h) or None
    """
    if not landmarks:
        return None
    
    h, w = image.shape[:2]
    
    x_coords = [lm.x * w for lm in landmarks.landmark]
    y_coords = [lm.y * h for lm in landmarks.landmark]
    
    x_min = int(min(x_coords))
    x_max = int(max(x_coords))
    y_min = int(min(y_coords))
    y_max = int(max(y_coords))
    
    # Add padding
    padding = 20
    x_min = max(0, x_min - padding)
    y_min = max(0, y_min - padding)
    x_max = min(w, x_max + padding)
    y_max = min(h, y_max + padding)
    
    return (x_min, y_min, x_max - x_min, y_max - y_min)
