"""
Unit tests for API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.models import Base, engine
import io
from PIL import Image
import numpy as np

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_database():
    """Setup test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def create_test_image(size=(512, 512), color=(200, 150, 150)):
    """Create a test image."""
    img_array = np.full((size[0], size[1], 3), color, dtype=np.uint8)
    img = Image.fromarray(img_array)
    
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    return img_bytes


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data


def test_scan_upload_valid_image(setup_database):
    """Test scan upload with valid image."""
    img_bytes = create_test_image()
    
    response = client.post(
        "/api/v1/scan",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "scan_id" in data
    assert "quality" in data
    assert "timestamp" in data
    
    # Check QC report
    assert "sharpness" in data["quality"]
    assert "brightness" in data["quality"]
    assert "quality_pass" in data["quality"]


def test_scan_upload_invalid_file():
    """Test scan upload with invalid file type."""
    # Create a text file
    text_bytes = io.BytesIO(b"This is not an image")
    
    response = client.post(
        "/api/v1/scan",
        files={"file": ("test.txt", text_bytes, "text/plain")}
    )
    
    assert response.status_code == 400


def test_scan_upload_small_image():
    """Test scan upload with too small image."""
    img_bytes = create_test_image(size=(100, 100))
    
    response = client.post(
        "/api/v1/scan",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    
    assert response.status_code == 400


def test_get_scan_not_found():
    """Test retrieving non-existent scan."""
    response = client.get("/api/v1/scan/nonexistent-id")
    assert response.status_code == 404


def test_get_scan_existing(setup_database):
    """Test retrieving existing scan."""
    # First create a scan
    img_bytes = create_test_image()
    create_response = client.post(
        "/api/v1/scan",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    
    assert create_response.status_code == 200
    scan_id = create_response.json()["scan_id"]
    
    # Now retrieve it
    get_response = client.get(f"/api/v1/scan/{scan_id}")
    assert get_response.status_code == 200
    
    data = get_response.json()
    assert data["scan_id"] == scan_id


def test_get_report(setup_database):
    """Test report generation."""
    # First create a scan
    img_bytes = create_test_image()
    create_response = client.post(
        "/api/v1/scan",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    
    assert create_response.status_code == 200
    scan_id = create_response.json()["scan_id"]
    
    # Get report
    report_response = client.get(f"/api/v1/report/{scan_id}")
    assert report_response.status_code == 200
    assert report_response.headers["content-type"] == "application/pdf"


def test_metrics_endpoint():
    """Test Prometheus metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "scan_requests_total" in response.text
