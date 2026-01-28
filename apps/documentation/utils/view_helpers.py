"""Shared view helper utilities for documentation views.

This module provides common utility functions used across multiple view files
to reduce code duplication and improve maintainability (Task 2.3.1).
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional, Tuple

from django.http import HttpRequest

logger = logging.getLogger(__name__)

# Default pagination constants
DEFAULT_LIMIT = 20
MAX_LIMIT = 500
DEFAULT_OFFSET = 0

# Valid detail tabs for different resource types
VALID_DETAIL_TABS_PAGES = frozenset({"overview", "content", "relationships", "endpoints", "components", "access", "raw"})
VALID_DETAIL_TABS_ENDPOINTS = frozenset({"overview", "request", "response", "graphql", "relationships", "raw"})
VALID_DETAIL_TABS_RELATIONSHIPS = frozenset({"overview", "connection", "usage", "related", "raw"})
VALID_DETAIL_TABS_POSTMAN = frozenset({"overview", "collection", "requests", "environments", "mappings", "raw"})


def parse_limit_offset(
    request: HttpRequest,
    default_limit: int = DEFAULT_LIMIT,
    max_limit: int = MAX_LIMIT,
    default_offset: int = DEFAULT_OFFSET
) -> Tuple[int, int]:
    """
    Parse and validate limit/offset from request query parameters.
    
    Args:
        request: HTTP request object
        default_limit: Default limit value (default: 20)
        max_limit: Maximum allowed limit (default: 500)
        default_offset: Default offset value (default: 0)
        
    Returns:
        Tuple of (limit, offset) as integers
        
    Example:
        >>> limit, offset = parse_limit_offset(request)
        >>> limit, offset = parse_limit_offset(request, default_limit=50, max_limit=1000)
    """
    try:
        limit = int(request.GET.get("limit", default_limit))
    except (TypeError, ValueError):
        limit = default_limit
    limit = max(1, min(limit, max_limit))

    try:
        offset = int(request.GET.get("offset", default_offset))
    except (TypeError, ValueError):
        offset = default_offset
    offset = max(0, offset)

    return limit, offset


def parse_json_body(request: HttpRequest) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Parse JSON body from request.
    
    Args:
        request: HTTP request object with JSON body
        
    Returns:
        Tuple of (data_dict, error_message)
        - data_dict: Parsed JSON data as dictionary, or None if error
        - error_message: Error message string, or None if successful
        
    Example:
        >>> data, error = parse_json_body(request)
        >>> if error:
        ...     return error_response(error)
        >>> # Use data...
    """
    try:
        body = request.body
        if not body:
            return None, "Request body is required"
        data = json.loads(body)
        if not isinstance(data, dict):
            return None, "Request body must be a JSON object"
        return data, None
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON: {e}"


def validate_detail_tab(
    tab: Optional[str],
    resource_type: str = "pages"
) -> str:
    """
    Validate and normalize tab query parameter for detail views.
    
    Args:
        tab: Tab name from query parameter
        resource_type: Type of resource ('pages', 'endpoints', 'relationships', 'postman')
        
    Returns:
        Valid tab name, or default tab if invalid
        
    Example:
        >>> tab = validate_detail_tab(request.GET.get('tab'), 'pages')
        >>> # Returns 'overview' if tab is None or invalid
    """
    # Select appropriate valid tabs set based on resource type
    if resource_type == "pages":
        valid_tabs = VALID_DETAIL_TABS_PAGES
        default_tab = "overview"
    elif resource_type == "endpoints":
        valid_tabs = VALID_DETAIL_TABS_ENDPOINTS
        default_tab = "overview"
    elif resource_type == "relationships":
        valid_tabs = VALID_DETAIL_TABS_RELATIONSHIPS
        default_tab = "overview"
    elif resource_type == "postman":
        valid_tabs = VALID_DETAIL_TABS_POSTMAN
        default_tab = "overview"
    else:
        # Default fallback
        valid_tabs = VALID_DETAIL_TABS_PAGES
        default_tab = "overview"
    
    if not tab or tab not in valid_tabs:
        return default_tab
    return tab
