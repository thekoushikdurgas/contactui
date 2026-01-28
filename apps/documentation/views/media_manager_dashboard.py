"""Media Manager Dashboard Views - Service-based implementation."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.utils.safestring import mark_safe

from apps.documentation.services import (
    get_pages_service,
    get_endpoints_service,
    get_relationships_service,
    get_postman_service,
    get_media_manager_dashboard_service,
)
from apps.documentation.utils.health_checks import get_comprehensive_health_status
from apps.documentation.utils.api_responses import (
    success_response,
    error_response,
    not_found_response,
)

logger = logging.getLogger(__name__)

VALID_TABS = frozenset({"pages", "endpoints", "relationships", "postman"})
VALID_VIEW_MODES = frozenset({"list", "grid", "detail"})


def _validate_tab(tab: Optional[str]) -> str:
    """Validate and normalize tab query parameter."""
    if not tab or tab not in VALID_TABS:
        return "pages"
    return tab


def _validate_view_mode(view_mode: Optional[str]) -> str:
    """Validate and normalize view mode query parameter."""
    if not view_mode or view_mode not in VALID_VIEW_MODES:
        return "list"
    return view_mode


def _render_resource_view(
    request: HttpRequest,
    template_name: str,
    context: Dict[str, Any],
    error_message: Optional[str] = None,
) -> HttpResponse:
    """
    Reusable helper to render resource views with standardized error handling.
    
    Args:
        request: HTTP request object
        template_name: Template path relative to documentation/media_manager/
        context: Template context dictionary
        error_message: Optional error message to include in context
        
    Returns:
        HttpResponse with rendered template
    """
    if error_message:
        context['error'] = error_message
        logger.warning(f"View error: {error_message}")
    
    full_template_path = f'documentation/media_manager/{template_name}'
    return render(request, full_template_path, context)


def _handle_service_call(
    service_call: callable,
    resource_name: str,
    resource_id: Optional[str] = None,
) -> tuple[Optional[Any], Optional[str]]:
    """
    Reusable helper to handle service calls with standardized error handling.
    
    Args:
        service_call: Callable that returns service result
        resource_name: Name of resource type (for error messages)
        resource_id: Optional resource ID (for error messages)
        
    Returns:
        Tuple of (result, error_message)
        - result: Service result or None if error
        - error_message: Error message string or None if success
    """
    try:
        result = service_call()
        return result, None
    except Http404:
        raise
    except Exception as e:
        error_msg = f"Error loading {resource_name}"
        if resource_id:
            error_msg += f" {resource_id}"
        error_msg += f": {e}"
        logger.error(error_msg, exc_info=True)
        return None, error_msg


@login_required
def media_manager_dashboard(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Main view.
    
    GET /docs/media-manager/
    GET /docs/media-manager/pages/
    GET /docs/media-manager/endpoints/
    GET /docs/media-manager/relationships/
    GET /docs/media-manager/postman/
    
    Query params:
    - tab: pages|endpoints|relationships|postman (default: pages)
    - view: list|grid|detail (default: list)
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20)
    - search: Search query
    - sort: Sort field
    - order: Sort order (asc|desc)
    - Additional filters per resource type
    """
    # Determine active tab from URL path or query param
    path_parts = request.path.strip('/').split('/')
    if len(path_parts) >= 3 and path_parts[1] == 'media-manager' and path_parts[2] in VALID_TABS:
        active_tab = path_parts[2]
    else:
        active_tab = request.GET.get('tab', 'pages')
    
    active_tab = _validate_tab(active_tab)
    view_mode = _validate_view_mode(request.GET.get('view', 'list'))
    
    # Initialize services
    dashboard_service = get_media_manager_dashboard_service()
    
    # Get overview statistics
    try:
        overview_stats = dashboard_service.get_dashboard_overview()
    except Exception as e:
        logger.error(f"Failed to get overview stats: {e}", exc_info=True)
        overview_stats = {}
    
    # Get health status
    try:
        health_status = dashboard_service.get_health_status()
    except Exception as e:
        logger.error(f"Failed to get health status: {e}", exc_info=True)
        health_status = {}
    
    # Get initial data for active tab
    initial_data: Dict[str, Any] = {}
    try:
        # Extract filters from query params
        filters = {
            'limit': int(request.GET.get('per_page', 20)),
            'offset': (int(request.GET.get('page', 1)) - 1) * int(request.GET.get('per_page', 20)),
        }
        
        # Add resource-specific filters
        if active_tab == 'pages':
            if request.GET.get('page_type'):
                filters['page_type'] = request.GET.get('page_type')
            if request.GET.get('status'):
                filters['status'] = request.GET.get('status')
            if request.GET.get('state'):
                filters['state'] = request.GET.get('state')
            if request.GET.get('include_drafts'):
                filters['include_drafts'] = request.GET.get('include_drafts', 'true').lower() == 'true'
            if request.GET.get('include_deleted'):
                filters['include_deleted'] = request.GET.get('include_deleted', 'false').lower() == 'true'
            
            result = dashboard_service.get_resource_list('pages', filters)
            initial_data = {
                'pages': result.get('pages', [])[:filters['limit']],
                'total': result.get('total', 0),
                'source': result.get('source', 'local'),
            }
        
        elif active_tab == 'endpoints':
            if request.GET.get('api_version'):
                filters['api_version'] = request.GET.get('api_version')
            if request.GET.get('method'):
                filters['method'] = request.GET.get('method')
            if request.GET.get('state'):
                filters['state'] = request.GET.get('state')
            if request.GET.get('lambda_service'):
                filters['lambda_service'] = request.GET.get('lambda_service')
            
            result = dashboard_service.get_resource_list('endpoints', filters)
            initial_data = {
                'endpoints': result.get('endpoints', [])[:filters['limit']],
                'total': result.get('total', 0),
                'source': result.get('source', 'local'),
            }
        
        elif active_tab == 'relationships':
            if request.GET.get('page_id'):
                filters['page_id'] = request.GET.get('page_id')
            if request.GET.get('endpoint_id'):
                filters['endpoint_id'] = request.GET.get('endpoint_id')
            if request.GET.get('usage_type'):
                filters['usage_type'] = request.GET.get('usage_type')
            if request.GET.get('usage_context'):
                filters['usage_context'] = request.GET.get('usage_context')
            
            result = dashboard_service.get_resource_list('relationships', filters)
            initial_data = {
                'relationships': result.get('relationships', [])[:filters['limit']],
                'total': result.get('total', 0),
                'source': result.get('source', 'local'),
            }
        
        elif active_tab == 'postman':
            if request.GET.get('state'):
                filters['state'] = request.GET.get('state')
            
            result = dashboard_service.get_resource_list('postman', filters)
            initial_data = {
                'postman': result.get('configurations', [])[:filters['limit']],
                'total': result.get('total', 0),
                'source': result.get('source', 'local'),
            }
    
    except Exception as e:
        logger.error(f"Error loading initial data for tab {active_tab}: {e}", exc_info=True)
        initial_data = {
            'pages': [],
            'endpoints': [],
            'relationships': [],
            'postman': [],
            'total': 0,
        }
    
    context: Dict[str, Any] = {
        'active_tab': active_tab,
        'view_mode': view_mode,
        'overview_stats': overview_stats,
        'health_status': health_status,
        'initial_data': mark_safe(json.dumps(initial_data)),
    }
    
    return render(request, 'documentation/media_manager_dashboard.html', context)


@login_required
def media_manager_page_detail(request: HttpRequest, page_id: str) -> HttpResponse:
    """
    Media Manager Dashboard - Page detail view.
    
    GET /docs/media-manager/pages/<page_id>/
    """
    try:
        pages_service = get_pages_service()
        page = pages_service.get_page(page_id)
        
        if not page:
            raise Http404(f"Page not found: {page_id}")
        
        # Get related data
        page_sections = pages_service.get_page_sections(page_id)
        page_components = pages_service.get_page_components(page_id)
        page_endpoints = pages_service.get_page_endpoints(page_id)
        page_versions = pages_service.get_page_versions(page_id)
        access_control = pages_service.get_page_access_control(page_id)
        
        context: Dict[str, Any] = {
            'page': page,
            'page_sections': page_sections,
            'page_components': page_components,
            'page_endpoints': page_endpoints,
            'page_versions': page_versions,
            'access_control': access_control,
        }
        
        return render(request, 'documentation/media_manager/page_detail.html', context)
    
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error loading page detail {page_id}: {e}", exc_info=True)
        raise Http404(f"Error loading page: {page_id}")


@login_required
def media_manager_endpoint_detail(request: HttpRequest, endpoint_id: str) -> HttpResponse:
    """
    Media Manager Dashboard - Endpoint detail view.
    
    GET /docs/media-manager/endpoints/<endpoint_id>/
    """
    try:
        endpoints_service = get_endpoints_service()
        endpoint = endpoints_service.get_endpoint(endpoint_id)
        
        if not endpoint:
            raise Http404(f"Endpoint not found: {endpoint_id}")
        
        # Get related data
        pages_using = endpoints_service.get_endpoint_pages(endpoint_id)
        access_control = endpoints_service.get_endpoint_access_control(endpoint_id)
        lambda_services = endpoints_service.get_endpoint_lambda_services(endpoint_id)
        files = endpoints_service.get_endpoint_files(endpoint_id)
        dependencies = endpoints_service.get_endpoint_dependencies(endpoint_id)
        
        context: Dict[str, Any] = {
            'endpoint': endpoint,
            'pages_using': pages_using.get('pages', []),
            'access_control': access_control,
            'lambda_services': lambda_services or [],
            'files': files or [],
            'dependencies': dependencies or [],
        }
        
        return render(request, 'documentation/media_manager/endpoint_detail.html', context)
    
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error loading endpoint detail {endpoint_id}: {e}", exc_info=True)
        raise Http404(f"Error loading endpoint: {endpoint_id}")


@login_required
def media_manager_relationship_detail(request: HttpRequest, relationship_id: str) -> HttpResponse:
    """
    Media Manager Dashboard - Relationship detail view.
    
    GET /docs/media-manager/relationships/<relationship_id>/
    """
    try:
        relationships_service = get_relationships_service()
        relationship = relationships_service.get_relationship(relationship_id)
        
        if not relationship:
            raise Http404(f"Relationship not found: {relationship_id}")
        
        # Get related data
        access_control = relationships_service.get_relationship_access_control(relationship_id)
        data_flow = relationships_service.get_relationship_data_flow(relationship_id)
        performance = relationships_service.get_relationship_performance(relationship_id)
        dependencies = relationships_service.get_relationship_dependencies(relationship_id)
        postman_config = relationships_service.get_relationship_postman(relationship_id)
        
        context: Dict[str, Any] = {
            'relationship': relationship,
            'access_control': access_control,
            'data_flow': data_flow,
            'performance': performance,
            'dependencies': dependencies or [],
            'postman_config': postman_config,
        }
        
        return render(request, 'documentation/media_manager/relationship_detail.html', context)
    
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error loading relationship detail {relationship_id}: {e}", exc_info=True)
        raise Http404(f"Error loading relationship: {relationship_id}")


@login_required
def media_manager_postman_detail(request: HttpRequest, config_id: str) -> HttpResponse:
    """
    Media Manager Dashboard - Postman configuration detail view.
    
    GET /docs/media-manager/postman/<config_id>/
    """
    try:
        postman_service = get_postman_service()
        configuration = postman_service.get_configuration(config_id)
        
        if not configuration:
            raise Http404(f"Postman configuration not found: {config_id}")
        
        # Get related data
        collection = postman_service.get_collection(config_id)
        environments = postman_service.get_environments(config_id)
        mappings = postman_service.get_endpoint_mappings(config_id)
        test_suites = postman_service.get_test_suites(config_id)
        access_control = postman_service.get_access_control(config_id)
        
        context: Dict[str, Any] = {
            'configuration': configuration,
            'collection': collection,
            'environments': environments or [],
            'mappings': mappings or [],
            'test_suites': test_suites or [],
            'access_control': access_control,
        }
        
        return render(request, 'documentation/media_manager/postman_detail.html', context)
    
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error loading Postman detail {config_id}: {e}", exc_info=True)
        raise Http404(f"Error loading Postman configuration: {config_id}")


