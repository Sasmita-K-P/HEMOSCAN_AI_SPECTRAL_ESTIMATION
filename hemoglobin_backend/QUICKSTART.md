# Quick Start Guide

## Installation

```bash
cd hemoglobin_backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
copy .env.example .env
```

## Running the Server

```bash
# Development mode
uvicorn app.main:app --reload

# Access API docs
# http://localhost:8000/docs
```

## Testing the API

```bash
# Using curl
curl -X POST "http://localhost:8000/api/v1/scan" \
  -F "file=@test_image.jpg"

# Using Python
import requests

with open('nail_image.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/scan',
        files={'file': f}
    )
    print(response.json())
```

## Running Tests

```bash
pytest tests/ -v
```

## Next Steps

1. **Train models** - Place trained weights in `data/models/`
2. **Configure .env** - Update thresholds and paths
3. **Deploy** - See README.md for deployment options

## Key Files

- `app/main.py` - Application entry point
- `app/routes/scan.py` - API endpoints
- `app/config.py` - Configuration
- `README.md` - Full documentation
- `walkthrough.md` - Implementation details
