# Backend + Frontend Integration Guide

## 📁 Backend Location

**Your backend is saved at:**
```
C:\Users\saskp\.gemini\antigravity\scratch\hemoglobin_backend\
```

## 📂 Complete Backend Structure

```
hemoglobin_backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    ⭐ Main FastAPI application
│   ├── config.py                  ⚙️ Configuration settings
│   ├── schemas.py                 📋 Request/Response models
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   └── scan.py               🌐 API endpoints
│   │
│   ├── models/
│   │   ├── unet.py               🧠 UNet segmentation model
│   │   └── hb_predictor.py       🧠 Hemoglobin prediction model
│   │
│   ├── services/
│   │   ├── validation.py         ✅ Input validation
│   │   ├── quality_control.py    🔍 QC metrics
│   │   ├── preprocessing.py      🎨 Image preprocessing
│   │   ├── segmentation.py       ✂️ Nail-bed segmentation
│   │   ├── feature_extraction.py 📊 Feature extraction
│   │   ├── prediction.py         🎯 Hb prediction
│   │   ├── explainability.py     💡 Grad-CAM + SHAP
│   │   └── report_generator.py   📄 PDF reports
│   │
│   ├── database/
│   │   ├── models.py             💾 Database models
│   │   └── crud.py               💾 Database operations
│   │
│   └── utils/
│       ├── logger.py             📝 Logging
│       ├── security.py           🔒 Security utilities
│       └── monitoring.py         📈 Metrics
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api.py               🧪 API tests
│   ├── test_preprocessing.py     🧪 Preprocessing tests
│   └── test_features.py          🧪 Feature tests
│
├── data/
│   ├── uploads/                  📤 Uploaded images
│   ├── processed/                🔄 Processed outputs
│   └── models/                   🧠 Model weights (.h5 files)
│
├── requirements.txt              📦 Dependencies
├── requirements-dev.txt          📦 Dev dependencies
├── .env.example                  ⚙️ Config template
├── .gitignore
├── README.md                     📖 Full documentation
└── QUICKSTART.md                 🚀 Quick start guide
```

## 🎯 Your Frontend Location

**Your React frontend is at:**
```
C:\Users\saskp\OneDrive\Desktop\.antigravity\
```

I can see from your screenshot it's a **React + TypeScript + Vite + Tailwind** project!

## 🔗 How to Run Both Together

### Step 1: Start the Backend

```bash
# Open Terminal 1
cd C:\Users\saskp\.gemini\antigravity\scratch\hemoglobin_backend

# Create virtual environment (first time only)
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Copy environment file (first time only)
copy .env.example .env

# Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

✅ Backend will run on: **http://localhost:8000**

### Step 2: Start the Frontend

```bash
# Open Terminal 2 (new terminal)
cd C:\Users\saskp\OneDrive\Desktop\.antigravity

# Install dependencies (if not already done)
npm install

# Start frontend dev server
npm run dev
```

✅ Frontend will run on: **http://localhost:5173** (or similar)

### Step 3: Configure Frontend API Calls

In your React frontend, update the API base URL to point to the backend:

**Create/Update: `src/config.ts` or similar:**
```typescript
export const API_BASE_URL = 'http://localhost:8000';
```

**In your API service file:**
```typescript
import { API_BASE_URL } from './config';

export async function uploadScan(imageFile: File) {
  const formData = new FormData();
  formData.append('file', imageFile);
  
  const response = await fetch(`${API_BASE_URL}/api/v1/scan`, {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    throw new Error('Upload failed');
  }
  
  return response.json();
}

export async function getScanResults(scanId: string) {
  const response = await fetch(`${API_BASE_URL}/api/v1/scan/${scanId}`);
  return response.json();
}

export async function downloadReport(scanId: string) {
  window.open(`${API_BASE_URL}/api/v1/report/${scanId}`, '_blank');
}
```

## 🎨 Frontend Integration Example

**Example React component:**
```tsx
import { useState } from 'react';
import { uploadScan } from './services/api';

function ScanUpload() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setLoading(true);
    try {
      const data = await uploadScan(file);
      
      // Check quality
      if (!data.quality.quality_pass) {
        alert(data.quality.fail_reasons.join('\n'));
        return;
      }
      
      // Check uncertainty
      if (data.prediction?.uncertainty_flag) {
        alert(data.prediction.message);
        return;
      }
      
      setResult(data);
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div>
      <input type="file" accept="image/*" onChange={handleUpload} />
      
      {loading && <p>Analyzing...</p>}
      
      {result && (
        <div>
          <h2>Results</h2>
          <p>Hemoglobin: {result.prediction.hb_g_per_dl} g/dL</p>
          <p>Anemia Stage: {result.prediction.anemia_stage}</p>
          <p>Confidence: {(1 - result.prediction.uncertainty) * 100}%</p>
          
          {/* Display Grad-CAM */}
          <img src={result.explainability.gradcam_nail_overlay} alt="Grad-CAM" />
          
          {/* Download report */}
          <button onClick={() => downloadReport(result.scan_id)}>
            Download Report
          </button>
        </div>
      )}
    </div>
  );
}
```

## 🚀 Quick Start Commands

**Run both in 2 terminals:**

**Terminal 1 (Backend):**
```bash
cd C:\Users\saskp\.gemini\antigravity\scratch\hemoglobin_backend
venv\Scripts\activate
uvicorn app.main:app --reload
```

**Terminal 2 (Frontend):**
```bash
cd C:\Users\saskp\OneDrive\Desktop\.antigravity
npm run dev
```

## ✅ Verify Integration

1. Backend API docs: http://localhost:8000/docs
2. Frontend app: http://localhost:5173 (or your Vite port)
3. Test upload in frontend → should call backend API
4. Check browser Network tab to see API calls

## 🔧 Troubleshooting

**CORS errors?**
- Backend already has CORS enabled for all origins
- Check browser console for specific errors

**Connection refused?**
- Make sure backend is running on port 8000
- Check `API_BASE_URL` in frontend matches backend port

**File upload fails?**
- Check file size < 8MB
- Check file type is JPEG/PNG
- Check image resolution ≥ 512x512

---

**Need help integrating?** Let me know what specific issues you're facing!