@login_required
def media_manager_health(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Health status view.
    
    GET /docs/media-manager/health/
    """
    try:
        health_status = get_comprehensive_health_status()
        
        context: Dict[str, Any] = {
            'health_status': health_status,
        }
        
        return render(request, 'documentation/media_manager/health.html', context)
    
    except Exception as e:
        logger.error(f"Error loading health status: {e}", exc_info=True)
        context: Dict[str, Any] = {
            'health_status': {
                'status': 'error',
                'error': str(e),
            },
        }
        return render(request, 'documentation/media_manager/health.html', context)


@login_required
def media_manager_statistics(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Statistics overview view.
    
    GET /docs/media-manager/statistics/
    """
    try:
        dashboard_service = get_media_manager_dashboard_service()
        
        # Get statistics from all services
        pages_stats = dashboard_service.pages_service.get_pages_statistics()
        endpoints_stats = dashboard_service.endpoints_service.get_api_version_statistics()
        relationships_stats = dashboard_service.relationships_service.get_statistics()
        postman_stats = dashboard_service.postman_service.get_statistics()
        
        context: Dict[str, Any] = {
            'pages_statistics': pages_stats,
            'endpoints_statistics': endpoints_stats,
            'relationships_statistics': relationships_stats,
            'postman_statistics': postman_stats,
        }
        
        return render(request, 'documentation/media_manager/statistics.html', context)
    
    except Exception as e:
        logger.error(f"Error loading statistics: {e}", exc_info=True)
        context: Dict[str, Any] = {
            'pages_statistics': {},
            'endpoints_statistics': {},
            'relationships_statistics': {},
            'postman_statistics': {},
            'error': str(e),
        }
        return render(request, 'documentation/media_manager/statistics.html', context)


# ============================================================================
# Pages API Views - Enhanced routes (mirroring /api/v1/pages/)
# ============================================================================

@login_required
def media_manager_pages_statistics(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Pages statistics view.
    
    GET /docs/media-manager/pages/statistics/
    Mirrors: GET /api/v1/pages/statistics/
    """
    try:
        pages_service = get_pages_service()
        stats = pages_service.get_pages_statistics()
        
        from apps.documentation.services import get_shared_s3_index_manager
        index_manager = get_shared_s3_index_manager()
        index_data = index_manager.read_index("pages")
        
        context: Dict[str, Any] = {
            'statistics': {
                'total': index_data.get("total", 0),
                'version': index_data.get("version"),
                'last_updated': index_data.get("last_updated"),
                'statistics': index_data.get("statistics", {}),
                'indexes': index_data.get("indexes", {}),
            },
            'pages_statistics': stats,
        }
        
        return _render_resource_view(request, 'pages_statistics.html', context)
    
    except Exception as e:
        logger.error(f"Error loading pages statistics: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'pages_statistics.html',
            {'statistics': {}, 'pages_statistics': {}, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_pages_format(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Pages format examples view.
    
    GET /docs/pages/format/
    Mirrors: GET /api/v1/pages/format/
    """
    try:
        from apps.documentation.api.v1.pages_views import pages_format as api_pages_format
        from django.http import JsonResponse
        import json
        
        # Call the API function to get format data
        json_response = api_pages_format(request)
        format_data = json.loads(json_response.content)
        
        # Format examples for display
        examples = None
        if 'examples' in format_data:
            examples = json.dumps(format_data['examples'], indent=2)
        
        analyse_payload_example = None
        if 'analyse_payload_example' in format_data:
            analyse_payload_example = json.dumps(format_data['analyse_payload_example'], indent=2)
        
        context: Dict[str, Any] = {
            'format_data': format_data,
            'examples': examples,
            'analyse_payload_example': analyse_payload_example,
        }
        
        return _render_resource_view(request, 'pages_format.html', context)
    
    except Exception as e:
        logger.error(f"Error loading pages format: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'pages_format.html',
            {'format_data': {}, 'examples': None, 'analyse_payload_example': None, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_pages_types(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Pages types view.
    
    GET /docs/media-manager/pages/types/
    Mirrors: GET /api/v1/pages/types/
    """
    try:
        pages_service = get_pages_service()
        types_data = []
        for pt in ["docs", "marketing", "dashboard"]:
            count = pages_service.count_pages_by_type(pt)
            types_data.append({"type": pt, "count": count})
        total = sum(t["count"] for t in types_data)
        
        context: Dict[str, Any] = {
            'types': types_data,
            'total': total,
        }
        
        return _render_resource_view(request, 'pages_types.html', context)
    
    except Exception as e:
        logger.error(f"Error loading pages types: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'pages_types.html',
            {'types': [], 'total': 0, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_pages_by_type_docs(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Pages by type (docs) view.
    
    GET /docs/media-manager/pages/by-type/docs/
    Mirrors: GET /api/v1/pages/by-type/docs/
    """
    try:
        pages_service = get_pages_service()
        result = pages_service.list_pages(page_type="docs", limit=None, offset=0)
        
        context: Dict[str, Any] = {
            'pages': result.get("pages", []),
            'total': result.get("total", 0),
            'page_type': 'docs',
            'filters': {'page_type': 'docs'},
        }
        
        return _render_resource_view(request, 'pages_by_type.html', context)
    
    except Exception as e:
        logger.error(f"Error loading pages by type docs: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'pages_by_type.html',
            {'pages': [], 'total': 0, 'page_type': 'docs', 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_pages_by_type_marketing(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Pages by type (marketing) view.
    
    GET /docs/media-manager/pages/by-type/marketing/
    Mirrors: GET /api/v1/pages/by-type/marketing/
    """
    try:
        pages_service = get_pages_service()
        result = pages_service.list_pages(page_type="marketing", limit=None, offset=0)
        
        context: Dict[str, Any] = {
            'pages': result.get("pages", []),
            'total': result.get("total", 0),
            'page_type': 'marketing',
            'filters': {'page_type': 'marketing'},
        }
        
        return _render_resource_view(request, 'pages_by_type.html', context)
    
    except Exception as e:
        logger.error(f"Error loading pages by type marketing: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'pages_by_type.html',
            {'pages': [], 'total': 0, 'page_type': 'marketing', 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_pages_by_type_dashboard(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Pages by type (dashboard) view.
    
    GET /docs/media-manager/pages/by-type/dashboard/
    Mirrors: GET /api/v1/pages/by-type/dashboard/
    """
    try:
        pages_service = get_pages_service()
        result = pages_service.list_pages(page_type="dashboard", limit=None, offset=0)
        
        context: Dict[str, Any] = {
            'pages': result.get("pages", []),
            'total': result.get("total", 0),
            'page_type': 'dashboard',
            'filters': {'page_type': 'dashboard'},
        }
        
        return _render_resource_view(request, 'pages_by_type.html', context)
    
    except Exception as e:
        logger.error(f"Error loading pages by type dashboard: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'pages_by_type.html',
            {'pages': [], 'total': 0, 'page_type': 'dashboard', 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_pages_by_type(request: HttpRequest, page_type: str) -> HttpResponse:
    """
    Media Manager Dashboard - Pages by type (generic) view.
    
    GET /docs/pages/by-type/<page_type>/
    Mirrors: GET /api/v1/pages/by-type/<page_type>/
    """
    try:
        pages_service = get_pages_service()
        result = pages_service.list_pages(page_type=page_type, limit=None, offset=0)
        
        context: Dict[str, Any] = {
            'pages': result.get("pages", []),
            'total': result.get("total", 0),
            'page_type': page_type,
            'filters': {'page_type': page_type},
        }
        
        return _render_resource_view(request, 'pages_by_type.html', context)
    
    except Exception as e:
        logger.error(f"Error loading pages by type {page_type}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'pages_by_type.html',
            {'pages': [], 'total': 0, 'page_type': page_type, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_pages_by_type_count(request: HttpRequest, page_type: str) -> HttpResponse:
    """
    Media Manager Dashboard - Pages by type count view.
    
    GET /docs/media-manager/pages/by-type/<page_type>/count/
    Mirrors: GET /api/v1/pages/by-type/<page_type>/count/
    """
    try:
        pages_service = get_pages_service()
        count = pages_service.count_pages_by_type(page_type)
        
        context: Dict[str, Any] = {
            'page_type': page_type,
            'count': count,
        }
        
        return _render_resource_view(request, 'pages_count.html', context)
    
    except Exception as e:
        logger.error(f"Error loading pages by type count for {page_type}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'pages_count.html',
            {'page_type': page_type, 'count': 0, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_pages_by_type_published(request: HttpRequest, page_type: str) -> HttpResponse:
    """
    Media Manager Dashboard - Pages by type published view.
    
    GET /docs/media-manager/pages/by-type/<page_type>/published/
    Mirrors: GET /api/v1/pages/by-type/<page_type>/published/
    """
    try:
        pages_service = get_pages_service()
        result = pages_service.list_pages(
            page_type=page_type,
            include_drafts=False,
            include_deleted=False,
            page_state="published",
            limit=None,
            offset=0
        )
        
        context: Dict[str, Any] = {
            'pages': result.get("pages", []),
            'total': result.get("total", 0),
            'page_type': page_type,
            'state': 'published',
            'filters': {'page_type': page_type, 'state': 'published'},
        }
        
        return _render_resource_view(request, 'pages_by_type.html', context)
    
    except Exception as e:
        logger.error(f"Error loading pages by type published for {page_type}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'pages_by_type.html',
            {'pages': [], 'total': 0, 'page_type': page_type, 'state': 'published', 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_pages_by_type_draft(request: HttpRequest, page_type: str) -> HttpResponse:
    """
    Media Manager Dashboard - Pages by type draft view.
    
    GET /docs/media-manager/pages/by-type/<page_type>/draft/
    Mirrors: GET /api/v1/pages/by-type/<page_type>/draft/
    """
    try:
        pages_service = get_pages_service()
        result = pages_service.list_pages(
            page_type=page_type,
            include_drafts=True,
            include_deleted=False,
            page_state="draft",
            limit=None,
            offset=0
        )
        
        context: Dict[str, Any] = {
            'pages': result.get("pages", []),
            'total': result.get("total", 0),
            'page_type': page_type,
            'state': 'draft',
            'filters': {'page_type': page_type, 'state': 'draft'},
        }
        
        return _render_resource_view(request, 'pages_by_type.html', context)
    
    except Exception as e:
        logger.error(f"Error loading pages by type draft for {page_type}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'pages_by_type.html',
            {'pages': [], 'total': 0, 'page_type': page_type, 'state': 'draft', 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_pages_by_type_stats(request: HttpRequest, page_type: str) -> HttpResponse:
    """
    Media Manager Dashboard - Pages by type statistics view.
    
    GET /docs/media-manager/pages/by-type/<page_type>/stats/
    Mirrors: GET /api/v1/pages/by-type/<page_type>/stats/
    """
    try:
        pages_service = get_pages_service()
        stats = pages_service.get_type_statistics()
        statistics = stats.get("statistics", [])
        type_stats = next((s for s in statistics if s.get("type") == page_type), {})
        
        from apps.documentation.services import get_shared_s3_index_manager
        index_manager = get_shared_s3_index_manager()
        index_data = index_manager.read_index("pages")
        
        context: Dict[str, Any] = {
            'page_type': page_type,
            'total': type_stats.get("count", 0),
            'published': type_stats.get("published", 0),
            'draft': type_stats.get("draft", 0),
            'deleted': type_stats.get("deleted", 0),
            'last_updated': index_data.get("last_updated"),
        }
        
        return _render_resource_view(request, 'pages_stats.html', context)
    
    except Exception as e:
        logger.error(f"Error loading pages by type stats for {page_type}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'pages_stats.html',
            {'page_type': page_type, 'total': 0, 'published': 0, 'draft': 0, 'deleted': 0, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_pages_by_state(request: HttpRequest, state: str) -> HttpResponse:
    """
    Media Manager Dashboard - Pages by state view.
    
    GET /docs/media-manager/pages/by-state/<state>/
    Mirrors: GET /api/v1/pages/by-state/<state>/
    """
    try:
        pages_service = get_pages_service()
        result = pages_service.list_pages(page_state=state, limit=None, offset=0)
        
        context: Dict[str, Any] = {
            'pages': result.get("pages", []),
            'total': result.get("total", 0),
            'state': state,
            'filters': {'state': state},
        }
        
        return _render_resource_view(request, 'pages_by_state.html', context)
    
    except Exception as e:
        logger.error(f"Error loading pages by state {state}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'pages_by_state.html',
            {'pages': [], 'total': 0, 'state': state, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_pages_by_state_count(request: HttpRequest, state: str) -> HttpResponse:
    """
    Media Manager Dashboard - Pages by state count view.
    
    GET /docs/media-manager/pages/by-state/<state>/count/
    Mirrors: GET /api/v1/pages/by-state/<state>/count/
    """
    try:
        pages_service = get_pages_service()
        result = pages_service.list_pages(page_state=state, limit=None, offset=0)
        count = result.get("total", 0)
        
        context: Dict[str, Any] = {
            'state': state,
            'count': count,
        }
        
        return _render_resource_view(request, 'pages_count.html', context)
    
    except Exception as e:
        logger.error(f"Error loading pages by state count for {state}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'pages_count.html',
            {'state': state, 'count': 0, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_pages_by_user_type(request: HttpRequest, user_type: str) -> HttpResponse:
    """
    Media Manager Dashboard - Pages by user type view.
    
    GET /docs/media-manager/pages/by-user-type/<user_type>/
    Mirrors: GET /api/v1/pages/<user_type>/
    """
    try:
        pages_service = get_pages_service()
        page_type = request.GET.get("page_type")
        include_drafts = request.GET.get("include_drafts", "true").lower() == "true"
        include_deleted = request.GET.get("include_deleted", "false").lower() == "true"
        status_filter = request.GET.get("status")
        
        result = pages_service.list_pages_by_user_type(
            user_type=user_type,
            page_type=page_type,
            include_drafts=include_drafts,
            include_deleted=include_deleted,
            status=status_filter,
        )
        
        context: Dict[str, Any] = {
            'pages': result.get("pages", []),
            'total': result.get("total", 0),
            'user_type': user_type,
            'filters': {'user_type': user_type},
        }
        
        return _render_resource_view(request, 'pages_by_user_type.html', context)
    
    except ValueError as e:
        logger.error(f"Invalid user type {user_type}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'pages_by_user_type.html',
            {'pages': [], 'total': 0, 'user_type': user_type, 'error': str(e)},
            error_message=str(e)
        )
    except Exception as e:
        logger.error(f"Error loading pages by user type {user_type}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'pages_by_user_type.html',
            {'pages': [], 'total': 0, 'user_type': user_type, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_page_sections(request: HttpRequest, page_id: str) -> HttpResponse:
    """
    Media Manager Dashboard - Page sections view.
    
    GET /docs/media-manager/pages/<page_id>/sections/
    Mirrors: GET /api/v1/pages/<page_id>/sections/
    """
    try:
        pages_service = get_pages_service()
        page = pages_service.get_page(page_id)
        
        if not page:
            raise Http404(f"Page not found: {page_id}")
        
        sections = pages_service.get_page_sections(page_id)
        
        context: Dict[str, Any] = {
            'page': page,
            'page_id': page_id,
            'sections': sections,
        }
        
        return _render_resource_view(request, 'page_sections.html', context)
    
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error loading page sections for {page_id}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'page_sections.html',
            {'page_id': page_id, 'sections': None, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_page_components(request: HttpRequest, page_id: str) -> HttpResponse:
    """
    Media Manager Dashboard - Page components view.
    
    GET /docs/media-manager/pages/<page_id>/components/
    Mirrors: GET /api/v1/pages/<page_id>/components/
    """
    try:
        pages_service = get_pages_service()
        page = pages_service.get_page(page_id)
        
        if not page:
            raise Http404(f"Page not found: {page_id}")
        
        components = pages_service.get_page_components(page_id)
        # Also get components from sections
        sections = page.get("sections", {})
        section_components = sections.get("components", []) if sections else []
        
        context: Dict[str, Any] = {
            'page': page,
            'page_id': page_id,
            'components': section_components,
            'ui_components': components or [],
            'total': len(section_components) + len(components or []),
        }
        
        return _render_resource_view(request, 'page_components.html', context)
    
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error loading page components for {page_id}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'page_components.html',
            {'page_id': page_id, 'components': [], 'ui_components': [], 'total': 0, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_page_endpoints(request: HttpRequest, page_id: str) -> HttpResponse:
    """
    Media Manager Dashboard - Page endpoints view.
    
    GET /docs/media-manager/pages/<page_id>/endpoints/
    Mirrors: GET /api/v1/pages/<page_id>/endpoints/
    """
    try:
        pages_service = get_pages_service()
        page = pages_service.get_page(page_id)
        
        if not page:
            raise Http404(f"Page not found: {page_id}")
        
        endpoints = pages_service.get_page_endpoints(page_id)
        
        context: Dict[str, Any] = {
            'page': page,
            'page_id': page_id,
            'section_endpoints': [],
            'metadata_endpoints': endpoints or [],
            'total': len(endpoints or []),
        }
        
        return _render_resource_view(request, 'page_endpoints.html', context)
    
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error loading page endpoints for {page_id}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'page_endpoints.html',
            {'page_id': page_id, 'section_endpoints': [], 'metadata_endpoints': [], 'total': 0, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_page_versions(request: HttpRequest, page_id: str) -> HttpResponse:
    """
    Media Manager Dashboard - Page versions view.
    
    GET /docs/media-manager/pages/<page_id>/versions/
    Mirrors: GET /api/v1/pages/<page_id>/versions/
    """
    try:
        pages_service = get_pages_service()
        page = pages_service.get_page(page_id)
        
        if not page:
            raise Http404(f"Page not found: {page_id}")
        
        versions = pages_service.get_page_versions(page_id)
        
        context: Dict[str, Any] = {
            'page': page,
            'page_id': page_id,
            'versions': versions or [],
            'count': len(versions or []),
        }
        
        return _render_resource_view(request, 'page_versions.html', context)
    
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error loading page versions for {page_id}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'page_versions.html',
            {'page_id': page_id, 'versions': [], 'count': 0, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_page_access_control(request: HttpRequest, page_id: str) -> HttpResponse:
    """
    Media Manager Dashboard - Page access control view.
    
    GET /docs/media-manager/pages/<page_id>/access-control/
    Mirrors: GET /api/v1/pages/<page_id>/access-control/
    """
    try:
        pages_service = get_pages_service()
        page = pages_service.get_page(page_id)
        
        if not page:
            raise Http404(f"Page not found: {page_id}")
        
        access_control = pages_service.get_page_access_control(page_id)
        
        context: Dict[str, Any] = {
            'page': page,
            'page_id': page_id,
            'access_control': access_control,
        }
        
        return _render_resource_view(request, 'page_access_control.html', context)
    
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error loading page access control for {page_id}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'page_access_control.html',
            {'page_id': page_id, 'access_control': None, 'error': str(e)},
            error_message=str(e)
        )


# ============================================================================
# Endpoints API Views - Enhanced routes (mirroring /api/v1/endpoints/)
# ============================================================================

@login_required
def media_manager_endpoints_statistics(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Endpoints statistics view.
    
    GET /docs/media-manager/endpoints/statistics/
    Mirrors: GET /api/v1/endpoints/api-versions/ + GET /api/v1/endpoints/methods/
    """
    try:
        endpoints_service = get_endpoints_service()
        api_version_stats = endpoints_service.get_api_version_statistics()
        method_stats = endpoints_service.get_method_statistics()
        
        context: Dict[str, Any] = {
            'api_version_statistics': api_version_stats,
            'method_statistics': method_stats,
        }
        
        return _render_resource_view(request, 'statistics_endpoints.html', context)
    
    except Exception as e:
        logger.error(f"Error loading endpoints statistics: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'statistics_endpoints.html',
            {'api_version_statistics': {}, 'method_statistics': {}, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_endpoints_format(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Endpoints format examples view.
    
    GET /docs/endpoints/format/
    Mirrors: GET /api/v1/endpoints/format/
    """
    try:
        from apps.documentation.api.v1.endpoints_views import endpoints_format as api_endpoints_format
        import json
        
        # Call the API function to get format data
        json_response = api_endpoints_format(request)
        format_data = json.loads(json_response.content)
        
        # Format examples for display
        examples = None
        if 'examples' in format_data:
            examples = json.dumps(format_data['examples'], indent=2)
        
        analyse_payload_example = None
        if 'analyse_payload_example' in format_data:
            analyse_payload_example = json.dumps(format_data['analyse_payload_example'], indent=2)
        
        context: Dict[str, Any] = {
            'format_data': format_data,
            'examples': examples,
            'analyse_payload_example': analyse_payload_example,
        }
        
        return _render_resource_view(request, 'endpoints_format.html', context)
    
    except Exception as e:
        logger.error(f"Error loading endpoints format: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'endpoints_format.html',
            {'format_data': {}, 'examples': None, 'analyse_payload_example': None, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_endpoints_api_versions(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Endpoints API versions view.
    
    GET /docs/media-manager/endpoints/api-versions/
    Mirrors: GET /api/v1/endpoints/api-versions/
    """
    try:
        endpoints_service = get_endpoints_service()
        stats = endpoints_service.get_api_version_statistics()
        
        context: Dict[str, Any] = {
            'api_versions': stats.get("versions", []),
            'total': stats.get("total", 0),
        }
        
        return _render_resource_view(request, 'endpoints_api_versions.html', context)
    
    except Exception as e:
        logger.error(f"Error loading endpoints api versions: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'endpoints_api_versions.html',
            {'api_versions': [], 'total': 0, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_endpoints_methods(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Endpoints methods view.
    
    GET /docs/media-manager/endpoints/methods/
    Mirrors: GET /api/v1/endpoints/methods/
    """
    try:
        endpoints_service = get_endpoints_service()
        stats = endpoints_service.get_method_statistics()
        
        context: Dict[str, Any] = {
            'methods': stats.get("methods", []),
            'total': stats.get("total", 0),
        }
        
        return _render_resource_view(request, 'endpoints_methods.html', context)
    
    except Exception as e:
        logger.error(f"Error loading endpoints methods: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'endpoints_methods.html',
            {'methods': [], 'total': 0, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_endpoints_by_api_version(request: HttpRequest, api_version: str) -> HttpResponse:
    """
    Media Manager Dashboard - Endpoints by API version (generic) view.
    
    GET /docs/endpoints/by-api-version/<api_version>/
    Mirrors: GET /api/v1/endpoints/by-api-version/<api_version>/
    """
    try:
        endpoints_service = get_endpoints_service()
        endpoints = endpoints_service.get_endpoints_by_api_version(api_version)
        
        context: Dict[str, Any] = {
            'endpoints': endpoints,
            'total': len(endpoints),
            'api_version': api_version,
            'filters': {'api_version': api_version},
        }
        
        return _render_resource_view(request, 'endpoints_by_api_version.html', context)
    
    except Exception as e:
        logger.error(f"Error loading endpoints by api version {api_version}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'endpoints_by_api_version.html',
            {'endpoints': [], 'total': 0, 'api_version': api_version, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_endpoints_by_api_version_v1(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Endpoints by API version (v1) view.
    
    GET /docs/media-manager/endpoints/by-api-version/v1/
    Mirrors: GET /api/v1/endpoints/by-api-version/v1/
    """
    try:
        endpoints_service = get_endpoints_service()
        endpoints = endpoints_service.get_endpoints_by_api_version("v1")
        
        context: Dict[str, Any] = {
            'endpoints': endpoints,
            'total': len(endpoints),
            'api_version': 'v1',
            'filters': {'api_version': 'v1'},
        }
        
        return _render_resource_view(request, 'endpoints_by_api_version.html', context)
    
    except Exception as e:
        logger.error(f"Error loading endpoints by api version v1: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'endpoints_by_api_version.html',
            {'endpoints': [], 'total': 0, 'api_version': 'v1', 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_endpoints_by_api_version_v4(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Endpoints by API version (v4) view.
    
    GET /docs/media-manager/endpoints/by-api-version/v4/
    Mirrors: GET /api/v1/endpoints/by-api-version/v4/
    """
    try:
        endpoints_service = get_endpoints_service()
        endpoints = endpoints_service.get_endpoints_by_api_version("v4")
        
        context: Dict[str, Any] = {
            'endpoints': endpoints,
            'total': len(endpoints),
            'api_version': 'v4',
            'filters': {'api_version': 'v4'},
        }
        
        return _render_resource_view(request, 'endpoints_by_api_version.html', context)
    
    except Exception as e:
        logger.error(f"Error loading endpoints by api version v4: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'endpoints_by_api_version.html',
            {'endpoints': [], 'total': 0, 'api_version': 'v4', 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_endpoints_by_api_version_graphql(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Endpoints by API version (graphql) view.
    
    GET /docs/media-manager/endpoints/by-api-version/graphql/
    Mirrors: GET /api/v1/endpoints/by-api-version/graphql/
    """
    try:
        endpoints_service = get_endpoints_service()
        endpoints = endpoints_service.get_endpoints_by_api_version("graphql")
        
        context: Dict[str, Any] = {
            'endpoints': endpoints,
            'total': len(endpoints),
            'api_version': 'graphql',
            'filters': {'api_version': 'graphql'},
        }
        
        return _render_resource_view(request, 'endpoints_by_api_version.html', context)
    
    except Exception as e:
        logger.error(f"Error loading endpoints by api version graphql: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'endpoints_by_api_version.html',
            {'endpoints': [], 'total': 0, 'api_version': 'graphql', 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_endpoints_by_api_version_count(request: HttpRequest, api_version: str) -> HttpResponse:
    """
    Media Manager Dashboard - Endpoints by API version count view.
    
    GET /docs/media-manager/endpoints/by-api-version/<api_version>/count/
    Mirrors: GET /api/v1/endpoints/by-api-version/<api_version>/count/
    """
    try:
        endpoints_service = get_endpoints_service()
        count = endpoints_service.count_endpoints_by_api_version(api_version)
        
        context: Dict[str, Any] = {
            'api_version': api_version,
            'count': count,
        }
        
        return _render_resource_view(request, 'endpoints_count.html', context)
    
    except Exception as e:
        logger.error(f"Error loading endpoints by api version count for {api_version}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'endpoints_count.html',
            {'api_version': api_version, 'count': 0, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_endpoints_by_api_version_stats(request: HttpRequest, api_version: str) -> HttpResponse:
    """
    Media Manager Dashboard - Endpoints by API version statistics view.
    
    GET /docs/media-manager/endpoints/by-api-version/<api_version>/stats/
    Mirrors: GET /api/v1/endpoints/by-api-version/<api_version>/stats/
    """
    try:
        from collections import Counter
        endpoints_service = get_endpoints_service()
        endpoints = endpoints_service.get_endpoints_by_api_version(api_version)
        by_method = Counter(ep.get("method", "GET") for ep in endpoints)
        
        context: Dict[str, Any] = {
            'api_version': api_version,
            'total': len(endpoints),
            'by_method': dict(by_method),
        }
        
        return _render_resource_view(request, 'endpoints_stats.html', context)
    
    except Exception as e:
        logger.error(f"Error loading endpoints by api version stats for {api_version}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'endpoints_stats.html',
            {'api_version': api_version, 'total': 0, 'by_method': {}, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_endpoints_by_api_version_by_method(request: HttpRequest, api_version: str, method: str) -> HttpResponse:
    """
    Media Manager Dashboard - Endpoints by API version and method view.
    
    GET /docs/media-manager/endpoints/by-api-version/<api_version>/by-method/<method>/
    Mirrors: GET /api/v1/endpoints/by-api-version/<api_version>/by-method/<method>/
    """
    try:
        endpoints_service = get_endpoints_service()
        endpoints = endpoints_service.get_endpoints_by_version_and_method(api_version, method)
        
        context: Dict[str, Any] = {
            'endpoints': endpoints,
            'total': len(endpoints),
            'api_version': api_version,
            'method': method,
            'filters': {'api_version': api_version, 'method': method},
        }
        
        return _render_resource_view(request, 'endpoints_by_api_version.html', context)
    
    except Exception as e:
        logger.error(f"Error loading endpoints by api version {api_version} and method {method}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'endpoints_by_api_version.html',
            {'endpoints': [], 'total': 0, 'api_version': api_version, 'method': method, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_endpoints_by_method(request: HttpRequest, method: str) -> HttpResponse:
    """
    Media Manager Dashboard - Endpoints by method (generic) view.
    
    GET /docs/endpoints/by-method/<method>/
    Mirrors: GET /api/v1/endpoints/by-method/<method>/
    """
    try:
        endpoints_service = get_endpoints_service()
        endpoints = endpoints_service.get_endpoints_by_method(method)
        
        context: Dict[str, Any] = {
            'endpoints': endpoints,
            'total': len(endpoints),
            'method': method,
            'filters': {'method': method},
        }
        
        return _render_resource_view(request, 'endpoints_by_method.html', context)
    
    except Exception as e:
        logger.error(f"Error loading endpoints by method {method}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'endpoints_by_method.html',
            {'endpoints': [], 'total': 0, 'method': method, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_endpoints_by_method_get(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Endpoints by method (GET) view.
    
    GET /docs/media-manager/endpoints/by-method/GET/
    Mirrors: GET /api/v1/endpoints/by-method/GET/
    """
    try:
        endpoints_service = get_endpoints_service()
        endpoints = endpoints_service.get_endpoints_by_method("GET")
        
        context: Dict[str, Any] = {
            'endpoints': endpoints,
            'total': len(endpoints),
            'method': 'GET',
            'filters': {'method': 'GET'},
        }
        
        return _render_resource_view(request, 'endpoints_by_method.html', context)
    
    except Exception as e:
        logger.error(f"Error loading endpoints by method GET: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'endpoints_by_method.html',
            {'endpoints': [], 'total': 0, 'method': 'GET', 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_endpoints_by_method_post(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Endpoints by method (POST) view.
    
    GET /docs/media-manager/endpoints/by-method/POST/
    Mirrors: GET /api/v1/endpoints/by-method/POST/
    """
    try:
        endpoints_service = get_endpoints_service()
        endpoints = endpoints_service.get_endpoints_by_method("POST")
        
        context: Dict[str, Any] = {
            'endpoints': endpoints,
            'total': len(endpoints),
            'method': 'POST',
            'filters': {'method': 'POST'},
        }
        
        return _render_resource_view(request, 'endpoints_by_method.html', context)
    
    except Exception as e:
        logger.error(f"Error loading endpoints by method POST: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'endpoints_by_method.html',
            {'endpoints': [], 'total': 0, 'method': 'POST', 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_endpoints_by_method_query(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Endpoints by method (QUERY) view.
    
    GET /docs/media-manager/endpoints/by-method/QUERY/
    Mirrors: GET /api/v1/endpoints/by-method/QUERY/
    """
    try:
        endpoints_service = get_endpoints_service()
        endpoints = endpoints_service.get_endpoints_by_method("QUERY")
        
        context: Dict[str, Any] = {
            'endpoints': endpoints,
            'total': len(endpoints),
            'method': 'QUERY',
            'filters': {'method': 'QUERY'},
        }
        
        return _render_resource_view(request, 'endpoints_by_method.html', context)
    
    except Exception as e:
        logger.error(f"Error loading endpoints by method QUERY: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'endpoints_by_method.html',
            {'endpoints': [], 'total': 0, 'method': 'QUERY', 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_endpoints_by_method_mutation(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Endpoints by method (MUTATION) view.
    
    GET /docs/media-manager/endpoints/by-method/MUTATION/
    Mirrors: GET /api/v1/endpoints/by-method/MUTATION/
    """
    try:
        endpoints_service = get_endpoints_service()
        endpoints = endpoints_service.get_endpoints_by_method("MUTATION")
        
        context: Dict[str, Any] = {
            'endpoints': endpoints,
            'total': len(endpoints),
            'method': 'MUTATION',
            'filters': {'method': 'MUTATION'},
        }
        
        return _render_resource_view(request, 'endpoints_by_method.html', context)
    
    except Exception as e:
        logger.error(f"Error loading endpoints by method MUTATION: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'endpoints_by_method.html',
            {'endpoints': [], 'total': 0, 'method': 'MUTATION', 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_endpoints_by_method_count(request: HttpRequest, method: str) -> HttpResponse:
    """
    Media Manager Dashboard - Endpoints by method count view.
    
    GET /docs/media-manager/endpoints/by-method/<method>/count/
    Mirrors: GET /api/v1/endpoints/by-method/<method>/count/
    """
    try:
        endpoints_service = get_endpoints_service()
        count = endpoints_service.count_endpoints_by_method(method)
        
        context: Dict[str, Any] = {
            'method': method,
            'count': count,
        }
        
        return _render_resource_view(request, 'endpoints_count.html', context)
    
    except Exception as e:
        logger.error(f"Error loading endpoints by method count for {method}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'endpoints_count.html',
            {'method': method, 'count': 0, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_endpoints_by_method_stats(request: HttpRequest, method: str) -> HttpResponse:
    """
    Media Manager Dashboard - Endpoints by method statistics view.
    
    GET /docs/media-manager/endpoints/by-method/<method>/stats/
    Mirrors: GET /api/v1/endpoints/by-method/<method>/stats/
    """
    try:
        from collections import Counter
        endpoints_service = get_endpoints_service()
        endpoints = endpoints_service.get_endpoints_by_method(method)
        by_version = Counter(ep.get("api_version", "v1") for ep in endpoints)
        
        context: Dict[str, Any] = {
            'method': method,
            'total': len(endpoints),
            'by_api_version': dict(by_version),
        }
        
        return _render_resource_view(request, 'endpoints_stats.html', context)
    
    except Exception as e:
        logger.error(f"Error loading endpoints by method stats for {method}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'endpoints_stats.html',
            {'method': method, 'total': 0, 'by_api_version': {}, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_endpoints_by_state(request: HttpRequest, state: str) -> HttpResponse:
    """
    Media Manager Dashboard - Endpoints by state view.
    
    GET /docs/media-manager/endpoints/by-state/<state>/
    Mirrors: GET /api/v1/endpoints/by-state/<state>/
    """
    try:
        endpoints_service = get_endpoints_service()
        result = endpoints_service.list_endpoints(endpoint_state=state, limit=None, offset=0)
        
        context: Dict[str, Any] = {
            'endpoints': result.get("endpoints", []),
            'total': result.get("total", 0),
            'state': state,
            'filters': {'state': state},
        }
        
        return _render_resource_view(request, 'endpoints_by_state.html', context)
    
    except Exception as e:
        logger.error(f"Error loading endpoints by state {state}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'endpoints_by_state.html',
            {'endpoints': [], 'total': 0, 'state': state, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_endpoints_by_state_count(request: HttpRequest, state: str) -> HttpResponse:
    """
    Media Manager Dashboard - Endpoints by state count view.
    
    GET /docs/media-manager/endpoints/by-state/<state>/count/
    Mirrors: GET /api/v1/endpoints/by-state/<state>/count/
    """
    try:
        endpoints_service = get_endpoints_service()
        result = endpoints_service.list_endpoints(endpoint_state=state, limit=None, offset=0)
        count = result.get("total", 0)
        
        context: Dict[str, Any] = {
            'state': state,
            'count': count,
        }
        
        return _render_resource_view(request, 'endpoints_count.html', context)
    
    except Exception as e:
        logger.error(f"Error loading endpoints by state count for {state}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'endpoints_count.html',
            {'state': state, 'count': 0, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_endpoints_by_lambda(request: HttpRequest, service_name: str) -> HttpResponse:
    """
    Media Manager Dashboard - Endpoints by Lambda service view.
    
    GET /docs/media-manager/endpoints/by-lambda/<service_name>/
    Mirrors: GET /api/v1/endpoints/by-lambda/<service_name>/
    """
    try:
        endpoints_service = get_endpoints_service()
        result = endpoints_service.list_endpoints(limit=None, offset=0)
        endpoints = result.get("endpoints", [])
        filtered = []
        for ep in endpoints:
            ls = ep.get("lambda_services") or {}
            primary = ls.get("primary") or {}
            if primary.get("service_name") == service_name:
                filtered.append(ep)
                continue
            for dep in (ls.get("dependencies") or []):
                if dep.get("service_name") == service_name:
                    filtered.append(ep)
                    break
        
        context: Dict[str, Any] = {
            'endpoints': filtered,
            'total': len(filtered),
            'service_name': service_name,
            'filters': {'lambda_service': service_name},
        }
        
        return _render_resource_view(request, 'endpoints_by_lambda.html', context)
    
    except Exception as e:
        logger.error(f"Error loading endpoints by lambda service {service_name}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'endpoints_by_lambda.html',
            {'endpoints': [], 'total': 0, 'service_name': service_name, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_endpoints_by_lambda_count(request: HttpRequest, service_name: str) -> HttpResponse:
    """
    Media Manager Dashboard - Endpoints by Lambda service count view.
    
    GET /docs/media-manager/endpoints/by-lambda/<service_name>/count/
    Mirrors: GET /api/v1/endpoints/by-lambda/<service_name>/count/
    """
    try:
        endpoints_service = get_endpoints_service()
        result = endpoints_service.list_endpoints(limit=None, offset=0)
        endpoints = result.get("endpoints", [])
        count = 0
        for ep in endpoints:
            ls = ep.get("lambda_services") or {}
            primary = ls.get("primary") or {}
            if primary.get("service_name") == service_name:
                count += 1
                continue
            for dep in (ls.get("dependencies") or []):
                if dep.get("service_name") == service_name:
                    count += 1
                    break
        
        context: Dict[str, Any] = {
            'service_name': service_name,
            'count': count,
        }
        
        return _render_resource_view(request, 'endpoints_count.html', context)
    
    except Exception as e:
        logger.error(f"Error loading endpoints by lambda service count for {service_name}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'endpoints_count.html',
            {'service_name': service_name, 'count': 0, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_endpoint_pages(request: HttpRequest, endpoint_id: str) -> HttpResponse:
    """
    Media Manager Dashboard - Endpoint pages view.
    
    GET /docs/media-manager/endpoints/<endpoint_id>/pages/
    Mirrors: GET /api/v1/endpoints/<endpoint_id>/pages/
    """
    try:
        endpoints_service = get_endpoints_service()
        endpoint = endpoints_service.get_endpoint(endpoint_id)
        
        if not endpoint:
            raise Http404(f"Endpoint not found: {endpoint_id}")
        
        pages_result = endpoints_service.get_endpoint_pages(endpoint_id)
        pages = pages_result.get('pages', []) if isinstance(pages_result, dict) else pages_result or []
        
        context: Dict[str, Any] = {
            'endpoint': endpoint,
            'endpoint_id': endpoint_id,
            'pages': pages,
            'count': len(pages),
        }
        
        return _render_resource_view(request, 'endpoint_pages.html', context)
    
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error loading endpoint pages for {endpoint_id}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'endpoint_pages.html',
            {'endpoint_id': endpoint_id, 'pages': [], 'count': 0, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_endpoint_access_control(request: HttpRequest, endpoint_id: str) -> HttpResponse:
    """
    Media Manager Dashboard - Endpoint access control view.
    
    GET /docs/media-manager/endpoints/<endpoint_id>/access-control/
    Mirrors: GET /api/v1/endpoints/<endpoint_id>/access-control/
    """
    try:
        endpoints_service = get_endpoints_service()
        endpoint = endpoints_service.get_endpoint(endpoint_id)
        
        if not endpoint:
            raise Http404(f"Endpoint not found: {endpoint_id}")
        
        access_control = endpoints_service.get_endpoint_access_control(endpoint_id)
        
        context: Dict[str, Any] = {
            'endpoint': endpoint,
            'endpoint_id': endpoint_id,
            'access_control': access_control,
        }
        
        return _render_resource_view(request, 'endpoint_access_control.html', context)
    
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error loading endpoint access control for {endpoint_id}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'endpoint_access_control.html',
            {'endpoint_id': endpoint_id, 'access_control': None, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_endpoint_lambda_services(request: HttpRequest, endpoint_id: str) -> HttpResponse:
    """
    Media Manager Dashboard - Endpoint Lambda services view.
    
    GET /docs/media-manager/endpoints/<endpoint_id>/lambda-services/
    Mirrors: GET /api/v1/endpoints/<endpoint_id>/lambda-services/
    """
    try:
        endpoints_service = get_endpoints_service()
        endpoint = endpoints_service.get_endpoint(endpoint_id)
        
        if not endpoint:
            raise Http404(f"Endpoint not found: {endpoint_id}")
        
        lambda_services = endpoints_service.get_endpoint_lambda_services(endpoint_id)
        
        context: Dict[str, Any] = {
            'endpoint': endpoint,
            'endpoint_id': endpoint_id,
            'lambda_services': lambda_services or {},
        }
        
        return _render_resource_view(request, 'endpoint_lambda_services.html', context)
    
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error loading endpoint lambda services for {endpoint_id}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'endpoint_lambda_services.html',
            {'endpoint_id': endpoint_id, 'lambda_services': {}, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_endpoint_files(request: HttpRequest, endpoint_id: str) -> HttpResponse:
    """
    Media Manager Dashboard - Endpoint files view.
    
    GET /docs/media-manager/endpoints/<endpoint_id>/files/
    Mirrors: GET /api/v1/endpoints/<endpoint_id>/files/
    """
    try:
        endpoints_service = get_endpoints_service()
        endpoint = endpoints_service.get_endpoint(endpoint_id)
        
        if not endpoint:
            raise Http404(f"Endpoint not found: {endpoint_id}")
        
        files = endpoints_service.get_endpoint_files(endpoint_id)
        
        context: Dict[str, Any] = {
            'endpoint': endpoint,
            'endpoint_id': endpoint_id,
            'service_file': endpoint.get("service_file"),
            'router_file': endpoint.get("router_file"),
            'files': files or [],
        }
        
        return _render_resource_view(request, 'endpoint_files.html', context)
    
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error loading endpoint files for {endpoint_id}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'endpoint_files.html',
            {'endpoint_id': endpoint_id, 'service_file': None, 'router_file': None, 'files': [], 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_endpoint_methods(request: HttpRequest, endpoint_id: str) -> HttpResponse:
    """
    Media Manager Dashboard - Endpoint methods view.
    
    GET /docs/media-manager/endpoints/<endpoint_id>/methods/
    Mirrors: GET /api/v1/endpoints/<endpoint_id>/methods/
    """
    try:
        endpoints_service = get_endpoints_service()
        endpoint = endpoints_service.get_endpoint(endpoint_id)
        
        if not endpoint:
            raise Http404(f"Endpoint not found: {endpoint_id}")
        
        methods = endpoint.get("service_methods") or []
        
        context: Dict[str, Any] = {
            'endpoint': endpoint,
            'endpoint_id': endpoint_id,
            'methods': methods,
            'count': len(methods),
        }
        
        return _render_resource_view(request, 'endpoint_methods.html', context)
    
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error loading endpoint methods for {endpoint_id}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'endpoint_methods.html',
            {'endpoint_id': endpoint_id, 'methods': [], 'count': 0, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_endpoint_used_by_pages(request: HttpRequest, endpoint_id: str) -> HttpResponse:
    """
    Media Manager Dashboard - Endpoint used by pages view.
    
    GET /docs/media-manager/endpoints/<endpoint_id>/used-by-pages/
    Mirrors: GET /api/v1/endpoints/<endpoint_id>/used-by-pages/
    """
    try:
        endpoints_service = get_endpoints_service()
        endpoint = endpoints_service.get_endpoint(endpoint_id)
        
        if not endpoint:
            raise Http404(f"Endpoint not found: {endpoint_id}")
        
        pages = endpoint.get("used_by_pages") or []
        
        context: Dict[str, Any] = {
            'endpoint': endpoint,
            'endpoint_id': endpoint_id,
            'used_by_pages': pages,
            'count': len(pages),
        }
        
        return _render_resource_view(request, 'endpoint_used_by_pages.html', context)
    
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error loading endpoint used by pages for {endpoint_id}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'endpoint_used_by_pages.html',
            {'endpoint_id': endpoint_id, 'used_by_pages': [], 'count': 0, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_endpoint_dependencies(request: HttpRequest, endpoint_id: str) -> HttpResponse:
    """
    Media Manager Dashboard - Endpoint dependencies view.
    
    GET /docs/media-manager/endpoints/<endpoint_id>/dependencies/
    Mirrors: GET /api/v1/endpoints/<endpoint_id>/dependencies/
    """
    try:
        endpoints_service = get_endpoints_service()
        endpoint = endpoints_service.get_endpoint(endpoint_id)
        
        if not endpoint:
            raise Http404(f"Endpoint not found: {endpoint_id}")
        
        dependencies = endpoints_service.get_endpoint_dependencies(endpoint_id)
        deps = dependencies if isinstance(dependencies, list) else (endpoint.get("lambda_services") or {}).get("dependencies") or []
        
        context: Dict[str, Any] = {
            'endpoint': endpoint,
            'endpoint_id': endpoint_id,
            'dependencies': deps,
            'count': len(deps),
        }
        
        return _render_resource_view(request, 'endpoint_dependencies.html', context)
    
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error loading endpoint dependencies for {endpoint_id}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'endpoint_dependencies.html',
            {'endpoint_id': endpoint_id, 'dependencies': [], 'count': 0, 'error': str(e)},
            error_message=str(e)
        )


# ============================================================================
# Relationships API Views - Enhanced routes (mirroring /api/v1/relationships/)
# ============================================================================

@login_required
def media_manager_relationships_statistics(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Relationships statistics view.
    
    GET /docs/media-manager/relationships/statistics/
    Mirrors: GET /api/v1/relationships/statistics/
    """
    try:
        relationships_service = get_relationships_service()
        stats = relationships_service.get_statistics()
        
        context: Dict[str, Any] = {
            'statistics': stats,
        }
        
        return _render_resource_view(request, 'relationships_statistics.html', context)
    
    except Exception as e:
        logger.error(f"Error loading relationships statistics: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'relationships_statistics.html',
            {'statistics': {}, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_relationships_format(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Relationships format examples view.
    
    GET /docs/relationships/format/
    Mirrors: GET /api/v1/relationships/format/
    """
    try:
        from apps.documentation.api.v1.relationships_views import relationships_format as api_relationships_format
        import json
        
        # Call the API function to get format data
        json_response = api_relationships_format(request)
        format_data = json.loads(json_response.content)
        
        # Format examples for display
        examples = None
        if 'examples' in format_data:
            examples = json.dumps(format_data['examples'], indent=2)
        
        analyse_payload_example = None
        if 'analyse_payload_example' in format_data:
            analyse_payload_example = json.dumps(format_data['analyse_payload_example'], indent=2)
        
        context: Dict[str, Any] = {
            'format_data': format_data,
            'examples': examples,
            'analyse_payload_example': analyse_payload_example,
        }
        
        return _render_resource_view(request, 'relationships_format.html', context)
    
    except Exception as e:
        logger.error(f"Error loading relationships format: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'relationships_format.html',
            {'format_data': {}, 'examples': None, 'analyse_payload_example': None, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_relationships_graph(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Relationships graph view.
    
    GET /docs/media-manager/relationships/graph/
    Mirrors: GET /api/v1/relationships/graph/
    """
    try:
        relationships_service = get_relationships_service()
        graph = relationships_service.get_graph()
        
        context: Dict[str, Any] = {
            'graph': graph,
            'nodes': graph.get("nodes", []),
            'edges': graph.get("edges", []),
        }
        
        return _render_resource_view(request, 'relationships_graph.html', context)
    
    except Exception as e:
        logger.error(f"Error loading relationships graph: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'relationships_graph.html',
            {'graph': {}, 'nodes': [], 'edges': [], 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_relationships_usage_types(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Relationships usage types view.
    
    GET /docs/media-manager/relationships/usage-types/
    Mirrors: GET /api/v1/relationships/usage-types/
    """
    try:
        relationships_service = get_relationships_service()
        stats = relationships_service.get_statistics()
        by_ut = stats.get("by_usage_type", {})
        types_data = [{"usage_type": k, "count": v} for k, v in by_ut.items()]
        
        context: Dict[str, Any] = {
            'usage_types': types_data,
            'total': sum(v for v in by_ut.values()),
        }
        
        return _render_resource_view(request, 'relationships_usage_types.html', context)
    
    except Exception as e:
        logger.error(f"Error loading relationships usage types: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'relationships_usage_types.html',
            {'usage_types': [], 'total': 0, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_relationships_usage_contexts(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Relationships usage contexts view.
    
    GET /docs/media-manager/relationships/usage-contexts/
    Mirrors: GET /api/v1/relationships/usage-contexts/
    """
    try:
        relationships_service = get_relationships_service()
        stats = relationships_service.get_statistics()
        by_uc = stats.get("by_usage_context", {})
        ctx_data = [{"usage_context": k, "count": v} for k, v in by_uc.items()]
        
        context: Dict[str, Any] = {
            'usage_contexts': ctx_data,
            'total': sum(v for v in by_uc.values()),
        }
        
        return _render_resource_view(request, 'relationships_usage_contexts.html', context)
    
    except Exception as e:
        logger.error(f"Error loading relationships usage contexts: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'relationships_usage_contexts.html',
            {'usage_contexts': [], 'total': 0, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_relationships_by_page(request: HttpRequest, page_id: str) -> HttpResponse:
    """
    Media Manager Dashboard - Relationships by page view.
    
    GET /docs/media-manager/relationships/by-page/<page_id>/
    Mirrors: GET /api/v1/relationships/by-page/<page_id>/
    """
    try:
        relationships_service = get_relationships_service()
        result = relationships_service.list_relationships(page_id=page_id, limit=None, offset=0)
        
        context: Dict[str, Any] = {
            'relationships': result.get("relationships", []),
            'total': result.get("total", 0),
            'page_id': page_id,
            'filters': {'page_id': page_id},
        }
        
        return _render_resource_view(request, 'relationships_by_page.html', context)
    
    except Exception as e:
        logger.error(f"Error loading relationships by page {page_id}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'relationships_by_page.html',
            {'relationships': [], 'total': 0, 'page_id': page_id, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_relationships_by_page_count(request: HttpRequest, page_id: str) -> HttpResponse:
    """
    Media Manager Dashboard - Relationships by page count view.
    
    GET /docs/media-manager/relationships/by-page/<page_id>/count/
    Mirrors: GET /api/v1/relationships/by-page/<page_id>/count/
    """
    try:
        relationships_service = get_relationships_service()
        result = relationships_service.list_relationships(page_id=page_id, limit=None, offset=0)
        count = result.get("total", 0)
        
        context: Dict[str, Any] = {
            'page_id': page_id,
            'count': count,
        }
        
        return _render_resource_view(request, 'relationships_count.html', context)
    
    except Exception as e:
        logger.error(f"Error loading relationships by page count for {page_id}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'relationships_count.html',
            {'page_id': page_id, 'count': 0, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_relationships_by_page_primary(request: HttpRequest, page_id: str) -> HttpResponse:
    """
    Media Manager Dashboard - Relationships by page (primary) view.
    
    GET /docs/media-manager/relationships/by-page/<page_id>/primary/
    Mirrors: GET /api/v1/relationships/by-page/<page_id>/primary/
    """
    try:
        relationships_service = get_relationships_service()
        result = relationships_service.list_relationships(page_id=page_id, usage_type="primary", limit=None, offset=0)
        
        context: Dict[str, Any] = {
            'relationships': result.get("relationships", []),
            'total': result.get("total", 0),
            'page_id': page_id,
            'usage_type': 'primary',
            'filters': {'page_id': page_id, 'usage_type': 'primary'},
        }
        
        return _render_resource_view(request, 'relationships_by_page.html', context)
    
    except Exception as e:
        logger.error(f"Error loading relationships by page {page_id} primary: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'relationships_by_page.html',
            {'relationships': [], 'total': 0, 'page_id': page_id, 'usage_type': 'primary', 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_relationships_by_page_secondary(request: HttpRequest, page_id: str) -> HttpResponse:
    """
    Media Manager Dashboard - Relationships by page (secondary) view.
    
    GET /docs/media-manager/relationships/by-page/<page_id>/secondary/
    Mirrors: GET /api/v1/relationships/by-page/<page_id>/secondary/
    """
    try:
        relationships_service = get_relationships_service()
        result = relationships_service.list_relationships(page_id=page_id, usage_type="secondary", limit=None, offset=0)
        
        context: Dict[str, Any] = {
            'relationships': result.get("relationships", []),
            'total': result.get("total", 0),
            'page_id': page_id,
            'usage_type': 'secondary',
            'filters': {'page_id': page_id, 'usage_type': 'secondary'},
        }
        
        return _render_resource_view(request, 'relationships_by_page.html', context)
    
    except Exception as e:
        logger.error(f"Error loading relationships by page {page_id} secondary: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'relationships_by_page.html',
            {'relationships': [], 'total': 0, 'page_id': page_id, 'usage_type': 'secondary', 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_relationships_by_page_by_usage_type(request: HttpRequest, page_id: str, usage_type: str) -> HttpResponse:
    """
    Media Manager Dashboard - Relationships by page and usage type view.
    
    GET /docs/media-manager/relationships/by-page/<page_id>/by-usage-type/<usage_type>/
    Mirrors: GET /api/v1/relationships/by-page/<page_id>/by-usage-type/<usage_type>/
    """
    try:
        relationships_service = get_relationships_service()
        result = relationships_service.list_relationships(page_id=page_id, usage_type=usage_type, limit=None, offset=0)
        
        context: Dict[str, Any] = {
            'relationships': result.get("relationships", []),
            'total': result.get("total", 0),
            'page_id': page_id,
            'usage_type': usage_type,
            'filters': {'page_id': page_id, 'usage_type': usage_type},
        }
        
        return _render_resource_view(request, 'relationships_by_page.html', context)
    
    except Exception as e:
        logger.error(f"Error loading relationships by page {page_id} and usage type {usage_type}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'relationships_by_page.html',
            {'relationships': [], 'total': 0, 'page_id': page_id, 'usage_type': usage_type, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_relationships_by_endpoint(request: HttpRequest, endpoint_id: str) -> HttpResponse:
    """
    Media Manager Dashboard - Relationships by endpoint view.
    
    GET /docs/media-manager/relationships/by-endpoint/<endpoint_id>/
    Mirrors: GET /api/v1/relationships/by-endpoint/<endpoint_id>/
    """
    try:
        relationships_service = get_relationships_service()
        result = relationships_service.list_relationships(endpoint_id=endpoint_id, limit=None, offset=0)
        
        context: Dict[str, Any] = {
            'relationships': result.get("relationships", []),
            'total': result.get("total", 0),
            'endpoint_id': endpoint_id,
            'filters': {'endpoint_id': endpoint_id},
        }
        
        return _render_resource_view(request, 'relationships_by_endpoint.html', context)
    
    except Exception as e:
        logger.error(f"Error loading relationships by endpoint {endpoint_id}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'relationships_by_endpoint.html',
            {'relationships': [], 'total': 0, 'endpoint_id': endpoint_id, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_relationships_by_endpoint_count(request: HttpRequest, endpoint_id: str) -> HttpResponse:
    """
    Media Manager Dashboard - Relationships by endpoint count view.
    
    GET /docs/media-manager/relationships/by-endpoint/<endpoint_id>/count/
    Mirrors: GET /api/v1/relationships/by-endpoint/<endpoint_id>/count/
    """
    try:
        relationships_service = get_relationships_service()
        result = relationships_service.list_relationships(endpoint_id=endpoint_id, limit=None, offset=0)
        count = result.get("total", 0)
        
        context: Dict[str, Any] = {
            'endpoint_id': endpoint_id,
            'count': count,
        }
        
        return _render_resource_view(request, 'relationships_count.html', context)
    
    except Exception as e:
        logger.error(f"Error loading relationships by endpoint count for {endpoint_id}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'relationships_count.html',
            {'endpoint_id': endpoint_id, 'count': 0, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_relationships_by_endpoint_pages(request: HttpRequest, endpoint_id: str) -> HttpResponse:
    """
    Media Manager Dashboard - Relationships by endpoint pages view.
    
    GET /docs/media-manager/relationships/by-endpoint/<endpoint_id>/pages/
    Mirrors: GET /api/v1/relationships/by-endpoint/<endpoint_id>/pages/
    """
    try:
        relationships_service = get_relationships_service()
        result = relationships_service.list_relationships(endpoint_id=endpoint_id, limit=None, offset=0)
        rels = result.get("relationships", [])
        pages = []
        for rel in rels:
            if rel.get("page_path"):
                pages.append({"page_path": rel.get("page_path"), "page_title": rel.get("page_title", "")})
        
        context: Dict[str, Any] = {
            'endpoint_id': endpoint_id,
            'pages': pages,
            'count': len(pages),
        }
        
        return _render_resource_view(request, 'relationships_by_endpoint_pages.html', context)
    
    except Exception as e:
        logger.error(f"Error loading relationships by endpoint pages for {endpoint_id}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'relationships_by_endpoint_pages.html',
            {'endpoint_id': endpoint_id, 'pages': [], 'count': 0, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_relationships_by_endpoint_by_usage_context(request: HttpRequest, endpoint_id: str, usage_context: str) -> HttpResponse:
    """
    Media Manager Dashboard - Relationships by endpoint and usage context view.
    
    GET /docs/media-manager/relationships/by-endpoint/<endpoint_id>/by-usage-context/<usage_context>/
    Mirrors: GET /api/v1/relationships/by-endpoint/<endpoint_id>/by-usage-context/<usage_context>/
    """
    try:
        relationships_service = get_relationships_service()
        result = relationships_service.list_relationships(endpoint_id=endpoint_id, usage_context=usage_context, limit=None, offset=0)
        rels = result.get("relationships", [])
        
        context: Dict[str, Any] = {
            'endpoint_id': endpoint_id,
            'usage_context': usage_context,
            'relationships': rels,
            'count': len(rels),
            'filters': {'endpoint_id': endpoint_id, 'usage_context': usage_context},
        }
        
        return _render_resource_view(request, 'relationships_by_endpoint.html', context)
    
    except Exception as e:
        logger.error(f"Error loading relationships by endpoint {endpoint_id} and usage context {usage_context}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'relationships_by_endpoint.html',
            {'relationships': [], 'count': 0, 'endpoint_id': endpoint_id, 'usage_context': usage_context, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_relationships_by_usage_type(request: HttpRequest, usage_type: str) -> HttpResponse:
    """
    Media Manager Dashboard - Relationships by usage type (generic) view.
    
    GET /docs/relationships/by-usage-type/<usage_type>/
    Mirrors: GET /api/v1/relationships/by-usage-type/<usage_type>/
    """
    try:
        relationships_service = get_relationships_service()
        relationships = relationships_service.get_relationships_by_usage_type(usage_type)
        
        context: Dict[str, Any] = {
            'relationships': relationships,
            'total': len(relationships) if isinstance(relationships, list) else relationships.get("total", 0),
            'usage_type': usage_type,
            'filters': {'usage_type': usage_type},
        }
        
        return _render_resource_view(request, 'relationships_by_usage_type.html', context)
    
    except Exception as e:
        logger.error(f"Error loading relationships by usage type {usage_type}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'relationships_by_usage_type.html',
            {'relationships': [], 'total': 0, 'usage_type': usage_type, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_relationships_by_usage_type_primary(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Relationships by usage type (primary) view.
    
    GET /docs/media-manager/relationships/by-usage-type/primary/
    Mirrors: GET /api/v1/relationships/by-usage-type/primary/
    """
    try:
        relationships_service = get_relationships_service()
        result = relationships_service.list_relationships(usage_type="primary", limit=None, offset=0)
        
        context: Dict[str, Any] = {
            'relationships': result.get("relationships", []),
            'total': result.get("total", 0),
            'usage_type': 'primary',
            'filters': {'usage_type': 'primary'},
        }
        
        return _render_resource_view(request, 'relationships_by_usage_type.html', context)
    
    except Exception as e:
        logger.error(f"Error loading relationships by usage type primary: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'relationships_by_usage_type.html',
            {'relationships': [], 'total': 0, 'usage_type': 'primary', 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_relationships_by_usage_type_secondary(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Relationships by usage type (secondary) view.
    
    GET /docs/media-manager/relationships/by-usage-type/secondary/
    Mirrors: GET /api/v1/relationships/by-usage-type/secondary/
    """
    try:
        relationships_service = get_relationships_service()
        result = relationships_service.list_relationships(usage_type="secondary", limit=None, offset=0)
        
        context: Dict[str, Any] = {
            'relationships': result.get("relationships", []),
            'total': result.get("total", 0),
            'usage_type': 'secondary',
            'filters': {'usage_type': 'secondary'},
        }
        
        return _render_resource_view(request, 'relationships_by_usage_type.html', context)
    
    except Exception as e:
        logger.error(f"Error loading relationships by usage type secondary: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'relationships_by_usage_type.html',
            {'relationships': [], 'total': 0, 'usage_type': 'secondary', 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_relationships_by_usage_type_conditional(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Relationships by usage type (conditional) view.
    
    GET /docs/media-manager/relationships/by-usage-type/conditional/
    Mirrors: GET /api/v1/relationships/by-usage-type/conditional/
    """
    try:
        relationships_service = get_relationships_service()
        result = relationships_service.list_relationships(usage_type="conditional", limit=None, offset=0)
        
        context: Dict[str, Any] = {
            'relationships': result.get("relationships", []),
            'total': result.get("total", 0),
            'usage_type': 'conditional',
            'filters': {'usage_type': 'conditional'},
        }
        
        return _render_resource_view(request, 'relationships_by_usage_type.html', context)
    
    except Exception as e:
        logger.error(f"Error loading relationships by usage type conditional: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'relationships_by_usage_type.html',
            {'relationships': [], 'total': 0, 'usage_type': 'conditional', 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_relationships_by_usage_type_count(request: HttpRequest, usage_type: str) -> HttpResponse:
    """
    Media Manager Dashboard - Relationships by usage type count view.
    
    GET /docs/media-manager/relationships/by-usage-type/<usage_type>/count/
    Mirrors: GET /api/v1/relationships/by-usage-type/<usage_type>/count/
    """
    try:
        relationships_service = get_relationships_service()
        result = relationships_service.list_relationships(usage_type=usage_type, limit=None, offset=0)
        count = result.get("total", 0)
        
        context: Dict[str, Any] = {
            'usage_type': usage_type,
            'count': count,
        }
        
        return _render_resource_view(request, 'relationships_count.html', context)
    
    except Exception as e:
        logger.error(f"Error loading relationships by usage type count for {usage_type}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'relationships_count.html',
            {'usage_type': usage_type, 'count': 0, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_relationships_by_usage_type_by_usage_context(request: HttpRequest, usage_type: str, usage_context: str) -> HttpResponse:
    """
    Media Manager Dashboard - Relationships by usage type and usage context view.
    
    GET /docs/media-manager/relationships/by-usage-type/<usage_type>/by-usage-context/<usage_context>/
    Mirrors: GET /api/v1/relationships/by-usage-type/<usage_type>/by-usage-context/<usage_context>/
    """
    try:
        relationships_service = get_relationships_service()
        result = relationships_service.list_relationships(usage_type=usage_type, usage_context=usage_context, limit=None, offset=0)
        
        context: Dict[str, Any] = {
            'relationships': result.get("relationships", []),
            'total': result.get("total", 0),
            'usage_type': usage_type,
            'usage_context': usage_context,
            'filters': {'usage_type': usage_type, 'usage_context': usage_context},
        }
        
        return _render_resource_view(request, 'relationships_by_usage_type.html', context)
    
    except Exception as e:
        logger.error(f"Error loading relationships by usage type {usage_type} and usage context {usage_context}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'relationships_by_usage_type.html',
            {'relationships': [], 'total': 0, 'usage_type': usage_type, 'usage_context': usage_context, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_relationships_by_usage_context(request: HttpRequest, usage_context: str) -> HttpResponse:
    """
    Media Manager Dashboard - Relationships by usage context (generic) view.
    
    GET /docs/relationships/by-usage-context/<usage_context>/
    Mirrors: GET /api/v1/relationships/by-usage-context/<usage_context>/
    """
    try:
        relationships_service = get_relationships_service()
        result = relationships_service.list_relationships(usage_context=usage_context, limit=None, offset=0)
        
        context: Dict[str, Any] = {
            'relationships': result.get("relationships", []),
            'total': result.get("total", 0),
            'usage_context': usage_context,
            'filters': {'usage_context': usage_context},
        }
        
        return _render_resource_view(request, 'relationships_by_usage_context.html', context)
    
    except Exception as e:
        logger.error(f"Error loading relationships by usage context {usage_context}: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'relationships_by_usage_context.html',
            {'relationships': [], 'total': 0, 'usage_context': usage_context, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_relationships_by_usage_context_data_fetching(request: HttpRequest) -> HttpResponse:
    """GET /docs/media-manager/relationships/by-usage-context/data_fetching/"""
    try:
        relationships_service = get_relationships_service()
        result = relationships_service.list_relationships(usage_context="data_fetching", limit=None, offset=0)
        context: Dict[str, Any] = {
            'relationships': result.get("relationships", []),
            'total': result.get("total", 0),
            'usage_context': 'data_fetching',
            'filters': {'usage_context': 'data_fetching'},
        }
        return _render_resource_view(request, 'relationships_by_usage_context.html', context)
    except Exception as e:
        logger.error(f"Error loading relationships by usage context data_fetching: {e}", exc_info=True)
        return _render_resource_view(request, 'relationships_by_usage_context.html', {'relationships': [], 'total': 0, 'usage_context': 'data_fetching', 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_relationships_by_usage_context_data_mutation(request: HttpRequest) -> HttpResponse:
    """GET /docs/media-manager/relationships/by-usage-context/data_mutation/"""
    try:
        relationships_service = get_relationships_service()
        result = relationships_service.list_relationships(usage_context="data_mutation", limit=None, offset=0)
        context: Dict[str, Any] = {
            'relationships': result.get("relationships", []),
            'total': result.get("total", 0),
            'usage_context': 'data_mutation',
            'filters': {'usage_context': 'data_mutation'},
        }
        return _render_resource_view(request, 'relationships_by_usage_context.html', context)
    except Exception as e:
        logger.error(f"Error loading relationships by usage context data_mutation: {e}", exc_info=True)
        return _render_resource_view(request, 'relationships_by_usage_context.html', {'relationships': [], 'total': 0, 'usage_context': 'data_mutation', 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_relationships_by_usage_context_authentication(request: HttpRequest) -> HttpResponse:
    """GET /docs/media-manager/relationships/by-usage-context/authentication/"""
    try:
        relationships_service = get_relationships_service()
        result = relationships_service.list_relationships(usage_context="authentication", limit=None, offset=0)
        context: Dict[str, Any] = {
            'relationships': result.get("relationships", []),
            'total': result.get("total", 0),
            'usage_context': 'authentication',
            'filters': {'usage_context': 'authentication'},
        }
        return _render_resource_view(request, 'relationships_by_usage_context.html', context)
    except Exception as e:
        logger.error(f"Error loading relationships by usage context authentication: {e}", exc_info=True)
        return _render_resource_view(request, 'relationships_by_usage_context.html', {'relationships': [], 'total': 0, 'usage_context': 'authentication', 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_relationships_by_usage_context_analytics(request: HttpRequest) -> HttpResponse:
    """GET /docs/media-manager/relationships/by-usage-context/analytics/"""
    try:
        relationships_service = get_relationships_service()
        result = relationships_service.list_relationships(usage_context="analytics", limit=None, offset=0)
        context: Dict[str, Any] = {
            'relationships': result.get("relationships", []),
            'total': result.get("total", 0),
            'usage_context': 'analytics',
            'filters': {'usage_context': 'analytics'},
        }
        return _render_resource_view(request, 'relationships_by_usage_context.html', context)
    except Exception as e:
        logger.error(f"Error loading relationships by usage context analytics: {e}", exc_info=True)
        return _render_resource_view(request, 'relationships_by_usage_context.html', {'relationships': [], 'total': 0, 'usage_context': 'analytics', 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_relationships_by_usage_context_count(request: HttpRequest, usage_context: str) -> HttpResponse:
    """GET /docs/media-manager/relationships/by-usage-context/<usage_context>/count/"""
    try:
        relationships_service = get_relationships_service()
        result = relationships_service.list_relationships(usage_context=usage_context, limit=None, offset=0)
        context: Dict[str, Any] = {'usage_context': usage_context, 'count': result.get("total", 0)}
        return _render_resource_view(request, 'relationships_count.html', context)
    except Exception as e:
        logger.error(f"Error loading relationships by usage context count for {usage_context}: {e}", exc_info=True)
        return _render_resource_view(request, 'relationships_count.html', {'usage_context': usage_context, 'count': 0, 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_relationships_by_state(request: HttpRequest, state: str) -> HttpResponse:
    """GET /docs/media-manager/relationships/by-state/<state>/"""
    try:
        relationships_service = get_relationships_service()
        result = relationships_service.list_relationships(limit=None, offset=0)
        rels = [x for x in (result.get("relationships") or []) if (x.get("state") or x.get("relationship_state")) == state]
        context: Dict[str, Any] = {'relationships': rels, 'total': len(rels), 'state': state, 'filters': {'state': state}}
        return _render_resource_view(request, 'relationships_by_state.html', context)
    except Exception as e:
        logger.error(f"Error loading relationships by state {state}: {e}", exc_info=True)
        return _render_resource_view(request, 'relationships_by_state.html', {'relationships': [], 'total': 0, 'state': state, 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_relationships_by_state_count(request: HttpRequest, state: str) -> HttpResponse:
    """GET /docs/media-manager/relationships/by-state/<state>/count/"""
    try:
        relationships_service = get_relationships_service()
        result = relationships_service.list_relationships(limit=None, offset=0)
        rels = [x for x in (result.get("relationships") or []) if (x.get("state") or x.get("relationship_state")) == state]
        context: Dict[str, Any] = {'state': state, 'count': len(rels)}
        return _render_resource_view(request, 'relationships_count.html', context)
    except Exception as e:
        logger.error(f"Error loading relationships by state count for {state}: {e}", exc_info=True)
        return _render_resource_view(request, 'relationships_count.html', {'state': state, 'count': 0, 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_relationships_by_lambda(request: HttpRequest, service_name: str) -> HttpResponse:
    """GET /docs/media-manager/relationships/by-lambda/<service_name>/"""
    try:
        relationships_service = get_relationships_service()
        result = relationships_service.list_relationships(limit=None, offset=0)
        rels = [x for x in (result.get("relationships") or []) if (x.get("lambda_service") or x.get("via_service")) == service_name]
        context: Dict[str, Any] = {'relationships': rels, 'total': len(rels), 'service_name': service_name, 'filters': {'lambda_service': service_name}}
        return _render_resource_view(request, 'relationships_by_lambda.html', context)
    except Exception as e:
        logger.error(f"Error loading relationships by lambda {service_name}: {e}", exc_info=True)
        return _render_resource_view(request, 'relationships_by_lambda.html', {'relationships': [], 'total': 0, 'service_name': service_name, 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_relationships_by_invocation_pattern(request: HttpRequest, pattern: str) -> HttpResponse:
    """GET /docs/media-manager/relationships/by-invocation-pattern/<pattern>/"""
    try:
        relationships_service = get_relationships_service()
        result = relationships_service.list_relationships(limit=None, offset=0)
        rels = [x for x in (result.get("relationships") or []) if pattern in str(x.get("via_hook", "")) or pattern in str(x.get("via_service", ""))]
        context: Dict[str, Any] = {'relationships': rels, 'total': len(rels), 'pattern': pattern, 'filters': {'pattern': pattern}}
        return _render_resource_view(request, 'relationships_by_invocation_pattern.html', context)
    except Exception as e:
        logger.error(f"Error loading relationships by invocation pattern {pattern}: {e}", exc_info=True)
        return _render_resource_view(request, 'relationships_by_invocation_pattern.html', {'relationships': [], 'total': 0, 'pattern': pattern, 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_relationships_by_postman_config(request: HttpRequest, config_id: str) -> HttpResponse:
    """GET /docs/media-manager/relationships/by-postman-config/<config_id>/"""
    try:
        relationships_service = get_relationships_service()
        result = relationships_service.list_relationships(limit=None, offset=0)
        rels = [x for x in (result.get("relationships") or []) if x.get("postman_config_id") == config_id]
        context: Dict[str, Any] = {'relationships': rels, 'total': len(rels), 'config_id': config_id, 'filters': {'postman_config_id': config_id}}
        return _render_resource_view(request, 'relationships_by_postman_config.html', context)
    except Exception as e:
        logger.error(f"Error loading relationships by postman config {config_id}: {e}", exc_info=True)
        return _render_resource_view(request, 'relationships_by_postman_config.html', {'relationships': [], 'total': 0, 'config_id': config_id, 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_relationships_performance_slow(request: HttpRequest) -> HttpResponse:
    """GET /docs/media-manager/relationships/performance/slow/"""
    try:
        relationships_service = get_relationships_service()
        result = relationships_service.list_relationships(limit=None, offset=0)
        rels = [x for x in (result.get("relationships") or []) if (x.get("performance") or {}).get("slow")]
        context: Dict[str, Any] = {'relationships': rels, 'total': len(rels), 'performance_type': 'slow'}
        return _render_resource_view(request, 'relationships_performance.html', context)
    except Exception as e:
        logger.error(f"Error loading slow performance relationships: {e}", exc_info=True)
        return _render_resource_view(request, 'relationships_performance.html', {'relationships': [], 'total': 0, 'performance_type': 'slow', 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_relationships_performance_errors(request: HttpRequest) -> HttpResponse:
    """GET /docs/media-manager/relationships/performance/errors/"""
    try:
        relationships_service = get_relationships_service()
        result = relationships_service.list_relationships(limit=None, offset=0)
        rels = [x for x in (result.get("relationships") or []) if (x.get("performance") or {}).get("errors")]
        context: Dict[str, Any] = {'relationships': rels, 'total': len(rels), 'performance_type': 'errors'}
        return _render_resource_view(request, 'relationships_performance.html', context)
    except Exception as e:
        logger.error(f"Error loading error performance relationships: {e}", exc_info=True)
        return _render_resource_view(request, 'relationships_performance.html', {'relationships': [], 'total': 0, 'performance_type': 'errors', 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_relationship_access_control(request: HttpRequest, relationship_id: str) -> HttpResponse:
    """GET /docs/media-manager/relationships/<relationship_id>/access-control/"""
    try:
        relationships_service = get_relationships_service()
        relationship = relationships_service.get_relationship(relationship_id)
        if not relationship:
            raise Http404(f"Relationship not found: {relationship_id}")
        context: Dict[str, Any] = {'relationship': relationship, 'relationship_id': relationship_id, 'access_control': relationship.get("access_control")}
        return _render_resource_view(request, 'relationship_access_control.html', context)
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error loading relationship access control for {relationship_id}: {e}", exc_info=True)
        return _render_resource_view(request, 'relationship_access_control.html', {'relationship_id': relationship_id, 'access_control': None, 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_relationship_data_flow(request: HttpRequest, relationship_id: str) -> HttpResponse:
    """GET /docs/media-manager/relationships/<relationship_id>/data-flow/"""
    try:
        relationships_service = get_relationships_service()
        relationship = relationships_service.get_relationship(relationship_id)
        if not relationship:
            raise Http404(f"Relationship not found: {relationship_id}")
        context: Dict[str, Any] = {'relationship': relationship, 'relationship_id': relationship_id, 'data_flow': relationship.get("data_flow")}
        return _render_resource_view(request, 'relationship_data_flow.html', context)
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error loading relationship data flow for {relationship_id}: {e}", exc_info=True)
        return _render_resource_view(request, 'relationship_data_flow.html', {'relationship_id': relationship_id, 'data_flow': None, 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_relationship_performance(request: HttpRequest, relationship_id: str) -> HttpResponse:
    """GET /docs/media-manager/relationships/<relationship_id>/performance/"""
    try:
        relationships_service = get_relationships_service()
        relationship = relationships_service.get_relationship(relationship_id)
        if not relationship:
            raise Http404(f"Relationship not found: {relationship_id}")
        context: Dict[str, Any] = {'relationship': relationship, 'relationship_id': relationship_id, 'performance': relationship.get("performance")}
        return _render_resource_view(request, 'relationship_performance.html', context)
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error loading relationship performance for {relationship_id}: {e}", exc_info=True)
        return _render_resource_view(request, 'relationship_performance.html', {'relationship_id': relationship_id, 'performance': None, 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_relationship_dependencies(request: HttpRequest, relationship_id: str) -> HttpResponse:
    """GET /docs/media-manager/relationships/<relationship_id>/dependencies/"""
    try:
        relationships_service = get_relationships_service()
        relationship = relationships_service.get_relationship(relationship_id)
        if not relationship:
            raise Http404(f"Relationship not found: {relationship_id}")
        context: Dict[str, Any] = {'relationship': relationship, 'relationship_id': relationship_id, 'dependencies': relationship.get("dependencies", [])}
        return _render_resource_view(request, 'relationship_dependencies.html', context)
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error loading relationship dependencies for {relationship_id}: {e}", exc_info=True)
        return _render_resource_view(request, 'relationship_dependencies.html', {'relationship_id': relationship_id, 'dependencies': [], 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_relationship_postman(request: HttpRequest, relationship_id: str) -> HttpResponse:
    """GET /docs/media-manager/relationships/<relationship_id>/postman/"""
    try:
        relationships_service = get_relationships_service()
        relationship = relationships_service.get_relationship(relationship_id)
        if not relationship:
            raise Http404(f"Relationship not found: {relationship_id}")
        context: Dict[str, Any] = {'relationship': relationship, 'relationship_id': relationship_id, 'postman': relationship.get("postman")}
        return _render_resource_view(request, 'relationship_postman.html', context)
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error loading relationship postman for {relationship_id}: {e}", exc_info=True)
        return _render_resource_view(request, 'relationship_postman.html', {'relationship_id': relationship_id, 'postman': None, 'error': str(e)}, error_message=str(e))


# ============================================================================
# Postman API Views - Enhanced routes (mirroring /api/v1/postman/)
# ============================================================================

@login_required
def media_manager_postman_statistics(request: HttpRequest) -> HttpResponse:
    """GET /docs/media-manager/postman/statistics/"""
    try:
        postman_service = get_postman_service()
        stats = postman_service.get_statistics()
        context: Dict[str, Any] = {'statistics': stats}
        return _render_resource_view(request, 'postman_statistics.html', context)
    except Exception as e:
        logger.error(f"Error loading postman statistics: {e}", exc_info=True)
        return _render_resource_view(request, 'postman_statistics.html', {'statistics': {}, 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_postman_format(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Postman format examples view.
    
    GET /docs/postman/format/
    Mirrors: GET /api/v1/postman/format/
    """
    try:
        from apps.documentation.api.v1.postman_views import postman_format as api_postman_format
        import json
        
        # Call the API function to get format data
        json_response = api_postman_format(request)
        format_data = json.loads(json_response.content)
        
        # Format examples for display
        examples = None
        if 'examples' in format_data:
            examples = json.dumps(format_data['examples'], indent=2)
        
        # Note: postman_format doesn't have analyse_payload_example like others
        analyse_payload_example = None
        if 'analyse_payload_example' in format_data:
            analyse_payload_example = json.dumps(format_data['analyse_payload_example'], indent=2)
        
        context: Dict[str, Any] = {
            'format_data': format_data,
            'examples': examples,
            'analyse_payload_example': analyse_payload_example,
        }
        
        return _render_resource_view(request, 'postman_format.html', context)
    
    except Exception as e:
        logger.error(f"Error loading postman format: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'postman_format.html',
            {'format_data': {}, 'examples': None, 'analyse_payload_example': None, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_postman_by_state(request: HttpRequest, state: str) -> HttpResponse:
    """GET /docs/media-manager/postman/by-state/<state>/"""
    try:
        postman_service = get_postman_service()
        result = postman_service.list_by_state(state)
        context: Dict[str, Any] = {
            'configurations': result.get("configurations", []),
            'total': result.get("total", 0),
            'state': state,
            'filters': {'state': state},
        }
        return _render_resource_view(request, 'postman_by_state.html', context)
    except Exception as e:
        logger.error(f"Error loading postman by state {state}: {e}", exc_info=True)
        return _render_resource_view(request, 'postman_by_state.html', {'configurations': [], 'total': 0, 'state': state, 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_postman_by_state_count(request: HttpRequest, state: str) -> HttpResponse:
    """GET /docs/media-manager/postman/by-state/<state>/count/"""
    try:
        postman_service = get_postman_service()
        count = postman_service.count_by_state(state)
        context: Dict[str, Any] = {'state': state, 'count': count}
        return _render_resource_view(request, 'postman_count.html', context)
    except Exception as e:
        logger.error(f"Error loading postman by state count for {state}: {e}", exc_info=True)
        return _render_resource_view(request, 'postman_count.html', {'state': state, 'count': 0, 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_postman_collection(request: HttpRequest, config_id: str) -> HttpResponse:
    """GET /docs/media-manager/postman/<config_id>/collection/"""
    try:
        postman_service = get_postman_service()
        configuration = postman_service.get_configuration(config_id)
        if not configuration:
            raise Http404(f"Postman configuration not found: {config_id}")
        collection = postman_service.get_collection(config_id)
        context: Dict[str, Any] = {'configuration': configuration, 'config_id': config_id, 'collection': collection}
        return _render_resource_view(request, 'postman_collection.html', context)
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error loading postman collection for {config_id}: {e}", exc_info=True)
        return _render_resource_view(request, 'postman_collection.html', {'config_id': config_id, 'collection': None, 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_postman_environments(request: HttpRequest, config_id: str) -> HttpResponse:
    """GET /docs/media-manager/postman/<config_id>/environments/"""
    try:
        postman_service = get_postman_service()
        configuration = postman_service.get_configuration(config_id)
        if not configuration:
            raise Http404(f"Postman configuration not found: {config_id}")
        environments = postman_service.get_environments(config_id)
        context: Dict[str, Any] = {'configuration': configuration, 'config_id': config_id, 'environments': environments or []}
        return _render_resource_view(request, 'postman_environments.html', context)
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error loading postman environments for {config_id}: {e}", exc_info=True)
        return _render_resource_view(request, 'postman_environments.html', {'config_id': config_id, 'environments': [], 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_postman_environment(request: HttpRequest, config_id: str, env_name: str) -> HttpResponse:
    """GET /docs/media-manager/postman/<config_id>/environments/<env_name>/"""
    try:
        postman_service = get_postman_service()
        configuration = postman_service.get_configuration(config_id)
        if not configuration:
            raise Http404(f"Postman configuration not found: {config_id}")
        environment = postman_service.get_environment(config_id, env_name)
        if not environment:
            raise Http404(f"Environment '{env_name}' not found")
        context: Dict[str, Any] = {'configuration': configuration, 'config_id': config_id, 'env_name': env_name, 'environment': environment}
        return _render_resource_view(request, 'postman_environment.html', context)
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error loading postman environment {env_name} for {config_id}: {e}", exc_info=True)
        return _render_resource_view(request, 'postman_environment.html', {'config_id': config_id, 'env_name': env_name, 'environment': None, 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_postman_mappings(request: HttpRequest, config_id: str) -> HttpResponse:
    """GET /docs/media-manager/postman/<config_id>/mappings/"""
    try:
        postman_service = get_postman_service()
        configuration = postman_service.get_configuration(config_id)
        if not configuration:
            raise Http404(f"Postman configuration not found: {config_id}")
        mappings = postman_service.get_endpoint_mappings(config_id)
        context: Dict[str, Any] = {'configuration': configuration, 'config_id': config_id, 'mappings': mappings or []}
        return _render_resource_view(request, 'postman_mappings.html', context)
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error loading postman mappings for {config_id}: {e}", exc_info=True)
        return _render_resource_view(request, 'postman_mappings.html', {'config_id': config_id, 'mappings': [], 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_postman_mapping(request: HttpRequest, config_id: str, mapping_id: str) -> HttpResponse:
    """GET /docs/media-manager/postman/<config_id>/mappings/<mapping_id>/"""
    try:
        postman_service = get_postman_service()
        configuration = postman_service.get_configuration(config_id)
        if not configuration:
            raise Http404(f"Postman configuration not found: {config_id}")
        mappings = postman_service.get_endpoint_mappings(config_id)
        mapping = next((x for x in (mappings or []) if str(x.get("id")) == str(mapping_id) or x.get("mapping_id") == mapping_id), None)
        if not mapping:
            raise Http404(f"Mapping '{mapping_id}' not found")
        context: Dict[str, Any] = {'configuration': configuration, 'config_id': config_id, 'mapping_id': mapping_id, 'mapping': mapping}
        return _render_resource_view(request, 'postman_mapping.html', context)
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error loading postman mapping {mapping_id} for {config_id}: {e}", exc_info=True)
        return _render_resource_view(request, 'postman_mapping.html', {'config_id': config_id, 'mapping_id': mapping_id, 'mapping': None, 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_postman_test_suites(request: HttpRequest, config_id: str) -> HttpResponse:
    """GET /docs/media-manager/postman/<config_id>/test-suites/"""
    try:
        postman_service = get_postman_service()
        configuration = postman_service.get_configuration(config_id)
        if not configuration:
            raise Http404(f"Postman configuration not found: {config_id}")
        test_suites = postman_service.get_test_suites(config_id)
        context: Dict[str, Any] = {'configuration': configuration, 'config_id': config_id, 'test_suites': test_suites or []}
        return _render_resource_view(request, 'postman_test_suites.html', context)
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error loading postman test suites for {config_id}: {e}", exc_info=True)
        return _render_resource_view(request, 'postman_test_suites.html', {'config_id': config_id, 'test_suites': [], 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_postman_test_suite(request: HttpRequest, config_id: str, suite_id: str) -> HttpResponse:
    """GET /docs/media-manager/postman/<config_id>/test-suites/<suite_id>/"""
    try:
        postman_service = get_postman_service()
        configuration = postman_service.get_configuration(config_id)
        if not configuration:
            raise Http404(f"Postman configuration not found: {config_id}")
        suite = postman_service.get_test_suite(config_id, suite_id)
        if not suite:
            raise Http404(f"Test suite '{suite_id}' not found")
        context: Dict[str, Any] = {'configuration': configuration, 'config_id': config_id, 'suite_id': suite_id, 'suite': suite}
        return _render_resource_view(request, 'postman_test_suite.html', context)
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error loading postman test suite {suite_id} for {config_id}: {e}", exc_info=True)
        return _render_resource_view(request, 'postman_test_suite.html', {'config_id': config_id, 'suite_id': suite_id, 'suite': None, 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_postman_access_control(request: HttpRequest, config_id: str) -> HttpResponse:
    """GET /docs/media-manager/postman/<config_id>/access-control/"""
    try:
        postman_service = get_postman_service()
        configuration = postman_service.get_configuration(config_id)
        if not configuration:
            raise Http404(f"Postman configuration not found: {config_id}")
        access_control = postman_service.get_access_control(config_id)
        context: Dict[str, Any] = {'configuration': configuration, 'config_id': config_id, 'access_control': access_control}
        return _render_resource_view(request, 'postman_access_control.html', context)
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error loading postman access control for {config_id}: {e}", exc_info=True)
        return _render_resource_view(request, 'postman_access_control.html', {'config_id': config_id, 'access_control': None, 'error': str(e)}, error_message=str(e))


# ============================================================================
# Health & Index API Views - Enhanced routes (mirroring /api/v1/health/ and /api/v1/index/)
# ============================================================================

@login_required
def media_manager_health_database(request: HttpRequest) -> HttpResponse:
    """GET /docs/media-manager/health/database/"""
    try:
        from apps.documentation.utils.health_checks import check_database_health
        db_health = check_database_health()
        context: Dict[str, Any] = {'health_type': 'database', 'health_data': db_health}
        return _render_resource_view(request, 'health_detail.html', context)
    except Exception as e:
        logger.error(f"Error loading database health: {e}", exc_info=True)
        return _render_resource_view(request, 'health_detail.html', {'health_type': 'database', 'health_data': {}, 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_health_cache(request: HttpRequest) -> HttpResponse:
    """GET /docs/media-manager/health/cache/"""
    try:
        from apps.documentation.utils.health_checks import check_cache_health
        cache_health = check_cache_health()
        context: Dict[str, Any] = {'health_type': 'cache', 'health_data': cache_health}
        return _render_resource_view(request, 'health_detail.html', context)
    except Exception as e:
        logger.error(f"Error loading cache health: {e}", exc_info=True)
        return _render_resource_view(request, 'health_detail.html', {'health_type': 'cache', 'health_data': {}, 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_health_storage(request: HttpRequest) -> HttpResponse:
    """GET /docs/media-manager/health/storage/"""
    try:
        from apps.documentation.utils.health_checks import check_storage_health
        storage_health = check_storage_health()
        context: Dict[str, Any] = {'health_type': 'storage', 'health_data': storage_health}
        return _render_resource_view(request, 'health_detail.html', context)
    except Exception as e:
        logger.error(f"Error loading storage health: {e}", exc_info=True)
        return _render_resource_view(request, 'health_detail.html', {'health_type': 'storage', 'health_data': {}, 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_index_pages(request: HttpRequest) -> HttpResponse:
    """GET /docs/media-manager/index/pages/"""
    try:
        from apps.documentation.services import get_shared_s3_index_manager
        index_manager = get_shared_s3_index_manager()
        index_data = index_manager.read_index("pages")
        context: Dict[str, Any] = {'index_type': 'pages', 'index_data': index_data}
        return _render_resource_view(request, 'index_detail.html', context)
    except Exception as e:
        logger.error(f"Error loading pages index: {e}", exc_info=True)
        return _render_resource_view(request, 'index_detail.html', {'index_type': 'pages', 'index_data': {}, 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_index_endpoints(request: HttpRequest) -> HttpResponse:
    """GET /docs/media-manager/index/endpoints/"""
    try:
        from apps.documentation.services import get_shared_s3_index_manager
        index_manager = get_shared_s3_index_manager()
        index_data = index_manager.read_index("endpoints")
        context: Dict[str, Any] = {'index_type': 'endpoints', 'index_data': index_data}
        return _render_resource_view(request, 'index_detail.html', context)
    except Exception as e:
        logger.error(f"Error loading endpoints index: {e}", exc_info=True)
        return _render_resource_view(request, 'index_detail.html', {'index_type': 'endpoints', 'index_data': {}, 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_index_relationships(request: HttpRequest) -> HttpResponse:
    """GET /docs/media-manager/index/relationships/"""
    try:
        from apps.documentation.services import get_shared_s3_index_manager
        index_manager = get_shared_s3_index_manager()
        index_data = index_manager.read_index("relationships")
        context: Dict[str, Any] = {'index_type': 'relationships', 'index_data': index_data}
        return _render_resource_view(request, 'index_detail.html', context)
    except Exception as e:
        logger.error(f"Error loading relationships index: {e}", exc_info=True)
        return _render_resource_view(request, 'index_detail.html', {'index_type': 'relationships', 'index_data': {}, 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_index_postman(request: HttpRequest) -> HttpResponse:
    """GET /docs/media-manager/index/postman/"""
    try:
        from apps.documentation.services import get_shared_s3_index_manager
        index_manager = get_shared_s3_index_manager()
        index_data = index_manager.read_index("postman")
        context: Dict[str, Any] = {'index_type': 'postman', 'index_data': index_data}
        return _render_resource_view(request, 'index_detail.html', context)
    except Exception as e:
        logger.error(f"Error loading postman index: {e}", exc_info=True)
        return _render_resource_view(request, 'index_detail.html', {'index_type': 'postman', 'index_data': {}, 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_index_pages_validate(request: HttpRequest) -> HttpResponse:
    """GET /docs/media-manager/index/pages/validate/"""
    try:
        from apps.documentation.services import get_shared_s3_index_manager
        index_manager = get_shared_s3_index_manager()
        result = index_manager.validate_index("pages")
        context: Dict[str, Any] = {'index_type': 'pages', 'validation_result': result}
        return _render_resource_view(request, 'index_validate.html', context)
    except Exception as e:
        logger.error(f"Error validating pages index: {e}", exc_info=True)
        return _render_resource_view(request, 'index_validate.html', {'index_type': 'pages', 'validation_result': {'valid': False, 'error': str(e)}, 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_index_endpoints_validate(request: HttpRequest) -> HttpResponse:
    """GET /docs/media-manager/index/endpoints/validate/"""
    try:
        from apps.documentation.services import get_shared_s3_index_manager
        index_manager = get_shared_s3_index_manager()
        result = index_manager.validate_index("endpoints")
        context: Dict[str, Any] = {'index_type': 'endpoints', 'validation_result': result}
        return _render_resource_view(request, 'index_validate.html', context)
    except Exception as e:
        logger.error(f"Error validating endpoints index: {e}", exc_info=True)
        return _render_resource_view(request, 'index_validate.html', {'index_type': 'endpoints', 'validation_result': {'valid': False, 'error': str(e)}, 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_index_relationships_validate(request: HttpRequest) -> HttpResponse:
    """GET /docs/media-manager/index/relationships/validate/"""
    try:
        from apps.documentation.services import get_shared_s3_index_manager
        index_manager = get_shared_s3_index_manager()
        result = index_manager.validate_index("relationships")
        context: Dict[str, Any] = {'index_type': 'relationships', 'validation_result': result}
        return _render_resource_view(request, 'index_validate.html', context)
    except Exception as e:
        logger.error(f"Error validating relationships index: {e}", exc_info=True)
        return _render_resource_view(request, 'index_validate.html', {'index_type': 'relationships', 'validation_result': {'valid': False, 'error': str(e)}, 'error': str(e)}, error_message=str(e))


@login_required
def media_manager_index_postman_validate(request: HttpRequest) -> HttpResponse:
    """GET /docs/media-manager/index/postman/validate/"""
    try:
        from apps.documentation.services import get_shared_s3_index_manager
        index_manager = get_shared_s3_index_manager()
        result = index_manager.validate_index("postman")
        context: Dict[str, Any] = {'index_type': 'postman', 'validation_result': result}
        return _render_resource_view(request, 'index_validate.html', context)
    except Exception as e:
        logger.error(f"Error validating postman index: {e}", exc_info=True)
        return _render_resource_view(request, 'index_validate.html', {'index_type': 'postman', 'validation_result': {'valid': False, 'error': str(e)}, 'error': str(e)}, error_message=str(e))


# ============================================================================
# Service Info & Docs Meta Views - Root and endpoint stats
# ============================================================================

@login_required
def media_manager_service_info(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Service info view.
    
    GET /docs/media-manager/service-info/
    Mirrors: GET /api/v1/
    """
    try:
        from apps.documentation.api.v1.health import service_info
        from django.http import JsonResponse
        
        # Get service info data
        json_response = service_info(request)
        import json
        data = json.loads(json_response.content)
        
        context: Dict[str, Any] = {
            'service_info': data.get('data', {}),
            'success': data.get('success', True),
        }
        
        return _render_resource_view(request, 'service_info.html', context)
    
    except Exception as e:
        logger.error(f"Error loading service info: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'service_info.html',
            {'service_info': {}, 'success': False, 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_docs_endpoint_stats(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Docs endpoint stats view.
    
    GET /docs/media-manager/docs/endpoint-stats/
    Mirrors: GET /api/v1/docs/endpoint-stats/
    """
    try:
        from apps.documentation.api.v1.docs_meta import endpoint_stats
        from django.http import JsonResponse
        
        # Get endpoint stats data
        json_response = endpoint_stats(request)
        import json
        data = json.loads(json_response.content)
        
        context: Dict[str, Any] = {
            'endpoint_stats': data.get('data', {}),
            'success': data.get('success', True),
        }
        
        return _render_resource_view(request, 'docs_endpoint_stats.html', context)
    
    except Exception as e:
        logger.error(f"Error loading endpoint stats: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'docs_endpoint_stats.html',
            {'endpoint_stats': {}, 'success': False, 'error': str(e)},
            error_message=str(e)
        )


# ============================================================================
# Format/Example Views - JSON examples for API documentation
# ============================================================================

# ============================================================================
# Dashboard API Views - AJAX endpoints with UI views
# ============================================================================

@login_required
def media_manager_dashboard_pages(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Dashboard pages API view.
    
    GET /docs/media-manager/dashboard/pages/
    Mirrors: GET /api/v1/dashboard/pages/
    """
    try:
        from apps.documentation.api.v1.core import dashboard_pages
        from django.http import JsonResponse
        
        json_response = dashboard_pages(request)
        import json
        data = json.loads(json_response.content)
        
        context: Dict[str, Any] = {
            'resource': 'pages',
            'dashboard_data': data,
            'items': data.get('items', []),
            'pagination': data.get('pagination', {}),
        }
        
        return _render_resource_view(request, 'dashboard_pages.html', context)
    
    except Exception as e:
        logger.error(f"Error loading dashboard pages: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'dashboard_pages.html',
            {'resource': 'pages', 'dashboard_data': {}, 'items': [], 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_dashboard_endpoints(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Dashboard endpoints API view.
    
    GET /docs/media-manager/dashboard/endpoints/
    Mirrors: GET /api/v1/dashboard/endpoints/
    """
    try:
        from apps.documentation.api.v1.core import dashboard_endpoints
        from django.http import JsonResponse
        
        json_response = dashboard_endpoints(request)
        import json
        data = json.loads(json_response.content)
        
        context: Dict[str, Any] = {
            'resource': 'endpoints',
            'dashboard_data': data,
            'items': data.get('items', []),
            'pagination': data.get('pagination', {}),
        }
        
        return _render_resource_view(request, 'dashboard_endpoints.html', context)
    
    except Exception as e:
        logger.error(f"Error loading dashboard endpoints: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'dashboard_endpoints.html',
            {'resource': 'endpoints', 'dashboard_data': {}, 'items': [], 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_dashboard_relationships(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Dashboard relationships API view.
    
    GET /docs/media-manager/dashboard/relationships/
    Mirrors: GET /api/v1/dashboard/relationships/
    """
    try:
        from apps.documentation.api.v1.core import dashboard_relationships
        from django.http import JsonResponse
        
        json_response = dashboard_relationships(request)
        import json
        data = json.loads(json_response.content)
        
        context: Dict[str, Any] = {
            'resource': 'relationships',
            'dashboard_data': data,
            'items': data.get('items', []),
            'pagination': data.get('pagination', {}),
        }
        
        return _render_resource_view(request, 'dashboard_relationships.html', context)
    
    except Exception as e:
        logger.error(f"Error loading dashboard relationships: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'dashboard_relationships.html',
            {'resource': 'relationships', 'dashboard_data': {}, 'items': [], 'error': str(e)},
            error_message=str(e)
        )


@login_required
def media_manager_dashboard_postman(request: HttpRequest) -> HttpResponse:
    """
    Media Manager Dashboard - Dashboard postman API view.
    
    GET /docs/media-manager/dashboard/postman/
    Mirrors: GET /api/v1/dashboard/postman/
    """
    try:
        from apps.documentation.api.v1.core import dashboard_postman
        from django.http import JsonResponse
        
        json_response = dashboard_postman(request)
        import json
        data = json.loads(json_response.content)
        
        context: Dict[str, Any] = {
            'resource': 'postman',
            'dashboard_data': data,
            'items': data.get('items', []),
            'pagination': data.get('pagination', {}),
        }
        
        return _render_resource_view(request, 'dashboard_postman.html', context)
    
    except Exception as e:
        logger.error(f"Error loading dashboard postman: {e}", exc_info=True)
        return _render_resource_view(
            request,
            'dashboard_postman.html',
            {'resource': 'postman', 'dashboard_data': {}, 'items': [], 'error': str(e)},
            error_message=str(e)
        )
