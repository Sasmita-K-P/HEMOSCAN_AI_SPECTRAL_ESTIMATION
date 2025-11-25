# Clinical Hemoglobin Estimation Backend

A production-ready FastAPI backend for camera-based hemoglobin estimation and anemia risk prediction using nail-bed images.

## Features

- **Clinical-Grade Quality Control**: Automated image quality assessment (sharpness, brightness, contrast)
- **Fairness-Aware Preprocessing**: Skin-tone normalization to ensure unbiased predictions
- **Deep Learning Pipeline**: UNet segmentation + dual-pathway (CNN + MLP) hemoglobin prediction
- **Uncertainty Quantification**: MC Dropout for confidence estimation
- **Explainability**: Grad-CAM visualizations and feature importance
- **Clinical Reporting**: Automated PDF report generation
- **Production Ready**: Monitoring, logging, security, and database storage

## Architecture

```
┌─────────────┐
│   Upload    │
│   Image     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Validation  │ ─── File type, size, resolution
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Quality QC  │ ─── Sharpness, brightness, contrast
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Preprocessing│ ─── White balance, CLAHE, glare removal, tone normalization
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Segmentation │ ─── UNet nail-bed segmentation
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Features   │ ─── Color (LAB, RGB), Texture (GLCM, LBP), Vascular (Frangi)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Prediction  │ ─── Dual-pathway model (CNN + MLP) with MC Dropout
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Explainability│ ─── Grad-CAM + SHAP feature importance
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Report    │ ─── Clinical PDF report
└─────────────┘
```

## Installation

### Prerequisites

- Python 3.9+
- pip

### Setup

```bash
# Clone or navigate to the project directory
cd hemoglobin_backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt

# Copy environment template
copy .env.example .env

# Edit .env with your configuration
```

## Configuration

Edit `.env` file to configure:

- **Model paths**: Point to your trained UNet and Hb predictor models
- **Thresholds**: QC thresholds, uncertainty threshold, anemia thresholds
- **Storage**: Upload and processed data directories
- **Database**: Database URL (SQLite by default)
- **Security**: Encryption settings

## Running the Server

### Development

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Access the API:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health
- **Metrics**: http://localhost:8000/metrics

## API Endpoints

### POST /api/v1/scan

Upload and analyze nail-bed image.

**Request:**
- Multipart form data with `file` field (JPEG/PNG image)

**Response:**
```json
{
  "scan_id": "uuid",
  "timestamp": "2025-11-25T10:50:00Z",
  "quality": {
    "sharpness": 57.2,
    "brightness": 128.5,
    "contrast": 31.4,
    "quality_pass": true,
    "fail_reasons": []
  },
  "preprocessing": {
    "tone_cluster": 2,
    "lab_mean": [180.0, 128.0, 132.0],
    "scaling_factor": 0.95,
    "glare_mask_coverage": 0.02
  },
  "segmentation": {
    "iou_estimate": 0.88,
    "mask_path": "...",
    "roi_path": "..."
  },
  "features": { ... },
  "prediction": {
    "hb_g_per_dl": 11.2,
    "hb_ci_95": [10.5, 11.9],
    "uncertainty": 0.35,
    "anemia_stage": "mild",
    "risk_score": 0.72
  },
  "explainability": {
    "gradcam_nail_overlay": "data:image/png;base64,...",
    "top_features": [...]
  },
  "version": {
    "preprocess": "1.0.0",
    "unet": "1.0.0",
    "hb_model": "1.0.0"
  }
}
```

### GET /api/v1/scan/{scan_id}

Retrieve scan results by ID.

### GET /api/v1/report/{scan_id}

Download clinical PDF report.

## Model Training

The backend expects trained models at the paths specified in `.env`:

- **UNet Model**: `./data/models/unet_v1.0.0.h5`
- **Hb Predictor**: `./data/models/hb_predictor_v1.0.0.h5`

Training scripts are provided in the `training/` directory:

```bash
# Train UNet segmentation model
python training/train_unet.py --data_dir /path/to/nail_dataset

# Train hemoglobin prediction model
python training/train_hb_model.py --data_dir /path/to/hb_dataset

# Evaluate models
python training/evaluate.py --model_path /path/to/model
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py -v
```

## Monitoring

The backend exposes Prometheus metrics at `/metrics`:

- `scan_requests_total`: Total scan requests by status
- `scan_duration_seconds`: Processing time by pipeline stage
- `qc_failures_total`: QC failures by reason
- `prediction_uncertainty`: Distribution of prediction uncertainties
- `feature_drift_score`: Feature distribution drift detection

## Security & Privacy

- **No PHI in logs**: All logging is anonymized
- **UUID scan IDs**: No personally identifiable information
- **Optional encryption**: File encryption at rest
- **HTTPS recommended**: Use reverse proxy (nginx/traefik) in production

## Frontend Integration

The backend is designed to work with Flutter/React frontends. Example integration:

```javascript
// Upload image
const formData = new FormData();
formData.append('file', imageFile);

const response = await fetch('http://localhost:8000/api/v1/scan', {
  method: 'POST',
  body: formData
});

const result = await response.json();

// Check quality
if (!result.quality.quality_pass) {
  showError(result.quality.fail_reasons);
  return;
}

// Check prediction
if (result.prediction.uncertainty_flag) {
  showWarning(result.prediction.message);
  return;
}

// Display results
displayHemoglobin(result.prediction.hb_g_per_dl);
displayAnemiaStage(result.prediction.anemia_stage);
displayGradCAM(result.explainability.gradcam_nail_overlay);

// Download report
window.open(`http://localhost:8000/api/v1/report/${result.scan_id}`);
```

## License

This project is for research and educational purposes. Consult with legal and medical professionals before deploying in clinical settings.

## Disclaimer

**This is not a medical device.** The hemoglobin estimates are for screening purposes only and should not replace laboratory testing. Always confirm with a complete blood count (CBC) test and consult qualified healthcare professionals.
