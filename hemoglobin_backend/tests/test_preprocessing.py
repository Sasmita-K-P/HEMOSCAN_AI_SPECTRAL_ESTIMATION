"""
Unit tests for preprocessing pipeline.
"""
import pytest
import numpy as np
from PIL import Image
import cv2
from app.services.preprocessing import (
    center_crop_and_resize,
    apply_white_balance,
    detect_glare,
    estimate_skin_tone,
    preprocess_image
)


def create_test_image(size=(512, 512), color=(180, 140, 140)):
    """Create a test image array."""
    img_array = np.full((size[0], size[1], 3), color, dtype=np.uint8)
    return img_array


def test_center_crop_and_resize():
    """Test center crop and resize."""
    # Rectangular image
    img = create_test_image(size=(600, 400))
    
    resized = center_crop_and_resize(img, target_size=256)
    
    assert resized.shape == (256, 256, 3)


def test_apply_white_balance():
    """Test white balance correction."""
    img = create_test_image()
    img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    
    balanced = apply_white_balance(img_bgr)
    
    assert balanced.shape == img_bgr.shape
    assert balanced.dtype == np.uint8


def test_detect_glare():
    """Test glare detection."""
    img = create_test_image()
    
    # Add bright spot (glare)
    img[100:150, 100:150] = [250, 250, 250]
    img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    
    glare_mask, coverage = detect_glare(img_bgr)
    
    assert glare_mask.shape == (512, 512)
    assert 0 <= coverage <= 1
    assert coverage > 0  # Should detect the bright spot


def test_estimate_skin_tone():
    """Test skin tone estimation."""
    img = create_test_image()
    img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    
    cluster_id, lab_mean = estimate_skin_tone(img_bgr)
    
    assert 0 <= cluster_id < 5
    assert len(lab_mean) == 3
    assert 0 <= lab_mean[0] <= 255  # L channel


def test_preprocess_image():
    """Test complete preprocessing pipeline."""
    pil_image = Image.fromarray(create_test_image())
    
    preprocessed, report = preprocess_image(pil_image)
    
    # Check output shape
    assert preprocessed.shape == (512, 512, 3)
    
    # Check report
    assert hasattr(report, 'tone_cluster')
    assert hasattr(report, 'lab_mean')
    assert hasattr(report, 'scaling_factor')
    assert hasattr(report, 'glare_mask_coverage')
    
    assert 0 <= report.tone_cluster < 5
    assert len(report.lab_mean) == 3
    assert 0 < report.scaling_factor < 2
    assert 0 <= report.glare_mask_coverage <= 1
