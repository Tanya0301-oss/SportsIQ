"""
In-memory cache and pub/sub services.
For local dev: uses Python dicts + asyncio queues (no Redis required).
For production: swap to Redis by setting REDIS_URL in environment.

The interface is identical regardless of backend, so the rest of the app
doesn't need to know which is active.
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Callable
from loguru import logger
from app.config import get_settings

settings = get_settings()

# ── In-memory storage ─────────────────────────────────────────────────────────

_cache: dict[str, tuple[Any, datetime]] = {}          # key → (value, expires_at)
_subscribers: dict[str, list[asyncio.Queue]] = {}      # channel → [queues]


# ── Cache operations ─────────────────────────────────────────────────────────

async def cache_set(key: str, value: Any, ttl_seconds: int = 60) -> None:
    """Store a value with TTL. Falls back to Redis if configured."""
    if settings.redis_url:
        await _redis_set(key, value, ttl_seconds)
        return
    expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
    _cache[key] = (value, expires_at)


async def cache_get(key: str) -> Any | None:
    """Retrieve a cached value, returning None if missing or expired."""
    if settings.redis_url:
        return await _redis_get(key)
    entry = _cache.get(key)
    if entry is None:
        return None
    value, expires_at = entry
    if datetime.utcnow() > expires_at:
        del _cache[key]
        return None
    return value


# ── Pub/sub operations ───────────────────────────────────────────────────────

async def publish(channel: str, message: dict) -> None:
    """Publish a message to a channel."""
    if settings.redis_url:
        await _redis_publish(channel, message)
        return
    queues = _subscribers.get(channel, [])
    payload = json.dumps(message)
    for q in queues:
        await q.put(payload)
    logger.debug(f"Published to {channel} ({len(queues)} subscribers)")


async def subscribe(channel: str) -> asyncio.Queue:
    """Subscribe to a channel, returns a queue that receives messages."""
    if settings.redis_url:
        return await _redis_subscribe(channel)
    q: asyncio.Queue = asyncio.Queue()
    _subscribers.setdefault(channel, []).append(q)
    return q


async def unsubscribe(channel: str, queue: asyncio.Queue) -> None:
    """Remove a subscription."""
    if settings.redis_url:
        return  # Redis handles cleanup automatically
    queues = _subscribers.get(channel, [])
    if queue in queues:
        queues.remove(queue)


# ── Redis backend (only imported if REDIS_URL is set) ────────────────────────

_redis_client = None


async def _get_redis():
    global _redis_client
    if _redis_client is None:
        import redis.asyncio as aioredis
        _redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


async def _redis_set(key: str, value: Any, ttl: int):
    r = await _get_redis()
    await r.setex(key, ttl, json.dumps(value))


async def _redis_get(key: str) -> Any | None:
    r = await _get_redis()
    raw = await r.get(key)
    return json.loads(raw) if raw else None


async def _redis_publish(channel: str, message: dict):
    r = await _get_redis()
    await r.publish(channel, json.dumps(message))


async def _redis_subscribe(channel: str) -> asyncio.Queue:
    r = await _get_redis()
    pubsub = r.pubsub()
    await pubsub.subscribe(channel)
    q: asyncio.Queue = asyncio.Queue()

    async def _listener():
        async for msg in pubsub.listen():
            if msg["type"] == "message":
                await q.put(msg["data"])

    asyncio.create_task(_listener())
    return q
