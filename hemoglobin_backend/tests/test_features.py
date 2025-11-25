"""
Unit tests for feature extraction.
"""
import pytest
import numpy as np
from app.services.feature_extraction import (
    extract_color_features,
    extract_texture_features,
    extract_vascular_features,
    extract_all_features
)


def create_test_roi(size=(256, 256)):
    """Create a test ROI image."""
    # Create gradient image for more realistic features
    roi = np.zeros((size[0], size[1], 3), dtype=np.uint8)
    
    for i in range(size[0]):
        for j in range(size[1]):
            roi[i, j] = [
                int(150 + 50 * i / size[0]),
                int(130 + 30 * j / size[1]),
                int(140 + 40 * (i + j) / (size[0] + size[1]))
            ]
    
    return roi


def test_extract_color_features():
    """Test color feature extraction."""
    roi = create_test_roi()
    
    features = extract_color_features(roi)
    
    # Check all fields exist
    assert hasattr(features, 'mean_L')
    assert hasattr(features, 'mean_R')
    assert hasattr(features, 'ratio_R_G')
    
    # Check value ranges
    assert 0 <= features.mean_L <= 255
    assert 0 <= features.mean_R <= 255
    assert features.ratio_R_G > 0


def test_extract_texture_features():
    """Test texture feature extraction."""
    roi = create_test_roi()
    
    features = extract_texture_features(roi)
    
    # Check all fields exist
    assert hasattr(features, 'glcm_contrast')
    assert hasattr(features, 'glcm_homogeneity')
    assert hasattr(features, 'lbp_uniformity')
    assert hasattr(features, 'fft_highfreq_power')
    
    # Check value ranges
    assert features.glcm_contrast >= 0
    assert 0 <= features.glcm_homogeneity <= 1
    assert 0 <= features.lbp_uniformity <= 1


def test_extract_vascular_features():
    """Test vascular feature extraction."""
    roi = create_test_roi()
    
    features = extract_vascular_features(roi)
    
    # Check all fields exist
    assert hasattr(features, 'vessel_density')
    assert hasattr(features, 'mean_thickness')
    assert hasattr(features, 'orientation_entropy')
    
    # Check value ranges
    assert 0 <= features.vessel_density <= 1
    assert features.mean_thickness >= 0
    assert features.orientation_entropy >= 0


def test_extract_all_features():
    """Test complete feature extraction."""
    roi = create_test_roi()
    
    features = extract_all_features(roi)
    
    # Check all feature groups exist
    assert hasattr(features, 'color')
    assert hasattr(features, 'texture')
    assert hasattr(features, 'vascular')
    
    # Spot check some values
    assert features.color.mean_L > 0
    assert features.texture.glcm_contrast >= 0
    assert 0 <= features.vascular.vessel_density <= 1
