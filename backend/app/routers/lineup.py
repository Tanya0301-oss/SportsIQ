"""
Lineup optimizer router — POST /api/v1/lineup/optimize
"""
from fastapi import APIRouter

from app.schemas import LineupRequest, LineupResponse
from optimizer.lineup import optimise_lineup

router = APIRouter(prefix="/lineup", tags=["lineup"])


@router.post("/optimize", response_model=dict)
async def optimize_lineup(request: LineupRequest):
    """
    Solve the fantasy lineup ILP problem.
    Returns optimal squad within budget and formation constraints.
    """
    players_dicts = [p.model_dump() for p in request.players]
    result = optimise_lineup(players_dicts, budget=request.budget, formation=request.formation)
    return result
