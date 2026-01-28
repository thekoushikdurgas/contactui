"""API docs UI view: list of all GET endpoints with per-endpoint statistics."""

from __future__ import annotations

import math
import time

from django.http import HttpRequest
from django.shortcuts import render

from apps.documentation.api.v1.api_docs_registry import (
    GROUPS,
    get_all_endpoint_keys,
    get_total_endpoint_count,
)
from apps.documentation.utils.api_tracking_storage import get_endpoint_stats


def _format_last_called(ts: float | None) -> str:
    """Return human-readable last-called time (e.g. '2 min ago', 'Never')."""
    if ts is None:
        return "Never"
    now = time.time()
    delta = now - ts
    if delta < 60:
        return "Just now"
    if delta < 3600:
        m = max(1, int(math.floor(delta / 60)))
        return f"{m} min ago"
    if delta < 86400:
        h = max(1, int(math.floor(delta / 3600)))
        return f"{h} hour{'s' if h != 1 else ''} ago"
    if delta < 604800:
        d = max(1, int(math.floor(delta / 86400)))
        return f"{d} day{'s' if d != 1 else ''} ago"
    return "Long ago"


def api_docs_index(request: HttpRequest):
    """
    Render the API reference page at /api/docs/ with all registered GET endpoints
    and their usage statistics (request count, last called).
    """
    keys = get_all_endpoint_keys()
    stats = get_endpoint_stats(keys)

    # Attach stats to each endpoint in groups; add last_called_display
    groups_with_stats = []
    for group in GROUPS:
        endpoints_with_stats = []
        for ep in group["endpoints"]:
            key = ep["endpoint_key"]
            ep_copy = dict(ep)
            s = stats.get(key, {})
            ep_copy["stats"] = s
            ep_copy["last_called_display"] = _format_last_called(s.get("last_called_at"))
            endpoints_with_stats.append(ep_copy)
        groups_with_stats.append({
            **group,
            "endpoints": endpoints_with_stats,
            "count": len(endpoints_with_stats),
        })

    total = get_total_endpoint_count()
    total_requests = sum(s.get("request_count", 0) or 0 for s in stats.values())

    context = {
        "groups": groups_with_stats,
        "total_endpoints": total,
        "total_requests": total_requests,
    }
    return render(request, "documentation/api_docs/index.html", context)
