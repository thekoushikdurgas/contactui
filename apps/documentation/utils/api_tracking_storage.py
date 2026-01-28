"""
API request tracking storage: record hits and read per-endpoint statistics.

Uses Django cache (Redis or LocMem) with keys:
- api_tracking:count:{endpoint_key}
- api_tracking:last_ts:{endpoint_key}

Optional (for success rate / duration):
- api_tracking:status_2xx:{endpoint_key}, status_4xx, status_5xx
- api_tracking:duration_sum:{endpoint_key}, duration_count
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List

from django.core.cache import cache

logger = logging.getLogger(__name__)

NAMESPACE = "api_tracking"
# Long TTL for count/last_ts so stats persist (e.g. 30 days); cache backends may cap
DEFAULT_TTL = 60 * 60 * 24 * 30  # 30 days


def _key(suffix: str, endpoint_key: str) -> str:
    return f"{NAMESPACE}:{suffix}:{endpoint_key}"


def record_hit(endpoint_key: str, status_code: int, duration_ms: float) -> None:
    """
    Record one request hit for the given endpoint.
    Does not raise; logs and returns on cache errors.
    """
    if not endpoint_key:
        return
    try:
        # Count: increment (Redis) or get+set (LocMem)
        count_key = _key("count", endpoint_key)
        try:
            cache.incr(count_key)
        except (ValueError, TypeError):
            # Key missing or backend doesn't support incr
            count = cache.get(count_key, 0) or 0
            cache.set(count_key, count + 1, DEFAULT_TTL)

        # Last called timestamp
        cache.set(_key("last_ts", endpoint_key), time.time(), DEFAULT_TTL)

        # Optional: status buckets
        if 200 <= status_code < 300:
            _incr_or_set(_key("status_2xx", endpoint_key))
        elif 400 <= status_code < 500:
            _incr_or_set(_key("status_4xx", endpoint_key))
        elif status_code >= 500:
            _incr_or_set(_key("status_5xx", endpoint_key))

        # Optional: duration for average (get/set to support float)
        dur_sum_key = _key("duration_sum", endpoint_key)
        dur_count_key = _key("duration_count", endpoint_key)
        _incr_or_set(dur_count_key)
        s = cache.get(dur_sum_key, 0) or 0
        cache.set(dur_sum_key, s + duration_ms, DEFAULT_TTL)
    except Exception as e:
        logger.warning("api_tracking record_hit failed for %s: %s", endpoint_key, e)


def _incr_or_set(key: str) -> None:
    try:
        cache.incr(key)
    except (ValueError, TypeError):
        val = cache.get(key, 0) or 0
        cache.set(key, val + 1, DEFAULT_TTL)


def get_endpoint_stats(endpoint_keys: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Return per-endpoint stats for the given keys.
    Each value has: request_count, last_called_at (Unix float or None), and optionally
    status_2xx, status_4xx, status_5xx, avg_duration_ms.
    """
    result: Dict[str, Dict[str, Any]] = {}
    for key in endpoint_keys:
        result[key] = _get_single_stats(key)
    return result


def _get_single_stats(endpoint_key: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "request_count": 0,
        "last_called_at": None,
    }
    try:
        count = cache.get(_key("count", endpoint_key))
        if count is not None:
            out["request_count"] = int(count)
        ts = cache.get(_key("last_ts", endpoint_key))
        if ts is not None:
            out["last_called_at"] = float(ts)
        s2 = cache.get(_key("status_2xx", endpoint_key))
        s4 = cache.get(_key("status_4xx", endpoint_key))
        s5 = cache.get(_key("status_5xx", endpoint_key))
        if s2 is not None or s4 is not None or s5 is not None:
            out["status_2xx"] = int(s2 or 0)
            out["status_4xx"] = int(s4 or 0)
            out["status_5xx"] = int(s5 or 0)
        dur_sum = cache.get(_key("duration_sum", endpoint_key))
        dur_count = cache.get(_key("duration_count", endpoint_key))
        if dur_count and int(dur_count) > 0 and dur_sum is not None:
            out["avg_duration_ms"] = round(float(dur_sum) / int(dur_count), 2)
    except Exception as e:
        logger.warning("api_tracking get_endpoint_stats failed for %s: %s", endpoint_key, e)
    return out
