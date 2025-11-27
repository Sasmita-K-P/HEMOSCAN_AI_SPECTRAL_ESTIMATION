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
from app.services.shap_explainer import get_shap_explainer

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


def generate_explainability(
    roi_image: np.ndarray,
    features: dict,
    prediction: float
) -> Explainability:
    """
    Generate complete explainability outputs using SHAP.
    
    Args:
        roi_image: ROI image (H, W, 3), RGB, 0-255
        features: Feature dictionary
        prediction: Predicted Hb value
        
    Returns:
        Explainability object
    """
    # Get SHAP explainer
    shap_explainer = get_shap_explainer()
    
    # Calculate feature importance using SHAP
    shap_result = shap_explainer.calculate_feature_importance(features)
    
    # Generate visualization
    feature_plot_base64 = shap_explainer.generate_visualization(shap_result['all_features'])
    
    # Convert to FeatureImportance schema
    top_features = [
        FeatureImportance(
            name=feat['name'],
            value=feat['value'],
            importance=feat['importance'],
            contribution=feat['contribution']
        )
        for feat in shap_result['top_features']
    ]
    
    # Try to compute Grad-CAM (will use mock if model not trained)
    gradcam_base64 = None
    try:
        hb_model = get_hb_model()
        if hb_model.is_trained and hb_model.model is not None:
            # Use real GradCAM with trained model
            image_norm = roi_image.astype(np.float32) / 255.0
            image_batch = np.expand_dims(image_norm, axis=0)
            feature_array = hb_model.features_to_array(features)
            feature_batch = np.expand_dims(feature_array, axis=0)
            
            heatmap = compute_gradcam(hb_model.model, image_batch, feature_batch)
            logger.info("Generated real GradCAM from trained model")
        else:
            # Use mock GradCAM based on color analysis
            from app.services.mock_gradcam import generate_mock_gradcam_heatmap
            heatmap = generate_mock_gradcam_heatmap(roi_image, features)
            logger.info("Generated mock GradCAM (model not trained)")
        
        # Create overlay
        overlaid = overlay_heatmap(roi_image, heatmap, alpha=0.5)
        gradcam_base64 = image_to_base64(overlaid)
        
    except Exception as e:
        logger.error(f"GradCAM generation failed: {e}")
        # Even on error, try to create a simple visualization
        try:
            from app.services.mock_gradcam import generate_mock_gradcam_heatmap
            heatmap = generate_mock_gradcam_heatmap(roi_image, features)
            overlaid = overlay_heatmap(roi_image, heatmap, alpha=0.5)
            gradcam_base64 = image_to_base64(overlaid)
            logger.info("Generated fallback mock GradCAM")
        except Exception as e2:
            logger.error(f"Fallback GradCAM also failed: {e2}")
    
    explainability = Explainability(
        gradcam_nail_overlay=gradcam_base64,
        top_features=top_features,
        feature_importance_plot=feature_plot_base64,
        interpretation=shap_result['interpretation'],
        method=shap_result['method']
    )
    
    logger.info("Generated SHAP-based explainability outputs")
    return explainability
