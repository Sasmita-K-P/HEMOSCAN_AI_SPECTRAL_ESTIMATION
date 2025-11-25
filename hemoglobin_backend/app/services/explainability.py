"""
Explainability service with Grad-CAM and SHAP.
"""
import tensorflow as tf
import numpy as np
import cv2
from typing import List, Optional
import base64
from io import BytesIO
from PIL import Image
from app.schemas import Explainability, FeatureImportance
from app.models.hb_predictor import get_hb_model
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def compute_gradcam(
    model: tf.keras.Model,
    image: np.ndarray,
    features: np.ndarray,
    layer_name: str = None
) -> np.ndarray:
    """
    Compute Grad-CAM heatmap for the image pathway.
    
    Args:
        model: Trained model
        image: Input image (1, H, W, 3), normalized
        features: Tabular features (1, F)
        layer_name: Target layer name (if None, uses last conv layer)
        
    Returns:
        Heatmap array (H, W)
    """
    # Find last convolutional layer if not specified
    if layer_name is None:
        for layer in reversed(model.layers):
            if 'conv' in layer.name.lower():
                layer_name = layer.name
                break
    
    if layer_name is None:
        logger.warning("No convolutional layer found for Grad-CAM")
        return np.zeros(image.shape[1:3])
    
    # Create gradient model
    grad_model = tf.keras.Model(
        inputs=model.inputs,
        outputs=[
            model.get_layer(layer_name).output,
            model.output[0]  # Regression output
        ]
    )
    
    # Compute gradients
    with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model([image, features])
        loss = predictions[0, 0]
    
    # Get gradients of the loss w.r.t. conv layer output
    grads = tape.gradient(loss, conv_outputs)
    
    # Global average pooling of gradients
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    
    # Weight the channels by the gradients
    conv_outputs = conv_outputs[0]
    pooled_grads = pooled_grads.numpy()
    conv_outputs = conv_outputs.numpy()
    
    for i in range(pooled_grads.shape[0]):
        conv_outputs[:, :, i] *= pooled_grads[i]
    
    # Average across channels
    heatmap = np.mean(conv_outputs, axis=-1)
    
    # Normalize to [0, 1]
    heatmap = np.maximum(heatmap, 0)
    if heatmap.max() > 0:
        heatmap /= heatmap.max()
    
    logger.debug(f"Computed Grad-CAM on layer: {layer_name}")
    return heatmap


def overlay_heatmap(
    image: np.ndarray,
    heatmap: np.ndarray,
    alpha: float = 0.4,
    colormap: int = cv2.COLORMAP_JET
) -> np.ndarray:
    """
    Overlay heatmap on image.
    
    Args:
        image: Original image (H, W, 3), RGB, 0-255
        heatmap: Heatmap (H', W'), 0-1
        alpha: Overlay transparency
        colormap: OpenCV colormap
        
    Returns:
        Overlaid image (H, W, 3), RGB, 0-255
    """
    # Resize heatmap to match image
    heatmap_resized = cv2.resize(heatmap, (image.shape[1], image.shape[0]))
    
    # Convert to uint8
    heatmap_uint8 = (heatmap_resized * 255).astype(np.uint8)
    
    # Apply colormap
    heatmap_colored = cv2.applyColorMap(heatmap_uint8, colormap)
    heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)
    
    # Overlay
    overlaid = cv2.addWeighted(image, 1 - alpha, heatmap_colored, alpha, 0)
    
    return overlaid


def image_to_base64(image: np.ndarray) -> str:
    """
    Convert numpy image to base64 string.
    
    Args:
        image: Image array (H, W, 3), RGB, 0-255
        
    Returns:
        Base64-encoded PNG string
    """
    pil_image = Image.fromarray(image.astype(np.uint8))
    buffer = BytesIO()
    pil_image.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"


def compute_shap_importance(
    features: dict,
    prediction: float,
    baseline_prediction: float = 12.0
) -> List[FeatureImportance]:
    """
    Compute simplified SHAP-like feature importance.
    (Full SHAP requires training data; this is a placeholder approximation)
    
    Args:
        features: Feature dictionary
        prediction: Model prediction
        baseline_prediction: Baseline (average) prediction
        
    Returns:
        List of FeatureImportance objects
    """
    # Simplified approach: compute correlation-based importance
    # In production, use proper SHAP with background dataset
    
    color = features['color']
    texture = features['texture']
    vascular = features['vascular']
    
    # Heuristic importance based on clinical knowledge
    # Lower L*, lower R/G, lower vessel density → lower Hb
    importances = [
        FeatureImportance(
            name="mean_L",
            shap_value=float((color['mean_L'] - 180) / 180 * (prediction - baseline_prediction))
        ),
        FeatureImportance(
            name="ratio_R_G",
            shap_value=float((color['ratio_R_G'] - 1.0) * (prediction - baseline_prediction))
        ),
        FeatureImportance(
            name="vessel_density",
            shap_value=float((vascular['vessel_density'] - 0.15) * 10 * (prediction - baseline_prediction))
        ),
        FeatureImportance(
            name="mean_a",
            shap_value=float((color['mean_a'] - 128) / 128 * (prediction - baseline_prediction))
        ),
        FeatureImportance(
            name="glcm_contrast",
            shap_value=float((texture['glcm_contrast'] - 1.0) * (prediction - baseline_prediction) * 0.5)
        ),
    ]
    
    # Sort by absolute value
    importances.sort(key=lambda x: abs(x.shap_value), reverse=True)
    
    logger.debug(f"Computed feature importances: top={importances[0].name}")
    return importances[:5]  # Top 5


def generate_explainability(
    roi_image: np.ndarray,
    features: dict,
    prediction: float
) -> Explainability:
    """
    Generate complete explainability outputs.
    
    Args:
        roi_image: ROI image (H, W, 3), RGB, 0-255
        features: Feature dictionary
        prediction: Predicted Hb value
        
    Returns:
        Explainability object
    """
    # Get model
    hb_model = get_hb_model()
    
    # Prepare inputs
    image_norm = roi_image.astype(np.float32) / 255.0
    image_batch = np.expand_dims(image_norm, axis=0)
    
    feature_array = hb_model.features_to_array(features)
    feature_batch = np.expand_dims(feature_array, axis=0)
    
    # Compute Grad-CAM
    try:
        heatmap = compute_gradcam(hb_model.model, image_batch, feature_batch)
        overlaid = overlay_heatmap(roi_image, heatmap, alpha=0.5)
        gradcam_base64 = image_to_base64(overlaid)
    except Exception as e:
        logger.error(f"Grad-CAM failed: {e}")
        gradcam_base64 = None
    
    # Compute feature importance
    top_features = compute_shap_importance(features, prediction)
    
    explainability = Explainability(
        gradcam_nail_overlay=gradcam_base64,
        top_features=top_features
    )
    
    logger.info("Generated explainability outputs")
    return explainability
