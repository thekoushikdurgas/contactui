"""
Admin utilities for logs and shared helpers.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from urllib.parse import urlencode


# Valid time ranges for Lambda logs.api
VALID_TIME_RANGES = ("1h", "24h", "7d", "30d")
TIME_RANGE_DELTAS = {
    "1h": timedelta(hours=1),
    "24h": timedelta(days=1),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}


def time_range_to_iso(
    time_range: str,
) -> Tuple[Optional[str], Optional[str]]:
    """Convert time_range (1h, 24h, 7d, 30d) to (start_time, end_time) ISO strings.

    Args:
        time_range: One of '1h', '24h', '7d', '30d'

    Returns:
        Tuple of (start_time_iso, end_time_iso) or (None, None) if invalid
    """
    if time_range not in TIME_RANGE_DELTAS:
        return None, None
    now = datetime.now(timezone.utc)
    delta = TIME_RANGE_DELTAS[time_range]
    start = now - delta
    return start.isoformat(), now.isoformat()


def build_logs_query_params(
    *,
    page: int = 1,
    per_page: int = 50,
    time_range: str = "24h",
    level: str = "",
    logger_filter: str = "",
    user_id: str = "",
    search: str = "",
) -> str:
    """Build query string for admin logs URL with all filter params preserved.

    Args:
        page: Current page number
        per_page: Items per page
        time_range: Time range filter
        level: Log level filter
        logger_filter: Logger name filter
        user_id: User ID filter
        search: Full-text search query

    Returns:
        Query string (without leading '?')
    """
    params = {"page": page}
    if per_page not in (10, 25, 50, 100):
        per_page = 50
    params["per_page"] = per_page
    if time_range in VALID_TIME_RANGES:
        params["time_range"] = time_range
    if level:
        params["level"] = level
    if logger_filter:
        params["logger"] = logger_filter
    if user_id:
        params["user_id"] = user_id
    if search:
        params["search"] = search
    return urlencode(params)
