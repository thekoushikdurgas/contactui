"""
Response Caching Decorators for API views.

Enhanced with RedisCacheManager for better cache management, namespacing, and metrics.
"""

import logging
import hashlib
import json
from functools import wraps
from typing import Callable, Optional, Dict, Any
from django.http import JsonResponse, HttpResponse

from apps.core.utils.redis_cache import cache_manager, CACHE_PREFIX_LAMBDA_API, MEDIUM_TTL

logger = logging.getLogger(__name__)


def cache_response(
    timeout: int = MEDIUM_TTL,
    key_prefix: str = '',
    namespace: Optional[str] = None,
    vary_on_headers: Optional[list] = None,
    vary_on_query_params: Optional[list] = None,
    condition: Optional[Callable[[Any], bool]] = None
):
    """
    Decorator to cache API responses using RedisCacheManager.
    
    Args:
        timeout: Cache timeout in seconds (default: MEDIUM_TTL = 300)
        key_prefix: Prefix for cache key
        namespace: Optional namespace for cache key (default: 'api_responses')
        vary_on_headers: List of headers to include in cache key
        vary_on_query_params: List of query parameters to include in cache key
        condition: Optional function to determine if response should be cached
    
    Usage:
        @cache_response(timeout=600, vary_on_query_params=['page_type', 'status'])
        def my_api_view(request):
            return JsonResponse({'data': ...})
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Generate cache key
            cache_key_parts = [key_prefix or func.__name__]
            
            # Add path
            cache_key_parts.append(request.path)
            
            # Add query parameters if specified
            if vary_on_query_params:
                query_params = {}
                for param in vary_on_query_params:
                    if param in request.GET:
                        query_params[param] = request.GET[param]
                if query_params:
                    cache_key_parts.append(json.dumps(query_params, sort_keys=True))
            elif request.GET:
                # Include all query params if not specified
                query_params = dict(request.GET)
                cache_key_parts.append(json.dumps(query_params, sort_keys=True))
            
            # Add headers if specified
            if vary_on_headers:
                header_values = {}
                for header in vary_on_headers:
                    if header in request.META:
                        header_values[header] = request.META[header]
                if header_values:
                    cache_key_parts.append(json.dumps(header_values, sort_keys=True))
            
            # Add args and kwargs
            if args:
                cache_key_parts.append(str(args))
            if kwargs:
                cache_key_parts.append(json.dumps(kwargs, sort_keys=True))
            
            # Create hash for cache key
            cache_key_str = ':'.join(str(part) for part in cache_key_parts)
            cache_key_hash = hashlib.md5(cache_key_str.encode()).hexdigest()
            cache_key = f"api_response:{cache_key_hash}"
            
            # Use default namespace if not specified
            cache_namespace = namespace or "api_responses"
            
            # Check cache using RedisCacheManager
            cached_response = cache_manager.get(cache_key, namespace=cache_namespace)
            if cached_response is not None:
                logger.debug(f"API response cache hit for {func.__name__}: {cache_key}")
                return JsonResponse(cached_response)
            
            # Execute function
            response = func(request, *args, **kwargs)
            
            # Cache successful responses
            if isinstance(response, JsonResponse):
                try:
                    response_data = json.loads(response.content)
                    
                    # Check condition if provided
                    should_cache = True
                    if condition:
                        should_cache = condition(response_data, response, request)
                    
                    # Only cache successful responses (200-299)
                    if should_cache and 200 <= response.status_code < 300:
                        cache_manager.set(
                            cache_key,
                            response_data,
                            timeout=timeout,
                            namespace=cache_namespace
                        )
                        logger.debug(f"Cached API response for {func.__name__}: {cache_key} (TTL: {timeout}s)")
                except Exception as e:
                    logger.warning(f"Failed to cache API response for {func.__name__}: {e}")
            
            return response
        
        return wrapper
    return decorator


def cache_api_response(
    timeout: int = MEDIUM_TTL,
    key_func: Optional[Callable] = None,
    namespace: Optional[str] = None,
    condition: Optional[Callable[[Any], bool]] = None
):
    """
    Simplified decorator for caching API responses using RedisCacheManager.
    
    Args:
        timeout: Cache timeout in seconds (default: MEDIUM_TTL = 300)
        key_func: Optional function to generate custom cache key
        namespace: Optional namespace for cache key (default: 'api_responses')
        condition: Optional function to determine if response should be cached
    
    Usage:
        @cache_api_response(timeout=600)
        def my_api_view(request):
            return JsonResponse({'data': ...})
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(request, *args, **kwargs)
            else:
                # Default: use path + query string
                cache_key_str = f"{request.path}?{request.META.get('QUERY_STRING', '')}"
                cache_key_hash = hashlib.md5(cache_key_str.encode()).hexdigest()
                cache_key = f"api_response:{cache_key_hash}"
            
            # Use default namespace if not specified
            cache_namespace = namespace or "api_responses"
            
            # Check cache using RedisCacheManager
            cached_data = cache_manager.get(cache_key, namespace=cache_namespace)
            if cached_data is not None:
                logger.debug(f"API response cache hit for {func.__name__}: {cache_key}")
                return JsonResponse(cached_data)
            
            # Execute function
            response = func(request, *args, **kwargs)
            
            # Cache successful responses
            if isinstance(response, JsonResponse):
                try:
                    response_data = json.loads(response.content)
                    
                    # Check condition if provided
                    should_cache = True
                    if condition:
                        should_cache = condition(response_data, response, request)
                    
                    # Only cache successful responses (200-299)
                    if should_cache and 200 <= response.status_code < 300:
                        cache_manager.set(
                            cache_key,
                            response_data,
                            timeout=timeout,
                            namespace=cache_namespace
                        )
                        logger.debug(f"Cached API response for {func.__name__}: {cache_key} (TTL: {timeout}s)")
                except Exception as e:
                    logger.warning(f"Failed to cache API response for {func.__name__}: {e}")
            
            return response
        
        return wrapper
    return decorator


def invalidate_api_cache(
    pattern: Optional[str] = None,
    namespace: Optional[str] = None
):
    """
    Decorator to invalidate API response cache after function execution.
    
    Args:
        pattern: Pattern for cache keys to invalidate (e.g., 'api_response:*')
        namespace: Optional namespace for cache keys (default: 'api_responses')
    
    Usage:
        @invalidate_api_cache(pattern='api_response:pages:*')
        def update_page(request, page_id):
            # After this function, matching cache entries will be invalidated
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Execute function
            response = func(request, *args, **kwargs)
            
            # Invalidate cache
            cache_namespace = namespace or "api_responses"
            
            if pattern:
                try:
                    cache_manager.delete_pattern(pattern, namespace=cache_namespace)
                    logger.debug(f"Invalidated API cache pattern: {pattern} in namespace: {cache_namespace}")
                except Exception as e:
                    logger.warning(f"Failed to invalidate API cache: {e}")
            else:
                # Default: invalidate all API responses for this endpoint
                default_pattern = f"api_response:{request.path}*"
                try:
                    cache_manager.delete_pattern(default_pattern, namespace=cache_namespace)
                    logger.debug(f"Invalidated API cache for path: {request.path}")
                except Exception as e:
                    logger.warning(f"Failed to invalidate API cache: {e}")
            
            return response
        
        return wrapper
    return decorator
