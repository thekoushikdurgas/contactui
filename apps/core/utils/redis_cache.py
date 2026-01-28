"""Redis caching utilities with connection management, decorators, and key management."""

from __future__ import annotations

import functools
import hashlib
import json
import logging
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from django.conf import settings
from django.core.cache import cache
from django.core.cache.backends.base import BaseCache

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Cache key prefixes
CACHE_PREFIX_PAGES = "pages"
CACHE_PREFIX_ENDPOINTS = "endpoints"
CACHE_PREFIX_RELATIONSHIPS = "relationships"
CACHE_PREFIX_POSTMAN = "postman"
CACHE_PREFIX_GRAPHQL = "graphql"
CACHE_PREFIX_LAMBDA_API = "lambda_api"
CACHE_PREFIX_STATISTICS = "statistics"
CACHE_PREFIX_INDEX = "index"

# Default TTL values (in seconds)
DEFAULT_TTL = 300  # 5 minutes
SHORT_TTL = 60  # 1 minute
MEDIUM_TTL = 300  # 5 minutes
LONG_TTL = 3600  # 1 hour
VERY_LONG_TTL = 86400  # 24 hours

# Cache version for selective invalidation (Task 2.2.1)
CACHE_VERSION = "1.0"  # Increment to invalidate all caches

# Dynamic TTL configuration by data type (Task 2.2.2)
CACHE_TTL_CONFIG = {
    # Static data - rarely changes
    "static": LONG_TTL,  # 1 hour
    "index": MEDIUM_TTL,  # 5 minutes (index.json)
    "statistics": SHORT_TTL * 2,  # 2 minutes
    
    # Dynamic data - changes frequently
    "list": SHORT_TTL * 2,  # 2 minutes (list operations)
    "detail": MEDIUM_TTL,  # 5 minutes (single item)
    "graph": MEDIUM_TTL * 2,  # 10 minutes (graph data)
    
    # Frequently accessed - balance freshness and performance
    "frequent": MEDIUM_TTL,  # 5 minutes
}


