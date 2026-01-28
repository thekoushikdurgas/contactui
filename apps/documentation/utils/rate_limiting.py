"""
Rate limiting utilities for API endpoints.

Provides decorators for rate limiting function-based views using Redis.
"""

from __future__ import annotations

import functools
import logging
import time
from typing import Any, Callable, Optional, TypeVar

from django.core.cache import cache
from django.http import HttpRequest, JsonResponse

from apps.documentation.utils.api_responses import rate_limited_response

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable)


def _get_client_identifier(request: HttpRequest) -> str:
    """
    Get unique identifier for rate limiting.
    
    Uses authenticated user ID if available, otherwise IP address.
    """
    if request.user.is_authenticated:
        return f"user:{request.user.id}"
    else:
        # Get IP address
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "unknown")
        return f"ip:{ip}"


def _get_rate_limit_key(
    identifier: str,
    endpoint: str,
    method: str = "GET",
) -> str:
    """Generate cache key for rate limiting."""
    return f"ratelimit:{method}:{endpoint}:{identifier}"


def _check_rate_limit(
    key: str,
    limit: int,
    window: int,
) -> tuple[bool, int, int]:
    """
    Check if request is within rate limit.
    
    Args:
        key: Cache key for rate limit
        limit: Maximum requests allowed
        window: Time window in seconds
        
    Returns:
        Tuple of (is_allowed, remaining, reset_time)
    """
    try:
        # Get current count
        current_count = cache.get(key, 0)
        
        if current_count >= limit:
            # Calculate reset time
            ttl = cache.ttl(key)
            if ttl is None or ttl < 0:
                reset_time = int(time.time()) + window
            else:
                reset_time = int(time.time()) + ttl
            
            return False, 0, reset_time
        
        # Increment count
        new_count = cache.incr(key)
        if new_count == 1:
            # First request, set expiration
            cache.set(key, 1, timeout=window)
        
        remaining = max(0, limit - new_count)
        ttl = cache.ttl(key)
        reset_time = int(time.time()) + (ttl if ttl else window)
        
        return True, remaining, reset_time
    except Exception as e:
        logger.warning("Rate limit check failed for key %s: %s", key, e)
        # On error, allow request (fail open)
        return True, limit, int(time.time()) + window


def rate_limit(
    limit: int = 100,
    window: int = 3600,
    per: str = "user",
    method: Optional[str] = None,
    key_func: Optional[Callable[[HttpRequest], str]] = None,
) -> Callable[[F], F]:
    """
    Decorator to rate limit API endpoints.
    
    Args:
        limit: Maximum number of requests allowed
        window: Time window in seconds (default: 3600 = 1 hour)
        per: Rate limit per "user" (authenticated) or "ip" (IP address)
        method: HTTP method to limit (None = all methods)
        key_func: Custom function to generate rate limit key
        
    Returns:
        Decorated function with rate limiting
        
    Example:
        @rate_limit(limit=100, window=3600, per="user")
        def my_api(request: HttpRequest) -> JsonResponse:
            ...
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
            # Check if method matches
            if method and request.method != method:
                return func(request, *args, **kwargs)
            
            # Get endpoint identifier
            endpoint = request.path
            
            # Get client identifier
            if key_func:
                identifier = key_func(request)
            elif per == "user":
                identifier = _get_client_identifier(request)
            else:  # per == "ip"
                x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
                if x_forwarded_for:
                    ip = x_forwarded_for.split(",")[0].strip()
                else:
                    ip = request.META.get("REMOTE_ADDR", "unknown")
                identifier = f"ip:{ip}"
            
            # Generate cache key
            cache_key = _get_rate_limit_key(identifier, endpoint, request.method)
            
            # Check rate limit
            is_allowed, remaining, reset_time = _check_rate_limit(
                cache_key,
                limit,
                window
            )
            
            if not is_allowed:
                logger.warning(
                    "Rate limit exceeded for %s on %s %s",
                    identifier,
                    request.method,
                    endpoint
                )
                
                # Calculate retry_after
                retry_after = max(1, reset_time - int(time.time()))
                
                response = rate_limited_response(
                    message=f"Rate limit exceeded: {limit} requests per {window} seconds",
                    retry_after=retry_after
                ).to_json_response()
                
                # Add rate limit headers
                response["X-RateLimit-Limit"] = str(limit)
                response["X-RateLimit-Remaining"] = "0"
                response["X-RateLimit-Reset"] = str(reset_time)
                response["Retry-After"] = str(retry_after)
                
                return response
            
            # Call original function
            result = func(request, *args, **kwargs)
            
            # Add rate limit headers to response
            if isinstance(result, JsonResponse):
                result["X-RateLimit-Limit"] = str(limit)
                result["X-RateLimit-Remaining"] = str(remaining)
                result["X-RateLimit-Reset"] = str(reset_time)
            
            return result
        
        return wrapper  # type: ignore
    return decorator


# Pre-configured rate limit decorators for common use cases

def rate_limit_per_user(
    limit: int = 1000,
    window: int = 3600,
) -> Callable[[F], F]:
    """Rate limit per authenticated user (default: 1000/hour)."""
    return rate_limit(limit=limit, window=window, per="user")


def rate_limit_per_ip(
    limit: int = 100,
    window: int = 3600,
) -> Callable[[F], F]:
    """Rate limit per IP address (default: 100/hour)."""
    return rate_limit(limit=limit, window=window, per="ip")


def rate_limit_heavy_endpoint(
    limit: int = 100,
    window: int = 3600,
) -> Callable[[F], F]:
    """Rate limit for heavy endpoints (default: 100/hour)."""
    return rate_limit(limit=limit, window=window, per="user")


def rate_limit_light_endpoint(
    limit: int = 5000,
    window: int = 3600,
) -> Callable[[F], F]:
    """Rate limit for light endpoints (default: 5000/hour)."""
    return rate_limit(limit=limit, window=window, per="user")


# Endpoint-specific rate limits

def rate_limit_create_endpoint() -> Callable[[F], F]:
    """Rate limit for create endpoints (50/hour per user)."""
    return rate_limit(limit=50, window=3600, per="user")


def rate_limit_list_endpoint() -> Callable[[F], F]:
    """Rate limit for list endpoints (1000/hour per user)."""
    return rate_limit(limit=1000, window=3600, per="user")


def rate_limit_detail_endpoint() -> Callable[[F], F]:
    """Rate limit for detail endpoints (2000/hour per user)."""
    return rate_limit(limit=2000, window=3600, per="user")


def rate_limit_update_endpoint() -> Callable[[F], F]:
    """Rate limit for update endpoints (100/hour per user)."""
    return rate_limit(limit=100, window=3600, per="user")


def rate_limit_delete_endpoint() -> Callable[[F], F]:
    """Rate limit for delete endpoints (50/hour per user)."""
    return rate_limit(limit=50, window=3600, per="user")
