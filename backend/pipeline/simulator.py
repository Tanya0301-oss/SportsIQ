"""
Realistic live football match simulator.
Generates minute-by-minute events for demo matches without requiring an external API.

Each match progresses from minute 0 to 90 with probabilistic events:
  - Goals (Poisson-distributed, ~2.7 per match average)
  - Yellow cards (~3 per match)
  - Red cards (~0.3 per match)
  - Possession drift
  - Shots on target

Publishes to the pub/sub system so the Kafka consumer pattern is preserved.
"""
import asyncio
import random
import json
from datetime import datetime
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.config import get_settings
from app.database import AsyncSessionLocal
from app import models
from app.services import cache

settings = get_settings()

# Probability per minute for each event type
GOAL_PROB = 0.025          # ~2.25 goals per 90 min
YELLOW_PROB = 0.033        # ~3 yellows
RED_PROB = 0.003           # ~0.27 reds
SHOT_PROB = 0.08           # shots on target (per team)


class MatchSimulator:
    """
    Manages simulation state for a single live match.
    """
    def __init__(self, match_id: int, home_team: str, away_team: str,
                 home_form: float = 0.5, away_form: float = 0.5):
        self.match_id = match_id
        self.home_team = home_team
        self.away_team = away_team
        self.home_form = home_form
        self.away_form = away_form

        # State
        self.minute = 0
        self.home_goals = 0
        self.away_goals = 0
        self.home_red = 0
        self.away_red = 0
        self.home_yellow = 0
        self.away_yellow = 0
        self.home_shots = 0
        self.away_shots = 0
        self.home_possession = 50.0 + (home_form - 0.5) * 20   # form → possession
        self.finished = False

    def _home_prob_multiplier(self) -> float:
        """Home team scores more when ahead in form and has more possession."""
        return 0.5 + self.home_form * 0.5

    def _away_prob_multiplier(self) -> float:
        return 0.5 + self.away_form * 0.5

    def tick(self) -> dict:
        """Advance one minute and return the event dict."""
        if self.finished:
            return self._build_state("finished", "")

        self.minute += 1
        if self.minute > 90:
            self.finished = True
            return self._build_state("finished", "")

        event_type = "tick"
        event_team = ""

        # Injury time: extend up to 95 min
        if self.minute == 90:
            self.minute += random.randint(2, 5)

        # Goal events
        home_mult = self._home_prob_multiplier()
        away_mult = self._away_prob_multiplier()

        # Reduce probabilities if a team has red card
        home_goal_p = GOAL_PROB * home_mult * max(0.4, 1 - self.home_red * 0.3)
        away_goal_p = GOAL_PROB * away_mult * max(0.4, 1 - self.away_red * 0.3)

        if random.random() < home_goal_p:
            self.home_goals += 1
            event_type = "goal"
            event_team = "home"
        elif random.random() < away_goal_p:
            self.away_goals += 1
            event_type = "goal"
            event_team = "away"

        # Yellow cards
        if event_type == "tick":
            if random.random() < YELLOW_PROB:
                event_type = "yellow_card"
                event_team = random.choice(["home", "away"])
                if event_team == "home":
                    self.home_yellow += 1
                else:
                    self.away_yellow += 1

        # Red cards (rare)
        if event_type == "tick" and self.minute > 20:
            if random.random() < RED_PROB:
                event_type = "red_card"
                event_team = random.choice(["home", "away"])
                if event_team == "home":
                    self.home_red += 1
                    self.home_possession = max(30, self.home_possession - 5)
                else:
                    self.away_red += 1
                    self.home_possession = min(70, self.home_possession + 5)

        # Shots on target
        if random.random() < SHOT_PROB:
            self.home_shots += 1
        if random.random() < SHOT_PROB:
            self.away_shots += 1

        # Possession drift (random walk ±0.5 per minute)
        self.home_possession = max(25, min(75, self.home_possession + random.uniform(-0.5, 0.5)))

        return self._build_state(event_type, event_team)

    def _build_state(self, event_type: str, event_team: str) -> dict:
        return {
            "match_id": self.match_id,
            "minute": self.minute,
            "home_goals": self.home_goals,
            "away_goals": self.away_goals,
            "home_red_cards": self.home_red,
            "away_red_cards": self.away_red,
            "home_yellow_cards": self.home_yellow,
            "away_yellow_cards": self.away_yellow,
            "home_shots_on_target": self.home_shots,
            "away_shots_on_target": self.away_shots,
            "home_possession": round(self.home_possession, 1),
            "event_type": event_type,
            "event_team": event_team,
        }


# ── Simulator runner ─────────────────────────────────────────────────────────

_active_simulators: dict[int, MatchSimulator] = {}


async def run_match_simulation(match_id: int):
    """
    Background task: simulates a live match, writing states to DB
    and publishing events to the pub/sub system.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(models.Match).where(models.Match.id == match_id))
        match = result.scalar_one_or_none()
        if not match:
            logger.error(f"Match {match_id} not found")
            return

        sim = MatchSimulator(
            match_id=match_id,
            home_team=match.home_team,
            away_team=match.away_team,
            home_form=match.home_form,
            away_form=match.away_form,
        )
        _active_simulators[match_id] = sim

        # Mark match as live
        await db.execute(
            update(models.Match)
            .where(models.Match.id == match_id)
            .values(status="live")
        )
        await db.commit()

    logger.info(f"Simulator started for match {match_id}: {match.home_team} vs {match.away_team}")

    tick_interval = settings.simulator_tick_seconds

    while not sim.finished:
        state = sim.tick()

        # Write state to DB
        async with AsyncSessionLocal() as db:
            db.add(models.MatchState(**state))
            await db.execute(
                update(models.Match)
                .where(models.Match.id == match_id)
                .values(
                    home_goals=state["home_goals"],
                    away_goals=state["away_goals"],
                )
            )
            await db.commit()

        # Publish raw state event for the consumer/prediction pipeline
        await cache.publish(f"match:{match_id}:state", state)

        if state["event_type"] != "tick":
            logger.info(
                f"Match {match_id} min {state['minute']}: "
                f"{state['event_type'].upper()} ({state['event_team']}) | "
                f"{state['home_goals']}-{state['away_goals']}"
            )

        await asyncio.sleep(tick_interval)

    # Mark match as finished
    async with AsyncSessionLocal() as db:
        await db.execute(
            update(models.Match)
            .where(models.Match.id == match_id)
            .values(status="finished")
        )
        await db.commit()

    logger.info(f"Match {match_id} simulation finished")
    _active_simulators.pop(match_id, None)


async def start_all_live_matches():
    """Called at app startup to resume any matches already marked live."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(models.Match).where(models.Match.status == "scheduled")
        )
        matches = result.scalars().all()

    for match in matches:
        asyncio.create_task(run_match_simulation(match.id))
        logger.info(f"Queued simulation for match {match.id}")
