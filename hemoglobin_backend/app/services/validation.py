"""
Input validation for uploaded images.
"""
from pathlib import Path
from typing import Tuple, Optional
from PIL import Image
import io
from app.config import settings
from app.utils.logger import setup_logger

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


def validate_upload(file_bytes: bytes, filename: str) -> Image.Image:
    """
    Complete validation pipeline for uploaded image.
    
    Args:
        file_bytes: Raw file bytes
        filename: Original filename
        
    Returns:
        Validated PIL Image object
        
    Raises:
        ValidationError: If any validation fails
    """
    validate_file_type(file_bytes, filename)
    validate_file_size(file_bytes)
    validate_image_resolution(file_bytes)
    img = validate_image_integrity(file_bytes)
    
    logger.info(f"Upload validation complete: {filename}")
    return img
