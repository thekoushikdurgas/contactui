"""Documentation Dashboard Views."""

from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Set, Tuple

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.safestring import mark_safe

from apps.documentation.services import (
    pages_service,
    endpoints_service,
    relationships_service,
    postman_service,
)
from apps.documentation.repositories.local_json_storage import LocalJSONStorage
from apps.documentation.services.media_manager_service import MediaManagerService
from apps.documentation.utils.api_responses import (
    error_response,
    server_error_response,
    success_response,
)
from apps.core.utils.redis_cache import (
    cache_manager,
    CACHE_PREFIX_STATISTICS,
    MEDIUM_TTL,
    LONG_TTL,
)

logger = logging.getLogger(__name__)
GRAPH_DATA_CACHE_KEY = "dashboard:graph_data"
GRAPH_DATA_CACHE_TTL = 600  # 10 minutes
STATISTICS_CACHE_KEY = "dashboard:statistics"
STATISTICS_CACHE_TTL = 300  # 5 minutes
VALID_TABS = frozenset({"pages", "endpoints", "relationships", "postman", "graph"})
VALID_VIEW_MODES = frozenset({"list", "files", "sync"})


# Removed custom helpers - now using api_responses utilities
# _format_api_success, _format_api_error, _json_success, _json_error removed


def build_graph_data(
    pages_svc: Any,
    endpoints_svc: Any,
    relationships_svc: Any,
) -> Dict[str, Any]:
    """
    Build graph structure from pages, endpoints, and relationships. Cached 10 min.
    
    Args:
        pages_svc: Pages service instance
        endpoints_svc: Endpoints service instance
        relationships_svc: Relationships service instance
        
    Returns:
        Dict with 'nodes', 'edges', and 'statistics'
    """
    cached = cache_manager.get(GRAPH_DATA_CACHE_KEY, namespace="dashboard")
    if cached is not None:
        return cached

    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    node_ids: Set[str] = set()
    fallback: Dict[str, Any] = {"nodes": [], "edges": [], "statistics": {}}

    try:
        # Parallelize service calls for better performance
        # Expected improvement: 3x faster (sequential → parallel)
        pages_result = None
        endpoints_result = None
        relationships_result = None
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all three service calls concurrently
            pages_future = executor.submit(pages_svc.list_pages, limit=1000)
            endpoints_future = executor.submit(endpoints_svc.list_endpoints, limit=1000)
            relationships_future = executor.submit(relationships_svc.list_relationships, limit=1000)
            
            # Wait for all results with error handling
            try:
                pages_result = pages_future.result(timeout=30)
            except Exception as e:
                logger.warning(f"Error fetching pages for graph: {e}")
                pages_result = {"pages": []}
            
            try:
                endpoints_result = endpoints_future.result(timeout=30)
            except Exception as e:
                logger.warning(f"Error fetching endpoints for graph: {e}")
                endpoints_result = {"endpoints": []}
            
            try:
                relationships_result = relationships_future.result(timeout=30)
            except Exception as e:
                logger.warning(f"Error fetching relationships for graph: {e}")
                relationships_result = {"relationships": []}
        
        pages = pages_result.get("pages", []) if pages_result else []
        endpoints = endpoints_result.get("endpoints", []) if endpoints_result else []
        relationships = relationships_result.get("relationships", []) if relationships_result else []

        # Optimize node processing with list comprehension where possible
        # Pre-compile metadata access patterns for better performance
        for page in pages:
            try:
                page_id = page.get("page_id") or page.get("_id")
                if not page_id or page_id in node_ids:
                    continue
                
                # Safely access nested metadata (optimized access pattern)
                metadata = page.get("metadata") or {}
                content_sections = metadata.get("content_sections") or {}
                title = content_sections.get("title") or page_id
                route = metadata.get("route") or page.get("route")
                status = metadata.get("status")
                
                node_id = f"page_{page_id}"
                nodes.append({
                    "id": node_id,
                    "label": title,
                    "type": "page",
                    "data": {
                        "page_id": page_id,
                        "route": route,
                        "page_type": page.get("page_type"),
                        "status": status,
                    },
                })
                node_ids.add(node_id)
            except Exception as e:
                logger.warning(f"Error processing page node: {e}")
                continue

        # Optimize endpoint node processing
        for endpoint in endpoints:
            try:
                endpoint_id = endpoint.get("endpoint_id") or endpoint.get("_id")
                if not endpoint_id:
                    continue
                
                node_id = f"endpoint_{endpoint_id}"
                if node_id in node_ids:
                    continue
                
                nodes.append({
                    "id": node_id,
                    "label": endpoint_id,
                    "type": "endpoint",
                    "data": {
                        "endpoint_id": endpoint_id,
                        "endpoint_path": endpoint.get("endpoint_path"),
                        "method": endpoint.get("method", "QUERY"),
                        "api_version": endpoint.get("api_version"),
                    },
                })
                node_ids.add(node_id)
            except Exception as e:
                logger.warning(f"Error processing endpoint node: {e}")
                continue

        # Optimize edge processing with set operations for faster lookups
        for rel in relationships:
            try:
                pid = rel.get("page_id") or rel.get("page_path")
                eid = rel.get("endpoint_id") or rel.get("endpoint_path")
                
                if not pid or not eid:
                    continue
                
                source_id = f"page_{pid}"
                target_id = f"endpoint_{eid}"
                
                # Use set membership check (O(1)) instead of list check (O(n))
                if source_id in node_ids and target_id in node_ids:
                    edges.append({
                        "id": rel.get("relationship_id", f"{source_id}_{target_id}"),
                        "source": source_id,
                        "target": target_id,
                        "type": rel.get("usage_type", "primary"),
                        "label": rel.get("usage_type", "primary"),
                        "data": {
                            "relationship_id": rel.get("relationship_id"),
                            "usage_type": rel.get("usage_type"),
                            "usage_context": rel.get("usage_context"),
                            "method": rel.get("method"),
                        },
                    })
            except Exception as e:
                logger.warning(f"Error processing relationship edge: {e}")
                continue

        # Optimize statistics calculation using pre-computed values
        pages_count = sum(1 for n in nodes if n.get("type") == "page")
        endpoints_count = sum(1 for n in nodes if n.get("type") == "endpoint")
        
        stats = {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "pages_count": pages_count,
            "endpoints_count": endpoints_count,
            "relationships_count": len(edges),
        }
        result: Dict[str, Any] = {"nodes": nodes, "edges": edges, "statistics": stats}
        
        # Cache using RedisCacheManager with namespace and dynamic TTL (Task 2.2.2)
        cache_manager.set(
            GRAPH_DATA_CACHE_KEY,
            result,
            timeout=GRAPH_DATA_CACHE_TTL,
            namespace="dashboard",
            data_type="graph",  # Use graph data type for appropriate TTL
        )
        logger.debug("Graph data cached successfully")
        return result
    except Exception as e:
        logger.error("Error building graph data: %s", e, exc_info=True)
        # Return fallback instead of raising exception
        return fallback


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


