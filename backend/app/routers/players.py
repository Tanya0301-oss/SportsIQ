"""
Players router — GET /api/v1/players, GET /api/v1/players/{id}/stats
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/players", tags=["players"])


@router.get("", response_model=list[schemas.PlayerOut])
async def list_players(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Player).order_by(models.Player.expected_points.desc()))
    return result.scalars().all()


@router.get("/{player_id}/stats", response_model=schemas.PlayerOut)
async def get_player_stats(player_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.Player).where(models.Player.id == player_id)
    )
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player
