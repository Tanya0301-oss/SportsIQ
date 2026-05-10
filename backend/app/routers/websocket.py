"""
WebSocket router — WS /ws/match/{id}

Connection flow:
  1. Client connects
  2. Server immediately sends the latest cached prediction
  3. Server subscribes to in-memory pub/sub for match:{id}:prediction
  4. Every time the simulator publishes a new prediction, it's pushed to the client
  5. On disconnect, subscription is cleaned up
"""
import asyncio
import json

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.database import get_db
from app.services.cache import cache_get, subscribe, unsubscribe
from app.ws.manager import manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/match/{match_id}")
async def match_websocket(match_id: int, ws: WebSocket):
    await manager.connect(match_id, ws)

    # Send latest cached prediction immediately on connect
    cached = await cache_get(f"pred:{match_id}")
    if cached:
        try:
            await ws.send_text(json.dumps(cached))
        except Exception:
            pass

    # Subscribe to pub/sub channel
    queue = await subscribe(f"match:{match_id}:prediction")

    try:
        while True:
            # Wait for next prediction from the pub/sub queue
            try:
                message = await asyncio.wait_for(queue.get(), timeout=30.0)
                payload = json.loads(message) if isinstance(message, str) else message
                await ws.send_text(json.dumps(payload))
            except asyncio.TimeoutError:
                # Send a heartbeat ping to keep connection alive
                try:
                    await ws.send_text(json.dumps({"type": "heartbeat"}))
                except Exception:
                    break
    except WebSocketDisconnect:
        logger.info(f"WS client disconnected from match {match_id}")
    except Exception as e:
        logger.warning(f"WS error for match {match_id}: {e}")
    finally:
        manager.disconnect(match_id, ws)
        await unsubscribe(f"match:{match_id}:prediction", queue)
