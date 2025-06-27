@echo off
echo ==============================================
echo       Kharkiv Repairs - Development Setup
echo ==============================================

echo.
echo Creating necessary directories...
if not exist "frontend\static" mkdir "frontend\static"
if not exist "frontend\dist" mkdir "frontend\dist"
if not exist "frontend\dist\assets" mkdir "frontend\dist\assets"

echo.
echo Checking if backend is running...
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% neq 0 (
    echo Backend is not running. Starting backend...
    start "Backend Server" cmd /k "python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"
    timeout /t 3 /nobreak >nul
) else (
    echo Backend is already running.
)

echo.
echo Starting frontend development server...
echo Frontend will be available at: http://localhost:3000
echo Backend API will be available at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the development server
echo.

npm run dev

echo.
echo Development server stopped.
pause 