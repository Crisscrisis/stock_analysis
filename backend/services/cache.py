"""Simple in-memory TTL cache to reduce external API calls."""
from __future__ import annotations

import time
from typing import Any


class TTLCache:
    def __init__(self, ttl: float = 10.0) -> None:
        self._ttl = ttl
        self._store: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Any | None:
        if key not in self._store:
            return None
        value, expires_at = self._store[key]
        if time.monotonic() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (value, time.monotonic() + self._ttl)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()


# Global cache instances (TTL in seconds)
quote_cache = TTLCache(ttl=10)
ohlcv_cache = TTLCache(ttl=60)
fundamentals_cache = TTLCache(ttl=3600)
