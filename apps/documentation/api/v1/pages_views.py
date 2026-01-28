"""
Pages API v1 - Lambda-parity GET endpoints (20 routes).

Response shapes match Lambda documentation.api for compatibility.
Static routes must be defined before parameterized ones ({page_id}, {user_type}).
"""

from __future__ import annotations

import logging
from django.views.decorators.http import require_http_methods
from django.http import HttpRequest, JsonResponse

from apps.documentation.services import get_pages_service
from apps.documentation.utils.format_examples import page_examples, analysis_examples
from apps.documentation.utils.exceptions import DocumentationNotFoundError
from apps.documentation.utils.cache_decorator import cache_documentation_get
from django.conf import settings
from apps.documentation.utils.list_projectors import should_expand_full, to_page_list_item

logger = logging.getLogger(__name__)

VALID_USER_TYPES = frozenset(["super_admin", "admin", "pro_user", "free_user", "guest"])
DATA_PREFIX = getattr(settings, "S3_DATA_PREFIX", "data/")


@require_http_methods(["GET"])
@cache_documentation_get(timeout=300)
def pages_list(request: HttpRequest) -> JsonResponse:
    """GET /api/v1/pages/ - List all pages (Lambda shape)."""
    try:
        service = get_pages_service()
        page_type = request.GET.get("page_type")
        include_drafts = request.GET.get("include_drafts", "true").lower() == "true"
        include_deleted = request.GET.get("include_deleted", "false").lower() == "true"
        status_filter = request.GET.get("status")
        limit = request.GET.get("limit")
        offset = int(request.GET.get("offset", 0))
        if limit is not None:
            limit = int(limit)
        result = service.list_pages(
            page_type=page_type,
            include_drafts=include_drafts,
            include_deleted=include_deleted,
            status=status_filter,
            limit=limit,
            offset=offset,
        )
        pages = result.get("pages", [])
        if not should_expand_full(request.GET):
            pages = [to_page_list_item(p) for p in pages]
        return JsonResponse({"pages": pages, "total": result.get("total", 0)})
    except Exception as e:
        logger.exception("pages list failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
@cache_documentation_get(timeout=3600)
def pages_format(request: HttpRequest) -> JsonResponse:
    """GET /api/v1/pages/format/ - JSON examples for pages."""
    examples = page_examples(DATA_PREFIX)
    return JsonResponse({
        "resource": "pages",
        "s3_data_prefix": DATA_PREFIX,
        "examples": examples,
        "analyse_payload_example": analysis_examples().get("pages_analysis"),
    })


@require_http_methods(["GET"])
@cache_documentation_get(timeout=300)
def pages_statistics(request: HttpRequest) -> JsonResponse:
    """GET /api/v1/pages/statistics/ - Pages index statistics."""
    try:
        service = get_pages_service()
        stats = service.get_type_statistics()
        from apps.documentation.services import get_shared_s3_index_manager
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
        logger.exception("pages statistics failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
@cache_documentation_get(timeout=300)
def pages_types(request: HttpRequest) -> JsonResponse:
    """GET /api/v1/pages/types/ - List page types with counts."""
    try:
        service = get_pages_service()
        types_data = []
        for pt in ["docs", "marketing", "dashboard"]:
            count = service.count_pages_by_type(pt)
            types_data.append({"type": pt, "count": count})
        total = sum(t["count"] for t in types_data)
        return JsonResponse({"types": types_data, "total": total})
    except Exception as e:
        logger.exception("pages types failed")
        return JsonResponse({"detail": str(e)}, status=500)


# ----- by-type (static before parameterized) -----

@require_http_methods(["GET"])
@cache_documentation_get(timeout=300)
def pages_by_type_docs(request: HttpRequest) -> JsonResponse:
    """GET /api/v1/pages/by-type/docs/"""
    try:
        service = get_pages_service()
        result = service.list_pages(page_type="docs", limit=None, offset=0)
        return JsonResponse({"pages": result.get("pages", []), "total": result.get("total", 0)})
    except Exception as e:
        logger.exception("pages by-type docs failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
@cache_documentation_get(timeout=300)
def pages_by_type_marketing(request: HttpRequest) -> JsonResponse:
    """GET /api/v1/pages/by-type/marketing/"""
    try:
        service = get_pages_service()
        result = service.list_pages(page_type="marketing", limit=None, offset=0)
        return JsonResponse({"pages": result.get("pages", []), "total": result.get("total", 0)})
    except Exception as e:
        logger.exception("pages by-type marketing failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
@cache_documentation_get(timeout=300)
def pages_by_type_dashboard(request: HttpRequest) -> JsonResponse:
    """GET /api/v1/pages/by-type/dashboard/"""
    try:
        service = get_pages_service()
        result = service.list_pages(page_type="dashboard", limit=None, offset=0)
        return JsonResponse({"pages": result.get("pages", []), "total": result.get("total", 0)})
    except Exception as e:
        logger.exception("pages by-type dashboard failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def pages_by_type_count(request: HttpRequest, page_type: str) -> JsonResponse:
    """GET /api/v1/pages/by-type/{page_type}/count/"""
    try:
        service = get_pages_service()
        count = service.count_pages_by_type(page_type)
        return JsonResponse({"page_type": page_type, "count": count})
    except Exception as e:
        logger.exception("pages by-type count failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def pages_by_type_published(request: HttpRequest, page_type: str) -> JsonResponse:
    """GET /api/v1/pages/by-type/{page_type}/published/
    
    Returns pages with status="published" OR page_state="published".
    This matches Lambda API behavior and handles both legacy status and lifecycle page_state.
    """
    try:
        service = get_pages_service()
        # Use page_state="published" instead of status="published" for consistency
        result = service.list_pages(page_type=page_type, include_drafts=False, include_deleted=False, page_state="published", limit=None, offset=0)
        return JsonResponse({"pages": result.get("pages", []), "total": result.get("total", 0)})
    except Exception as e:
        logger.exception("pages by-type published failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def pages_by_type_draft(request: HttpRequest, page_type: str) -> JsonResponse:
    """GET /api/v1/pages/by-type/{page_type}/draft/
    
    Returns pages with status="draft" OR page_state="draft".
    This matches Lambda API behavior and handles both legacy status and lifecycle page_state.
    """
    try:
        service = get_pages_service()
        # Use page_state="draft" instead of status="draft" to match lifecycle state
        # This is more flexible and handles both status and page_state fields
        result = service.list_pages(page_type=page_type, include_drafts=True, include_deleted=False, page_state="draft", limit=None, offset=0)
        return JsonResponse({"pages": result.get("pages", []), "total": result.get("total", 0)})
    except Exception as e:
        logger.exception("pages by-type draft failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
@cache_documentation_get(timeout=300)
def pages_by_type_stats(request: HttpRequest, page_type: str) -> JsonResponse:
    """GET /api/v1/pages/by-type/{page_type}/stats/"""
    try:
        service = get_pages_service()
        stats = service.get_type_statistics()
        statistics = stats.get("statistics", [])
        type_stats = next((s for s in statistics if s.get("type") == page_type), {})
        from apps.documentation.services import get_shared_s3_index_manager
        index_manager = get_shared_s3_index_manager()
        index_data = index_manager.read_index("pages")
        return JsonResponse({
            "page_type": page_type,
            "total": type_stats.get("count", 0),
            "published": type_stats.get("published", 0),
            "draft": type_stats.get("draft", 0),
            "deleted": type_stats.get("deleted", 0),
            "last_updated": index_data.get("last_updated"),
        })
    except Exception as e:
        logger.exception("pages by-type stats failed")
        return JsonResponse({"detail": str(e)}, status=500)


# ----- by-state -----

@require_http_methods(["GET"])
@cache_documentation_get(timeout=300)
def pages_by_state_list(request: HttpRequest, state: str) -> JsonResponse:
    """GET /api/v1/pages/by-state/{state}/"""
    try:
        service = get_pages_service()
        result = service.list_pages(page_state=state, limit=None, offset=0)
        return JsonResponse({"pages": result.get("pages", []), "total": result.get("total", 0)})
    except Exception as e:
        logger.exception("pages by-state list failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def pages_by_state_count(request: HttpRequest, state: str) -> JsonResponse:
    """GET /api/v1/pages/by-state/{state}/count/"""
    try:
        service = get_pages_service()
        result = service.list_pages(page_state=state, limit=None, offset=0)
        return JsonResponse({"state": state, "count": result.get("total", 0)})
    except Exception as e:
        logger.exception("pages by-state count failed")
        return JsonResponse({"detail": str(e)}, status=500)


# ----- user_type or page_id (single segment: dispatch by value) -----

@require_http_methods(["GET"])
def pages_by_user_type_or_page_detail(request: HttpRequest, segment: str) -> JsonResponse:
    """
    GET /api/v1/pages/{user_type}/ or GET /api/v1/pages/{page_id}/
    If segment is a valid user_type (super_admin, admin, ...), list pages by user type.
    Otherwise get page by ID.
    """
    if segment in VALID_USER_TYPES:
        try:
            service = get_pages_service()
            page_type = request.GET.get("page_type")
            include_drafts = request.GET.get("include_drafts", "true").lower() == "true"
            include_deleted = request.GET.get("include_deleted", "false").lower() == "true"
            status_filter = request.GET.get("status")
            result = service.list_pages_by_user_type(
                user_type=segment,
                page_type=page_type,
                include_drafts=include_drafts,
                include_deleted=include_deleted,
                status=status_filter,
            )
            return JsonResponse({"pages": result.get("pages", []), "total": result.get("total", 0)})
        except ValueError as e:
            return JsonResponse({"detail": str(e)}, status=400)
        except Exception as e:
            logger.exception("pages by user_type failed")
            return JsonResponse({"detail": str(e)}, status=500)
    # Else treat as page_id
    try:
        service = get_pages_service()
        page_type = request.GET.get("page_type")
        page = service.get_page_by_id(segment, page_type=page_type)
        if not page:
            return JsonResponse({"detail": f"Documentation page '{segment}' not found"}, status=404)
        return JsonResponse(page)
    except DocumentationNotFoundError:
        return JsonResponse({"detail": f"Documentation page '{segment}' not found"}, status=404)
    except Exception as e:
        logger.exception("pages detail failed")
        return JsonResponse({"detail": str(e)}, status=500)


# ----- page sub-resources (must be after {page_id} so use same segment + path) -----

@require_http_methods(["GET"])
def pages_detail_access_control(request: HttpRequest, page_id: str) -> JsonResponse:
    """GET /api/v1/pages/{page_id}/access-control/
    
    Returns access_control for a page. Matches Lambda API behavior:
    - Returns 404 only if page not found
    - Returns access_control=None if page exists but has no access_control field
    """
    try:
        service = get_pages_service()
        # Check if page exists first
        page = service.get_page(page_id)
        if not page:
            return JsonResponse({"detail": f"Page '{page_id}' not found"}, status=404)
        
        # Get access_control (may be None if field doesn't exist)
        ac = page.get("access_control")
        # Return response matching Lambda API: always return page_id and access_control (even if None)
        return JsonResponse({"page_id": page_id, "access_control": ac})
    except Exception as e:
        logger.exception("pages detail access control failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def pages_detail_sections(request: HttpRequest, page_id: str) -> JsonResponse:
    """GET /api/v1/pages/{page_id}/sections/
    
    Returns sections for a page. Matches Lambda API behavior:
    - Returns 404 only if page not found
    - Returns sections=None if page exists but has no sections field
    """
    try:
        service = get_pages_service()
        # Check if page exists first
        page = service.get_page(page_id)
        if not page:
            return JsonResponse({"detail": f"Page '{page_id}' not found"}, status=404)
        
        # Get sections (may be None if field doesn't exist)
        sections = page.get("sections") or (page.get("metadata") or {}).get("content_sections")
        return JsonResponse({"page_id": page_id, "sections": sections})
    except Exception as e:
        logger.exception("pages detail sections failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def pages_detail_components(request: HttpRequest, page_id: str) -> JsonResponse:
    """GET /api/v1/pages/{page_id}/components/
    
    Returns components for a page. Matches Lambda API behavior:
    - Returns 404 only if page not found
    - Returns empty lists if page exists but has no components
    """
    try:
        service = get_pages_service()
        page = service.get_page(page_id)
        if not page:
            return JsonResponse({"detail": f"Page '{page_id}' not found"}, status=404)
        # Match Lambda API: get components from sections, ui_components from metadata
        sections = page.get("sections", {})
        components = sections.get("components", []) if sections else []
        ui_components = (page.get("metadata") or {}).get("ui_components", [])
        return JsonResponse({
            "page_id": page_id,
            "components": components,
            "ui_components": ui_components,
            "total": len(components) + len(ui_components),
        })
    except Exception as e:
        logger.exception("pages detail components failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def pages_detail_endpoints(request: HttpRequest, page_id: str) -> JsonResponse:
    """GET /api/v1/pages/{page_id}/endpoints/
    
    Returns endpoints for a page. Matches Lambda API behavior:
    - Returns 404 only if page not found
    - Returns empty lists if page exists but has no endpoints
    """
    try:
        service = get_pages_service()
        # Check if page exists first
        page = service.get_page(page_id)
        if not page:
            return JsonResponse({"detail": f"Page '{page_id}' not found"}, status=404)
        
        # Get endpoints from metadata (may be None if field doesn't exist)
        metadata_endpoints = (page.get("metadata") or {}).get("uses_endpoints", [])
        return JsonResponse({
            "page_id": page_id,
            "section_endpoints": [],
            "metadata_endpoints": metadata_endpoints,
            "total": len(metadata_endpoints),
        })
    except Exception as e:
        logger.exception("pages detail endpoints failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def pages_detail_versions(request: HttpRequest, page_id: str) -> JsonResponse:
    """GET /api/v1/pages/{page_id}/versions/
    
    Returns versions for a page. Matches Lambda API behavior:
    - Returns 404 only if page not found
    - Returns versions=[] if page exists but has no versions field
    """
    try:
        service = get_pages_service()
        # Check if page exists first
        page = service.get_page(page_id)
        if not page:
            return JsonResponse({"detail": f"Page '{page_id}' not found"}, status=404)
        
        # Get versions from metadata (may be None if field doesn't exist)
        versions = (page.get("metadata") or {}).get("versions")
        # Return response matching Lambda API: always return page_id and versions (empty list if None)
        return JsonResponse({"page_id": page_id, "versions": versions or [], "count": len(versions or [])})
    except Exception as e:
        logger.exception("pages detail versions failed")
        return JsonResponse({"detail": str(e)}, status=500)
