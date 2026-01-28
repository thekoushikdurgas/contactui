"""
API docs registry: single source of truth for the 110 GET endpoints at /api/v1/.

Used by:
- API docs UI at /api/docs/ (list + per-endpoint docs)
- Path → endpoint_key resolver for request tracking
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

# Base path for all v1 API routes
API_V1_PREFIX = "/api/v1/"


def _endpoint(
    path_suffix: str,
    endpoint_key: str,
    name: str,
    description: str,
    query_params: Optional[List[Dict[str, str]]] = None,
    path_params: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Build endpoint dict. path_suffix is relative to /api/v1/ (no leading slash)."""
    path = f"{API_V1_PREFIX}{path_suffix.rstrip('/')}/" if path_suffix else API_V1_PREFIX.rstrip("/") + "/"
    return {
        "path": path,
        "path_pattern": path_suffix if path_suffix else "",
        "endpoint_key": endpoint_key,
        "method": "GET",
        "name": name,
        "description": description,
        "query_params": query_params or [],
        "path_params": path_params or [],
    }


# Order of path_patterns matters for resolver: more specific (longer) first.
# We sort by path_pattern length desc when building the matcher.
GROUPS: List[Dict[str, Any]] = [
    {
        "id": "health",
        "name": "Health & root",
        "description": "Service info and health checks",
        "endpoints": [
            _endpoint("", "root", "Service info", "Get service information (name, version, status)."),
            _endpoint("health/", "health", "Health", "Get comprehensive health (app, database, cache, storage, external API)."),
            _endpoint("health/database/", "health_database", "Health database", "Get database health status."),
            _endpoint("health/cache/", "health_cache", "Health cache", "Get cache health status."),
            _endpoint("health/storage/", "health_storage", "Health storage", "Get storage health status."),
            _endpoint("docs/endpoint-stats/", "docs_endpoint_stats", "Endpoint stats", "Get per-endpoint request counts and last-called timestamps (JSON)."),
        ],
    },
    {
        "id": "pages",
        "name": "Pages",
        "description": "Documentation pages (20 GETs)",
        "endpoints": [
            _endpoint("pages/", "pages_list", "List pages", "List all documentation pages.", query_params=[{"name": "page_type"}, {"name": "include_drafts"}, {"name": "include_deleted"}, {"name": "status"}, {"name": "limit"}, {"name": "offset"}]),
            _endpoint("pages/by-type/docs/", "pages_by_type_docs", "Pages by type docs", "List docs-type pages."),
            _endpoint("pages/by-type/marketing/", "pages_by_type_marketing", "Pages by type marketing", "List marketing-type pages."),
            _endpoint("pages/by-type/dashboard/", "pages_by_type_dashboard", "Pages by type dashboard", "List dashboard-type pages."),
            _endpoint("pages/by-type/{page_type}/count/", "pages_by_type_count", "Pages by type count", "Count pages by type.", path_params=[{"name": "page_type"}]),
            _endpoint("pages/by-type/{page_type}/published/", "pages_by_type_published", "Pages by type published", "List published pages by type.", path_params=[{"name": "page_type"}]),
            _endpoint("pages/by-type/{page_type}/draft/", "pages_by_type_draft", "Pages by type draft", "List draft pages by type.", path_params=[{"name": "page_type"}]),
            _endpoint("pages/by-type/{page_type}/stats/", "pages_by_type_stats", "Pages by type stats", "Stats for a page type.", path_params=[{"name": "page_type"}]),
            _endpoint("pages/by-state/{state}/", "pages_by_state_list", "Pages by state", "List pages by state.", path_params=[{"name": "state"}]),
            _endpoint("pages/by-state/{state}/count/", "pages_by_state_count", "Pages by state count", "Count pages by state.", path_params=[{"name": "state"}]),
            _endpoint("pages/{page_id}/access-control/", "pages_detail_access_control", "Page access control", "Get page access control.", path_params=[{"name": "page_id"}]),
            _endpoint("pages/{page_id}/sections/", "pages_detail_sections", "Page sections", "Get page sections.", path_params=[{"name": "page_id"}]),
            _endpoint("pages/{page_id}/components/", "pages_detail_components", "Page components", "Get page components and ui_components.", path_params=[{"name": "page_id"}]),
            _endpoint("pages/{page_id}/endpoints/", "pages_detail_endpoints", "Page endpoints", "Get endpoints used by page.", path_params=[{"name": "page_id"}]),
            _endpoint("pages/{page_id}/versions/", "pages_detail_versions", "Page versions", "Get page versions.", path_params=[{"name": "page_id"}]),
            _endpoint("pages/{segment}/", "pages_user_type_or_detail", "Pages by user type or detail", "List by user_type (super_admin, admin, …) or get page by ID.", path_params=[{"name": "segment"}]),
        ],
    },
    {
        "id": "endpoints",
        "name": "Endpoints",
        "description": "API endpoints (28 GETs)",
        "endpoints": [
            _endpoint("endpoints/", "endpoints_list", "List endpoints", "List all API endpoints.", query_params=[{"name": "limit"}, {"name": "offset"}]),
            _endpoint("endpoints/by-api-version/v1/", "endpoints_by_api_version_v1", "By API version v1", "List endpoints for API version v1."),
            _endpoint("endpoints/by-api-version/v4/", "endpoints_by_api_version_v4", "By API version v4", "List endpoints for API version v4."),
            _endpoint("endpoints/by-api-version/graphql/", "endpoints_by_api_version_graphql", "By API version graphql", "List GraphQL endpoints."),
            _endpoint("endpoints/by-api-version/{api_version}/count/", "endpoints_by_api_version_count", "By API version count", "Count by API version.", path_params=[{"name": "api_version"}]),
            _endpoint("endpoints/by-api-version/{api_version}/stats/", "endpoints_by_api_version_stats", "By API version stats", "Stats by API version.", path_params=[{"name": "api_version"}]),
            _endpoint("endpoints/by-api-version/{api_version}/by-method/{method}/", "endpoints_by_api_version_by_method", "By API version and method", "List by API version and method.", path_params=[{"name": "api_version"}, {"name": "method"}]),
            _endpoint("endpoints/by-method/GET/", "endpoints_by_method_get", "By method GET", "List GET endpoints."),
            _endpoint("endpoints/by-method/POST/", "endpoints_by_method_post", "By method POST", "List POST endpoints."),
            _endpoint("endpoints/by-method/QUERY/", "endpoints_by_method_query", "By method QUERY", "List GraphQL QUERY endpoints."),
            _endpoint("endpoints/by-method/MUTATION/", "endpoints_by_method_mutation", "By method MUTATION", "List GraphQL MUTATION endpoints."),
            _endpoint("endpoints/by-method/{method}/count/", "endpoints_by_method_count", "By method count", "Count by method.", path_params=[{"name": "method"}]),
            _endpoint("endpoints/by-method/{method}/stats/", "endpoints_by_method_stats", "By method stats", "Stats by method.", path_params=[{"name": "method"}]),
            _endpoint("endpoints/by-state/{state}/", "endpoints_by_state_list", "Endpoints by state", "List endpoints by state.", path_params=[{"name": "state"}]),
            _endpoint("endpoints/by-state/{state}/count/", "endpoints_by_state_count", "Endpoints by state count", "Count by state.", path_params=[{"name": "state"}]),
            _endpoint("endpoints/by-lambda/{service_name}/", "endpoints_by_lambda_list", "Endpoints by Lambda", "List endpoints by Lambda service.", path_params=[{"name": "service_name"}]),
            _endpoint("endpoints/by-lambda/{service_name}/count/", "endpoints_by_lambda_count", "Endpoints by Lambda count", "Count by Lambda service.", path_params=[{"name": "service_name"}]),
            _endpoint("endpoints/{endpoint_id}/", "endpoints_detail", "Endpoint detail", "Get endpoint by ID.", path_params=[{"name": "endpoint_id"}]),
            _endpoint("endpoints/{endpoint_id}/pages/", "endpoints_detail_pages", "Endpoint pages", "Pages that use this endpoint.", path_params=[{"name": "endpoint_id"}]),
            _endpoint("endpoints/{endpoint_id}/access-control/", "endpoints_detail_access_control", "Endpoint access control", "Endpoint access control.", path_params=[{"name": "endpoint_id"}]),
            _endpoint("endpoints/{endpoint_id}/lambda-services/", "endpoints_detail_lambda_services", "Endpoint Lambda services", "Lambda services for endpoint.", path_params=[{"name": "endpoint_id"}]),
            _endpoint("endpoints/{endpoint_id}/files/", "endpoints_detail_files", "Endpoint files", "Service/router files for endpoint.", path_params=[{"name": "endpoint_id"}]),
            _endpoint("endpoints/{endpoint_id}/methods/", "endpoints_detail_methods", "Endpoint methods", "Methods for endpoint.", path_params=[{"name": "endpoint_id"}]),
            _endpoint("endpoints/{endpoint_id}/used-by-pages/", "endpoints_detail_used_by_pages", "Endpoint used-by pages", "Pages that use this endpoint.", path_params=[{"name": "endpoint_id"}]),
            _endpoint("endpoints/{endpoint_id}/dependencies/", "endpoints_detail_dependencies", "Endpoint dependencies", "Endpoint dependencies.", path_params=[{"name": "endpoint_id"}]),
        ],
    },
    {
        "id": "relationships",
        "name": "Relationships",
        "description": "Page–endpoint relationships (38 GETs)",
        "endpoints": [
            _endpoint("relationships/", "relationships_list", "List relationships", "List all relationships."),
            _endpoint("relationships/usage-types/", "relationships_usage_types", "Usage types", "List usage types."),
            _endpoint("relationships/usage-contexts/", "relationships_usage_contexts", "Usage contexts", "List usage contexts."),
            _endpoint("relationships/by-page/{page_id}/", "relationships_by_page", "By page", "Relationships by page.", path_params=[{"name": "page_id"}]),
            _endpoint("relationships/by-page/{page_id}/count/", "relationships_by_page_count", "By page count", "Count by page.", path_params=[{"name": "page_id"}]),
            _endpoint("relationships/by-page/{page_id}/primary/", "relationships_by_page_primary", "By page primary", "Primary relationships by page.", path_params=[{"name": "page_id"}]),
            _endpoint("relationships/by-page/{page_id}/secondary/", "relationships_by_page_secondary", "By page secondary", "Secondary relationships by page.", path_params=[{"name": "page_id"}]),
            _endpoint("relationships/by-page/{page_id}/by-usage-type/{usage_type}/", "relationships_by_page_by_usage_type", "By page and usage type", "By page and usage type.", path_params=[{"name": "page_id"}, {"name": "usage_type"}]),
            _endpoint("relationships/by-endpoint/{endpoint_id}/", "relationships_by_endpoint", "By endpoint", "Relationships by endpoint.", path_params=[{"name": "endpoint_id"}]),
            _endpoint("relationships/by-endpoint/{endpoint_id}/count/", "relationships_by_endpoint_count", "By endpoint count", "Count by endpoint.", path_params=[{"name": "endpoint_id"}]),
            _endpoint("relationships/by-endpoint/{endpoint_id}/pages/", "relationships_by_endpoint_pages", "By endpoint pages", "Pages by endpoint.", path_params=[{"name": "endpoint_id"}]),
            _endpoint("relationships/by-endpoint/{endpoint_id}/by-usage-context/{usage_context}/", "relationships_by_endpoint_by_usage_context", "By endpoint and context", "By endpoint and usage context.", path_params=[{"name": "endpoint_id"}, {"name": "usage_context"}]),
            _endpoint("relationships/by-usage-type/primary/", "relationships_by_usage_type_primary", "By usage type primary", "Primary usage type relationships."),
            _endpoint("relationships/by-usage-type/secondary/", "relationships_by_usage_type_secondary", "By usage type secondary", "Secondary usage type relationships."),
            _endpoint("relationships/by-usage-type/conditional/", "relationships_by_usage_type_conditional", "By usage type conditional", "Conditional usage type relationships."),
            _endpoint("relationships/by-usage-type/{usage_type}/count/", "relationships_by_usage_type_count", "By usage type count", "Count by usage type.", path_params=[{"name": "usage_type"}]),
            _endpoint("relationships/by-usage-type/{usage_type}/by-usage-context/{usage_context}/", "relationships_by_usage_type_by_usage_context", "By usage type and context", "By usage type and context.", path_params=[{"name": "usage_type"}, {"name": "usage_context"}]),
            _endpoint("relationships/by-usage-context/data_fetching/", "relationships_by_usage_context_data_fetching", "By context data_fetching", "Data fetching context relationships."),
            _endpoint("relationships/by-usage-context/data_mutation/", "relationships_by_usage_context_data_mutation", "By context data_mutation", "Data mutation context relationships."),
            _endpoint("relationships/by-usage-context/authentication/", "relationships_by_usage_context_authentication", "By context authentication", "Authentication context relationships."),
            _endpoint("relationships/by-usage-context/analytics/", "relationships_by_usage_context_analytics", "By context analytics", "Analytics context relationships."),
            _endpoint("relationships/by-usage-context/{usage_context}/count/", "relationships_by_usage_context_count", "By usage context count", "Count by usage context.", path_params=[{"name": "usage_context"}]),
            _endpoint("relationships/by-state/{state}/", "relationships_by_state_list", "Relationships by state", "List by state.", path_params=[{"name": "state"}]),
            _endpoint("relationships/by-state/{state}/count/", "relationships_by_state_count", "Relationships by state count", "Count by state.", path_params=[{"name": "state"}]),
            _endpoint("relationships/by-lambda/{service_name}/", "relationships_by_lambda", "Relationships by Lambda", "By Lambda service.", path_params=[{"name": "service_name"}]),
            _endpoint("relationships/by-invocation-pattern/{pattern}/", "relationships_by_invocation_pattern", "By invocation pattern", "By invocation pattern.", path_params=[{"name": "pattern"}]),
            _endpoint("relationships/by-postman-config/{config_id}/", "relationships_by_postman_config", "By Postman config", "By Postman config ID.", path_params=[{"name": "config_id"}]),
            _endpoint("relationships/performance/slow/", "relationships_performance_slow", "Performance slow", "Slow performance relationships."),
            _endpoint("relationships/performance/errors/", "relationships_performance_errors", "Performance errors", "Error performance relationships."),
            _endpoint("relationships/{relationship_id}/", "relationships_detail", "Relationship detail", "Get relationship by ID.", path_params=[{"name": "relationship_id"}]),
            _endpoint("relationships/{relationship_id}/access-control/", "relationships_detail_access_control", "Relationship access control", "Access control for relationship.", path_params=[{"name": "relationship_id"}]),
            _endpoint("relationships/{relationship_id}/data-flow/", "relationships_detail_data_flow", "Relationship data flow", "Data flow for relationship.", path_params=[{"name": "relationship_id"}]),
            _endpoint("relationships/{relationship_id}/performance/", "relationships_detail_performance", "Relationship performance", "Performance for relationship.", path_params=[{"name": "relationship_id"}]),
            _endpoint("relationships/{relationship_id}/dependencies/", "relationships_detail_dependencies", "Relationship dependencies", "Dependencies for relationship.", path_params=[{"name": "relationship_id"}]),
            _endpoint("relationships/{relationship_id}/postman/", "relationships_detail_postman", "Relationship postman", "Postman config for relationship.", path_params=[{"name": "relationship_id"}]),
        ],
    },
    {
        "id": "postman",
        "name": "Postman",
        "description": "Postman configurations (14 GETs)",
        "endpoints": [
            _endpoint("postman/", "postman_list", "List Postman", "List Postman configurations."),
            _endpoint("postman/by-state/{state}/", "postman_by_state_list", "Postman by state", "List by state.", path_params=[{"name": "state"}]),
            _endpoint("postman/by-state/{state}/count/", "postman_by_state_count", "Postman by state count", "Count by state.", path_params=[{"name": "state"}]),
            _endpoint("postman/{config_id}/", "postman_detail", "Postman detail", "Get Postman config by ID.", path_params=[{"name": "config_id"}]),
            _endpoint("postman/{config_id}/collection/", "postman_detail_collection", "Postman collection", "Get collection for config.", path_params=[{"name": "config_id"}]),
            _endpoint("postman/{config_id}/environments/", "postman_detail_environments", "Postman environments", "List environments.", path_params=[{"name": "config_id"}]),
            _endpoint("postman/{config_id}/environments/{env_name}/", "postman_detail_environment", "Postman environment by name", "Get environment by name.", path_params=[{"name": "config_id"}, {"name": "env_name"}]),
            _endpoint("postman/{config_id}/mappings/", "postman_detail_mappings", "Postman mappings", "List mappings.", path_params=[{"name": "config_id"}]),
            _endpoint("postman/{config_id}/mappings/{mapping_id}/", "postman_detail_mapping", "Postman mapping by ID", "Get mapping by ID.", path_params=[{"name": "config_id"}, {"name": "mapping_id"}]),
            _endpoint("postman/{config_id}/test-suites/", "postman_detail_test_suites", "Postman test suites", "List test suites.", path_params=[{"name": "config_id"}]),
            _endpoint("postman/{config_id}/test-suites/{suite_id}/", "postman_detail_test_suite", "Postman test suite by ID", "Get test suite by ID.", path_params=[{"name": "config_id"}, {"name": "suite_id"}]),
            _endpoint("postman/{config_id}/access-control/", "postman_detail_access_control", "Postman access control", "Access control for config.", path_params=[{"name": "config_id"}]),
        ],
    },
]

