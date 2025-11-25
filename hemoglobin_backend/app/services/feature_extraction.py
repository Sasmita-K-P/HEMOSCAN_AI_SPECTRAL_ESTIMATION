"""
Multi-modal feature extraction: color, texture, and vascularity.
"""
import cv2
import numpy as np
from skimage.feature import graycomatrix, graycoprops, local_binary_pattern
from typing import Dict, Any
from app.schemas import ColorFeatures, TextureFeatures, VascularFeatures, Features
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def extract_color_features(roi: np.ndarray, mask: np.ndarray = None) -> ColorFeatures:
    """
    Extract color-based features from ROI.
    
    Args:
        roi: ROI image (H, W, 3), RGB, 0-255
        mask: Optional binary mask to restrict analysis
        
    Returns:
        ColorFeatures object
    """
    # Convert to different color spaces
    lab = cv2.cvtColor(roi, cv2.COLOR_RGB2LAB)
    hsv = cv2.cvtColor(roi, cv2.COLOR_RGB2HSV)
    
    # Apply mask if provided
    if mask is not None:
        mask_resized = cv2.resize(mask, (roi.shape[1], roi.shape[0])) > 0
        roi_masked = roi[mask_resized]
        lab_masked = lab[mask_resized]
    else:
        roi_masked = roi.reshape(-1, 3)
        lab_masked = lab.reshape(-1, 3)
    
    # RGB statistics
    mean_R = float(np.mean(roi_masked[:, 0]))
    mean_G = float(np.mean(roi_masked[:, 1]))
    mean_B = float(np.mean(roi_masked[:, 2]))
    
    # LAB statistics
    mean_L = float(np.mean(lab_masked[:, 0]))
    mean_a = float(np.mean(lab_masked[:, 1]))
    mean_b = float(np.mean(lab_masked[:, 2]))
    
    std_L = float(np.std(lab_masked[:, 0]))
    std_a = float(np.std(lab_masked[:, 1]))
    std_b = float(np.std(lab_masked[:, 2]))
    
    # Color ratios
    ratio_R_G = mean_R / (mean_G + 1e-6)
    ratio_R_B = mean_R / (mean_B + 1e-6)
    ratio_a_L = mean_a / (mean_L + 1e-6)
    
    features = ColorFeatures(
        mean_L=mean_L,
        mean_a=mean_a,
        mean_b=mean_b,
        mean_R=mean_R,
        mean_G=mean_G,
        mean_B=mean_B,
        std_L=std_L,
        std_a=std_a,
        std_b=std_b,
        ratio_R_G=ratio_R_G,
        ratio_R_B=ratio_R_B,
        ratio_a_L=ratio_a_L
    )
    
    logger.debug(f"Extracted color features: mean_L={mean_L:.2f}, ratio_R_G={ratio_R_G:.3f}")
    return features


