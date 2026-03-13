from __future__ import annotations

import json
import logging
import time
from typing import Any

from .config import settings


logger = logging.getLogger("signal-feed-cache")


class CacheClient:
    def __init__(self) -> None:
        self._memory: dict[str, tuple[float | None, str]] = {}
        self._redis = None
        if settings.enable_redis:
            try:
                from redis import Redis

                self._redis = Redis.from_url(settings.redis_url, decode_responses=True)
                self._redis.ping()
            except Exception as exc:
                logger.warning("Redis unavailable, falling back to memory cache: %s", exc)
                self._redis = None

    def get_json(self, key: str) -> Any | None:
        if self._redis:
            raw = self._redis.get(key)
            return json.loads(raw) if raw else None

        item = self._memory.get(key)
        if item is None:
            return None
        expires_at, raw = item
        if expires_at is not None and expires_at <= time.time():
            self._memory.pop(key, None)
            return None
        return json.loads(raw)

    def set_json(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        raw = json.dumps(value)
        ttl = ttl_seconds or settings.cache_ttl_seconds
        if self._redis:
            self._redis.set(key, raw, ex=ttl)
            return
        expires_at = time.time() + ttl if ttl > 0 else None
        self._memory[key] = (expires_at, raw)

    def publish(self, channel: str, value: Any) -> None:
        raw = json.dumps(value)
        if self._redis:
            self._redis.publish(channel, raw)
        else:
            self._memory[f"pubsub:{channel}"] = (time.time() + 30, raw)

    def invalidate(self, key: str) -> None:
        if self._redis:
            self._redis.delete(key)
        else:
            self._memory.pop(key, None)


cache = CacheClient()
