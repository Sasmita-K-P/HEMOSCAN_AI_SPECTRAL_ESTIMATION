# 🩺 HemoScan Antigravity

AI-powered hemoglobin estimation using nail bed images.

## 🚀 Quick Start

### Option 1: Automated Start (Easiest)
```powershell
# Run the launcher script
.\start-app.ps1
```

This will automatically:
- Start the backend server (http://localhost:8000)
- Start the frontend app (http://localhost:5173)
- Open both in separate terminal windows

### Option 2: Manual Start

**Terminal 1 - Backend:**
```powershell
cd hemoglobin_backend
.\venv\Scripts\Activate
python -m uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**
```powershell
cd hemoglobin_frontend
npm run dev
```

## 📖 Full Documentation

See [execution_guide.md](C:\Users\saskp\.gemini\antigravity\brain\479f621f-0acf-42b4-a099-e5b2b53c7426\execution_guide.md) for detailed instructions.

## 🔗 Access Points

- **Frontend App:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/api/v1/health

## 📁 Project Structure

```
hemoscan_antigravity/
├── hemoglobin_backend/     # FastAPI backend
│   ├── app/
│   │   ├── models/         # ML models (UNet, HbPredictor)
│   │   ├── services/       # Business logic
│   │   ├── routes/         # API endpoints
│   │   └── main.py         # Application entry
│   └── requirements.txt
│
├── hemoglobin_frontend/    # React frontend
│   ├── pages/              # App pages
│   ├── services/           # API services
│   ├── App.tsx             # Main component
│   └── package.json
│
└── start-app.ps1           # Quick launcher
```

## ✅ Status

- ✅ No errors in codebase
- ✅ Build successful
- ✅ Ready to run

## 🛠️ Tech Stack

**Backend:**
- FastAPI
- TensorFlow/Keras
- OpenCV
- SQLAlchemy

**Frontend:**
- React 19
- TypeScript
- Vite
- Tailwind CSS
- Gemini AI

## 📝 License

Clinical-grade hemoglobin estimation system.

---

**Last Updated:** 2025-11-25
