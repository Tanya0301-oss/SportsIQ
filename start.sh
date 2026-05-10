#!/bin/bash

# Sports Analytics Platform - Quick Start Script (Mac/Linux)
# This script sets up and starts the entire application

set -e

clear

echo ""
echo "========================================================================"
echo ""
echo "  SPORTS ANALYTICS PLATFORM - QUICK START"
echo ""
echo "========================================================================"
echo ""

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo "[!] .env file not found. Running setup wizard..."
    python3 setup.py
    if [ $? -ne 0 ]; then
        echo "Setup failed. Exiting."
        exit 1
    fi
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "[WARNING] Node.js not found. Frontend will not start."
    echo "Install from: https://nodejs.org/"
fi

echo "[*] Checking backend virtual environment..."
if [ ! -d "backend/venv" ]; then
    echo "[*] Creating virtual environment..."
    cd backend
    python3 -m venv venv
    cd ..
fi

echo "[*] Installing backend dependencies..."
source backend/venv/bin/activate
pip install -q -r backend/requirements.txt

echo "[*] Checking frontend dependencies..."
if [ ! -d "frontend/node_modules" ]; then
    echo "[*] Installing frontend dependencies (this may take a minute)..."
    cd frontend
    npm install --silent
    cd ..
fi

echo ""
echo "========================================================================"
echo "  STARTING APPLICATION"
echo "========================================================================"
echo ""
echo "[1] BACKEND API will start on: http://localhost:8000"
echo "[2] API DOCS available at: http://localhost:8000/docs"
echo "[3] FRONTEND will start on: http://localhost:5173"
echo ""
echo "Starting in 5 seconds (Ctrl+C to cancel)..."
sleep 5

# Start backend in background
echo "[*] Starting Backend API..."
(
    cd backend
    source venv/bin/activate
    python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
) &

BACKEND_PID=$!

sleep 3

# Start frontend in background
if [ -d "frontend/node_modules" ]; then
    echo "[*] Starting Frontend..."
    (
        cd frontend
        npm run dev
    ) &
    FRONTEND_PID=$!
else
    echo "[!] Frontend dependencies not installed. Skipping frontend."
    echo "[*] Install with: cd frontend && npm install && npm run dev"
fi

echo ""
echo "========================================================================"
echo "  APPLICATION STARTED"
echo "========================================================================"
echo ""
echo "[*] Backend running on http://localhost:8000"
echo "[*] Frontend running on http://localhost:5173"
echo "[*] API Docs on http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for processes
wait