class RedisCacheManager:
    """Manager for Redis cache operations with connection handling and key management.
    
    Enhanced with cache versioning and dynamic TTL support (Task 2.2).
    """
    
    def __init__(self, cache_version: str = CACHE_VERSION):
        """Initialize Redis cache manager.
        
        Args:
            cache_version: Cache version string for selective invalidation
        """
        self.is_redis_enabled = getattr(settings, "USE_REDIS_CACHE", False)
        self.cache_backend = cache
        self._connection_healthy = None
        self.cache_version = cache_version  # Cache versioning (Task 2.2.1)
        
        if self.is_redis_enabled:
            logger.info("RedisCacheManager initialized with Redis backend (version: %s)", cache_version)
        else:
            logger.info("RedisCacheManager initialized with Django default cache backend (LocMemCache, version: %s)", cache_version)
    
    def _is_redis_backend(self) -> bool:
        """Check if current cache backend is Redis."""
        if not self.is_redis_enabled:
            return False
        
        backend_class = self.cache_backend.__class__.__name__
        return "Redis" in backend_class or "redis" in backend_class.lower()
    
    def _test_connection(self) -> bool:
        """Test Redis connection health."""
        if self._connection_healthy is not None:
            return self._connection_healthy
        
        try:
            # Simple ping test
            test_key = "__redis_health_check__"
            self.cache_backend.set(test_key, "ok", 1)
            result = self.cache_backend.get(test_key)
            self.cache_backend.delete(test_key)
            self._connection_healthy = result == "ok"
            return self._connection_healthy
        except Exception as e:
            logger.warning("Redis connection test failed: %s", e)
            self._connection_healthy = False
            return False
    
    def get(
        self,
        key: str,
        default: Optional[Any] = None,
        namespace: Optional[str] = None,
    ) -> Optional[Any]:
        """
        Get value from cache with namespace support.
        
        Args:
            key: Cache key
            default: Default value if key not found
            namespace: Optional namespace prefix
            
        Returns:
            Cached value or default
        """
        full_key = self._build_key(key, namespace)
        
        try:
            value = self.cache_backend.get(full_key)
            if value is not None:
                logger.debug("Cache hit: %s", full_key)
                return value
            logger.debug("Cache miss: %s", full_key)
            return default
        except Exception as e:
            logger.warning("Cache get failed for key %s: %s", full_key, e)
            return default
    
    def set(
        self,
        key: str,
        value: Any,
        timeout: Optional[int] = None,
        namespace: Optional[str] = None,
        data_type: Optional[str] = None,
    ) -> bool:
        """
        Set value in cache with namespace and version support.
        
        Enhanced with dynamic TTL based on data type (Task 2.2.2).
        
        Args:
            key: Cache key
            value: Value to cache
            timeout: TTL in seconds (default: based on data_type or DEFAULT_TTL)
            namespace: Optional namespace prefix
            data_type: Type of data for dynamic TTL ('static', 'list', 'detail', etc.)
            
        Returns:
            True if successful, False otherwise
        """
        full_key = self._build_key(key, namespace)
        
        # Use dynamic TTL if data_type provided (Task 2.2.2)
        if timeout is None:
            if data_type:
                timeout = self.get_ttl_for_data_type(data_type)
            else:
                timeout = DEFAULT_TTL
        
        try:
            self.cache_backend.set(full_key, value, timeout)
            logger.debug("Cache set: %s (TTL: %ds, type: %s)", full_key, timeout, data_type or "default")
            return True
        except Exception as e:
            logger.warning("Cache set failed for key %s: %s", full_key, e)
            return False
    
    def invalidate_by_version(self, old_version: str) -> int:
        """
        Invalidate all cache entries with a specific version (Task 2.2.1).
        
        Args:
            old_version: Version to invalidate
            
        Returns:
            Number of keys deleted
        """
        pattern = f"*:v{old_version}:*"
        return self.delete_pattern(pattern)
    
    def invalidate_by_data_type(self, data_type: str, namespace: Optional[str] = None) -> int:
        """
        Invalidate cache entries by data type pattern (Task 2.2.2).
        
        Args:
            data_type: Data type to invalidate
            namespace: Optional namespace to limit invalidation
            
        Returns:
            Number of keys deleted
        """
        # This would require tracking data types in keys or using tags
        # For now, return 0 - can be enhanced with cache tags later
        logger.debug("Invalidate by data type not fully implemented yet (data_type: %s)", data_type)
        return 0
    
    def delete(self, key: str, namespace: Optional[str] = None) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            namespace: Optional namespace prefix
            
        Returns:
            True if successful, False otherwise
        """
        full_key = self._build_key(key, namespace)
        
        try:
            self.cache_backend.delete(full_key)
            logger.debug("Cache delete: %s", full_key)
            return True
        except Exception as e:
            logger.warning("Cache delete failed for key %s: %s", full_key, e)
            return False
    
    def delete_pattern(self, pattern: str, namespace: Optional[str] = None) -> int:
        """
        Delete all keys matching pattern (Redis only).
        
        Args:
            pattern: Key pattern (supports wildcards like 'pages:*')
            namespace: Optional namespace prefix
            
        Returns:
            Number of keys deleted
        """
        if not self._is_redis_backend():
            # Use debug level instead of warning for non-Redis backends
            # This is expected behavior when using LocMemCache
            logger.debug("delete_pattern only works with Redis backend (using %s), skipping pattern deletion", 
                       self.cache_backend.__class__.__name__)
            return 0
        
        full_pattern = self._build_key(pattern, namespace)
        
        try:
            # Use Redis client directly for pattern matching
            if hasattr(self.cache_backend, "client"):
                client = self.cache_backend.client.get_client()
                keys = client.keys(full_pattern)
                if keys:
                    deleted = client.delete(*keys)
                    logger.info("Deleted %d keys matching pattern %s", deleted, full_pattern)
                    return deleted
            return 0
        except Exception as e:
            logger.warning("Cache delete_pattern failed for pattern %s: %s", full_pattern, e)
            return 0
    
    def invalidate_namespace(self, namespace: str) -> int:
        """
        Invalidate all keys in a namespace.
        
        Args:
            namespace: Namespace to invalidate
            
        Returns:
            Number of keys deleted
        """
        pattern = f"{namespace}:*"
        return self.delete_pattern(pattern)
    
    def clear_all(self) -> bool:
        """
        Clear all cache (use with caution).
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cache_backend.clear()
            logger.warning("Cache cleared completely")
            return True
        except Exception as e:
            logger.error("Cache clear_all failed: %s", e)
            return False
    
    def _build_key(self, key: str, namespace: Optional[str] = None, include_version: bool = True) -> str:
        """
        Build full cache key with namespace and version (Task 2.2.1).
        
        Args:
            key: Base cache key
            namespace: Optional namespace prefix
            include_version: Whether to include cache version (default: True)
            
        Returns:
            Full cache key with version
        """
        parts = []
        if namespace:
            parts.append(namespace)
        if include_version:
            parts.append(f"v{self.cache_version}")
        parts.append(key)
        return ":".join(parts)
    
    def get_ttl_for_data_type(self, data_type: str) -> int:
        """
        Get TTL for a specific data type (Task 2.2.2).
        
        Args:
            data_type: Type of data ('static', 'dynamic', 'list', 'detail', etc.)
            
        Returns:
            TTL in seconds
        """
        return CACHE_TTL_CONFIG.get(data_type, DEFAULT_TTL)
    
    def generate_key(
        self,
        prefix: str,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """
        Generate cache key from prefix and arguments.
        
        Args:
            prefix: Key prefix
            *args: Positional arguments to include in key
            **kwargs: Keyword arguments to include in key
            
        Returns:
            Generated cache key
        """
        key_parts = [prefix]
        
        # Add args
        for arg in args:
            if arg is not None:
                key_parts.append(str(arg))
        
        # Add kwargs (sorted for consistency)
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            for k, v in sorted_kwargs:
                if v is not None:
                    key_parts.append(f"{k}:{v}")
        
        # Create hash for long keys
        key_string = ":".join(key_parts)
        if len(key_string) > 200:
            # Hash long keys
            key_hash = hashlib.md5(key_string.encode()).hexdigest()
            return f"{prefix}:{key_hash}"
        
        return key_string
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get cache metrics."""
        return {
            "redis_enabled": self.is_redis_enabled,
            "redis_backend": self._is_redis_backend(),
            "connection_healthy": self._test_connection(),
        }


# Global cache manager instance
cache_manager = RedisCacheManager()


def cache_result(
    timeout: Optional[int] = None,
    key_prefix: Optional[str] = None,
    namespace: Optional[str] = None,
    key_func: Optional[Callable[..., str]] = None,
    condition: Optional[Callable[..., bool]] = None,
):
    """
    Decorator to cache function results.
    
    Args:
        timeout: Cache TTL in seconds (default: DEFAULT_TTL)
        key_prefix: Prefix for cache key
        namespace: Optional namespace for cache key
        key_func: Custom function to generate cache key from function args
        condition: Optional function to determine if result should be cached
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                func_name = key_prefix or func.__name__
                cache_key = cache_manager.generate_key(func_name, *args, **kwargs)
            
            # Check cache
            cached_value = cache_manager.get(cache_key, namespace=namespace)
            if cached_value is not None:
                logger.debug("Cache hit for function %s with key %s", func.__name__, cache_key)
                return cached_value
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result if condition allows
            if condition is None or condition(result, *args, **kwargs):
                cache_manager.set(cache_key, result, timeout=timeout, namespace=namespace)
                logger.debug("Cached result for function %s with key %s", func.__name__, cache_key)
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache(
    key_prefix: Optional[str] = None,
    namespace: Optional[str] = None,
    pattern: Optional[str] = None,
):
    """
    Decorator to invalidate cache after function execution.
    
    Args:
        key_prefix: Prefix for cache keys to invalidate
        namespace: Optional namespace for cache keys
        pattern: Optional pattern for cache keys to invalidate
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Execute function
            result = func(*args, **kwargs)
            
            # Invalidate cache
            if pattern:
                cache_manager.delete_pattern(pattern, namespace=namespace)
            elif key_prefix:
                pattern_to_delete = f"{key_prefix}:*"
                cache_manager.delete_pattern(pattern_to_delete, namespace=namespace)
            elif namespace:
                cache_manager.invalidate_namespace(namespace)
            
            return result
        
        return wrapper
    return decorator


def cache_page_result(
    timeout: Optional[int] = None,
    page_id_key: str = "page_id",
):
    """
    Decorator to cache page-related function results.
    
    Args:
        timeout: Cache TTL in seconds
        page_id_key: Key name for page_id in kwargs
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            page_id = kwargs.get(page_id_key) or (args[0] if args else None)
            cache_key = cache_manager.generate_key(CACHE_PREFIX_PAGES, page_id=page_id)
            
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, timeout=timeout)
            return result
        
        return wrapper
    return decorator


