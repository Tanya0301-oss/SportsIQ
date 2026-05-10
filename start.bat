@echo off
REM Sports Analytics Platform - Quick Start Script (Windows)
REM This script sets up and starts the entire application

setlocal enabledelayedexpansion

cls
echo.
echo ========================================================================
echo.  SPORTS ANALYTICS PLATFORM - QUICK START
echo.
echo ========================================================================
echo.

REM Check if .env exists
if not exist "backend\.env" (
    echo [!] .env file not found. Running setup wizard...
    python setup.py
    if !errorlevel! neq 0 (
        echo Setup failed. Exiting.
        pause
        exit /b 1
    )
)

REM Check Python
python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check Node.js
node --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [WARNING] Node.js not found. Frontend will not start.
    echo Please install Node.js from https://nodejs.org/
)

echo [*] Checking backend virtual environment...
if not exist "backend\venv" (
    echo [*] Creating virtual environment...
    cd backend
    python -m venv venv
    cd ..
)

echo [*] Activating virtual environment and installing dependencies...
call backend\venv\Scripts\activate.bat
pip install -q -r backend\requirements.txt >nul 2>&1

echo [*] Checking frontend dependencies...
if not exist "frontend\node_modules" (
    echo [*] Installing frontend dependencies (this may take a minute)...
    cd frontend
    npm install --silent >nul 2>&1
    cd ..
)

echo.
echo ========================================================================
echo  STARTING APPLICATION
echo ========================================================================
echo.
echo [1] BACKEND API will start on: http://localhost:8000
echo [2] API DOCS available at: http://localhost:8000/docs
echo [3] FRONTEND will start on: http://localhost:5173
echo.
echo Starting in 5 seconds (Ctrl+C to cancel)...
timeout /t 5 /nobreak

REM Start backend in a new window
echo [*] Starting Backend API...
start "Sports Analytics - Backend" cmd /k ^
    cd /d "%cd%\backend" ^& ^
    venv\Scripts\activate.bat ^& ^
    python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

timeout /t 3 /nobreak

REM Start frontend in a new window
if exist "frontend\node_modules" (
    echo [*] Starting Frontend...
    start "Sports Analytics - Frontend" cmd /k ^
        cd /d "%cd%\frontend" ^& ^
        npm run dev
) else (
    echo [!] Frontend dependencies not installed. Skipping frontend.
    echo [*] Install with: cd frontend && npm install && npm run dev
)

echo.
echo ========================================================================
echo  APPLICATION STARTED
echo ========================================================================
echo.
echo [*] Backend running on http://localhost:8000
echo [*] Frontend running on http://localhost:5173
echo [*] API Docs on http://localhost:8000/docs
echo.
echo Close this window when done.
echo.

timeout /t 999999
