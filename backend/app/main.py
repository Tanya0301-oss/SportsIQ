"""
FastAPI application entry point.

Lifespan:
  - Loads ML artifacts into memory
  - Initialises the database (creates tables)
  - Seeds demo matches + players if DB is empty
  - Starts match simulators as background tasks
  - Starts the prediction consumer loop
"""
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import random

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import get_settings
from app.database import init_db, AsyncSessionLocal
from app import models
from app.services import prediction_service
from app.routers import matches, predictions, players, lineup, websocket
from pipeline.simulator import start_all_live_matches
from pipeline.live_feed import start_live_feed
from pipeline.consumer import start_consumer

settings = get_settings()


# ── Demo data ─────────────────────────────────────────────────────────────────

DEMO_MATCHES = [
    ("Manchester City", "Arsenal",       "Premier League", 0.62, 0.58),
    ("Liverpool",       "Chelsea",        "Premier League", 0.60, 0.55),
    ("Barcelona",       "Real Madrid",    "La Liga",        0.65, 0.63),
    ("Bayern Munich",   "Borussia Dortmund", "Bundesliga",  0.70, 0.52),
    ("PSG",             "Marseille",      "Ligue 1",        0.68, 0.48),
    ("Juventus",        "AC Milan",       "Serie A",        0.55, 0.53),
]

DEMO_PLAYERS = [
    # GKs
    ("Ederson",       "Manchester City",  "GK",  5.5, 6.2),
    ("Alisson",       "Liverpool",        "GK",  5.5, 6.0),
    # DEFs
    ("Trent Alexander-Arnold", "Liverpool", "DEF", 7.5, 8.1),
    ("Ruben Dias",    "Manchester City",  "DEF", 6.5, 7.2),
    ("Virgil van Dijk","Liverpool",       "DEF", 6.5, 7.0),
    ("Kyle Walker",   "Manchester City",  "DEF", 6.0, 6.5),
    ("Ben White",     "Arsenal",          "DEF", 5.5, 6.1),
    ("William Saliba","Arsenal",          "DEF", 5.5, 6.3),
    # MIDs
    ("Kevin De Bruyne","Manchester City", "MID", 12.0, 12.5),
    ("Martin Odegaard","Arsenal",         "MID", 8.5, 9.2),
    ("Rodri",         "Manchester City",  "MID", 6.5, 7.8),
    ("Bruno Fernandes","Manchester United","MID", 8.0, 8.5),
    ("Moises Caicedo","Chelsea",          "MID", 5.5, 6.8),
    # FWDs
    ("Erling Haaland","Manchester City",  "FWD", 14.0, 14.8),
    ("Bukayo Saka",   "Arsenal",          "FWD", 9.0, 10.1),
    ("Mohamed Salah", "Liverpool",        "FWD", 12.5, 13.2),
    ("Gabriel Martinelli","Arsenal",      "FWD", 7.5, 8.4),
    ("Nicolas Jackson","Chelsea",         "FWD", 7.0, 7.9),
]


async def seed_demo_data():
    """Insert demo matches and players if DB is empty."""
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select, func
        count_result = await db.execute(select(func.count()).select_from(models.Match))
        count = count_result.scalar()
        if count > 0:
            logger.info(f"DB already has {count} matches — skipping seed")
            return

        logger.info("Seeding demo data...")

        # Create matches staggered across today
        base_time = datetime.utcnow().replace(second=0, microsecond=0)
        for i, (home, away, league, hf, af) in enumerate(DEMO_MATCHES):
            match = models.Match(
                home_team=home,
                away_team=away,
                league=league,
                season="2024/25",
                match_date=base_time + timedelta(minutes=i * 5),
                status="scheduled",
                home_form=hf,
                away_form=af,
                venue=f"{home} Stadium",
            )
            db.add(match)

        # Create players
        for name, team, pos, salary, xpts in DEMO_PLAYERS:
            player = models.Player(
                name=name,
                team=team,
                position=pos,
                salary=salary,
                expected_points=xpts,
                recent_rating=round(random.uniform(6.0, 8.5), 1),
                goals_per_match=round(random.uniform(0.05, 0.45), 2),
                assists_per_match=round(random.uniform(0.05, 0.35), 2),
            )
            db.add(player)

        await db.commit()
        logger.info(f"Seeded {len(DEMO_MATCHES)} matches and {len(DEMO_PLAYERS)} players")


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=== Sports Analytics API starting up ===")
    logger.info(f"Data source: {settings.data_source.upper()}")

    # 1. Create DB tables
    await init_db()
    logger.info("Database tables ready")

    # 2. Seed demo data (no-op if already seeded)
    await seed_demo_data()

    # 3. Load ML artifacts
    prediction_service.load_artifacts()

    # 4. Start data source (simulator or live feed)
    if settings.data_source == "live":
        logger.info("🔴 Starting REAL LIVE DATA feed from football-data.org")
        feed_task = await start_live_feed()
    else:
        logger.info("🎮 Starting DEMO SIMULATOR (synthetic data)")
        await start_all_live_matches()
        feed_task = None

    # 5. Start the prediction consumer (listens to pub/sub)
    consumer_task = asyncio.create_task(start_consumer())

    logger.info("=== API ready ===")
    yield

    # Cleanup
    consumer_task.cancel()
    if feed_task:
        feed_task.cancel()
    logger.info("=== Sports Analytics API shut down ===")


# ── App factory ───────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.app_name,
    description="Real-Time Sports Analytics & Win Probability Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
if settings.enable_metrics:
    from prometheus_fastapi_instrumentator import Instrumentator
    Instrumentator().instrument(app).expose(app)

# Routers
app.include_router(matches.router, prefix=settings.api_prefix)
app.include_router(predictions.router, prefix=settings.api_prefix)
app.include_router(players.router, prefix=settings.api_prefix)
app.include_router(lineup.router, prefix=settings.api_prefix)
app.include_router(websocket.router)  # WS routes have no api prefix


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.app_name}