def cache_endpoint_result(
    timeout: Optional[int] = None,
    endpoint_id_key: str = "endpoint_id",
):
    """
    Decorator to cache endpoint-related function results.
    
    Args:
        timeout: Cache TTL in seconds
        endpoint_id_key: Key name for endpoint_id in kwargs
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            endpoint_id = kwargs.get(endpoint_id_key) or (args[0] if args else None)
            cache_key = cache_manager.generate_key(CACHE_PREFIX_ENDPOINTS, endpoint_id=endpoint_id)
            
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, timeout=timeout)
            return result
        
        return wrapper
    return decorator


def invalidate_page_cache(page_id: Optional[str] = None) -> int:
    """
    Invalidate page-related cache.
    
    Args:
        page_id: Optional specific page ID to invalidate
        
    Returns:
        Number of keys deleted
    """
    if page_id:
        pattern = cache_manager.generate_key(CACHE_PREFIX_PAGES, page_id=page_id)
        return cache_manager.delete_pattern(f"{pattern}*")
    else:
        return cache_manager.invalidate_namespace(CACHE_PREFIX_PAGES)


def invalidate_endpoint_cache(endpoint_id: Optional[str] = None) -> int:
    """
    Invalidate endpoint-related cache.
    
    Args:
        endpoint_id: Optional specific endpoint ID to invalidate
        
    Returns:
        Number of keys deleted
    """
    if endpoint_id:
        pattern = cache_manager.generate_key(CACHE_PREFIX_ENDPOINTS, endpoint_id=endpoint_id)
        return cache_manager.delete_pattern(f"{pattern}*")
    else:
        return cache_manager.invalidate_namespace(CACHE_PREFIX_ENDPOINTS)


def invalidate_relationship_cache(relationship_id: Optional[str] = None) -> int:
    """
    Invalidate relationship-related cache.
    
    Args:
        relationship_id: Optional specific relationship ID to invalidate
        
    Returns:
        Number of keys deleted
    """
    if relationship_id:
        pattern = cache_manager.generate_key(CACHE_PREFIX_RELATIONSHIPS, relationship_id=relationship_id)
        return cache_manager.delete_pattern(f"{pattern}*")
    else:
        return cache_manager.invalidate_namespace(CACHE_PREFIX_RELATIONSHIPS)


def invalidate_postman_cache(config_id: Optional[str] = None) -> int:
    """
    Invalidate Postman-related cache.
    
    Args:
        config_id: Optional specific config ID to invalidate
        
    Returns:
        Number of keys deleted
    """
    if config_id:
        pattern = cache_manager.generate_key(CACHE_PREFIX_POSTMAN, config_id=config_id)
        return cache_manager.delete_pattern(f"{pattern}*")
    else:
        return cache_manager.invalidate_namespace(CACHE_PREFIX_POSTMAN)


def invalidate_graphql_cache(query: Optional[str] = None) -> int:
    """
    Invalidate GraphQL query cache.
    
    Args:
        query: Optional specific query to invalidate
        
    Returns:
        Number of keys deleted
    """
    if query:
        # Hash query for key matching
        query_hash = hashlib.md5(query.encode()).hexdigest()
        pattern = cache_manager.generate_key(CACHE_PREFIX_GRAPHQL, query_hash=query_hash)
        return cache_manager.delete_pattern(f"{pattern}*")
    else:
        return cache_manager.invalidate_namespace(CACHE_PREFIX_GRAPHQL)


def invalidate_lambda_api_cache(endpoint: Optional[str] = None) -> int:
    """
    Invalidate Lambda API cache.
    
    Args:
        endpoint: Optional specific endpoint to invalidate
        
    Returns:
        Number of keys deleted
    """
    if endpoint:
        pattern = cache_manager.generate_key(CACHE_PREFIX_LAMBDA_API, endpoint=endpoint)
        return cache_manager.delete_pattern(f"{pattern}*")
    else:
        return cache_manager.invalidate_namespace(CACHE_PREFIX_LAMBDA_API)


def invalidate_statistics_cache() -> int:
    """
    Invalidate statistics cache.
    
    Returns:
        Number of keys deleted
    """
    return cache_manager.invalidate_namespace(CACHE_PREFIX_STATISTICS)


def invalidate_index_cache(index_type: Optional[str] = None) -> int:
    """
    Invalidate index cache.
    
    Args:
        index_type: Optional specific index type (pages, endpoints, etc.)
        
    Returns:
        Number of keys deleted
    """
    if index_type:
        pattern = cache_manager.generate_key(CACHE_PREFIX_INDEX, index_type=index_type)
        return cache_manager.delete_pattern(f"{pattern}*")
    else:
        return cache_manager.invalidate_namespace(CACHE_PREFIX_INDEX)
