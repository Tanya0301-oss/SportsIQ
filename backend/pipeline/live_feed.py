"""
Real-time football match data from football-data.org API.

This module fetches live match data and publishes match state events
to the pub/sub system, replacing the simulator for production use.

Matches are polled every 30 seconds for updates (respects API rate limits).

API: https://www.football-data.org/
Free tier: 10 requests/min, includes live matches in current season
"""
import asyncio
import json
from datetime import datetime

import httpx
from loguru import logger
from sqlalchemy import select, update

from app import models
from app.config import get_settings
from app.database import AsyncSessionLocal
from app.services import cache

settings = get_settings()


class LiveFeedManager:
    """
    Manages polling of football-data.org API and publishes match state events.
    """

    def __init__(self):
        self.client: httpx.AsyncClient | None = None
        self.seen_states = {}  # Track published states to avoid duplicates

    async def init_client(self):
        """Initialize HTTP client with API key."""
        if not settings.football_data_api_key:
            raise ValueError(
                "FOOTBALL_DATA_API_KEY not set. Get free key from https://www.football-data.org/"
            )
        self.client = httpx.AsyncClient(
            base_url=settings.football_data_base_url,
            headers={"X-Auth-Token": settings.football_data_api_key},
            timeout=30.0,
        )
        logger.info("Football-Data.org client initialized")

    async def close_client(self):
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()

    async def fetch_matches(self) -> list[dict]:
        """Fetch all live and upcoming matches from the API."""
        if not self.client:
            await self.init_client()

        try:
            # Fetch matches for active leagues
            all_matches = []
            for league in settings.active_leagues:
                try:
                    response = await self.client.get(f"/competitions/{league}/matches")
                    if response.status_code == 200:
                        data = response.json()
                        matches = data.get("matches", [])
                        all_matches.extend(matches)
                        logger.debug(f"Fetched {len(matches)} matches from league {league}")
                    elif response.status_code == 429:
                        logger.warning("Rate limited by API — waiting before retry")
                        return []
                    else:
                        logger.warning(f"API error for league {league}: {response.status_code}")
                except Exception as e:
                    logger.warning(f"Error fetching league {league}: {e}")
                    continue

            return all_matches
        except Exception as e:
            logger.error(f"Error fetching matches: {e}")
            return []

    async def sync_match_to_db(self, api_match: dict) -> models.Match | None:
        """Sync API match data to database, create or update."""
        try:
            match_id = api_match.get("id")
            home_team = api_match.get("homeTeam", {}).get("name", "Unknown")
            away_team = api_match.get("awayTeam", {}).get("name", "Unknown")
            status = api_match.get("status", "SCHEDULED").lower()

            # Map API status to our status
            status_map = {
                "scheduled": "scheduled",
                "live": "live",
                "in_play": "live",
                "paused": "live",
                "finished": "finished",
                "postponed": "scheduled",
                "suspended": "scheduled",
            }
            db_status = status_map.get(status, "scheduled")

            # Parse match date
            utc_date = api_match.get("utcDate")
            match_date = datetime.fromisoformat(utc_date.replace("Z", "+00:00")) if utc_date else datetime.utcnow()

            league = api_match.get("competition", {}).get("name", "Unknown League")
            season = api_match.get("season", {}).get("currentSeason", "2024/25")

            async with AsyncSessionLocal() as db:
                # Check if match exists
                result = await db.execute(
                    select(models.Match).where(models.Match.id == match_id)
                )
                match = result.scalar_one_or_none()

                if not match:
                    # Create new match
                    match = models.Match(
                        id=match_id,
                        home_team=home_team,
                        away_team=away_team,
                        league=league,
                        season=str(season),
                        match_date=match_date,
                        status=db_status,
                        home_form=0.5,  # Will be calculated from historical data
                        away_form=0.5,
                        venue=api_match.get("venue", "Unknown"),
                    )
                    db.add(match)
                    logger.info(f"Created new match: {home_team} vs {away_team} (ID: {match_id})")
                else:
                    # Update existing match status and goals
                    await db.execute(
                        update(models.Match)
                        .where(models.Match.id == match_id)
                        .values(
                            status=db_status,
                            home_goals=api_match.get("score", {}).get("fullTime", {}).get("home", 0),
                            away_goals=api_match.get("score", {}).get("fullTime", {}).get("away", 0),
                        )
                    )

                await db.commit()
                return match

        except Exception as e:
            logger.error(f"Error syncing match {api_match.get('id')}: {e}")
            return None

    async def extract_match_state(self, api_match: dict) -> dict | None:
        """Extract current match state from API response."""
        try:
            match_id = api_match.get("id")
            status = api_match.get("status", "SCHEDULED").lower()

            # Only process live and finished matches
            if status not in ["live", "in_play", "paused", "finished"]:
                return None

            score = api_match.get("score", {})

            # Get current score (live score)
            home_goals = score.get("fullTime", {}).get("home") or score.get("current", {}).get("home") or 0
            away_goals = score.get("fullTime", {}).get("away") or score.get("current", {}).get("away") or 0

            # Calculate minute based on status
            minute = 0
            if status in ["live", "in_play", "paused"]:
                # API doesn't directly give minute, estimate from elapsed time
                minute = 45  # Simplified: assume match is in progress
            elif status == "finished":
                minute = 90

            state = {
                "match_id": match_id,
                "minute": minute,
                "home_goals": home_goals,
                "away_goals": away_goals,
                "home_red_cards": 0,  # API doesn't expose directly in free tier
                "away_red_cards": 0,
                "home_yellow_cards": 0,
                "away_yellow_cards": 0,
                "home_shots_on_target": score.get("shots", {}).get("home", 0) if score.get("shots") else 0,
                "away_shots_on_target": score.get("shots", {}).get("away", 0) if score.get("shots") else 0,
                "home_possession": 50.0,  # API free tier doesn't include possession
                "event_type": "tick",
                "event_team": "",
                "status": status,
            }
            return state

        except Exception as e:
            logger.error(f"Error extracting state for match {api_match.get('id')}: {e}")
            return None

    async def publish_match_states(self, api_matches: list[dict]):
        """Publish all match states to pub/sub system."""
        for api_match in api_matches:
            state = await self.extract_match_state(api_match)
            if not state:
                continue

            match_id = state["match_id"]
            state_key = f"{match_id}:{state['minute']}:{state['home_goals']}:{state['away_goals']}"

            # Skip if we already published this exact state
            if match_id in self.seen_states and self.seen_states[match_id] == state_key:
                continue

            self.seen_states[match_id] = state_key

            # Publish to pub/sub
            await cache.publish(f"match:{match_id}:state", json.dumps(state))
            logger.debug(f"Published state for match {match_id}: {state['home_goals']}-{state['away_goals']} @ {state['minute']}'")

    async def poll_and_publish(self):
        """Main polling loop — fetch API every 30 seconds and publish updates."""
        logger.info("🔴 Live feed started (polling football-data.org)")

        try:
            while True:
                # Fetch all matches from API
                api_matches = await self.fetch_matches()

                if api_matches:
                    # Sync to database
                    for api_match in api_matches:
                        await self.sync_match_to_db(api_match)

                    # Publish states to pub/sub
                    await self.publish_match_states(api_matches)

                # Wait before next poll
                await asyncio.sleep(settings.live_feed_poll_seconds)

        except asyncio.CancelledError:
            logger.info("Live feed polling stopped")
        except Exception as e:
            logger.error(f"Live feed error: {e}")
        finally:
            await self.close_client()


# Global instance
_feed_manager: LiveFeedManager | None = None


async def start_live_feed() -> asyncio.Task:
    """Start the live feed polling task."""
    global _feed_manager
    _feed_manager = LiveFeedManager()
    task = asyncio.create_task(_feed_manager.poll_and_publish())
    return task


async def get_feed_manager() -> LiveFeedManager:
    """Get the current feed manager instance."""
    global _feed_manager
    if not _feed_manager:
        _feed_manager = LiveFeedManager()
    return _feed_manager
