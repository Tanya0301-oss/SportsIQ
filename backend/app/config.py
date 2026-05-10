"""
Application configuration via pydantic-settings.
Reads from .env file for local dev, environment variables in production.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = "Sports Analytics Platform"
    debug: bool = True
    api_prefix: str = "/api/v1"

    # Database — SQLite for local dev, Postgres URL for prod
    database_url: str = "sqlite+aiosqlite:///./sports.db"

    # Redis — empty string disables Redis (uses in-memory fallback)
    redis_url: str = ""

    # ML artifacts directory
    artifacts_dir: str = "ml/artifacts"

    # Data Source: "simulator" (demo) or "live" (real data)
    data_source: str = "live"  # Change to "simulator" for demo mode

    # Football-Data.org API (for live data)
    football_data_api_key: str = ""  # Get from https://www.football-data.org/
    football_data_base_url: str = "https://api.football-data.org/v4"

    # League IDs for football-data.org (matches season 2024/25)
    # Common leagues: PL (Premier League), SA (Serie A), DL (Bundesliga), etc.
    active_leagues: list[str] = ["PL", "SA", "DL", "FL1", "PPL"]

    # Simulator settings (only used if data_source="simulator")
    simulator_tick_seconds: int = 10   # How often simulator emits a new event

    # Live feed poll interval
    live_feed_poll_seconds: int = 30   # How often to check for new match events

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Prometheus
    enable_metrics: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
