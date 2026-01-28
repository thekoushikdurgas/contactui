"""
API Version Router for Documentation System.

Implements URL-based versioning (/docs/api/v1/, /docs/api/v2/) with:
- Version negotiation
- Deprecation handling
- Version fallback
- Version documentation endpoint
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse

from apps.documentation.utils.api_responses import success_response

logger = logging.getLogger(__name__)

# Supported API versions (default first)
SUPPORTED_VERSIONS = ("v1", "v2")
DEFAULT_VERSION = "v1"

# Deprecation info: version -> (deprecated: bool, sunset_date: str|None, successor: str|None)
VERSION_INFO: Dict[str, Dict[str, Any]] = {
    "v1": {
        "deprecated": False,
        "sunset_date": None,
        "successor": "v2",
        "description": "Stable API - pages, endpoints, relationships, postman, media, dashboard",
    },
    "v2": {
        "deprecated": False,
        "sunset_date": None,
        "successor": None,
        "description": "Future API - currently aliases to v1",
    },
}


def get_version_from_path(path: str) -> Optional[str]:
    """
    Extract API version from URL path.

    Examples:
        /docs/api/v1/pages/ -> v1
        /docs/api/v2/health/ -> v2
        /docs/api/pages/ -> None (no version)
    """
    parts = path.strip("/").split("/")
    try:
        # docs, api, v1, ...
        if len(parts) >= 3 and parts[0] == "docs" and parts[1] == "api":
            cand = parts[2].lower()
            if cand.startswith("v") and cand[1:].isdigit() and cand in SUPPORTED_VERSIONS:
                return cand
    except (IndexError, AttributeError):
        pass
    return None


def negotiate_version(request: HttpRequest, path: str) -> str:
    """
    Determine API version from URL path, Accept header, or query param.

    Priority:
    1. URL path (/docs/api/v1/...)
    2. Query param ?api_version=v1
    3. Accept header application/vnd.docsapi.v1+json
    4. Default to DEFAULT_VERSION
    """
    # 1. URL path
    version = get_version_from_path(path)
    if version:
        return version

    # 2. Query param
    version = request.GET.get("api_version", "").strip().lower()
    if version in SUPPORTED_VERSIONS:
        return version

    # 3. Accept header (e.g. Accept: application/vnd.docsapi.v1+json)
    accept = request.META.get("HTTP_ACCEPT", "") or ""
    for ver in SUPPORTED_VERSIONS:
        if f"application/vnd.docsapi.{ver}+json" in accept:
            return ver

    return DEFAULT_VERSION


@login_required
def version_info_response(request: HttpRequest) -> JsonResponse:
    """
    API version documentation endpoint.

    GET /docs/api/versions/ or GET /docs/api/v1/versions/
    Returns supported versions, default, deprecation info.
    """
    versions = []
    for v in SUPPORTED_VERSIONS:
        info = VERSION_INFO.get(v, {})
        versions.append({
            "version": v,
            "default": v == DEFAULT_VERSION,
            "deprecated": info.get("deprecated", False),
            "sunset_date": info.get("sunset_date"),
            "successor": info.get("successor"),
            "description": info.get("description", ""),
        })

    data = {
        "versions": versions,
        "default_version": DEFAULT_VERSION,
        "versioning": "url",
        "url_format": "/docs/api/{version}/...",
        "negotiation": [
            "URL path: /docs/api/v1/...",
            "Query param: ?api_version=v1",
            "Accept header: application/vnd.docsapi.v1+json",
        ],
    }
    return success_response(
        data=data,
        message="API version info",
        meta={"request_version": negotiate_version(request, request.path)},
    ).to_json_response()


def add_deprecation_headers(
    response: JsonResponse,
    version: str,
) -> JsonResponse:
    """Add deprecation-related headers to response if version is deprecated."""
    info = VERSION_INFO.get(version, {})
    if info.get("deprecated"):
        response["X-API-Deprecated"] = "true"
        response["X-API-Version"] = version
        if info.get("sunset_date"):
            response["X-API-Sunset"] = info["sunset_date"]
        if info.get("successor"):
            response["X-API-Successor"] = info["successor"]
    return response


def strip_version_from_path(path: str) -> str:
    """
    Remove version segment from path for routing.

    /docs/api/v1/pages/ -> /docs/api/pages/
    /docs/api/v2/health/ -> /docs/api/health/
    """
    parts = path.strip("/").split("/")
    if len(parts) >= 3 and parts[0] == "docs" and parts[1] == "api":
        cand = parts[2].lower()
        if cand in SUPPORTED_VERSIONS:
            # Rebuild without version
            return "/" + "/".join(parts[:2] + parts[3:]) + ("/" if path.endswith("/") else "")
    return path