@login_required
def documentation_dashboard(request: HttpRequest):
    """
    Unified Media Manager Dashboard - combines documentation dashboard and media manager.
    
    GET /docs/
    Query params: 
    - tab (pages|endpoints|relationships|postman|graph)
    - view (list|files|sync) - view mode: list view, file browser, or sync status
    - graph_tab
    """
    raw_tab = request.GET.get("tab", "pages")
    active_tab = _validate_tab(raw_tab)
    if raw_tab != active_tab:
        logger.debug("Invalid tab %r, defaulting to pages", raw_tab)
    
    # Get view mode (list, files, sync)
    raw_view = request.GET.get("view", "list")
    view_mode = _validate_view_mode(raw_view)
    if raw_view != view_mode:
        logger.debug("Invalid view mode %r, defaulting to list", raw_view)

    # List view pagination (used for initial SSR data consistency)
    # NOTE: the dashboard APIs already use page/page_size; this keeps initial_data aligned.
    raw_page = request.GET.get("page", "1")
    raw_page_size = request.GET.get("page_size", "20")
    try:
        page = max(int(raw_page), 1)
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = int(raw_page_size)
    except (TypeError, ValueError):
        page_size = 20
    if page_size <= 0:
        page_size = 20
    # Keep SSR payload reasonably small even if user passes huge page_size
    page_size = min(page_size, 200)
    offset = (page - 1) * page_size

    from apps.documentation.services import get_shared_local_storage
    local_storage = get_shared_local_storage()
    health_status: Dict[str, Any] = {
        "local_files": {
            "enabled": True,
            "status": "ok",
            "pages_count": 0,
            "endpoints_count": 0,
            "relationships_count": 0,
            "postman_count": 0,
        },
        "s3": {"enabled": False, "status": "unknown"},
        "graphql": {"enabled": False, "status": "unknown"},
        "lambda": {"enabled": False, "status": "unknown"},
    }

    try:
        pages_index = local_storage.get_index("pages")
        endpoints_index = local_storage.get_index("endpoints")
        relationships_index = local_storage.get_index("relationships")

        health_status["local_files"]["pages_count"] = pages_index.get("total", 0)
        health_status["local_files"]["endpoints_count"] = endpoints_index.get("total", 0)
        health_status["local_files"]["relationships_count"] = relationships_index.get("total", 0)

        try:
            postman_index = local_storage.get_index("postman")
            health_status["local_files"]["postman_count"] = postman_index.get("total", 0)
        except Exception:
            try:
                postman_result = postman_service.list_configurations()
                health_status["local_files"]["postman_count"] = postman_result.get("total", 0)
            except Exception:
                health_status["local_files"]["postman_count"] = 0
    except Exception as e:
        logger.error("Error loading local file stats: %s", e, exc_info=True)
        health_status["local_files"]["status"] = "error"

    overview_stats: Dict[str, Any] = {
        "total_pages": health_status["local_files"]["pages_count"],
        "total_endpoints": health_status["local_files"]["endpoints_count"],
        "total_relationships": health_status["local_files"]["relationships_count"],
        "total_postman": health_status["local_files"]["postman_count"],
        "pages_by_type": {},
        "endpoints_by_method": {},
    }

    initial_data: Dict[str, Any] = {}
    try:
        # For SSR, only load list data when in list view; files/sync are JS-driven.
        if active_tab == "graph":
            graph_data = build_graph_data(pages_service, endpoints_service, relationships_service)
            initial_data = {
                "graph": graph_data,
                "nodes_count": len(graph_data.get("nodes", [])),
                "edges_count": len(graph_data.get("edges", [])),
            }
        elif view_mode == "list":
            if active_tab == "pages":
                result = pages_service.list_pages(limit=page_size, offset=offset)
                initial_data = {
                    "pages": result.get("pages", []),
                    "total": result.get("total", 0),
                    "source": result.get("source", "local"),
                }
            elif active_tab == "endpoints":
                result = endpoints_service.list_endpoints(limit=page_size, offset=offset)
                initial_data = {
                    "endpoints": result.get("endpoints", []),
                    "total": result.get("total", 0),
                    "source": result.get("source", "local"),
                }
            elif active_tab == "relationships":
                result = relationships_service.list_relationships(limit=page_size, offset=offset)
                initial_data = {
                    "relationships": result.get("relationships", []),
                    "total": result.get("total", 0),
                    "source": result.get("source", "local"),
                }
            elif active_tab == "postman":
                result = postman_service.list_configurations(limit=page_size, offset=offset)
                configs = result.get("configurations", [])
                initial_data = {
                    "postman": configs,
                    "total": result.get("total", len(configs)),
                    "source": result.get("source", "lambda"),
                }
    except Exception as e:
        logger.error("Error loading initial data for tab %s: %s", active_tab, e, exc_info=True)
        initial_data = {
            "pages": [],
            "endpoints": [],
            "relationships": [],
            "postman": [],
            "graph": {"nodes": [], "edges": []},
            "total": 0,
        }

    graph_subtab = request.GET.get("graph_tab", "overview") or "overview"
    
    # Media Manager data (for file browser and sync views)
    sync_summary: Dict[str, Any] = {}
    file_counts: Dict[str, int] = {}
    resource_types = ["pages", "endpoints", "relationships", "postman", "n8n", "project"]
    
    try:
        media_service = MediaManagerService()
        sync_summary = media_service.get_sync_summary()
        file_counts = {
            rt: sync_summary.get("by_type", {}).get(rt, {}).get("total", 0) 
            for rt in resource_types
        }
    except Exception as e:
        logger.warning("Error loading media manager data: %s", e, exc_info=True)
        sync_summary = {}
        file_counts = {rt: 0 for rt in resource_types}
    
    context: Dict[str, Any] = {
        "active_tab": active_tab,
        "view_mode": view_mode,  # New: view mode (list, files, sync)
        "current_page": page,
        "page_size": page_size,
        "graph_subtab": graph_subtab,
        "health_status": health_status,
        "overview_stats": overview_stats,
        "initial_data": mark_safe(json.dumps(initial_data)),
        # Media Manager data
        "sync_summary": sync_summary,
        "file_counts": file_counts,
        "resource_types": resource_types,
    }
    return render(request, "documentation/dashboard.html", context)


