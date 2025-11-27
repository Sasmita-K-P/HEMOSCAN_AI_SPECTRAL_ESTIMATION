"""
Input validation for uploaded images.
"""
from pathlib import Path
from typing import Tuple, Optional
from PIL import Image
import io
from app.config import settings
from app.utils.logger import setup_logger
from app.services.hand_detector import validate_hand_in_image, HandDetectionError
from app.services.nail_polish_detector import detect_nail_polish, NailPolishDetectionError

logger = setup_logger(__name__)

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png'}
ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png'}


class ValidationError(Exception):
    """Custom exception for validation failures."""
    pass


def validate_file_type(file_bytes: bytes, filename: str) -> None:
    """
    Validate file type and extension.
    
    Args:
        file_bytes: Raw file bytes
        filename: Original filename
        
    Raises:
        ValidationError: If file type is invalid
    """
    # Check extension
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Invalid file extension: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check MIME type (using python-magic would require libmagic, using PIL instead)
    try:
        img = Image.open(io.BytesIO(file_bytes))
        mime_type = f"image/{img.format.lower()}"
        if mime_type not in ALLOWED_MIME_TYPES:
            raise ValidationError(f"Invalid MIME type: {mime_type}")
    except Exception as e:
        raise ValidationError(f"Cannot read image file: {str(e)}")
    
    logger.info(f"File type validated: {filename} ({mime_type})")


def validate_file_size(file_bytes: bytes) -> None:
    """
    Validate file size.
    
    Args:
        file_bytes: Raw file bytes
        
    Raises:
        ValidationError: If file is too large
    """
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > settings.max_upload_size_mb:
        raise ValidationError(
            f"File too large: {size_mb:.2f} MB. Maximum: {settings.max_upload_size_mb} MB"
        )
    
    logger.info(f"File size validated: {size_mb:.2f} MB")


def validate_image_resolution(file_bytes: bytes) -> Tuple[int, int]:
    """
    Validate image resolution and return dimensions.
    
    Args:
        file_bytes: Raw file bytes
        
    Returns:
        Tuple of (width, height)
        
    Raises:
        ValidationError: If resolution is too low
    """
    try:
        img = Image.open(io.BytesIO(file_bytes))
        width, height = img.size
        
        min_dimension = 512
        if width < min_dimension or height < min_dimension:
            raise ValidationError(
                f"Image resolution too low: {width}x{height}. "
                f"Minimum: {min_dimension}x{min_dimension}"
            )
        
        logger.info(f"Image resolution validated: {width}x{height}")
        return width, height
        
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Cannot read image dimensions: {str(e)}")


def validate_image_integrity(file_bytes: bytes) -> Image.Image:
    """
    Validate image can be loaded and is not corrupted.
    
    Args:
        file_bytes: Raw file bytes
        
    Returns:
        PIL Image object
        
    Raises:
        ValidationError: If image is corrupted
    """
    try:
        img = Image.open(io.BytesIO(file_bytes))
        img.verify()  # Verify integrity
        
        # Reload after verify (verify closes the file)
        img = Image.open(io.BytesIO(file_bytes))
        img.load()  # Force load to catch truncated images
        
        logger.info("Image integrity validated")
        return img
        
    except Exception as e:
        raise ValidationError(f"Corrupted or unreadable image: {str(e)}")


def validate_hand_presence(file_bytes: bytes) -> dict:
    """
    Validate that the image contains a hand/fingers.
    
    Args:
        file_bytes: Raw file bytes
        
    Returns:
        Hand detection info dictionary
        
    Raises:
        ValidationError: If no hand is detected
    """
    try:
        detection_info = validate_hand_in_image(file_bytes)
        logger.info(f"Hand presence validated: {detection_info}")
        return detection_info
    except HandDetectionError as e:
        # Convert HandDetectionError to ValidationError for consistency
        raise ValidationError(str(e))
    except Exception as e:
        logger.error(f"Hand validation failed: {e}")
        raise ValidationError(f"Failed to validate hand presence: {str(e)}")


def validate_no_nail_polish(file_bytes: bytes, hand_info: dict) -> None:
    """
    Validate that nails are not painted.
    
    Args:
        file_bytes: Raw file bytes
        hand_info: Hand detection info
        
    Raises:
        ValidationError: If nail polish is detected
    """
    try:
        result = detect_nail_polish(file_bytes, hand_info)
        if result['is_painted']:
            raise ValidationError(
                f"Nail polish detected ({result['reason']}). "
                "Please remove nail polish for accurate hemoglobin estimation."
            )
        logger.info(f"Nail polish check passed: {result['reason']}")
    except NailPolishDetectionError as e:
        raise ValidationError(str(e))
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Nail polish validation failed: {e}")
        # Don't block the user if detection fails - log and continue
        logger.warning("Nail polish detection failed, continuing with analysis")


def validate_upload(file_bytes: bytes, filename: str) -> Tuple[Image.Image, dict]:
    """
    Complete validation pipeline for uploaded image.
    
    Args:
        file_bytes: Raw file bytes
        filename: Original filename
        
    Returns:
        Tuple of (validated PIL Image object, hand_detection_info)
        
    Raises:
        ValidationError: If any validation fails
    """
    # Step 1: File type and format validation
    validate_file_type(file_bytes, filename)
    
    # Step 2: File size validation
    validate_file_size(file_bytes)
    
    # Step 3: Resolution validation
    validate_image_resolution(file_bytes)
    
    # Step 4: Hand detection validation
    hand_info = validate_hand_presence(file_bytes)
    
    # Step 5: Nail polish detection (NEW)
    validate_no_nail_polish(file_bytes, hand_info)
    
    # Step 6: Image integrity validation
    img = validate_image_integrity(file_bytes)
    
    logger.info(f"Upload validation complete: {filename}")
    return img, hand_info
