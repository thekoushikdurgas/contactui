"""Retry decorators and utilities for external API calls."""

import logging
import time
from functools import wraps
from typing import Callable, TypeVar, Any, Optional, Tuple
from django.core.cache import cache

logger = logging.getLogger(__name__)

T = TypeVar('T')


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retry_on: Optional[Tuple[Exception, ...]] = None,
    jitter: bool = True
):
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 60.0)
        exponential_base: Base for exponential backoff (default: 2.0)
        retry_on: Tuple of exception types to retry on (default: all exceptions)
        jitter: Whether to add random jitter to delay (default: True)
    
    Usage:
        @retry_with_backoff(max_retries=3, initial_delay=1.0)
        def call_external_api():
            # API call that may fail
            pass
    """
    import random
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Check if we should retry this exception
                    if retry_on and not isinstance(e, retry_on):
                        logger.debug(f"Exception {type(e).__name__} not in retry list, raising immediately")
                        raise
                    
                    # Don't retry on last attempt
                    if attempt == max_retries - 1:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} attempts: {e}",
                            exc_info=True
                        )
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        initial_delay * (exponential_base ** attempt),
                        max_delay
                    )
                    
                    # Add jitter if enabled
                    if jitter:
                        jitter_amount = delay * 0.1 * random.random()
                        delay += jitter_amount
                    
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            
            raise RuntimeError(f"{func.__name__} failed after {max_retries} attempts")
        
        return wrapper
    return decorator


def retry_on_network_error(
    max_retries: int = 3,
    initial_delay: float = 1.0
):
    """
    Decorator to retry on network-related errors.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
    
    Usage:
        @retry_on_network_error(max_retries=3)
        def call_external_api():
            # API call that may fail due to network issues
            pass
    """
    import httpx
    import requests
    
    network_exceptions = (
        httpx.TimeoutException,
        httpx.NetworkError,
        httpx.ConnectError,
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError,
        requests.exceptions.RequestException,
        ConnectionError,
        TimeoutError,
    )
    
    return retry_with_backoff(
        max_retries=max_retries,
        initial_delay=initial_delay,
        retry_on=network_exceptions
    )
