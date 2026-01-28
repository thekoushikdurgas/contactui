"""
Statistics API endpoints - Call services directly.

These endpoints provide statistics data for the dashboard.
Replaces API v1 statistics endpoints with direct service calls.
Matches API v1 response format for compatibility.
"""

import logging
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

from apps.documentation.services import (
    get_pages_service,
    get_endpoints_service,
    get_relationships_service,
    get_postman_service,
    get_shared_s3_index_manager,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Pages Statistics Endpoints
# =============================================================================

@login_required
@require_http_methods(["GET"])
def statistics_pages_statistics(request: HttpRequest) -> JsonResponse:
    """
    GET /docs/api/statistics/pages/statistics/
    
    Returns pages index statistics.
    Matches API v1 /api/v1/pages/statistics/ format.
    """
    try:
        index_manager = get_shared_s3_index_manager()
        index_data = index_manager.read_index("pages")
        return JsonResponse({
            "total": index_data.get("total", 0),
            "version": index_data.get("version"),
            "last_updated": index_data.get("last_updated"),
            "statistics": index_data.get("statistics", {}),
            "indexes": index_data.get("indexes", {}),
        })
    except Exception as e:
        logger.exception("statistics pages statistics failed")
        return JsonResponse({"detail": str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def statistics_pages_types(request: HttpRequest) -> JsonResponse:
    """
    GET /docs/api/statistics/pages/types/
    
    Returns page types with counts.
    Matches API v1 /api/v1/pages/types/ format.
    """
    try:
        pages_service = get_pages_service()
        types_data = []
        for pt in ["docs", "marketing", "dashboard"]:
            count = pages_service.count_pages_by_type(pt)
            types_data.append({"type": pt, "count": count})
        total = sum(t["count"] for t in types_data)
        return JsonResponse({"types": types_data, "total": total})
    except Exception as e:
        logger.exception("statistics pages types failed")
        return JsonResponse({"types": [], "total": 0})


# =============================================================================
# Endpoints Statistics Endpoints
# =============================================================================

@login_required
@require_http_methods(["GET"])
def statistics_endpoints_api_versions(request: HttpRequest) -> JsonResponse:
    """
    GET /docs/api/statistics/endpoints/api-versions/
    
    Returns API versions with counts.
    Matches API v1 /api/v1/endpoints/api-versions/ format.
    """
    try:
        endpoints_service = get_endpoints_service()
        stats = endpoints_service.get_api_version_statistics()
        return JsonResponse(stats)
    except Exception as e:
        logger.exception("statistics endpoints api-versions failed")
        return JsonResponse({"versions": [], "total": 0})


@login_required
@require_http_methods(["GET"])
def statistics_endpoints_methods(request: HttpRequest) -> JsonResponse:
    """
    GET /docs/api/statistics/endpoints/methods/
    
    Returns HTTP/GraphQL methods with counts.
    Matches API v1 /api/v1/endpoints/methods/ format.
    """
    try:
        endpoints_service = get_endpoints_service()
        stats = endpoints_service.get_method_statistics()
        return JsonResponse(stats)
    except Exception as e:
        logger.exception("statistics endpoints methods failed")
        return JsonResponse({"methods": [], "total": 0})


# =============================================================================
# Relationships Statistics Endpoints
# =============================================================================

@login_required
@require_http_methods(["GET"])
def statistics_relationships_statistics(request: HttpRequest) -> JsonResponse:
    """
    GET /docs/api/statistics/relationships/statistics/
    
    Returns relationships statistics.
    Matches API v1 /api/v1/relationships/statistics/ format.
    """
    try:
        relationships_service = get_relationships_service()
        stats = relationships_service.get_statistics()
        return JsonResponse(stats)
    except Exception as e:
        logger.exception("statistics relationships statistics failed")
        return JsonResponse({
            "total_relationships": 0,
            "unique_pages": 0,
            "unique_endpoints": 0
        })


# =============================================================================
# Postman Statistics Endpoints
# =============================================================================

@login_required
@require_http_methods(["GET"])
def statistics_postman_statistics(request: HttpRequest) -> JsonResponse:
    """
    GET /docs/api/statistics/postman/statistics/
    
    Returns postman statistics.
    Matches API v1 /api/v1/postman/statistics/ format.
    """
    try:
        postman_service = get_postman_service()
        stats = postman_service.get_statistics()
        return JsonResponse(stats)
    except Exception as e:
        logger.exception("statistics postman statistics failed")
        return JsonResponse({})