@login_required
@require_http_methods(["GET"])
def health_status_api(request: HttpRequest) -> JsonResponse:
    """
    API endpoint for comprehensive health status.
    
    GET /docs/api/health/
    Returns: { success, data: { status, components: { application, database, cache, storage, external_api } } }
    """
    try:
        from apps.documentation.utils.health_checks import get_comprehensive_health_status
        
        health_status = get_comprehensive_health_status()
        return success_response(
            data=health_status,
            message="Health status retrieved successfully"
        ).to_json_response()
    except Exception as e:
        logger.error("Error loading health status: %s", e, exc_info=True)
        return error_response(
            message="Failed to retrieve health status",
            errors=[str(e)],
            status_code=500
        ).to_json_response()


@login_required
@require_http_methods(["GET"])
def dashboard_stats_api(request: HttpRequest) -> JsonResponse:
    """
    API endpoint for dashboard statistics.
    
    GET /docs/api/stats/
    Returns: { success, data: { total_pages, total_endpoints, ... } }
    
    Statistics are cached for 5 minutes using RedisCacheManager.
    """
    # Try to get from cache first
    cached_stats = cache_manager.get(
        STATISTICS_CACHE_KEY,
        namespace=CACHE_PREFIX_STATISTICS,
    )
    if cached_stats is not None:
        logger.debug("Statistics cache hit")
        return success_response(
            data=cached_stats,
            message="Dashboard statistics retrieved successfully (cached)"
        ).to_json_response()
    
    from apps.documentation.services import get_shared_local_storage
    local_storage = get_shared_local_storage()
    stats: Dict[str, Any] = {
        "total_pages": 0,
        "total_endpoints": 0,
        "total_relationships": 0,
        "total_postman": 0,
        "pages_by_type": {},
        "endpoints_by_method": {},
    }

    try:
        pages_index = local_storage.get_index("pages")
        endpoints_index = local_storage.get_index("endpoints")
        relationships_index = local_storage.get_index("relationships")

        stats["total_pages"] = pages_index.get("total", 0)
        stats["total_endpoints"] = endpoints_index.get("total", 0)
        stats["total_relationships"] = relationships_index.get("total", 0)

        try:
            postman_index = local_storage.get_index("postman")
            stats["total_postman"] = postman_index.get("total", 0)
        except Exception:
            try:
                postman_result = postman_service.list_configurations()
                stats["total_postman"] = postman_result.get("total", 0)
            except Exception:
                stats["total_postman"] = 0

        stats["pages_by_type"] = pages_index.get("statistics", {}).get("by_type", {})
        by_method = endpoints_index.get("statistics", {}).get("by_method", {})
        stats["endpoints_by_method"] = {
            "QUERY": len(by_method.get("QUERY", [])),
            "MUTATION": len(by_method.get("MUTATION", [])),
        }
        
        # Cache statistics using RedisCacheManager
        cache_manager.set(
            STATISTICS_CACHE_KEY,
            stats,
            timeout=STATISTICS_CACHE_TTL,
            namespace=CACHE_PREFIX_STATISTICS,
        )
        logger.debug("Statistics cached successfully")
    except Exception as e:
        logger.error("Error loading dashboard stats: %s", e, exc_info=True)
        return server_error_response(f"Error loading dashboard stats: {str(e)}").to_json_response()

    return success_response(data=stats, message="Dashboard statistics retrieved successfully").to_json_response()


