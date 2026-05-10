#!/bin/bash
# 🚀 Sports Analytics - Local Development & Deployment Helper

set -e

echo "============================================"
echo "🏆 Sports Analytics Platform - Setup Helper"
echo "============================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    echo ""
    echo -e "${BLUE}Checking prerequisites...${NC}"
    
    # Check Python
    if command -v python &> /dev/null; then
        python_version=$(python --version 2>&1 | awk '{print $2}')
        print_success "Python $python_version found"
    else
        print_error "Python not found. Please install Python 3.9+"
        exit 1
    fi
    
    # Check Node.js
    if command -v node &> /dev/null; then
        node_version=$(node --version)
        print_success "Node.js $node_version found"
    else
        print_error "Node.js not found. Please install Node.js 16+"
        exit 1
    fi
    
    # Check npm
    if command -v npm &> /dev/null; then
        npm_version=$(npm --version)
        print_success "npm $npm_version found"
    else
        print_error "npm not found. Please install npm"
        exit 1
    fi
}

# Setup backend
setup_backend() {
    echo ""
    echo -e "${BLUE}Setting up Backend...${NC}"
    
    cd backend
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        print_info "Creating Python virtual environment..."
        python -m venv venv
        print_success "Virtual environment created"
    fi
    
    # Activate venv
    source venv/bin/activate
    print_success "Virtual environment activated"
    
    # Install dependencies
    if [ ! -f "venv/pyvenv.cfg" ]; then
        print_error "Virtual environment activation failed"
        exit 1
    fi
    
    print_info "Installing Python dependencies..."
    pip install --upgrade pip setuptools wheel > /dev/null 2>&1
    pip install -r requirements.txt
    print_success "Python dependencies installed"
    
    # Create .env if it doesn't exist
    if [ ! -f ".env" ]; then
        print_info "Creating .env file..."
        cp .env.example .env
        print_warning "Please edit backend/.env with your configuration"
    fi
    
    cd ..
}

# Setup frontend
setup_frontend() {
    echo ""
    echo -e "${BLUE}Setting up Frontend...${NC}"
    
    cd frontend
    
    print_info "Installing Node dependencies..."
    npm install
    print_success "Node dependencies installed"
    
    # Check if .env exists
    if [ ! -f ".env.local" ]; then
        print_warning "Create frontend/.env.local with VITE_API_URL and VITE_WS_URL"
    fi
    
    cd ..
}

# Train ML model
train_model() {
    echo ""
    echo -e "${BLUE}Training ML Model...${NC}"
    
    cd backend
    source venv/bin/activate
    
    print_info "Training XGBoost model (this may take a minute)..."
    python ml/train.py
    print_success "Model training complete"
    
    cd ..
}

# Run development servers
run_dev() {
    echo ""
    echo -e "${BLUE}Starting Development Servers...${NC}"
    echo ""
    
    print_info "Starting Backend on http://localhost:8000"
    print_info "Starting Frontend on http://localhost:5173"
    echo ""
    
    # Start backend in background
    cd backend
    source venv/bin/activate
    python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    cd ..
    
    sleep 2
    
    # Start frontend in background
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    
    print_success "Both servers started!"
    print_info "Backend PID: $BACKEND_PID"
    print_info "Frontend PID: $FRONTEND_PID"
    print_info ""
    print_info "Press Ctrl+C to stop both servers"
    
    # Handle cleanup
    trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
    
    # Wait for servers
    wait
}

# Deployment checklist
deployment_checklist() {
    echo ""
    echo -e "${BLUE}🚀 Deployment Checklist${NC}"
    echo ""
    echo "Before deploying, make sure you have:"
    echo ""
    echo -e "${YELLOW}Create Accounts:${NC}"
    echo "  [ ] Railway.app account (https://railway.app)"
    echo "  [ ] Vercel account (https://vercel.app)"
    echo "  [ ] GitHub account with code pushed"
    echo ""
    echo -e "${YELLOW}Prepare Environment:${NC}"
    echo "  [ ] Update backend/.env with production settings"
    echo "  [ ] Set SECRET_KEY to random value"
    echo "  [ ] Add Football Data API key (optional)"
    echo "  [ ] Prepare CORS_ORIGINS for your domain"
    echo ""
    echo -e "${YELLOW}Before Railway Deployment:${NC}"
    echo "  [ ] Commit and push all changes to GitHub"
    echo "  [ ] .env file should be in .gitignore"
    echo "  [ ] requirements.txt is up to date"
    echo "  [ ] Procfile or start command is configured"
    echo ""
    echo -e "${YELLOW}Before Vercel Deployment:${NC}"
    echo "  [ ] Frontend/.env.local is configured"
    echo "  [ ] VITE_API_URL points to your backend"
    echo "  [ ] VITE_WS_URL uses wss:// protocol"
    echo ""
    echo -e "${YELLOW}After Deployment:${NC}"
    echo "  [ ] Test API endpoints with /docs"
    echo "  [ ] Test WebSocket connection"
    echo "  [ ] Verify CORS is working"
    echo "  [ ] Check database is created"
    echo "  [ ] Monitor logs for errors"
    echo ""
}

# Main menu
show_menu() {
    echo ""
    echo -e "${BLUE}What would you like to do?${NC}"
    echo ""
    echo "1) Check prerequisites"
    echo "2) Setup backend"
    echo "3) Setup frontend"
    echo "4) Setup both (backend + frontend)"
    echo "5) Train ML model"
    echo "6) Run development servers"
    echo "7) Show deployment checklist"
    echo "8) Exit"
    echo ""
    read -p "Enter your choice (1-8): " choice
    
    case $choice in
        1) check_prerequisites ;;
        2) check_prerequisites && setup_backend ;;
        3) setup_frontend ;;
        4) check_prerequisites && setup_backend && setup_frontend ;;
        5) train_model ;;
        6) run_dev ;;
        7) deployment_checklist ;;
        8) print_info "Goodbye!"; exit 0 ;;
        *) print_error "Invalid choice. Please try again."; show_menu ;;
    esac
    
    show_menu
}

# Run menu if no arguments
if [ $# -eq 0 ]; then
    show_menu
else
    # Run specific command if provided
    case $1 in
        check) check_prerequisites ;;
        setup-backend) check_prerequisites && setup_backend ;;
        setup-frontend) setup_frontend ;;
        setup-all) check_prerequisites && setup_backend && setup_frontend ;;
        train) train_model ;;
        dev) run_dev ;;
        checklist) deployment_checklist ;;
        *)
            echo "Usage: ./setup.sh [check|setup-backend|setup-frontend|setup-all|train|dev|checklist]"
            exit 1
            ;;
    esac
fi
