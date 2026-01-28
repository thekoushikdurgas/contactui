"""Base utilities for API v1 (response helpers and query param extraction)."""

import logging
from typing import Any, Dict, Optional

from django.http import HttpRequest, JsonResponse

logger = logging.getLogger(__name__)


def api_response(data: Any, status: int = 200) -> JsonResponse:
    """Create a standard API JSON response."""
    return JsonResponse(
        data,
        status=status,
        json_dumps_params={'ensure_ascii': False}
    )


def api_error(message: str, status: int = 400) -> JsonResponse:
    """Create a standard error JSON response."""
    return JsonResponse(
        {'error': message, 'success': False},
        status=status
    )


def extract_query_params(
    request: HttpRequest,
    param_names: list[str],
    type_map: Optional[Dict[str, type]] = None
) -> Dict[str, Any]:
    """
    Extract and type-convert query parameters from request.

    Args:
        request: Django HttpRequest
        param_names: List of parameter names to extract
        type_map: Optional dict mapping param names to types (int, float, bool)

    Returns:
        Dict of param_name -> value (only includes params that were provided)
    """
    type_map = type_map or {}
    params = {}

    for name in param_names:
        value = request.GET.get(name)
        if value is not None:
            target_type = type_map.get(name)
            if target_type == int:
                try:
                    params[name] = int(value)
                except ValueError:
                    pass
            elif target_type == float:
                try:
                    params[name] = float(value)
                except ValueError:
                    pass
            elif target_type == bool:
                params[name] = value.lower() in ('true', '1', 'yes')
            else:
                params[name] = value

    return params
