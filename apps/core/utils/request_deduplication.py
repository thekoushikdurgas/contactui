"""
Request Deduplication Utility for preventing duplicate concurrent requests.
"""

import logging
import threading
from typing import Dict, Any, Callable, Optional
from concurrent.futures import Future, ThreadPoolExecutor
from django.core.cache import cache

logger = logging.getLogger(__name__)


class RequestDeduplicator:
    """
    Utility class for deduplicating concurrent requests.
    
    Prevents multiple identical requests from executing simultaneously
    by tracking pending requests and reusing their results.
    """
    
    def __init__(self, cache_timeout: int = 300):
        """
        Initialize request deduplicator.
        
        Args:
            cache_timeout: Timeout for pending request tracking (seconds)
        """
        self._pending_requests: Dict[str, Future] = {}
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=10)
        self.cache_timeout = cache_timeout
    
    def execute(
        self,
        request_key: str,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with deduplication.
        
        If the same request is already in progress, wait for its result.
        Otherwise, execute the function and cache the result for other concurrent requests.
        
        Args:
            request_key: Unique key for the request
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
            
        Returns:
            Function result
        """
        with self._lock:
            # Check if request is already in progress
            if request_key in self._pending_requests:
                future = self._pending_requests[request_key]
                logger.debug(f"Request deduplication: reusing pending request {request_key}")
                try:
                    # Wait for result (with timeout)
                    result = future.result(timeout=30)
                    return result
                except Exception as e:
                    logger.warning(f"Request deduplication wait failed for {request_key}: {e}")
                    # Remove failed future and continue
                    self._pending_requests.pop(request_key, None)
            
            # Create new future for this request
            future = self._executor.submit(func, *args, **kwargs)
            self._pending_requests[request_key] = future
        
        try:
            # Wait for result
            result = future.result(timeout=30)
            
            # Cache result for short period to handle rapid duplicate requests
            cache_key = f"dedup_result:{request_key}"
            try:
                cache.set(cache_key, result, timeout=min(60, self.cache_timeout))
            except Exception as cache_error:
                logger.warning(f"Cache set failed for request deduplication key {cache_key}: {cache_error}")
                # Continue without caching - deduplication still works via in-memory tracking
            
            return result
        except Exception as e:
            logger.error(f"Request deduplication execution failed for {request_key}: {e}")
            raise
        finally:
            # Clean up
            with self._lock:
                self._pending_requests.pop(request_key, None)
    
    def clear_pending(self, request_key: Optional[str] = None) -> None:
        """
        Clear pending requests.
        
        Args:
            request_key: Specific request key to clear, or None to clear all
        """
        with self._lock:
            if request_key:
                self._pending_requests.pop(request_key, None)
            else:
                self._pending_requests.clear()
    
    def get_pending_count(self) -> int:
        """Get number of pending requests."""
        with self._lock:
            return len(self._pending_requests)
