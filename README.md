# 🏆 Sports Analytics Platform

A full-stack **real-time sports analytics platform** combining machine learning predictions, live match event simulation, fantasy lineup optimization, and an interactive web dashboard. Built with FastAPI, React, XGBoost, and real football data integration.

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Tech Stack](#tech-stack)
3. [Project Architecture](#project-architecture)
4. [Project Structure](#project-structure)
5. [Installation & Setup](#installation--setup)
6. [How to Run](#how-to-run)
7. [API Documentation](#api-documentation)
8. [How Components Work](#how-components-work)
9. [Machine Learning Pipeline](#machine-learning-pipeline)
10. [Database Schema](#database-schema)
11. [Key Features](#key-features)
12. [Environment Variables](#environment-variables)
13. [Contributing](#contributing)

---

## 🎯 Project Overview

This platform provides real-time sports analytics by:

- **Predicting match outcomes** using machine learning (XGBoost model)
- **Streaming live predictions** via WebSocket with SHAP feature importance
- **Simulating match events** (goals, cards, shots) with realistic probabilities
- **Optimizing fantasy lineups** using integer linear programming
- **Displaying real-time dashboards** for match analysis and predictions
- **Integrating real live data** from the football-data.org API

### Key Capabilities:
- ⚡ Real-time WebSocket predictions
- 🤖 XGBoost-based match outcome prediction
- 📊 SHAP explainability for predictions
- ⚙️ Fantasy lineup optimization with budget & position constraints
- 🔄 Dual mode: Real API data OR Match simulator
- 📱 Interactive React dashboard
- 💾 Async SQLAlchemy ORM with SQLite/PostgreSQL support

---

## 🛠 Tech Stack

### **Backend**
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | FastAPI | 0.111.0 | Async web framework |
| Server | Uvicorn | 0.29.0 | ASGI server |
| ORM | SQLAlchemy | 2.0.30 | Database abstraction |
| DB (Dev) | SQLite + aiosqlite | - | Development database |
| DB (Prod) | PostgreSQL + asyncpg | 0.29.0 | Production database |
| Validation | Pydantic | 2.7.1 | Data validation & settings |
| WebSocket | websockets | 12.0 | Real-time communication |

### **Machine Learning**
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Model | XGBoost | 2.0.3 | Match outcome prediction |
| Explainability | SHAP | 0.45.0 | Feature importance |
| Feature Engineering | scikit-learn | 1.4.2 | Data preprocessing |
| Optimization | Optuna | 3.6.1 | Hyperparameter tuning |
| Experiment Tracking | MLflow | 2.12.1 | Model versioning |
| Numerical | NumPy, Pandas | 1.26.4, 2.2.2 | Data manipulation |

### **Optimization**
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Linear Programming | PuLP | 2.8.0 | Fantasy lineup optimization |

### **Frontend**
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | React | 18.3.1 | UI framework |
| Routing | React Router | 6.23.1 | Page navigation |
| Data Fetching | TanStack Query | 5.37.1 | Server state management |
| Charts | Recharts | 2.12.7 | Data visualization |
| Icons | Lucide React | 0.383.0 | Icon library |
| Build Tool | Vite | 5.2.12 | Fast build tool |
| Type Safety | TypeScript | 5.4.5 | Static typing |

### **DevOps & Monitoring**
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Containerization | Docker | - | Application packaging |
| Monitoring | Prometheus | 0.20.0 | Metrics collection |
| FastAPI Instrumentation | prometheus-fastapi-instrumentator | 6.1.0 | Performance metrics |
| Logging | loguru | 0.7.2 | Structured logging |
| Caching | Redis | 5.0.4 | Cache & message queue |
| Testing | pytest + pytest-asyncio | 8.2.0, 0.23.6 | Unit & async tests |
| Linting | ruff | 0.4.4 | Code quality |

---

## 🏗 Project Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + TypeScript)                │
│  - Match List       - Match Details      - Lineup Optimizer     │
│  - Real-time Charts - Probability Charts - SHAP Waterfall       │
└──────────────────────────┬──────────────────────────────────────┘
                           │ WebSocket + REST API
┌──────────────────────────▼──────────────────────────────────────┐
│                   BACKEND (FastAPI)                             │
│  ┌────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │   API Routers  │  │ WebSocket Server │  │  Services     │ │
│  │ - Matches      │  │ (Real-time)      │  │ - Prediction  │ │
│  │ - Predictions  │  │                  │  │ - Cache       │ │
│  │ - Players      │  │ (pub/sub system) │  │               │ │
│  │ - Lineup       │  │                  │  │               │ │
│  └────────────────┘  └──────────────────┘  └────────────────┘ │
└──────────────────────────┬──────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼──────┐  ┌────────▼───────┐  ┌──────▼──────┐
│   Pipeline   │  │   ML Service   │  │  Database  │
│ ┌──────────┐ │  │ ┌────────────┐ │  │ ┌────────┐ │
│ │Simulator │ │  │ │ Prediction │ │  │ │ Match  │ │
│ │  (opts)  │ │  │ │  Service   │ │  │ │ Models │ │
│ ├──────────┤ │  │ ├────────────┤ │  │ ├────────┤ │
│ │Live Feed │ │  │ │  SHAP      │ │  │ │ Player │ │
│ │ (opts)   │ │  │ │ Explainer  │ │  │ │ Data   │ │
│ ├──────────┤ │  │ ├────────────┤ │  │ │        │ │
│ │Consumer  │ │  │ │ XGBoost    │ │  │ └────────┘ │
│ │          │ │  │ │ Model      │ │  │            │
│ └──────────┘ │  │ └────────────┘ │  │ SQLite/    │
│              │  │                │  │ PostgreSQL │
└──────────────┘  └────────────────┘  └────────────┘
```

---

## 📁 Project Structure

```
sports-analytics/
├── backend/                          # FastAPI Backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app entry point, lifespan mgmt
│   │   ├── config.py                 # Settings & environment variables
│   │   ├── database.py               # SQLAlchemy setup, async session
│   │   ├── models.py                 # SQLAlchemy ORM models
│   │   ├── schemas.py                # Pydantic request/response schemas
│   │   ├── routers/                  # API endpoints
│   │   │   ├── matches.py            # GET /api/v1/matches/*
│   │   │   ├── predictions.py        # GET /api/v1/predictions/*
│   │   │   ├── players.py            # GET /api/v1/players
│   │   │   ├── lineup.py             # POST /api/v1/lineup/optimize
│   │   │   └── websocket.py          # WS /ws/match/{id}
│   │   └── services/
│   │       ├── prediction_service.py # ML inference + caching
│   │       └── cache.py              # In-memory cache manager
│   │
│   ├── ml/                           # Machine Learning
│   │   ├── train.py                  # XGBoost model training
│   │   ├── feature_extractor.py      # Feature engineering
│   │   ├── evaluate.py               # Model evaluation & SHAP analysis
│   │   └── artifacts/                # Model weights, scalers, encoders
│   │
│   ├── pipeline/                     # Real-time Data Processing
│   │   ├── simulator.py              # Match event simulator (Poisson distribution)
│   │   ├── live_feed.py              # football-data.org API integration
│   │   ├── consumer.py               # Async event consumer & inference runner
│   │   └── pub_sub.py                # Pub/Sub messaging system
│   │
│   ├── optimizer/
│   │   └── lineup.py                 # Fantasy lineup optimization (PuLP)
│   │
│   ├── scripts/
│   │   └── seed_data.py              # Demo data generation
│   │
│   ├── tests/
│   │   ├── test_features.py          # Feature engineering tests
│   │   ├── test_lineup.py            # Lineup optimizer tests
│   │   └── test_predictions.py       # Prediction service tests
│   │
│   ├── requirements.txt               # Python dependencies
│   ├── pytest.ini                     # Pytest configuration
│   ├── ruff.toml                      # Ruff linter config
│   ├── Dockerfile                     # Docker configuration
│   └── .env.example                   # Environment template
│
├── frontend/                         # React Frontend
│   ├── src/
│   │   ├── main.tsx                  # React entry point
│   │   ├── App.tsx                   # Main app component
│   │   ├── App.module.css             # App styles
│   │   ├── index.css                  # Global styles
│   │   ├── api/
│   │   │   └── client.ts              # API client (CRUD operations)
│   │   ├── components/                # Reusable UI components
│   │   │   ├── PitchLayout.tsx        # Football pitch visualization
│   │   │   ├── ProbabilityChart.tsx   # Probability bar charts
│   │   │   └── ShapWaterfallChart.tsx # SHAP value visualization
│   │   ├── hooks/
│   │   │   └── useMatchWebSocket.ts   # WebSocket connection hook
│   │   └── pages/                     # Full page components
│   │       ├── MatchList.tsx          # All matches page
│   │       ├── MatchDetail.tsx        # Single match analysis
│   │       └── LineupOptimizer.tsx    # Fantasy optimizer page
│   │
│   ├── package.json                   # Node dependencies
│   ├── tsconfig.json                  # TypeScript config
│   ├── vite.config.ts                 # Vite build config
│   ├── vercel.json                    # Vercel deployment config
│   └── index.html                     # HTML template
│
├── SETUP_GUIDE.md                     # Detailed setup instructions
├── PROJECT_STATUS_REPORT.md            # Project completion status
├── REAL_DATA_CHANGES.md               # Live API integration changes
├── README.md                          # This file
├── setup.py                           # Python package setup
├── start.bat                          # Windows startup script
└── start.sh                           # Linux/Mac startup script
```

---

## 🚀 Installation & Setup

### **Prerequisites**
- Python 3.9+
- Node.js 16+ & npm
- Git

### **Step 1: Clone the Repository**
```bash
git clone <your-repo-url>
cd sports-analytics
```

### **Step 2: Backend Setup**

#### **Create Virtual Environment**
```bash
cd backend

# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

#### **Install Dependencies**
```bash
pip install -r requirements.txt
```

#### **Configure Environment**
```bash
# Copy and edit .env file
cp .env.example .env

# Edit .env with your settings:
# - DATABASE_URL (default: sqlite+aiosqlite:///./sports.db)
# - DATA_SOURCE ("live" or "simulator")
# - FOOTBALL_DATA_API_KEY (from football-data.org)
# - ACTIVE_LEAGUES (e.g., "PL,SA,DL,FL1")
```

#### **Get API Key** (Optional, for live data)
1. Visit: https://www.football-data.org/
2. Register for free account
3. Copy API key to `.env` file as `FOOTBALL_DATA_API_KEY`

#### **Initialize Database & Train ML Model**
```bash
# This will:
# - Create database tables
# - Train XGBoost model on historical data
# - Save model artifacts to ml/artifacts/
python backend/scripts/train_model.py
```

### **Step 3: Frontend Setup**

```bash
cd frontend

# Install Node dependencies
npm install

# Build TypeScript (optional, Vite does this automatically)
npm run type-check
```

---

## ▶️ How to Run

### **Option 1: Start Both Services (Recommended)**

#### **Windows**
```bash
# From project root
start.bat
```

#### **Linux/Mac**
```bash
# From project root
chmod +x start.sh
./start.sh
```

### **Option 2: Start Services Manually**

#### **Terminal 1: Backend**
```bash
cd backend
venv\Scripts\activate  # Windows: activate, Linux/Mac: source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### **Terminal 2: Frontend**
```bash
cd frontend
npm run dev
```

### **URLs**
- 🌐 **Frontend:** http://localhost:5173
- 🔌 **API (Swagger Docs):** http://localhost:8000/docs
- 📊 **Prometheus Metrics:** http://localhost:8000/metrics

---

## 📡 API Documentation

### **Base URL**
```
http://localhost:8000/api/v1
```

### **1. Matches Endpoints**

#### **List All Matches**
```http
GET /matches
```
**Response:**
```json
{
  "matches": [
    {
      "id": 1,
      "home_team": "Manchester City",
      "away_team": "Arsenal",
      "league": "Premier League",
      "date": "2026-05-10T15:00:00",
      "status": "live",
      "home_goals": 2,
      "away_goals": 1
    }
  ]
}
```

#### **Get Match Details**
```http
GET /matches/{match_id}
```
**Response:**
```json
{
  "id": 1,
  "home_team": "Manchester City",
  "away_team": "Arsenal",
  "league": "Premier League",
  "date": "2026-05-10T15:00:00",
  "status": "live",
  "home_goals": 2,
  "away_goals": 1,
  "match_states": [
    {
      "minute": 0,
      "home_goals": 0,
      "away_goals": 0
    },
    {
      "minute": 45,
      "home_goals": 1,
      "away_goals": 0
    }
  ]
}
```

### **2. Predictions Endpoint**

#### **Get Latest Prediction for Match**
```http
GET /matches/{match_id}/prediction
```
**Response:**
```json
{
  "match_id": 1,
  "predicted_at": "2026-05-10T15:30:00",
  "probabilities": {
    "home_win": 0.62,
    "draw": 0.18,
    "away_win": 0.20
  },
  "shap_values": {
    "home_team_form": 0.15,
    "home_avg_goals": 0.12,
    "possession_home": 0.08
  },
  "model_version": "1.0.0"
}
```

### **3. Players Endpoint**

#### **List All Players**
```http
GET /players
```
**Response:**
```json
{
  "players": [
    {
      "id": 1,
      "name": "Erling Haaland",
      "team": "Manchester City",
      "position": "FWD",
      "salary": 14.8,
      "points": 350
    }
  ]
}
```

### **4. Lineup Optimization**

#### **Optimize Fantasy Lineup**
```http
POST /lineup/optimize
Content-Type: application/json

{
  "formation": "4-3-3",
  "budget": 100.0,
  "players": [1, 2, 3, ...],  // Player IDs
  "constraints": {
    "gk_min": 1,
    "def_min": 3,
    "mid_min": 3,
    "fwd_min": 1
  }
}
```
**Response:**
```json
{
  "formation": "4-3-3",
  "selected_players": [1, 3, 5, 7, 9, 11, 13, 15, 17, 18, 20],
  "total_salary": 99.5,
  "total_expected_points": 425,
  "status": "optimal"
}
```

### **5. WebSocket: Real-time Predictions**

#### **Connect to Live Predictions**
```
ws://localhost:8000/ws/match/{match_id}
```

**Message Format:**
```json
{
  "type": "prediction_update",
  "match_id": 1,
  "minute": 45,
  "probabilities": {
    "home_win": 0.65,
    "draw": 0.16,
    "away_win": 0.19
  },
  "home_goals": 2,
  "away_goals": 1,
  "timestamp": "2026-05-10T15:45:00"
}
```

---

## ⚙️ How Components Work

### **1. Match Simulator** (`pipeline/simulator.py`)

The simulator generates **realistic match progression** with probabilistic events:

```
Timeline: 0 → 90 minutes (tick-by-tick)

For each minute:
├── Calculate team form multiplier
├── Generate probabilistic events:
│   ├── Goals (Poisson: λ=2.25, multiplied by form)
│   ├── Yellow cards (~3 per match)
│   ├── Red cards (~0.27 per match)
│   └── Shots on target
├── Update match state
└── Publish to pub/sub system
```

**Key Features:**
- Uses Poisson distribution for realistic goal distribution
- Form-based multipliers affect goal probability
- Event probabilities based on real football statistics
- Real-time minute-by-minute updates

### **2. Live Feed Manager** (`pipeline/live_feed.py`)

Integrates with football-data.org API:

```
Every 30 seconds:
├── Fetch live matches from API
├── Extract: scores, status, timing
├── Sync to database
├── Publish to pub/sub system
└── Trigger prediction updates
```

**Data Flow:**
```
football-data.org API
        ↓
  LiveFeedManager
        ↓
  Extract & Transform
        ↓
  Sync to Database
        ↓
  Publish (pub/sub)
        ↓
  Prediction Consumer
        ↓
  WebSocket → Frontend
```

### **3. Prediction Consumer** (`pipeline/consumer.py`)

Async loop that watches for match events and triggers ML inference:

```
Consumer Loop:
├── Subscribe to pub/sub channel
├── Wait for match state events
├── On event:
│   ├── Extract features from match state
│   ├── Run XGBoost inference
│   ├── Calculate SHAP values
│   ├── Cache prediction
│   └── Publish to WebSocket
└── Repeat
```

### **4. WebSocket Manager** (`routers/websocket.py`)

Real-time bi-directional communication:

```
Client (React)
    ↑↓ (WebSocket)
FastAPI Server
    ├── Connection Manager (pub/sub)
    ├── Heartbeat (30-sec timeout)
    └── Message Broadcasting
```

**Features:**
- Multiple clients per match
- Automatic reconnection
- Message broadcasting
- Graceful disconnection

### **5. Prediction Service** (`services/prediction_service.py`)

Handles ML inference with caching:

```
Request for prediction:
├── Check in-memory cache
├── If found → return cached
└── If miss:
    ├── Extract features
    ├── Run XGBoost.predict_proba()
    ├── Calculate SHAP values
    ├── Cache result
    └── Return to client
```

**Cache Strategy:**
- 5-minute TTL (configurable)
- LRU eviction
- Automatic invalidation on new match state

---

## 🤖 Machine Learning Pipeline

### **Model Architecture**

**Algorithm:** XGBoost (Gradient Boosting)
**Task:** Multi-class Classification (Home Win, Draw, Away Win)
**Features:** 15+ engineered features

### **Feature Engineering** (`ml/feature_extractor.py`)

```
Match Data:
├── Team Form (last 5 matches)
├── Average Goals (home/away)
├── Average Conceded
├── Possession %
├── Shots on Target
├── Historical H2H record
└── League average metrics

↓ Feature Extraction ↓

Numerical Features (normalized):
├── home_team_form (0-1)
├── home_avg_goals (0-5)
├── home_avg_conceded (0-3)
├── away_* (same for away team)
├── h2h_home_wins (ratio)
└── ... (15 total)

↓ Feature Scaling (StandardScaler) ↓

Ready for Model Input
```

### **Training Pipeline** (`ml/train.py`)

```bash
python backend/ml/train.py

Steps:
1. Load historical match data (or generate synthetic)
2. Feature engineering on all matches
3. Train/test split (80/20)
4. XGBoost training with Optuna hyperparameter tuning
5. Evaluation (accuracy, F1, logloss)
6. SHAP value computation
7. Save artifacts:
   - model.pkl (XGBoost model)
   - scaler.pkl (StandardScaler)
   - label_encoder.pkl (team name encoding)
   - feature_names.json (feature metadata)
```

### **Inference & Explainability** (`services/prediction_service.py`)

```python
# Inference pipeline
features = extract_features(match_state)
features = scaler.transform(features)
probabilities = model.predict_proba(features)
shap_values = explainer.shap_values(features)

# Returns to frontend:
{
  "home_win": 0.62,
  "draw": 0.18,
  "away_win": 0.20,
  "top_features": {
    "home_team_form": 0.15,
    "away_avg_goals": 0.12,
    "possession_home": 0.08
  }
}
```

### **Model Performance Metrics**

Evaluated using:
- **Accuracy:** Overall correctness
- **F1 Score:** Balanced precision/recall
- **LogLoss:** Probability calibration
- **Confusion Matrix:** Per-class performance
- **SHAP Summary Plots:** Feature importance

---

## 💾 Database Schema

### **SQLAlchemy Models** (`app/models.py`)

#### **Match Model**
```python
class Match(Base):
    __tablename__ = "matches"
    
    id: int                    # Primary key
    home_team: str            # Team name
    away_team: str            # Team name
    league: str               # Premier League, La Liga, etc.
    date: datetime            # Match start time
    status: str               # "scheduled", "live", "finished"
    home_goals: int           # Current/final score
    away_goals: int
    home_win_prob: float      # ML prediction
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    match_states: List[MatchState]
    predictions: List[Prediction]
```

#### **MatchState Model**
```python
class MatchState(Base):
    __tablename__ = "match_states"
    
    id: int
    match_id: int             # Foreign key → Match
    minute: int               # 0-90
    home_goals: int           # Goals at this minute
    away_goals: int
    possession_home: float    # Possession %
    shots_home: int
    shots_away: int
    cards: json              # {"yellow": {...}, "red": {...}}
    created_at: datetime
```

#### **Prediction Model**
```python
class Prediction(Base):
    __tablename__ = "predictions"
    
    id: int
    match_id: int             # Foreign key → Match
    predicted_at: datetime
    home_win_prob: float      # P(Home Win)
    draw_prob: float          # P(Draw)
    away_win_prob: float      # P(Away Win)
    shap_values: json        # Feature importance
    model_version: str        # Model artifact version
```

#### **Player Model**
```python
class Player(Base):
    __tablename__ = "players"
    
    id: int
    name: str
    team: str
    position: str             # GK, DEF, MID, FWD
    salary: float             # Fantasy salary
    total_points: int         # Total points earned
```

### **Database Support**

- **Development:** SQLite (aiosqlite)
- **Production:** PostgreSQL (asyncpg)

**Connection String Examples:**
```python
# SQLite
DATABASE_URL = "sqlite+aiosqlite:///./sports.db"

# PostgreSQL
DATABASE_URL = "postgresql+asyncpg://user:password@localhost/sports_db"
```

---

## ✨ Key Features

### **1. Real-time Predictions**
- WebSocket streaming of match predictions
- Updates every minute during live matches
- Sub-second latency

### **2. Feature Explainability**
- SHAP values show which features drove predictions
- Waterfall charts on frontend
- Interpretable ML for stakeholders

### **3. Fantasy Lineup Optimization**
- Integer Linear Programming (PuLP solver)
- Multiple formation support (4-3-3, 4-4-2, 3-5-2)
- Budget constraints
- Position constraints

### **4. Dual Data Modes**
- **Simulator:** Realistic match events, great for demos
- **Live API:** Real match data from football-data.org
- Seamless switching via config

### **5. Performance Monitoring**
- Prometheus metrics at `/metrics` endpoint
- Request/response latencies
- Cache hit rates
- Database connection pool stats

### **6. Async Architecture**
- Non-blocking FastAPI with async/await
- Concurrent WebSocket connections
- Efficient database queries

---

## 🔧 Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Application
APP_NAME="Sports Analytics Platform"
DEBUG=True
SECRET_KEY="your-secret-key-here"

# Database
DATABASE_URL="sqlite+aiosqlite:///./sports.db"
# DATABASE_URL="postgresql+asyncpg://user:password@localhost/sports_db"

# Data Source
DATA_SOURCE="simulator"  # or "live"
LIVE_FEED_POLL_SECONDS=30

# Football Data API (for live data)
FOOTBALL_DATA_API_KEY="your-api-key-here"
FOOTBALL_DATA_BASE_URL="https://api.football-data.org/v4"
ACTIVE_LEAGUES="PL,SA,DL,FL1,PPL"  # Premier League, La Liga, Bundesliga, Ligue 1, Serie A

# Simulator
SIMULATOR_TICK_SECONDS=10  # Real seconds per match minute

# File Paths
ARTIFACTS_DIR="ml/artifacts"

# CORS
CORS_ORIGINS="http://localhost:5173,http://localhost:3000"

# Metrics
ENABLE_METRICS=True

# Logging
LOG_LEVEL="INFO"

# Redis (optional, for production caching)
REDIS_URL="redis://localhost:6379"
```

---

## 🧪 Testing

### **Run Tests**
```bash
cd backend

# All tests
pytest

# Specific test file
pytest tests/test_features.py -v

# With coverage
pytest --cov=app --cov=ml --cov-report=html
```

### **Test Files**
- `tests/test_features.py` - Feature engineering tests
- `tests/test_lineup.py` - Lineup optimizer tests
- `tests/test_predictions.py` - Prediction service tests

---

## 📦 Deployment

### **Docker**

```bash
# Build image
docker build -f backend/Dockerfile -t sports-analytics-backend .

# Run container
docker run -p 8000:8000 --env-file .env sports-analytics-backend
```

### **Frontend Deployment**

Deploy to Vercel (configured in `frontend/vercel.json`):
```bash
cd frontend
npm run build
vercel deploy
```

---

## 🤝 Contributing

### **Code Quality**

Run linter before committing:
```bash
ruff check backend/
ruff format backend/
```

### **Pull Request Process**
1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and test thoroughly
3. Run `ruff` to format code
4. Run `pytest` to ensure tests pass
5. Create pull request with description

---

## 📚 Additional Resources

- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **XGBoost Guide:** https://xgboost.readthedocs.io/
- **SHAP Documentation:** https://shap.readthedocs.io/
- **React Hooks:** https://react.dev/reference/react
- **SQLAlchemy Async:** https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- **Football Data API:** https://www.football-data.org/client

---

## 📝 License

[Add your license here]

---

## 👥 Authors

- **You** - Initial development

---

## ❓ FAQ

**Q: How often does the model retrain?**
A: The model is trained once during setup. For production, consider scheduling weekly retraining with new match data.

**Q: Can I use this with a different football API?**
A: Yes! Modify `pipeline/live_feed.py` to integrate with your preferred API (ESPN, StatsBomb, etc.).

**Q: What's the prediction accuracy?**
A: XGBoost typically achieves 55-60% accuracy on 3-way classification (Home/Draw/Away). This is better than random (33%) but imperfect—use for analysis, not gambling!

**Q: How do I scale this to more leagues?**
A: Add league codes to `ACTIVE_LEAGUES` in `.env`. The system scales horizontally with multiple consumer instances.

**Q: How much data do I need to train the model?**
A: Start with 500+ historical matches. More data = better predictions.

---

## 🐛 Troubleshooting

### **WebSocket Connection Issues**
- Check CORS settings in `app/config.py`
- Ensure backend is running on correct port (8000)
- Check browser console for error messages

### **Model Not Found**
- Run `python backend/ml/train.py` to generate artifacts
- Check `ml/artifacts/` directory exists

### **Database Locked**
- Close all other connections to SQLite
- For production, switch to PostgreSQL (better concurrency)

### **Predictions Not Updating**
- Check consumer is running (terminal output should show "Consumer started")
- Check database has match states (verify simulator/live feed is working)
- Check WebSocket connections are established

---

**Last Updated:** May 2026
**Status:** Production Ready (MVP Phase)
