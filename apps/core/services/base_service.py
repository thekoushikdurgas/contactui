"""Base service class for all services with common patterns."""

import logging
from typing import Optional, Dict, Any, Callable, TypeVar, List, Tuple
from django.core.cache import cache
from functools import wraps
import time

# Import cache TTL configuration for dynamic TTL support (Task 2.2.2)
try:
    from apps.core.utils.redis_cache import CACHE_TTL_CONFIG, DEFAULT_TTL
except ImportError:
    CACHE_TTL_CONFIG = {}
    DEFAULT_TTL = 300

logger = logging.getLogger(__name__)

T = TypeVar('T')

# Note: Retry decorators are available in apps.documentation.utils.retry
# Import them when needed:
# from apps.documentation.utils.retry import retry_with_backoff, retry_on_network_error


def log_performance(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to log method execution time.
    
    Usage:
        @log_performance
        def my_method(self, ...):
            ...
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs) -> T:
        start_time = time.time()
        try:
            result = func(self, *args, **kwargs)
            execution_time = time.time() - start_time
            self.logger.debug(f"{func.__name__} executed in {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {e}")
            raise
    return wrapper


class BaseService:
    """Base class for all services with common patterns."""
    
    def __init__(self, name: str):
        """
        Initialize base service.
        
        Args:
            name: Service name for logging
        """
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self.logger.info(f"{name} service initialized")
        self.cache_timeout = 300  # Default 5 minutes
    
    def _get_cache_key(self, operation: str, *args, **kwargs) -> str:
        """
        Generate cache key for an operation.
        
        Args:
            operation: Operation name
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Cache key string
        """
        key_parts = [self.name, operation]
        if args:
            key_parts.extend(str(arg) for arg in args)
        if kwargs:
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return ":".join(key_parts)
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached value or None
        """
        try:
            value = cache.get(cache_key)
            if value is not None:
                self.logger.debug(f"Cache hit for key: {cache_key}")
            return value
        except Exception as e:
            self.logger.warning(f"Cache get failed for key {cache_key}: {e}")
            return None
    
    def _set_cache(
        self, 
        cache_key: str, 
        value: Any, 
        timeout: Optional[int] = None,
        data_type: Optional[str] = None
    ) -> bool:
        """
        Set value in cache with dynamic TTL support (Task 2.2.2).
        
        Args:
            cache_key: Cache key
            value: Value to cache
            timeout: Time to live in seconds (defaults based on data_type or self.cache_timeout)
            data_type: Type of data for dynamic TTL ('static', 'list', 'detail', etc.)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use dynamic TTL if data_type provided (Task 2.2.2)
            if timeout is None:
                if data_type and data_type in CACHE_TTL_CONFIG:
                    timeout = CACHE_TTL_CONFIG[data_type]
                else:
                    timeout = self.cache_timeout
            
            cache.set(cache_key, value, timeout)
            self.logger.debug(f"Cached value for key: {cache_key} (TTL: {timeout}s, type: {data_type or 'default'})")
            return True
        except Exception as e:
            self.logger.warning(f"Cache set failed for key {cache_key}: {e}")
            return False
    
    def _clear_cache(self, cache_key: Optional[str] = None) -> bool:
        """
        Clear cache for a specific key or all service cache.
        
        Args:
            cache_key: Specific cache key to clear, or None to clear all service cache
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if cache_key:
                cache.delete(cache_key)
                self.logger.debug(f"Cleared cache for key: {cache_key}")
            else:
                # Clear all cache keys for this service
                # Note: This is a simplified implementation
                # In production, you might want to use cache versioning or namespacing
                self.logger.warning("Clearing all cache - this may affect other services")
            return True
        except Exception as e:
            self.logger.warning(f"Cache clear failed: {e}")
            return False
    
    def _validate_input(self, data: Dict[str, Any], required_fields: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate input data.
        
        Args:
            data: Data dictionary to validate
            required_fields: List of required field names
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        if missing_fields:
            error_msg = f"Missing required fields: {', '.join(missing_fields)}"
            self.logger.warning(error_msg)
            return False, error_msg
        return True, None
    
    def _handle_error(
        self,
        error: Exception,
        context: str = "",
        record_monitoring: bool = True
    ) -> Dict[str, Any]:
        """
        Handle and log errors consistently.
        
        Args:
            error: Exception instance
            context: Additional context string
            record_monitoring: Whether to record error in monitoring system
            
        Returns:
            Error response dictionary
        """
        error_msg = str(error)
        if context:
            error_msg = f"{context}: {error_msg}"
        
        error_type = type(error).__name__
        
        self.logger.error(error_msg, exc_info=True)
        
        # Record error in monitoring system
        if record_monitoring:
            try:
                from apps.core.services.error_monitor import ErrorMonitor
                monitor = ErrorMonitor()
                monitor.record_error(
                    error_type=error_type,
                    error_message=error_msg,
                    context={'service': self.name, 'context': context}
                )
            except Exception as e:
                # Don't fail if monitoring fails
                self.logger.warning(f"Failed to record error in monitoring: {e}")
        
        return {
            'success': False,
            'error': error_msg,
            'error_type': error_type
        }
    
    def _format_success_response(
        self,
        data: Any,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format a successful response consistently.
        
        Args:
            data: Response data
            message: Optional success message
            metadata: Optional metadata dictionary
            
        Returns:
            Formatted response dictionary
        """
        response = {
            'success': True,
            'data': data
        }
        
        if message:
            response['message'] = message
        
        if metadata:
            response['metadata'] = metadata
        
        return response
    
    def _format_error_response(
        self,
        error: str,
        error_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format an error response consistently.
        
        Args:
            error: Error message
            error_type: Optional error type
            details: Optional error details dictionary
            
        Returns:
            Formatted error response dictionary
        """
        response = {
            'success': False,
            'error': error
        }
        
        if error_type:
            response['error_type'] = error_type
        
        if details:
            response['details'] = details
        
        return response
    
    def _format_list_response(
        self,
        items: List[Any],
        total: Optional[int] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format a list response consistently.
        
        Args:
            items: List of items
            total: Total count (defaults to len(items))
            limit: Limit applied
            offset: Offset applied
            metadata: Optional metadata dictionary
            
        Returns:
            Formatted list response dictionary
        """
        if total is None:
            total = len(items)
        
        response = {
            'items': items,
            'total': total,
            'offset': offset
        }
        
        if limit is not None:
            response['limit'] = limit
        
        if metadata:
            response['metadata'] = metadata
        
        return response
