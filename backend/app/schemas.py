"""
Pydantic schemas for request/response validation and OpenAPI docs.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

# ── Match schemas ────────────────────────────────────────────────────────────

class MatchBase(BaseModel):
    home_team: str
    away_team: str
    league: str
    season: str
    match_date: datetime
    venue: str = "Home Stadium"


class MatchOut(MatchBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    home_goals: int
    away_goals: int
    home_form: float
    away_form: float


class MatchStateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    match_id: int
    minute: int
    home_goals: int
    away_goals: int
    home_red_cards: int
    away_red_cards: int
    home_shots_on_target: int
    away_shots_on_target: int
    home_possession: float
    event_type: str
    event_team: str


# ── Prediction schemas ───────────────────────────────────────────────────────

class ShapFeature(BaseModel):
    feature: str
    shap_value: float
    raw_value: float


class PredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    match_id: int
    minute: int
    prob_home_win: float
    prob_draw: float
    prob_away_win: float
    shap_features: list[ShapFeature]
    created_at: datetime


# ── WebSocket push payload ───────────────────────────────────────────────────

class WsPushPayload(BaseModel):
    """Payload pushed to all WebSocket clients on every prediction update."""
    match_id: int
    minute: int
    home_goals: int
    away_goals: int
    event_type: str
    event_team: str
    prob_home_win: float
    prob_draw: float
    prob_away_win: float
    shap_features: list[ShapFeature]


# ── Player schemas ───────────────────────────────────────────────────────────

class PlayerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    team: str
    position: str
    salary: float
    expected_points: float
    recent_rating: float
    goals_per_match: float
    assists_per_match: float


# ── Lineup optimizer schemas ─────────────────────────────────────────────────

class LineupRequest(BaseModel):
    budget: float = 100.0
    formation: str = "4-3-3"          # "4-3-3" | "4-4-2" | "3-5-2"
    players: list[PlayerOut]


class LineupResponse(BaseModel):
    selected_players: list[PlayerOut]
    total_salary: float
    total_expected_points: float
    formation: str
    status: str                        # "Optimal" | "Infeasible"
