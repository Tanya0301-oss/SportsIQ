"""
Matches router — GET /api/v1/matches, GET /api/v1/matches/{id}
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.database import get_db
from app.services.cache import cache_get

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=list[schemas.MatchOut])
async def list_matches(db: AsyncSession = Depends(get_db)):
    """Return all matches sorted by date, most recent first."""
    result = await db.execute(
        select(models.Match).order_by(models.Match.match_date.desc())
    )
    return result.scalars().all()


@router.get("/{match_id}", response_model=schemas.MatchOut)
async def get_match(match_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.Match).where(models.Match.id == match_id)
    )
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match


@router.get("/{match_id}/state", response_model=schemas.MatchStateOut | None)
async def get_latest_state(match_id: int, db: AsyncSession = Depends(get_db)):
    """Return the latest match state (most recent minute)."""
    result = await db.execute(
        select(models.MatchState)
        .where(models.MatchState.match_id == match_id)
        .order_by(models.MatchState.minute.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()
