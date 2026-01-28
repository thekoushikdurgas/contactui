"""
Dashboard API endpoints - Call services directly.

These endpoints call services directly (no Lambda client, no API proxying).
Used by UI for pagination and filtering.
"""

import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

from apps.documentation.services import (
    get_pages_service,
    get_endpoints_service,
    get_relationships_service,
    get_postman_service,
)
from apps.documentation.utils.list_projectors import (
    should_expand_full,
    to_page_list_item,
    to_endpoint_list_item,
    to_relationship_list_item,
    to_postman_list_item,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Dashboard API - Direct service calls
# =============================================================================

@login_required
@require_http_methods(["GET"])
def dashboard_pages_api(request):
    """
    GET /docs/api/dashboard/pages/

    Dashboard pagination endpoint for pages.
    Calls PagesService directly.
    """
    try:
        # Extract pagination parameters
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        offset = (page - 1) * page_size

        # Extract filter parameters
        page_type = request.GET.get('page_type')
        status = request.GET.get('status')
        search = request.GET.get('search')

        pages_service = get_pages_service()
        result = pages_service.list_pages(
            page_type=page_type,
            status=status,
            limit=page_size,
            offset=offset
        )

        # Apply client-side search if provided
        items = result.get('pages', [])
        if search:
            search_lower = search.lower()
            items = [item for item in items if
                    search_lower in str(item.get('page_id', '')).lower() or
                    search_lower in str(item.get('metadata', {}).get('title', '')).lower()]

        if not should_expand_full(request.GET):
            items = [to_page_list_item(p) for p in items]

        return JsonResponse({
            'success': True,
            'items': items,
            'pagination': {
                'total': result.get('total', 0),
                'page': page,
                'page_size': page_size,
                'total_pages': (result.get('total', 0) + page_size - 1) // page_size,
                'has_previous': page > 1,
                'has_next': page * page_size < result.get('total', 0)
            },
            'filters': {
                'page_type': page_type,
                'status': status,
                'search': search
            },
            'source': result.get('source', 'unknown')
        })
    except Exception as e:
        logger.error(f"Error in dashboard_pages_api: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def dashboard_endpoints_api(request):
    """
    GET /docs/api/dashboard/endpoints/

    Dashboard pagination endpoint for endpoints.
    Calls EndpointsService directly.
    """
    try:
        # Extract pagination parameters
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        offset = (page - 1) * page_size

        # Extract filter parameters
        api_version = request.GET.get('api_version')
        method = request.GET.get('method')
        search = request.GET.get('search')

        endpoints_svc = get_endpoints_service()
        result = endpoints_svc.list_endpoints(
            api_version=api_version,
            method=method,
            limit=page_size,
            offset=offset
        )

        # Apply client-side search if provided
        items = result.get('endpoints', [])
        if search:
            search_lower = search.lower()
            items = [item for item in items if
                    search_lower in str(item.get('endpoint_id', '')).lower() or
                    search_lower in str(item.get('endpoint_path', '')).lower()]

        if not should_expand_full(request.GET):
            items = [to_endpoint_list_item(ep) for ep in items]

        return JsonResponse({
            'success': True,
            'items': items,
            'pagination': {
                'total': result.get('total', 0),
                'page': page,
                'page_size': page_size,
                'total_pages': (result.get('total', 0) + page_size - 1) // page_size,
                'has_previous': page > 1,
                'has_next': page * page_size < result.get('total', 0)
            },
            'filters': {
                'api_version': api_version,
                'method': method,
                'search': search
            },
            'source': result.get('source', 'unknown')
        })
    except Exception as e:
        logger.error(f"Error in dashboard_endpoints_api: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def dashboard_relationships_api(request):
    """
    GET /docs/api/dashboard/relationships/

    Dashboard pagination endpoint for relationships.
    Calls RelationshipsService directly.
    """
    try:
        # Extract pagination parameters
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        offset = (page - 1) * page_size

        # Extract filter parameters
        page_id = request.GET.get('page_id')
        endpoint_id = request.GET.get('endpoint_id')
        usage_type = request.GET.get('usage_type')
        search = request.GET.get('search')

        relationships_service = get_relationships_service()
        result = relationships_service.list_relationships(
            page_id=page_id,
            endpoint_id=endpoint_id,
            limit=page_size,
            offset=offset
        )

        # Apply client-side filters
        items = result.get('relationships', [])
        if usage_type:
            items = [item for item in items if item.get('usage_type') == usage_type]

        if search:
            search_lower = search.lower()
            items = [item for item in items if
                    search_lower in str(item.get('relationship_id', '')).lower() or
                    search_lower in str(item.get('page_path', '')).lower() or
                    search_lower in str(item.get('endpoint_path', '')).lower()]

        if not should_expand_full(request.GET):
            items = [to_relationship_list_item(r) for r in items]

        return JsonResponse({
            'success': True,
            'items': items,
            'pagination': {
                'total': result.get('total', 0),
                'page': page,
                'page_size': page_size,
                'total_pages': (result.get('total', 0) + page_size - 1) // page_size,
                'has_previous': page > 1,
                'has_next': page * page_size < result.get('total', 0)
            },
            'filters': {
                'page_id': page_id,
                'endpoint_id': endpoint_id,
                'usage_type': usage_type,
                'search': search
            },
            'source': result.get('source', 'unknown')
        })
    except Exception as e:
        logger.error(f"Error in dashboard_relationships_api: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def dashboard_postman_api(request):
    """
    GET /docs/api/dashboard/postman/

    Dashboard pagination endpoint for Postman configurations.
    Calls PostmanService directly.
    """
    try:
        # Extract pagination parameters
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        offset = (page - 1) * page_size

        # Extract filter parameters
        state = request.GET.get('state')
        search = request.GET.get('search')

        postman_service = get_postman_service()
        result = postman_service.list_configurations(
            state=state,
            limit=page_size,
            offset=offset
        )

        # Apply client-side search if provided
        items = result.get('configurations', [])
        if search:
            search_lower = search.lower()
            items = [item for item in items if
                    search_lower in str(item.get('config_id', '')).lower() or
                    search_lower in str(item.get('name', '')).lower()]

        if not should_expand_full(request.GET):
            items = [to_postman_list_item(c) for c in items]

        return JsonResponse({
            'success': True,
            'items': items,
            'pagination': {
                'total': result.get('total', 0),
                'page': page,
                'page_size': page_size,
                'total_pages': (result.get('total', 0) + page_size - 1) // page_size,
                'has_previous': page > 1,
                'has_next': page * page_size < result.get('total', 0)
            },
            'filters': {
                'state': state,
                'search': search
            },
            'source': result.get('source', 'unknown')
        })
    except Exception as e:
        logger.error(f"Error in dashboard_postman_api: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)