@login_required
@require_http_methods(["GET"])
def dashboard_graph_api(request: HttpRequest) -> JsonResponse:
    """
    API endpoint for graph data.
    
    GET /docs/api/graph/ (or equivalent)
    Returns: { success, data: { nodes, edges, statistics } }
    """
    try:
        graph_data = build_graph_data(pages_service, endpoints_service, relationships_service)
        return success_response(data=graph_data, message="Graph data retrieved successfully").to_json_response()
    except Exception as e:
        logger.error("Error loading graph data: %s", e, exc_info=True)
        return server_error_response(f"Error loading graph data: {str(e)}").to_json_response()


# Cache invalidation utilities
def invalidate_graph_cache() -> None:
    """
    Invalidate graph data cache.
    
    Call this function when pages, endpoints, or relationships are created, updated, or deleted.
    """
    try:
        cache_manager.delete(GRAPH_DATA_CACHE_KEY, namespace="dashboard")
        logger.info("Graph data cache invalidated")
    except Exception as e:
        logger.warning("Failed to invalidate graph cache: %s", e)


def invalidate_statistics_cache() -> None:
    """
    Invalidate statistics cache.
    
    Call this function when any resource count changes (pages, endpoints, relationships, postman).
    """
    try:
        cache_manager.delete(STATISTICS_CACHE_KEY, namespace=CACHE_PREFIX_STATISTICS)
        logger.info("Statistics cache invalidated")
    except Exception as e:
        logger.warning("Failed to invalidate statistics cache: %s", e)


def invalidate_dashboard_caches() -> None:
    """
    Invalidate all dashboard-related caches (graph and statistics).
    
    Call this function when any major data change occurs.
    """
    invalidate_graph_cache()
    invalidate_statistics_cache()
    logger.info("All dashboard caches invalidated")
