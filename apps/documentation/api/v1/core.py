"""
Core API v1 - Simplified CRUD operations for all content types.

This replaces the complex 109+ endpoint API with a clean 14 endpoint API
that follows REST principles and uses the unified storage layer.
"""

from __future__ import annotations

import logging
from typing import Any

from django.views.decorators.http import require_http_methods
from django.http import HttpRequest, JsonResponse

from apps.documentation.services import (
    get_pages_service,
    get_endpoints_service,
    get_relationships_service,
    get_postman_service
)
from apps.documentation.utils.api_responses import (
    success_response,
    error_response,
    not_found_response,
    server_error_response,
    paginated_response
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
# Pages API
# =============================================================================

@require_http_methods(["GET"])
def pages_list(request: HttpRequest) -> JsonResponse:
    """
    GET /api/v1/pages/

    List pages with optional filtering and pagination.
    Query params: page_type, status, limit, offset
    """
    try:
        service = get_pages_service()

        # Extract query parameters
        page_type = request.GET.get('page_type')
        status = request.GET.get('status')
        limit = int(request.GET.get('limit', 50))
        offset = int(request.GET.get('offset', 0))

        result = service.list_pages(
            page_type=page_type,
            status=status,
            limit=limit,
            offset=offset
        )

        items = result.get('pages', [])
        if not should_expand_full(request.GET):
            items = [to_page_list_item(p) for p in items]
        total = result.get('total', 0)
        source = result.get('source', 'unknown')
        
        return paginated_response(
            data=items,
            total=total,
            page=1,
            page_size=limit,
            message=""
        ).to_json_response()
    except Exception as e:
        logger.error(f"Error in pages_list: {e}", exc_info=True)
        return server_error_response(
            message=f"Failed to list pages: {str(e)}"
        ).to_json_response()


@require_http_methods(["GET"])
def pages_detail(request: HttpRequest, page_id: str) -> JsonResponse:
    """
    GET /api/v1/pages/{page_id}/

    Get single page by ID.
    """
    try:
        service = get_pages_service()
        page = service.get_page(page_id)

        if not page:
            return JsonResponse({
                'success': False,
                'error': 'Page not found'
            }, status=404)

        return JsonResponse({
            'success': True,
            'data': page
        })
    except Exception as e:
        logger.error(f"Error in pages_detail: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


# =============================================================================
# Endpoints API
# =============================================================================

@require_http_methods(["GET"])
def endpoints_list(request: HttpRequest) -> JsonResponse:
    """
    GET /api/v1/endpoints/

    List endpoints with optional filtering and pagination.
    Query params: api_version, method, limit, offset
    """
    try:
        service = get_endpoints_service()

        # Extract query parameters
        api_version = request.GET.get('api_version')
        method = request.GET.get('method')
        limit = int(request.GET.get('limit', 50))
        offset = int(request.GET.get('offset', 0))

        result = service.list_endpoints(
            api_version=api_version,
            method=method,
            limit=limit,
            offset=offset
        )

        items = result.get('endpoints', [])
        if not should_expand_full(request.GET):
            items = [to_endpoint_list_item(ep) for ep in items]
        total = result.get('total', 0)
        
        return paginated_response(
            data=items,
            total=total,
            page=1,
            page_size=limit,
            message=""
        ).to_json_response()
    except Exception as e:
        logger.error(f"Error in endpoints_list: {e}", exc_info=True)
        return server_error_response(
            message=f"Failed to list endpoints: {str(e)}"
        ).to_json_response()


@require_http_methods(["GET"])
def endpoints_detail(request: HttpRequest, endpoint_id: str) -> JsonResponse:
    """
    GET /api/v1/endpoints/{endpoint_id}/

    Get single endpoint by ID.
    """
    try:
        service = get_endpoints_service()
        endpoint = service.get_endpoint(endpoint_id)

        if not endpoint:
            return JsonResponse({
                'success': False,
                'error': 'Endpoint not found'
            }, status=404)

        return JsonResponse({
            'success': True,
            'data': endpoint
        })
    except Exception as e:
        logger.error(f"Error in endpoints_detail: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


# =============================================================================
# Relationships API
# =============================================================================

@require_http_methods(["GET"])
def relationships_list(request: HttpRequest) -> JsonResponse:
    """
    GET /api/v1/relationships/

    List relationships with optional filtering and pagination.
    Query params: page_id, endpoint_id, limit, offset
    """
    try:
        service = get_relationships_service()

        # Extract query parameters
        page_id = request.GET.get('page_id')
        endpoint_id = request.GET.get('endpoint_id')
        limit = int(request.GET.get('limit', 50))
        offset = int(request.GET.get('offset', 0))

        result = service.list_relationships(
            page_id=page_id,
            endpoint_id=endpoint_id,
            limit=limit,
            offset=offset
        )

        items = result.get('relationships', [])
        if not should_expand_full(request.GET):
            items = [to_relationship_list_item(r) for r in items]
        total = result.get('total', 0)
        
        return paginated_response(
            data=items,
            total=total,
            page=1,
            page_size=limit,
            message=""
        ).to_json_response()
    except Exception as e:
        logger.error(f"Error in relationships_list: {e}", exc_info=True)
        return server_error_response(
            message=f"Failed to list relationships: {str(e)}"
        ).to_json_response()


@require_http_methods(["GET"])
def relationships_detail(request, relationship_id):
    """
    GET /api/v1/relationships/{relationship_id}/

    Get single relationship by ID.
    """
    try:
        service = get_relationships_service()
        relationship = service.get_relationship(relationship_id)

        if not relationship:
            return not_found_response(resource="Relationship").to_json_response()

        return success_response(data=relationship).to_json_response()
    except Exception as e:
        logger.error(f"Error in relationships_detail: {e}", exc_info=True)
        return server_error_response(
            message=f"Failed to get relationship: {str(e)}"
        ).to_json_response()


# =============================================================================
# Postman API
# =============================================================================

@require_http_methods(["GET"])
def postman_list(request: HttpRequest) -> JsonResponse:
    """
    GET /api/v1/postman/

    List Postman configurations with optional filtering and pagination.
    Query params: state, limit, offset
    """
    try:
        service = get_postman_service()

        # Extract query parameters
        state = request.GET.get('state')
        limit = int(request.GET.get('limit', 50))
        offset = int(request.GET.get('offset', 0))

        result = service.list_configurations(
            state=state,
            limit=limit,
            offset=offset
        )

        items = result.get('configurations', [])
        if not should_expand_full(request.GET):
            items = [to_postman_list_item(c) for c in items]

        return JsonResponse({
            'success': True,
            'items': items,
            'total': result.get('total', 0),
            'source': result.get('source', 'unknown')
        })
    except Exception as e:
        logger.error(f"Error in postman_list: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


@require_http_methods(["GET"])
def postman_detail(request: HttpRequest, postman_id: str) -> JsonResponse:
    """
    GET /api/v1/postman/{postman_id}/

    Get single Postman configuration by ID.
    """
    try:
        service = get_postman_service()
        config = service.get_configuration(postman_id)

        if not config:
            return not_found_response(resource="Postman configuration").to_json_response()

        return success_response(data=config).to_json_response()
    except Exception as e:
        logger.error(f"Error in postman_detail: {e}", exc_info=True)
        return server_error_response(
            message=f"Failed to get Postman configuration: {str(e)}"
        ).to_json_response()


# =============================================================================
# Dashboard API - Client-side pagination and filtering
# =============================================================================

@require_http_methods(["GET"])
def dashboard_pages(request: HttpRequest) -> JsonResponse:
    """
    GET /api/v1/dashboard/pages/

    Dashboard pagination endpoint for pages.
    Used by dashboard tab for client-side pagination and filtering.
    Query params: page, page_size, page_type, status, search
    """
    try:
        service = get_pages_service()

        # Extract pagination parameters
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        offset = (page - 1) * page_size

        # Extract filter parameters
        page_type = request.GET.get('page_type')
        status = request.GET.get('status')
        search = request.GET.get('search')

        result = service.list_pages(
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

        total = result.get('total', 0)
        return paginated_response(
            data=items,
            total=total,
            page=page,
            page_size=page_size,
            message=""
        ).to_json_response()
    except Exception as e:
        logger.error(f"Error in dashboard_pages: {e}", exc_info=True)
        return server_error_response(
            message=f"Failed to get dashboard pages: {str(e)}"
        ).to_json_response()


@require_http_methods(["GET"])
def dashboard_endpoints(request: HttpRequest) -> JsonResponse:
    """
    GET /api/v1/dashboard/endpoints/

    Dashboard pagination endpoint for endpoints.
    Query params: page, page_size, api_version, method, search
    """
    try:
        service = get_endpoints_service()

        # Extract pagination parameters
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        offset = (page - 1) * page_size

        # Extract filter parameters
        api_version = request.GET.get('api_version')
        method = request.GET.get('method')
        search = request.GET.get('search')

        result = service.list_endpoints(
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
        logger.error(f"Error in dashboard_endpoints: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


@require_http_methods(["GET"])
def dashboard_relationships(request: HttpRequest) -> JsonResponse:
    """
    GET /api/v1/dashboard/relationships/

    Dashboard pagination endpoint for relationships.
    Query params: page, page_size, page_id, endpoint_id, usage_type, search
    """
    try:
        service = get_relationships_service()

        # Extract pagination parameters
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        offset = (page - 1) * page_size

        # Extract filter parameters
        page_id = request.GET.get('page_id')
        endpoint_id = request.GET.get('endpoint_id')
        usage_type = request.GET.get('usage_type')
        search = request.GET.get('search')

        result = service.list_relationships(
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

        total = result.get('total', 0)
        return paginated_response(
            data=items,
            total=total,
            page=page,
            page_size=page_size,
            message=""
        ).to_json_response()
    except Exception as e:
        logger.error(f"Error in dashboard_relationships: {e}", exc_info=True)
        return server_error_response(
            message=f"Failed to get dashboard relationships: {str(e)}"
        ).to_json_response()


@require_http_methods(["GET"])
def dashboard_postman(request: HttpRequest) -> JsonResponse:
    """
    GET /api/v1/dashboard/postman/

    Dashboard pagination endpoint for Postman configurations.
    Query params: page, page_size, state, search
    """
    try:
        service = get_postman_service()

        # Extract pagination parameters
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        offset = (page - 1) * page_size

        # Extract filter parameters
        state = request.GET.get('state')
        search = request.GET.get('search')

        result = service.list_configurations(
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
        logger.error(f"Error in dashboard_postman: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


# =============================================================================
# Statistics Endpoints - Additional endpoints for statistics
# =============================================================================

@require_http_methods(["GET"])
def endpoints_methods(request: HttpRequest) -> JsonResponse:
    """
    GET /api/v1/endpoints/methods/
    
    List all HTTP/GraphQL methods with counts.
    """
    try:
        # Use service directly instead of Lambda client
        service = get_endpoints_service()
        result = service.list_endpoints(limit=10000)  # Get all for statistics
        endpoints = result.get('endpoints', [])
        
        methods = {}
        for ep in endpoints:
            method = ep.get('method', 'UNKNOWN')
            methods[method] = methods.get(method, 0) + 1
        
        method_list = [{'method': k, 'count': v} for k, v in methods.items()]
        return success_response(
            data={'methods': method_list, 'total': len(method_list)}
        ).to_json_response()
    except Exception as e:
        logger.error(f"Error in endpoints_methods: {e}", exc_info=True)
        return success_response(
            data={'methods': [], 'total': 0}
        ).to_json_response()


@require_http_methods(["GET"])
def endpoints_api_versions(request: HttpRequest) -> JsonResponse:
    """
    GET /api/v1/endpoints/api-versions/
    
    List all API versions with counts.
    """
    try:
        # Use service directly instead of Lambda client
        service = get_endpoints_service()
        result = service.list_endpoints(limit=10000)  # Get all for statistics
        endpoints = result.get('endpoints', [])
        
        versions = {}
        for ep in endpoints:
            api_version = ep.get('api_version') or ep.get('metadata', {}).get('api_version', 'unknown')
            versions[api_version] = versions.get(api_version, 0) + 1
        
        version_list = [{'version': k, 'count': v} for k, v in versions.items()]
        return JsonResponse({
            'success': True,
            'data': {'versions': version_list, 'total': len(version_list)}
        })
    except Exception as e:
        logger.error(f"Error in endpoints_api_versions: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


@require_http_methods(["GET"])
def pages_types(request: HttpRequest) -> JsonResponse:
    """
    GET /api/v1/pages/types/
    
    List all page types with counts.
    """
    try:
        # Use service directly instead of Lambda client
        service = get_pages_service()
        result = service.list_pages(limit=10000)  # Get all for statistics
        pages = result.get('pages', [])
        
        types = {}
        for page in pages:
            page_type = page.get('metadata', {}).get('page_type') or page.get('page_type', 'docs')
            types[page_type] = types.get(page_type, 0) + 1
        
        type_list = [{'type': k, 'count': v} for k, v in types.items()]
        return success_response(
            data={'types': type_list, 'total': len(type_list)}
        ).to_json_response()
    except Exception as e:
        logger.error(f"Error in pages_types: {e}", exc_info=True)
        return success_response(
            data={'types': [], 'total': 0}
        ).to_json_response()


@require_http_methods(["GET"])
def pages_statistics(request: HttpRequest) -> JsonResponse:
    """
    GET /api/v1/pages/statistics/
    
    Get overall pages statistics.
    """
    try:
        # Use service directly instead of Lambda client
        service = get_pages_service()
        result = service.list_pages(limit=10000)  # Get all for statistics
        pages = result.get('pages', [])
        
        return success_response(
            data={
                'total': len(pages),
                'statistics': {
                    'total_pages': len(pages),
                    'published': len([p for p in pages if p.get('metadata', {}).get('status') == 'published']),
                    'draft': len([p for p in pages if p.get('metadata', {}).get('status') == 'draft'])
                }
            }
        ).to_json_response()
    except Exception as e:
        logger.error(f"Error in pages_statistics: {e}", exc_info=True)
        return success_response(
            data={'total': 0, 'statistics': {}}
        ).to_json_response()


@require_http_methods(["GET"])
def relationships_statistics(request: HttpRequest) -> JsonResponse:
    """
    GET /api/v1/relationships/statistics/
    
    Get relationship statistics.
    """
    try:
        # Use service directly instead of Lambda client
        service = get_relationships_service()
        result = service.list_relationships(limit=10000)  # Get all for statistics
        relationships = result.get('relationships', [])
        
        unique_pages = set()
        unique_endpoints = set()
        for rel in relationships:
            if rel.get('page_path') or rel.get('page_id'):
                unique_pages.add(rel.get('page_path') or rel.get('page_id'))
            if rel.get('endpoint_path') or rel.get('endpoint_id'):
                unique_endpoints.add(rel.get('endpoint_path') or rel.get('endpoint_id'))
        
        return JsonResponse({
            'success': True,
            'data': {
                'total_relationships': len(relationships),
                'unique_pages': len(unique_pages),
                'unique_endpoints': len(unique_endpoints)
            }
        })
    except Exception as e:
        logger.error(f"Error in relationships_statistics: {e}")
        return JsonResponse({
            'success': True,
            'data': {
                'total_relationships': 0,
                'unique_pages': 0,
                'unique_endpoints': 0
            }
        })


@require_http_methods(["GET"])
def postman_statistics(request: HttpRequest) -> JsonResponse:
    """
    GET /api/v1/postman/statistics/
    
    Get Postman configuration statistics.
    """
    try:
        # Use service directly instead of Lambda client
        service = get_postman_service()
        result = service.list_configurations(limit=10000)  # Get all for statistics
        configurations = result.get('configurations', [])
        
        return success_response(
            data={
                'total': len(configurations),
                'statistics': {
                    'total_configurations': len(configurations)
                }
            }
        ).to_json_response()
    except Exception as e:
        logger.error(f"Error in postman_statistics: {e}", exc_info=True)
        return success_response(
            data={'total': 0, 'statistics': {}}
        ).to_json_response()