"""Example payload generators for /format endpoints.

Ported from Lambda documentation.api. These helpers provide copy/paste-friendly
JSON examples for:
- Pages
- Endpoints
- Relationships
- Postman configurations
- Analysis ingestion payloads

They are intentionally conservative (minimal required fields + common defaults).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def page_examples(data_prefix: str = "data/") -> Dict[str, Any]:
    page_id = "about_page"
    route = "/about"
    return {
        "s3": {
            "object_key": f"{data_prefix}pages/{page_id}.json",
        },
        "minimal": {
            "_id": f"{page_id}-001",
            "page_id": page_id,
            "page_type": "docs",
            "metadata": {
                "route": route,
                "file_path": "app/about/page.tsx",
                "purpose": "About page",
                "s3_key": f"{data_prefix}pages/{page_id}.json",
                "status": "published",
                "authentication": "Not required",
                "authorization": None,
                "page_state": "development",
                "last_updated": _now(),
                "uses_endpoints": [],
                "ui_components": [],
                "versions": [],
                "endpoint_count": 0,
                "api_versions": [],
            },
            "content": "# About\n\nThis is the about page.",
            "created_at": _now(),
            "access_control": {
                "super_admin": {"can_view": True, "can_edit": True, "can_delete": True},
                "admin": {"can_view": True, "can_edit": True, "can_delete": False},
                "pro_user": {"can_view": True, "can_edit": False, "can_delete": False},
                "free_user": {"can_view": True, "can_edit": False, "can_delete": False},
                "guest": {"can_view": False, "can_edit": False, "can_delete": False},
            },
        },
        "notes": [
            "Store pages at data/pages/{page_id}.json",
            "metadata.s3_key should point to the JSON object key (not markdown).",
            "metadata.status is legacy; metadata.page_state is lifecycle state (coming_soon/development/draft/test/published).",
        ],
    }


def endpoint_examples(data_prefix: str = "data/") -> Dict[str, Any]:
    endpoint_id = "get_users_v1"
    endpoint_path = "/api/v1/users"
    return {
        "s3": {"object_key": f"{data_prefix}endpoints/{endpoint_id}.json"},
        "minimal": {
            "_id": f"{endpoint_id}-001",
            "endpoint_id": endpoint_id,
            "endpoint_path": endpoint_path,
            "method": "GET",
            "api_version": "v1",
            "description": "Get list of users",
            "authentication": "Not specified",
            "authorization": None,
            "service_file": "app/services/users_service.py",
            "router_file": None,
            "service_methods": ["get_users"],
            "repository_methods": ["find_users"],
            "endpoint_state": "development",
            "used_by_pages": [],
            "page_count": 0,
            "created_at": _now(),
            "updated_at": _now(),
            "lambda_services": {
                "primary": {
                    "service_name": "users.api",
                    "function_name": "users-api-function",
                    "runtime": "python3.11",
                    "memory_mb": 256,
                    "timeout_seconds": 30,
                },
                "dependencies": [],
                "environment": {},
            },
        },
        "notes": [
            "Store endpoints at data/endpoints/{endpoint_id}.json",
            "At least one of service_file or router_file must be provided.",
            "Indexes are maintained in data/endpoints/index.json.",
        ],
    }


def relationship_examples(data_prefix: str = "data/") -> Dict[str, Any]:
    page_path = "/dashboard"
    endpoint_path = "graphql/GetUserStats"
    method = "QUERY"
    return {
        "s3": {
            "by_page_key": f"{data_prefix}relationships/by-page/dashboard.json",
            "by_endpoint_key": f"{data_prefix}relationships/by-endpoint/graphql_GetUserStats_QUERY.json",
            "index_key": f"{data_prefix}relationships/index.json",
        },
        "single_relationship_create": {
            "page_path": page_path,
            "endpoint_path": endpoint_path,
            "method": method,
            "api_version": "graphql",
            "via_service": "adminService",
            "via_hook": "useDashboardPage",
            "usage_type": "conditional",
            "usage_context": "analytics",
        },
        "by_page_file": {
            "page_path": page_path,
            "endpoints": [
                {
                    "page_path": page_path,
                    "endpoint_path": endpoint_path,
                    "method": method,
                    "api_version": "graphql",
                    "via_service": "adminService",
                    "via_hook": "useDashboardPage",
                    "usage_type": "conditional",
                    "usage_context": "analytics",
                    "updated_at": _now(),
                }
            ],
            "created_at": _now(),
            "updated_at": _now(),
        },
        "by_endpoint_file": {
            "endpoint_path": endpoint_path,
            "method": method,
            "api_version": "graphql",
            "pages": [
                {
                    "page_path": page_path,
                    "page_title": "Dashboard Page",
                    "via_service": "adminService",
                    "via_hook": "useDashboardPage",
                    "usage_type": "conditional",
                    "usage_context": "analytics",
                    "updated_at": _now(),
                }
            ],
            "created_at": _now(),
            "updated_at": _now(),
        },
        "notes": [
            "Relationships are materialized in two directions: by-page and by-endpoint.",
            "A master index exists at data/relationships/index.json for fast listing and statistics.",
        ],
    }


def postman_examples(data_prefix: str = "data/") -> Dict[str, Any]:
    config_id = "contact360"
    return {
        "s3": {
            "configuration_key": f"{data_prefix}postman/configurations/{config_id}.json",
            "index_key": f"{data_prefix}postman/index.json",
            "by_state_prefix": f"{data_prefix}postman/by-state/",
        },
        "minimal": {
            "_id": config_id,
            "config_id": config_id,
            "name": "Contact360 API",
            "description": "Postman configuration for Contact360 APIs",
            "state": "development",
            "collection": {
                "info": {
                    "name": "Contact360 API",
                    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
                },
                "item": [],
            },
            "environments": [],
            "endpoint_mappings": [],
            "test_suites": [],
            "access_control": None,
            "metadata": {
                "created_at": _now(),
                "updated_at": _now(),
                "version": "1.0.0",
                "tags": [],
                "notes": None,
            },
        },
        "notes": [
            "Postman configurations are stored under data/postman/configurations/.",
            "Indexes exist under data/postman/index.json and data/postman/by-state/{state}.json.",
        ],
    }


def analysis_examples() -> Dict[str, Any]:
    return {
        "pages_analysis": {
            "pages": [
                {
                    "page_path": "/dashboard",
                    "page_title": "Dashboard",
                    "page_file": "app/dashboard/page.tsx",
                    "ui_components": ["Chart", "Card"],
                    "pattern_components": [],
                    "feature_components": [],
                    "hooks": ["useDashboard"],
                    "services": ["adminService"],
                    "contexts": ["AuthContext"],
                }
            ]
        },
        "endpoints_analysis": {
            "endpoints": [
                {
                    "endpoint_id": "GetUserStats",
                    "endpoint_path": "graphql/GetUserStats",
                    "method": "QUERY",
                    "api_version": "graphql",
                    "router_file": "app/api/graphql/schema.py",
                    "service_methods": ["getUserStats"],
                    "repository_methods": [],
                    "authentication": "Not specified",
                    "description": "Fetch dashboard stats",
                }
            ]
        },
        "relationships_analysis": {
            "page_to_endpoints": {
                "/dashboard": [
                    {
                        "endpoint_path": "graphql/GetUserStats",
                        "method": "QUERY",
                        "api_version": "graphql",
                        "via_service": "adminService",
                        "via_hook": "useDashboardPage",
                        "usage_type": "primary",
                        "usage_context": "analytics",
                        "updated_at": _now(),
                    }
                ]
            },
            "endpoint_to_pages": {
                "QUERY:graphql/GetUserStats": [
                    {
                        "page_path": "/dashboard",
                        "page_title": "Dashboard Page",
                        "via_service": "adminService",
                        "via_hook": "useDashboardPage",
                        "usage_type": "primary",
                        "usage_context": "analytics",
                        "updated_at": _now(),
                    }
                ]
            },
        },
    }
