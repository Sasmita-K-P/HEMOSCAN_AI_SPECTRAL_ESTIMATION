"""
UNet model architecture for nail-bed segmentation.
"""
import tensorflow as tf
import keras
from keras import layers
from typing import Tuple
import numpy as np
from pathlib import Path
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def dice_coefficient(y_true, y_pred, smooth=1e-6):
    """
    Dice coefficient metric for segmentation.
    
    Args:
        y_true: Ground truth masks
        y_pred: Predicted masks
        smooth: Smoothing factor
        
    Returns:
        Dice score
    """
    y_true_f = keras.backend.flatten(y_true)
    y_pred_f = keras.backend.flatten(y_pred)
    intersection = keras.backend.sum(y_true_f * y_pred_f)
    return (2. * intersection + smooth) / (keras.backend.sum(y_true_f) + keras.backend.sum(y_pred_f) + smooth)


def dice_loss(y_true, y_pred):
    """Dice loss for training."""
    return 1 - dice_coefficient(y_true, y_pred)


def combined_loss(y_true, y_pred):
    """Combined Dice + Binary Cross-Entropy loss."""
    bce = keras.losses.binary_crossentropy(y_true, y_pred)
    dice = dice_loss(y_true, y_pred)
    return bce + dice


def iou_metric(y_true, y_pred, threshold=0.5):
    """
    Intersection over Union metric.
    
    Args:
        y_true: Ground truth masks
        y_pred: Predicted masks
        threshold: Threshold for binarization
        
    Returns:
        IOU score
    """
    y_pred = tf.cast(y_pred > threshold, tf.float32)
    intersection = tf.reduce_sum(y_true * y_pred)
    union = tf.reduce_sum(y_true) + tf.reduce_sum(y_pred) - intersection
    return intersection / (union + 1e-6)


def build_unet(input_shape: Tuple[int, int, int] = (512, 512, 3), num_classes: int = 1) -> keras.Model:
    """
    Build UNet architecture for nail-bed segmentation.
    
    Args:
        input_shape: Input image shape (H, W, C)
        num_classes: Number of output classes (1 for binary)
        
    Returns:
        Compiled Keras model
    """
    inputs = keras.Input(shape=input_shape)
    
    # Encoder
    c1 = layers.Conv2D(64, (3, 3), activation='relu', padding='same')(inputs)
    c1 = layers.Conv2D(64, (3, 3), activation='relu', padding='same')(c1)
    p1 = layers.MaxPooling2D((2, 2))(c1)
    
    c2 = layers.Conv2D(128, (3, 3), activation='relu', padding='same')(p1)
    c2 = layers.Conv2D(128, (3, 3), activation='relu', padding='same')(c2)
    p2 = layers.MaxPooling2D((2, 2))(c2)
    
    c3 = layers.Conv2D(256, (3, 3), activation='relu', padding='same')(p2)
    c3 = layers.Conv2D(256, (3, 3), activation='relu', padding='same')(c3)
    p3 = layers.MaxPooling2D((2, 2))(c3)
    
    c4 = layers.Conv2D(512, (3, 3), activation='relu', padding='same')(p3)
    c4 = layers.Conv2D(512, (3, 3), activation='relu', padding='same')(c4)
    p4 = layers.MaxPooling2D((2, 2))(c4)
    
    # Bottleneck
    c5 = layers.Conv2D(1024, (3, 3), activation='relu', padding='same')(p4)
    c5 = layers.Conv2D(1024, (3, 3), activation='relu', padding='same')(c5)
    
    # Decoder
    u6 = layers.Conv2DTranspose(512, (2, 2), strides=(2, 2), padding='same')(c5)
    u6 = layers.concatenate([u6, c4])
    c6 = layers.Conv2D(512, (3, 3), activation='relu', padding='same')(u6)
    c6 = layers.Conv2D(512, (3, 3), activation='relu', padding='same')(c6)
    
    u7 = layers.Conv2DTranspose(256, (2, 2), strides=(2, 2), padding='same')(c6)
    u7 = layers.concatenate([u7, c3])
    c7 = layers.Conv2D(256, (3, 3), activation='relu', padding='same')(u7)
    c7 = layers.Conv2D(256, (3, 3), activation='relu', padding='same')(c7)
    
    u8 = layers.Conv2DTranspose(128, (2, 2), strides=(2, 2), padding='same')(c7)
    u8 = layers.concatenate([u8, c2])
    c8 = layers.Conv2D(128, (3, 3), activation='relu', padding='same')(u8)
    c8 = layers.Conv2D(128, (3, 3), activation='relu', padding='same')(c8)
    
    u9 = layers.Conv2DTranspose(64, (2, 2), strides=(2, 2), padding='same')(c8)
    u9 = layers.concatenate([u9, c1])
    c9 = layers.Conv2D(64, (3, 3), activation='relu', padding='same')(u9)
    c9 = layers.Conv2D(64, (3, 3), activation='relu', padding='same')(c9)
    
    outputs = layers.Conv2D(num_classes, (1, 1), activation='sigmoid')(c9)
    
    model = keras.Model(inputs=[inputs], outputs=[outputs])
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=1e-4),
        loss=combined_loss,
        metrics=[dice_coefficient, iou_metric]
    )
    
    logger.info(f"Built UNet model: {model.count_params()} parameters")
    return model


class UNetSegmenter:
    """Wrapper class for UNet inference."""
    
    def __init__(self, model_path: Path = None):
        """
        Initialize UNet segmenter.
        
        Args:
            model_path: Path to trained model weights
        """
        self.model = None
        self.model_path = model_path or settings.unet_model_path
        
        if self.model_path.exists():
            self.load_model()
        else:
            logger.warning(f"UNet model not found at {self.model_path}. Using placeholder.")
            self.model = build_unet()
    
    def load_model(self):
        """Load trained model weights."""
        try:
            self.model = keras.models.load_model(
                str(self.model_path),
                custom_objects={
                    'combined_loss': combined_loss,
                    'dice_coefficient': dice_coefficient,
                    'iou_metric': iou_metric
                }
            )
            logger.info(f"Loaded UNet model from {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load UNet model: {e}")
            logger.warning("Using untrained model")
            self.model = build_unet()
    
    def predict(self, image: np.ndarray) -> np.ndarray:
        """
        Predict segmentation mask.
        
        Args:
            image: Preprocessed image (H, W, 3), RGB, 0-255
            
        Returns:
            Binary mask (H, W), values 0-1
        """
        # Normalize to [0, 1]
        image_norm = image.astype(np.float32) / 255.0
        
        # Add batch dimension
        image_batch = np.expand_dims(image_norm, axis=0)
        
        # Predict
        mask_pred = self.model.predict(image_batch, verbose=0)[0, :, :, 0]
        
        logger.debug(f"Predicted mask: shape={mask_pred.shape}, range=[{mask_pred.min():.3f}, {mask_pred.max():.3f}]")
        return mask_pred


# Global model instance (lazy loaded)
_unet_model = None

def get_unet_model() -> UNetSegmenter:
    """Get global UNet model instance."""
    global _unet_model
    if _unet_model is None:
        _unet_model = UNetSegmenter()
    return _unet_model
