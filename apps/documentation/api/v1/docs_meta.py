"""
Docs/meta API v1 - Endpoint statistics and docs metadata.

GET /api/v1/docs/endpoint-stats/ returns per-endpoint request counts and last_called_at.
"""

from __future__ import annotations

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_http_methods

from apps.documentation.api.v1.api_docs_registry import get_all_endpoint_keys, get_total_endpoint_count
from apps.documentation.utils.api_tracking_storage import get_endpoint_stats


@require_http_methods(["GET"])
def endpoint_stats(request: HttpRequest) -> JsonResponse:
    """
    GET /api/v1/docs/endpoint-stats/

    Returns JSON: { "success": true, "data": { "endpoints": {...}, "total_requests": N, "total_endpoints": N } }
    where endpoints is keyed by endpoint_key with request_count, last_called_at (Unix float or null), etc.
    """
    try:
        keys = get_all_endpoint_keys()
        stats = get_endpoint_stats(keys)
        total_requests = sum(s.get("request_count", 0) or 0 for s in stats.values())
        return JsonResponse({
            "success": True,
            "data": {
                "endpoints": stats,
                "total_requests": total_requests,
                "total_endpoints": get_total_endpoint_count(),
            },
        })
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e),
        }, status=500)
