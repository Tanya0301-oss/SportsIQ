"""
Predictions router — GET /api/v1/matches/{id}/prediction
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app import models, schemas
from app.services.cache import cache_get
from app.services import prediction_service

router = APIRouter(prefix="/matches", tags=["predictions"])


@router.get("/{match_id}/prediction", response_model=dict)
async def get_prediction(match_id: int, db: AsyncSession = Depends(get_db)):
    """
    Return the latest cached win probability prediction + SHAP values.
    If no cache hit, runs inference on the latest match state.
    """
    # Try cache first
    cached = await cache_get(f"pred:{match_id}")
    if cached:
        return cached

    # Fallback: get latest state from DB and run inference
    result = await db.execute(
        select(models.MatchState)
        .where(models.MatchState.match_id == match_id)
        .order_by(models.MatchState.minute.desc())
        .limit(1)
    )
    state = result.scalar_one_or_none()
    if not state:
        raise HTTPException(status_code=404, detail="No prediction available yet")

    match_result = await db.execute(
        select(models.Match).where(models.Match.id == match_id)
    )
    match = match_result.scalar_one_or_none()

    state_dict = {
        "minute": state.minute,
        "home_goals": state.home_goals,
        "away_goals": state.away_goals,
        "home_red_cards": state.home_red_cards,
        "away_red_cards": state.away_red_cards,
        "home_shots_on_target": state.home_shots_on_target,
        "away_shots_on_target": state.away_shots_on_target,
        "home_possession": state.home_possession,
        "event_type": state.event_type,
        "event_team": state.event_team,
        "home_form": match.home_form if match else 0.5,
        "away_form": match.away_form if match else 0.5,
    }

    return await prediction_service.predict(
        state_dict,
        match_id=match_id,
        home_team=match.home_team if match else "",
        away_team=match.away_team if match else "",
    )
