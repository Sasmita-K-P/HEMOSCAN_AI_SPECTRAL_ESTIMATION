"""
Hemoglobin prediction model with dual-pathway architecture and uncertainty quantification.
"""
import tensorflow as tf
import keras
from keras import layers
import numpy as np
from pathlib import Path
from typing import Tuple, Dict
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def build_cnn_backbone(input_shape: Tuple[int, int, int] = (256, 256, 3)) -> keras.Model:
    """
    Build CNN backbone for image feature extraction.
    Using EfficientNetB0 as base.
    
    Args:
        input_shape: Input image shape
        
    Returns:
        Feature extraction model
    """
    base_model = keras.applications.EfficientNetB0(
        include_top=False,
        weights='imagenet',
        input_shape=input_shape,
        pooling='avg'
    )
    
    # Fine-tune last few layers
    for layer in base_model.layers[:-20]:
        layer.trainable = False
    
    return base_model


def build_mlp_backbone(input_dim: int = 18) -> keras.Model:
    """
    Build MLP backbone for tabular features.
    
    Args:
        input_dim: Number of input features
        
    Returns:
        Feature extraction model
    """
    inputs = keras.Input(shape=(input_dim,))
    
    x = layers.Dense(128, activation='relu')(inputs)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(64, activation='relu')(x)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(32, activation='relu')(x)
    
    model = keras.Model(inputs=inputs, outputs=x)
    return model


def build_hb_predictor(
    image_shape: Tuple[int, int, int] = (256, 256, 3),
    tabular_dim: int = 18
) -> keras.Model:
    """
    Build complete hemoglobin prediction model with dual pathways.
    
    Args:
        image_shape: Input image shape
        tabular_dim: Number of tabular features
        
    Returns:
        Compiled model with regression and classification heads
    """
    # Image pathway
    image_input = keras.Input(shape=image_shape, name='image_input')
    cnn_backbone = build_cnn_backbone(image_shape)
    image_features = cnn_backbone(image_input)
    
    # Tabular pathway
    tabular_input = keras.Input(shape=(tabular_dim,), name='tabular_input')
    mlp_backbone = build_mlp_backbone(tabular_dim)
    tabular_features = mlp_backbone(tabular_input)
    
    # Fusion
    combined = layers.concatenate([image_features, tabular_features])
    
    x = layers.Dense(128, activation='relu')(combined)
    x = layers.Dropout(0.4)(x, training=True)  # Always on for MC Dropout
    x = layers.Dense(64, activation='relu')(x)
    x = layers.Dropout(0.4)(x, training=True)
    
    # Regression head (Hb in g/dL)
    hb_output = layers.Dense(1, activation='linear', name='hb_regression')(x)
    
    # Classification head (anemia stage: 0=normal, 1=mild, 2=moderate, 3=severe)
    anemia_output = layers.Dense(4, activation='softmax', name='anemia_classification')(x)
    
    model = keras.Model(
        inputs=[image_input, tabular_input],
        outputs=[hb_output, anemia_output]
    )
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=1e-4),
        loss={
            'hb_regression': 'mse',
            'anemia_classification': 'sparse_categorical_crossentropy'
        },
        loss_weights={
            'hb_regression': 1.0,
            'anemia_classification': 0.5
        },
        metrics={
            'hb_regression': ['mae', 'mse'],
            'anemia_classification': ['accuracy']
        }
    )
    
    logger.info(f"Built Hb predictor model: {model.count_params()} parameters")
    return model


class HbPredictor:
    """Wrapper class for hemoglobin prediction with uncertainty."""
    
    def __init__(self, model_path: Path = None):
        """
        Initialize Hb predictor.
        
        Args:
            model_path: Path to trained model weights
        """
        self.model = None
        self.model_path = model_path or settings.hb_model_path
        
        if self.model_path.exists():
            self.load_model()
        else:
            logger.warning(f"Hb model not found at {self.model_path}. Using placeholder.")
            self.model = build_hb_predictor()
    
    def load_model(self):
        """Load trained model weights."""
        try:
            self.model = keras.models.load_model(str(self.model_path))
            logger.info(f"Loaded Hb model from {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load Hb model: {e}")
            logger.warning("Using untrained model")
            self.model = build_hb_predictor()
    
    def features_to_array(self, features: Dict) -> np.ndarray:
        """
        Convert feature dict to numpy array.
        
        Args:
            features: Features object (as dict)
            
        Returns:
            Feature array (18,)
        """
        color = features['color']
        texture = features['texture']
        vascular = features['vascular']
        
        feature_array = np.array([
            color['mean_L'],
            color['mean_a'],
            color['mean_b'],
            color['mean_R'],
            color['mean_G'],
            color['mean_B'],
            color['ratio_R_G'],
            color['ratio_R_B'],
            texture['glcm_contrast'],
            texture['glcm_homogeneity'],
            texture['glcm_energy'],
            texture['lbp_uniformity'],
            texture['fft_highfreq_power'],
            vascular['vessel_density'],
            vascular['mean_thickness'],
            vascular['orientation_entropy'],
            color['std_L'],
            color['ratio_a_L']
        ], dtype=np.float32)
        
        return feature_array
    
    def predict_with_uncertainty(
        self,
        roi_image: np.ndarray,
        features: Dict,
        n_passes: int = None
    ) -> Tuple[float, float, float, np.ndarray]:
        """
        Predict Hb with uncertainty using MC Dropout.
        
        Args:
            roi_image: ROI image (H, W, 3), RGB, 0-255
            features: Feature dict
            n_passes: Number of MC dropout passes
            
        Returns:
            Tuple of (hb_mean, hb_std, uncertainty, anemia_probs)
        """
        n_passes = n_passes or settings.mc_dropout_passes
        
        # Prepare inputs
        image_norm = roi_image.astype(np.float32) / 255.0
        image_batch = np.expand_dims(image_norm, axis=0)
        
        feature_array = self.features_to_array(features)
        feature_batch = np.expand_dims(feature_array, axis=0)
        
        # Multiple forward passes
        hb_predictions = []
        anemia_predictions = []
        
        for _ in range(n_passes):
            hb_pred, anemia_pred = self.model.predict(
                [image_batch, feature_batch],
                verbose=0
            )
            hb_predictions.append(hb_pred[0, 0])
            anemia_predictions.append(anemia_pred[0])
        
        # Compute statistics
        hb_predictions = np.array(hb_predictions)
        hb_mean = float(np.mean(hb_predictions))
        hb_std = float(np.std(hb_predictions))
        
        # Uncertainty score (normalized std)
        uncertainty = min(hb_std / (hb_mean + 1e-6), 1.0)
        
        # Average anemia probabilities
        anemia_probs = np.mean(anemia_predictions, axis=0)
        
        logger.debug(
            f"Prediction: Hb={hb_mean:.2f}±{hb_std:.2f} g/dL, "
            f"uncertainty={uncertainty:.3f}"
        )
        
        return hb_mean, hb_std, uncertainty, anemia_probs


# Global model instance
_hb_model = None

def get_hb_model() -> HbPredictor:
    """Get global Hb predictor instance."""
    global _hb_model
    if _hb_model is None:
        _hb_model = HbPredictor()
    return _hb_model