def extract_texture_features(roi: np.ndarray, mask: np.ndarray = None) -> TextureFeatures:
    """
    Extract texture-based features from ROI.
    
    Args:
        roi: ROI image (H, W, 3), RGB, 0-255
        mask: Optional binary mask
        
    Returns:
        TextureFeatures object
    """
    # Convert to grayscale
    gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
    
    # GLCM features
    # Quantize to reduce computation
    gray_quantized = (gray // 16).astype(np.uint8)
    
    # Compute GLCM for multiple angles
    distances = [1]
    angles = [0, np.pi/4, np.pi/2, 3*np.pi/4]
    glcm = graycomatrix(
        gray_quantized,
        distances=distances,
        angles=angles,
        levels=16,
        symmetric=True,
        normed=True
    )
    
    # Aggregate across angles
    glcm_contrast = float(np.mean(graycoprops(glcm, 'contrast')))
    glcm_homogeneity = float(np.mean(graycoprops(glcm, 'homogeneity')))
    glcm_energy = float(np.mean(graycoprops(glcm, 'energy')))
    glcm_entropy = float(-np.sum(glcm * np.log2(glcm + 1e-10)))
    
    # LBP features
    radius = 3
    n_points = 8 * radius
    lbp = local_binary_pattern(gray, n_points, radius, method='uniform')
    lbp_hist, _ = np.histogram(lbp.ravel(), bins=n_points + 2, range=(0, n_points + 2), density=True)
    lbp_uniformity = float(np.sum(lbp_hist ** 2))
    
    # FFT features (high frequency power)
    f_transform = np.fft.fft2(gray)
    f_shift = np.fft.fftshift(f_transform)
    magnitude = np.abs(f_shift)
    
    h, w = magnitude.shape
    center_h, center_w = h // 2, w // 2
    radius_fft = min(h, w) // 4
    
    y, x = np.ogrid[:h, :w]
    mask_high_freq = ((x - center_w)**2 + (y - center_h)**2) > radius_fft**2
    fft_highfreq_power = float(np.mean(magnitude[mask_high_freq]))
    
    features = TextureFeatures(
        glcm_contrast=glcm_contrast,
        glcm_homogeneity=glcm_homogeneity,
        glcm_energy=glcm_energy,
        glcm_entropy=glcm_entropy,
        lbp_uniformity=lbp_uniformity,
        fft_highfreq_power=fft_highfreq_power
    )
    
    logger.debug(f"Extracted texture features: GLCM contrast={glcm_contrast:.3f}, LBP uniformity={lbp_uniformity:.3f}")
    return features


def frangi_filter(image: np.ndarray, scale_range=(1, 3), scale_step=1) -> np.ndarray:
    """
    Apply Frangi vesselness filter to enhance vessel-like structures.
    
    Args:
        image: Grayscale image
        scale_range: Range of scales (sigma values)
        scale_step: Step between scales
        
    Returns:
        Vesselness response image
    """
    from skimage.filters import frangi
    
    vessel_response = frangi(
        image,
        sigmas=range(scale_range[0], scale_range[1] + 1, scale_step),
        black_ridges=False
    )
    
    return vessel_response


def extract_vascular_features(roi: np.ndarray, mask: np.ndarray = None) -> VascularFeatures:
    """
    Extract vascularity-based features from ROI.
    
    Args:
        roi: ROI image (H, W, 3), RGB, 0-255
        mask: Optional binary mask
        
    Returns:
        VascularFeatures object
    """
    # Use green channel (better vessel contrast)
    green_channel = roi[:, :, 1]
    
    # Apply Frangi filter
    vessel_response = frangi_filter(green_channel, scale_range=(1, 4), scale_step=1)
    
    # Threshold to get vessel mask
    threshold = np.percentile(vessel_response, 90)  # Top 10%
    vessel_mask = vessel_response > threshold
    
    # Vessel density
    vessel_density = float(np.sum(vessel_mask) / vessel_mask.size)
    
    # Vessel thickness (using distance transform on vessel mask)
    if np.sum(vessel_mask) > 0:
        dist_transform = cv2.distanceTransform(vessel_mask.astype(np.uint8), cv2.DIST_L2, 5)
        mean_thickness = float(np.mean(dist_transform[vessel_mask]))
    else:
        mean_thickness = 0.0
    
    # Vessel orientation entropy
    # Compute gradients
    sobelx = cv2.Sobel(green_channel, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(green_channel, cv2.CV_64F, 0, 1, ksize=3)
    orientations = np.arctan2(sobely, sobelx)
    
    # Histogram of orientations (only in vessel regions)
    if np.sum(vessel_mask) > 0:
        vessel_orientations = orientations[vessel_mask]
        hist, _ = np.histogram(vessel_orientations, bins=18, range=(-np.pi, np.pi), density=True)
        # Entropy
        hist = hist + 1e-10
        orientation_entropy = float(-np.sum(hist * np.log2(hist)))
    else:
        orientation_entropy = 0.0
    
    features = VascularFeatures(
        vessel_density=vessel_density,
        mean_thickness=mean_thickness,
        orientation_entropy=orientation_entropy
    )
    
    logger.debug(f"Extracted vascular features: density={vessel_density:.3f}, thickness={mean_thickness:.2f}")
    return features


def extract_all_features(roi: np.ndarray, mask: np.ndarray = None) -> Features:
    """
    Extract complete feature set from ROI.
    
    Args:
        roi: ROI image (H, W, 3), RGB, 0-255
        mask: Optional binary mask
        
    Returns:
        Features object with all feature types
    """
    color_features = extract_color_features(roi, mask)
    texture_features = extract_texture_features(roi, mask)
    vascular_features = extract_vascular_features(roi, mask)
    
    features = Features(
        color=color_features,
        texture=texture_features,
        vascular=vascular_features
    )
    
    logger.info("Extracted all features successfully")
    return features
