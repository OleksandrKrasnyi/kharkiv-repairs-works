#!/usr/bin/env pwsh

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "      Kharkiv Repairs - Development Setup" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Creating necessary directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "frontend/static" | Out-Null
New-Item -ItemType Directory -Force -Path "frontend/dist/assets" | Out-Null
Write-Host "✓ Directories created" -ForegroundColor Green

Write-Host ""
Write-Host "Checking if backend is running..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✓ Backend is already running" -ForegroundColor Green
} catch {
    Write-Host "Backend is not running. Starting backend..." -ForegroundColor Yellow
    Start-Process -FilePath "pwsh" -ArgumentList "-Command", "python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload" -WindowStyle Normal
    Start-Sleep -Seconds 3
}

Write-Host ""
Write-Host "Starting frontend development server..." -ForegroundColor Yellow
Write-Host "Frontend will be available at: http://localhost:3000" -ForegroundColor Green
Write-Host "Backend API will be available at: http://localhost:8000" -ForegroundColor Green
Write-Host "API Documentation: http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the development server" -ForegroundColor Magenta
Write-Host ""

npm run dev

Write-Host ""
Write-Host "Development server stopped." -ForegroundColor Yellow
Read-Host "Press Enter to exit" 