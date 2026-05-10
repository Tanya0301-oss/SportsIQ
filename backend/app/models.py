"""
SQLAlchemy ORM models for the sports analytics platform.
"""
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    home_team: Mapped[str] = mapped_column(String(100))
    away_team: Mapped[str] = mapped_column(String(100))
    league: Mapped[str] = mapped_column(String(100), default="Premier League")
    season: Mapped[str] = mapped_column(String(20), default="2023/24")
    match_date: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20), default="scheduled")  # scheduled | live | finished
    home_goals: Mapped[int] = mapped_column(Integer, default=0)
    away_goals: Mapped[int] = mapped_column(Integer, default=0)
    home_form: Mapped[float] = mapped_column(Float, default=0.5)   # last-5 weighted win rate
    away_form: Mapped[float] = mapped_column(Float, default=0.5)
    venue: Mapped[str] = mapped_column(String(100), default="Home Stadium")

    states: Mapped[list["MatchState"]] = relationship(back_populates="match", cascade="all, delete-orphan")
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="match", cascade="all, delete-orphan")


class MatchState(Base):
    """Snapshot of match stats at a given minute."""
    __tablename__ = "match_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    match_id: Mapped[int] = mapped_column(Integer, ForeignKey("matches.id"), index=True)
    minute: Mapped[int] = mapped_column(Integer)
    home_goals: Mapped[int] = mapped_column(Integer, default=0)
    away_goals: Mapped[int] = mapped_column(Integer, default=0)
    home_red_cards: Mapped[int] = mapped_column(Integer, default=0)
    away_red_cards: Mapped[int] = mapped_column(Integer, default=0)
    home_yellow_cards: Mapped[int] = mapped_column(Integer, default=0)
    away_yellow_cards: Mapped[int] = mapped_column(Integer, default=0)
    home_shots_on_target: Mapped[int] = mapped_column(Integer, default=0)
    away_shots_on_target: Mapped[int] = mapped_column(Integer, default=0)
    home_possession: Mapped[float] = mapped_column(Float, default=50.0)
    event_type: Mapped[str] = mapped_column(String(50), default="tick")  # goal|red_card|yellow_card|tick
    event_team: Mapped[str] = mapped_column(String(10), default="")      # home|away|""
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    match: Mapped["Match"] = relationship(back_populates="states")


class Prediction(Base):
    """ML prediction + SHAP values for a given match state."""
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    match_id: Mapped[int] = mapped_column(Integer, ForeignKey("matches.id"), index=True)
    minute: Mapped[int] = mapped_column(Integer)
    prob_home_win: Mapped[float] = mapped_column(Float)
    prob_draw: Mapped[float] = mapped_column(Float)
    prob_away_win: Mapped[float] = mapped_column(Float)
    shap_values: Mapped[dict] = mapped_column(JSON)       # {feature_name: shap_value}
    feature_values: Mapped[dict] = mapped_column(JSON)    # {feature_name: raw_value}
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    match: Mapped["Match"] = relationship(back_populates="predictions")


class HistoricalMatch(Base):
    """Historical match result for ML training."""
    __tablename__ = "historical_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    season: Mapped[str] = mapped_column(String(20))
    home_team: Mapped[str] = mapped_column(String(100))
    away_team: Mapped[str] = mapped_column(String(100))
    home_goals: Mapped[int] = mapped_column(Integer)
    away_goals: Mapped[int] = mapped_column(Integer)
    result: Mapped[str] = mapped_column(String(1))   # H | D | A
    home_shots: Mapped[int] = mapped_column(Integer, default=0)
    away_shots: Mapped[int] = mapped_column(Integer, default=0)
    home_shots_on_target: Mapped[int] = mapped_column(Integer, default=0)
    away_shots_on_target: Mapped[int] = mapped_column(Integer, default=0)
    match_date: Mapped[str] = mapped_column(String(20))
    league: Mapped[str] = mapped_column(String(50), default="E0")


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    team: Mapped[str] = mapped_column(String(100))
    position: Mapped[str] = mapped_column(String(20))   # GK | DEF | MID | FWD
    salary: Mapped[float] = mapped_column(Float, default=8.0)
    expected_points: Mapped[float] = mapped_column(Float, default=5.0)
    recent_rating: Mapped[float] = mapped_column(Float, default=6.5)
    goals_per_match: Mapped[float] = mapped_column(Float, default=0.1)
    assists_per_match: Mapped[float] = mapped_column(Float, default=0.1)
