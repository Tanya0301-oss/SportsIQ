"""
Prediction consumer — subscribes to match state pub/sub events,
runs ML inference, and publishes predictions back out.

In production this would read from Kafka. Locally it reads from
the in-memory pub/sub that the simulator publishes to.
"""
import asyncio
import json
from loguru import logger

from app.services.cache import subscribe, unsubscribe
from app.services import prediction_service
from app.database import AsyncSessionLocal
from app import models
from sqlalchemy import select


async def handle_state_event(event: dict):
    """Process one match state event: run inference, save to DB, publish prediction."""
    match_id = event.get("match_id")
    if match_id is None:
        return

    # Fetch match metadata for team names + form
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(models.Match).where(models.Match.id == match_id)
        )
        match = result.scalar_one_or_none()

    if not match:
        return

    state = {**event, "home_form": match.home_form, "away_form": match.away_form}

    # Run ML inference (publishes prediction to match:{id}:prediction channel)
    prediction = await prediction_service.predict(
        state,
        match_id=match_id,
        home_team=match.home_team,
        away_team=match.away_team,
    )

    # Persist prediction to DB
    async with AsyncSessionLocal() as db:
        shap_dict = {f["feature"]: f["shap_value"] for f in prediction.get("shap_features", [])}
        feature_dict = {f["feature"]: f["raw_value"] for f in prediction.get("shap_features", [])}

        pred_record = models.Prediction(
            match_id=match_id,
            minute=prediction["minute"],
            prob_home_win=prediction["prob_home_win"],
            prob_draw=prediction["prob_draw"],
            prob_away_win=prediction["prob_away_win"],
            shap_values=shap_dict,
            feature_values=feature_dict,
        )
        db.add(pred_record)
        await db.commit()


async def _watch_match(match_id: int):
    """Subscribe to a single match's state events."""
    channel = f"match:{match_id}:state"
    queue = await subscribe(channel)
    logger.info(f"Consumer watching channel: {channel}")
    try:
        while True:
            try:
                raw = await asyncio.wait_for(queue.get(), timeout=120.0)
                event = json.loads(raw) if isinstance(raw, str) else raw
                if event.get("event_type") == "finished":
                    logger.info(f"Match {match_id} finished — stopping consumer")
                    break
                await handle_state_event(event)
            except asyncio.TimeoutError:
                continue
    finally:
        await unsubscribe(channel, queue)


async def start_consumer():
    """
    Start watching all live/scheduled matches.
    Spawns one watcher task per match.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(models.Match).where(
                models.Match.status.in_(["scheduled", "live"])
            )
        )
        matches = result.scalars().all()

    tasks = [asyncio.create_task(_watch_match(m.id)) for m in matches]
    logger.info(f"Consumer started watching {len(tasks)} matches")

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        for t in tasks:
            t.cancel()
        logger.info("Consumer shut down")
