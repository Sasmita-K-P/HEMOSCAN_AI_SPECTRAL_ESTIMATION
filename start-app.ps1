# HemoScan Quick Start Script
# Run this script to start both backend and frontend servers

Write-Host "🚀 Starting HemoScan Antigravity Application..." -ForegroundColor Cyan
Write-Host ""

# Get the script directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath

# Backend path
$backendPath = Join-Path $projectRoot "hemoglobin_backend"
# Frontend path
$frontendPath = Join-Path $projectRoot "hemoglobin_frontend"

Write-Host "📂 Project Root: $projectRoot" -ForegroundColor Yellow
Write-Host ""

# Function to start backend
function Start-Backend {
    Write-Host "🔧 Starting Backend Server..." -ForegroundColor Green
    
    # Check if venv exists
    $venvPath = Join-Path $backendPath "venv"
    if (-Not (Test-Path $venvPath)) {
        Write-Host "⚠️  Virtual environment not found. Creating..." -ForegroundColor Yellow
        Set-Location $backendPath
        python -m venv venv
        Write-Host "✅ Virtual environment created" -ForegroundColor Green
    }
    
    # Start backend in new window
    $backendScript = @"
Set-Location '$backendPath'
& '.\venv\Scripts\Activate.ps1'
Write-Host '🔧 Backend Server Starting...' -ForegroundColor Green
Write-Host 'Installing/Updating dependencies...' -ForegroundColor Yellow
pip install -q -r requirements.txt
Write-Host '✅ Dependencies ready' -ForegroundColor Green
Write-Host ''
Write-Host '🌐 Backend running at: http://localhost:8000' -ForegroundColor Cyan
Write-Host '📚 API Docs: http://localhost:8000/docs' -ForegroundColor Cyan
Write-Host ''
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"@
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendScript
    Write-Host "✅ Backend terminal opened" -ForegroundColor Green
}

# Function to start frontend
function Start-Frontend {
    Write-Host "🎨 Starting Frontend Server..." -ForegroundColor Green
    
    # Check if node_modules exists
    $nodeModulesPath = Join-Path $frontendPath "node_modules"
    if (-Not (Test-Path $nodeModulesPath)) {
        Write-Host "⚠️  Node modules not found. Will install..." -ForegroundColor Yellow
    }
    
    # Start frontend in new window
    $frontendScript = @"
Set-Location '$frontendPath'
Write-Host '🎨 Frontend Server Starting...' -ForegroundColor Green
if (-Not (Test-Path 'node_modules')) {
    Write-Host 'Installing dependencies (this may take a few minutes)...' -ForegroundColor Yellow
    npm install
    Write-Host '✅ Dependencies installed' -ForegroundColor Green
}
Write-Host ''
Write-Host '🌐 Frontend will open at: http://localhost:5173' -ForegroundColor Cyan
Write-Host ''
npm run dev
"@
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendScript
    Write-Host "✅ Frontend terminal opened" -ForegroundColor Green
}

# Main execution
Write-Host "Starting servers in separate windows..." -ForegroundColor Cyan
Write-Host ""

Start-Backend
Start-Sleep -Seconds 2
Start-Frontend

Write-Host ""
Write-Host "✅ Both servers are starting!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Wait for both terminals to show 'ready' messages"
Write-Host "  2. Backend: http://localhost:8000"
Write-Host "  3. Frontend: http://localhost:5173"
Write-Host "  4. Open http://localhost:5173 in your browser"
Write-Host ""
Write-Host "⚠️  Keep both terminal windows open while using the app" -ForegroundColor Yellow
Write-Host "🛑 To stop: Press Ctrl+C in each terminal window" -ForegroundColor Red
Write-Host ""
Write-Host "Press any key to exit this launcher..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
