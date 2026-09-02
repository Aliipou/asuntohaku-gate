"""Redis: search result caching and submission throttling. Nothing else.

SPEC section 3 names exactly two uses and says not to invent others, so this
module offers exactly two functions.

Redis is optional. With ``REDIS_URL`` unset the cache misses every time and the
throttle allows every request, which is what lets the test suite and CI run with
no Redis at all. That is a degradation, not a silent success: ``cache_enabled()``
reports it and the health endpoint shows it.
"""

from __future__ import annotations

import json
import os
from typing import Any

import redis

_client: redis.Redis | None = None
_configured = False

SEARCH_TTL_SECONDS = 60


def cache_enabled() -> bool:
    return _get_client() is not None


def _get_client() -> redis.Redis | None:
    global _client, _configured
    if not _configured:
        url = os.environ.get("REDIS_URL")
        _client = redis.from_url(url, decode_responses=True) if url else None
        _configured = True
    return _client


def reset_for_tests() -> None:
    """Forget the cached client so a test can change REDIS_URL."""
    global _client, _configured
    _client = None
    _configured = False


def get_json(key: str) -> Any | None:
    client = _get_client()
    if client is None:
        return None
    try:
        raw = client.get(key)
    except redis.RedisError:
        # A cache that is down must not take the search page down with it.
        return None
    return json.loads(raw) if raw else None


def set_json(key: str, value: Any, ttl_seconds: int = SEARCH_TTL_SECONDS) -> None:
    client = _get_client()
    if client is None:
        return
    try:
        client.setex(key, ttl_seconds, json.dumps(value, ensure_ascii=False))
    except redis.RedisError:
        return


def hit_rate_limit(key: str, limit: int, window_seconds: int) -> bool:
    """Count one request against ``key``. True when the caller is over the limit."""
    client = _get_client()
    if client is None:
        return False
    try:
        pipe = client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds, nx=True)
        count, _ = pipe.execute()
    except redis.RedisError:
        # Fail open: a Redis outage must not stop people applying for a home.
        return False
    return int(count) > limit