def get_all_endpoints() -> List[Dict[str, Any]]:
    """Return a flat list of all endpoints from all groups."""
    result: List[Dict[str, Any]] = []
    for group in GROUPS:
        for ep in group["endpoints"]:
            result.append({**ep, "group_id": group["id"], "group_name": group["name"]})
    return result


def get_all_endpoint_keys() -> List[str]:
    """Return list of all endpoint_key values (for stats lookup)."""
    return [ep["endpoint_key"] for ep in get_all_endpoints()]


def _path_pattern_to_regex(pattern: str) -> str:
    """Convert path_pattern with {param} placeholders to a regex string (anchored)."""
    if not pattern:
        return r"^$"
    # Escape regex specials then replace {name} with [^/]+
    escaped = re.escape(pattern)
    escaped = re.sub(r"\\\{[^}]+\\\}", "[^/]+", escaped)
    return r"^" + escaped.rstrip("/") + r"/?$"


# Cache (pattern_regex, endpoint_key) sorted by pattern length desc for longest match first
_resolver_cache: Optional[List[Tuple[str, str]]] = None


def _get_resolver_patterns() -> List[Tuple[str, str]]:
    """Build sorted list of (regex_pattern, endpoint_key) for resolver."""
    global _resolver_cache
    if _resolver_cache is not None:
        return _resolver_cache
    endpoints = get_all_endpoints()
    pairs: List[Tuple[str, str, int]] = []
    for ep in endpoints:
        pat = ep["path_pattern"]
        regex = _path_pattern_to_regex(pat)
        # Length of path_pattern (longer = more specific)
        pairs.append((regex, ep["endpoint_key"], len(pat)))
    pairs.sort(key=lambda x: -x[2])
    _resolver_cache = [(r, k) for r, k, _ in pairs]
    return _resolver_cache


def resolve_endpoint_key(request_path: str) -> Optional[str]:
    """
    Resolve a request path (e.g. /api/v1/pages/abc-123/) to the endpoint_key for tracking.

    Uses longest-match: more specific path patterns are tried first.
    Returns None if path is not under /api/v1/ or does not match any known endpoint.
    """
    if not request_path.startswith(API_V1_PREFIX):
        return None
    suffix = request_path[len(API_V1_PREFIX) :].rstrip("/")
    if suffix:
        suffix = suffix + "/"
    else:
        suffix = ""
    for regex, endpoint_key in _get_resolver_patterns():
        if re.match(regex, suffix):
            return endpoint_key
    return None


def get_total_endpoint_count() -> int:
    """Return total number of registered endpoints (for docs UI)."""
    return len(get_all_endpoint_keys())
