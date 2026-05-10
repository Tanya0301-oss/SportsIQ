@echo off
REM 🚀 Sports Analytics - Local Development & Deployment Helper (Windows)

setlocal enabledelayedexpansion
setlocal enableextensions

title Sports Analytics Platform - Setup Helper

echo ============================================
echo 🏆 Sports Analytics Platform - Setup Helper
echo ============================================
echo.

REM Colors using escape codes (Windows 10+)
REM Green: [92m, Yellow: [93m, Blue: [94m, Red: [91m

:menu
echo [94mWhat would you like to do?[0m
echo.
echo 1) Check prerequisites
echo 2) Setup backend
echo 3) Setup frontend
echo 4) Setup both (backend + frontend)
echo 5) Train ML model
echo 6) Run development servers
echo 7) Show deployment checklist
echo 8) Exit
echo.
set /p choice="Enter your choice (1-8): "

if "%choice%"=="1" goto check_prereqs
if "%choice%"=="2" goto setup_backend
if "%choice%"=="3" goto setup_frontend
if "%choice%"=="4" goto setup_all
if "%choice%"=="5" goto train_model
if "%choice%"=="6" goto run_dev
if "%choice%"=="7" goto checklist
if "%choice%"=="8" exit /b 0
echo Invalid choice. Please try again.
goto menu

:check_prereqs
echo.
echo [94mChecking prerequisites...[0m
echo.

python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [92m✓ Python found[0m
) else (
    echo [91m✗ Python not found. Please install Python 3.9+[0m
    goto menu
)

node --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [92m✓ Node.js found[0m
) else (
    echo [91m✗ Node.js not found. Please install Node.js 16+[0m
    goto menu
)

npm --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [92m✓ npm found[0m
) else (
    echo [91m✗ npm not found. Please install npm[0m
    goto menu
)

echo.
echo [92mAll prerequisites are met![0m
pause
goto menu

:setup_backend
echo.
echo [94mSetting up Backend...[0m
echo.

cd backend

if not exist "venv" (
    echo [94mℹ Creating Python virtual environment...[0m
    python -m venv venv
    echo [92m✓ Virtual environment created[0m
) else (
    echo [92m✓ Virtual environment already exists[0m
)

call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [91m✗ Virtual environment activation failed[0m
    cd ..
    goto menu
)
echo [92m✓ Virtual environment activated[0m

echo [94mℹ Installing Python dependencies...[0m
pip install --upgrade pip setuptools wheel >nul 2>&1
pip install -r requirements.txt
echo [92m✓ Python dependencies installed[0m

if not exist ".env" (
    echo [94mℹ Creating .env file...[0m
    copy .env.example .env
    echo [93m⚠ Please edit backend\.env with your configuration[0m
) else (
    echo [92m✓ .env file already exists[0m
)

cd ..
echo.
pause
goto menu

:setup_frontend
echo.
echo [94mSetting up Frontend...[0m
echo.

cd frontend

echo [94mℹ Installing Node dependencies...[0m
call npm install
echo [92m✓ Node dependencies installed[0m

if not exist ".env.local" (
    echo [93m⚠ Create frontend\.env.local with VITE_API_URL and VITE_WS_URL[0m
)

cd ..
echo.
pause
goto menu

:setup_all
echo.
echo [94mSetting up Backend...[0m
echo.

cd backend

if not exist "venv" (
    echo [94mℹ Creating Python virtual environment...[0m
    python -m venv venv
    echo [92m✓ Virtual environment created[0m
)

call venv\Scripts\activate.bat
echo [92m✓ Virtual environment activated[0m

echo [94mℹ Installing Python dependencies...[0m
pip install --upgrade pip setuptools wheel >nul 2>&1
pip install -r requirements.txt
echo [92m✓ Python dependencies installed[0m

if not exist ".env" (
    copy .env.example .env
    echo [93m⚠ Please edit backend\.env with your configuration[0m
)

cd ..

echo.
echo [94mSetting up Frontend...[0m
echo.

cd frontend

echo [94mℹ Installing Node dependencies...[0m
call npm install
echo [92m✓ Node dependencies installed[0m

if not exist ".env.local" (
    echo [93m⚠ Create frontend\.env.local with VITE_API_URL and VITE_WS_URL[0m
)

cd ..
echo.
echo [92m✓ Both backend and frontend are set up![0m
pause
goto menu

:train_model
echo.
echo [94mTraining ML Model...[0m
echo.

cd backend
call venv\Scripts\activate.bat

echo [94mℹ Training XGBoost model (this may take a minute)...[0m
python ml/train.py
echo [92m✓ Model training complete[0m

cd ..
echo.
pause
goto menu

:run_dev
echo.
echo [94mStarting Development Servers...[0m
echo.

echo [94mℹ Starting Backend on http://localhost:8000[0m
echo [94mℹ Starting Frontend on http://localhost:5173[0m
echo.

REM Start backend in new window
cd backend
call venv\Scripts\activate.bat
start "Sports Analytics Backend" cmd /k python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
cd ..

timeout /t 2

REM Start frontend in new window
cd frontend
start "Sports Analytics Frontend" cmd /k npm run dev
cd ..

echo [92m✓ Both servers started in new windows![0m
echo [94mℹ Press Ctrl+C in each window to stop[0m
echo.
pause
goto menu

:checklist
echo.
echo [94m🚀 Deployment Checklist[0m
echo.
echo Before deploying, make sure you have:
echo.
echo [93mCreate Accounts:[0m
echo   [ ] Railway.app account (https://railway.app)
echo   [ ] Vercel account (https://vercel.app)
echo   [ ] GitHub account with code pushed
echo.
echo [93mPrepare Environment:[0m
echo   [ ] Update backend\.env with production settings
echo   [ ] Set SECRET_KEY to random value
echo   [ ] Add Football Data API key (optional)
echo   [ ] Prepare CORS_ORIGINS for your domain
echo.
echo [93mBefore Railway Deployment:[0m
echo   [ ] Commit and push all changes to GitHub
echo   [ ] .env file should be in .gitignore
echo   [ ] requirements.txt is up to date
echo   [ ] Procfile or start command is configured
echo.
echo [93mBefore Vercel Deployment:[0m
echo   [ ] Frontend\.env.local is configured
echo   [ ] VITE_API_URL points to your backend
echo   [ ] VITE_WS_URL uses wss:// protocol
echo.
echo [93mAfter Deployment:[0m
echo   [ ] Test API endpoints with /docs
echo   [ ] Test WebSocket connection
echo   [ ] Verify CORS is working
echo   [ ] Check database is created
echo   [ ] Monitor logs for errors
echo.
pause
goto menu
