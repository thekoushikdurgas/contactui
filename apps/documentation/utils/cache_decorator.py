"""
GET response caching for documentation API v1.

Uses apps.core.decorators.cache_response with documentation-specific
namespace and TTL (60–600s). Apply to list/statistics/format GET views.
"""

from apps.core.decorators.cache_response import cache_response
from apps.core.utils.redis_cache import MEDIUM_TTL

# Namespace for documentation API cache keys
DOCUMENTATION_CACHE_NAMESPACE = "documentation_api"

# Default TTL for list/statistics/format endpoints (seconds)
DOCUMENTATION_CACHE_TTL = MEDIUM_TTL  # 300s; use 60–600 as needed per endpoint


def cache_documentation_get(
    timeout: int = DOCUMENTATION_CACHE_TTL,
    key_prefix: str = "",
    vary_on_query_params: list = None,
):
    """
    Cache GET responses for documentation API v1.

    Same as core cache_response but with namespace=documentation_api and
    default timeout suitable for list/statistics/format endpoints.
    """
    return cache_response(
        timeout=timeout,
        key_prefix=key_prefix or "doc_api",
        namespace=DOCUMENTATION_CACHE_NAMESPACE,
        vary_on_query_params=vary_on_query_params,
    )


# Convenience for common TTLs (in seconds)
CACHE_SHORT = 60
CACHE_MEDIUM = 300
CACHE_LONG = 600
