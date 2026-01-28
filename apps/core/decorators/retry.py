"""
Retry decorator with exponential backoff for resilient API calls.

This module provides a comprehensive retry decorator that can be applied to
functions that make external API calls or perform operations that may fail
temporarily and should be retried.
"""

import logging
import random
import time
from functools import wraps
from typing import Any, Callable, Optional, Tuple, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


def retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retryable_exceptions: Optional[Tuple[type[Exception], ...]] = None,
    jitter: bool = True,
    retry_logging: bool = True,
):
    """
    Decorator to retry a function with exponential backoff.
    
    This decorator implements exponential backoff retry logic with configurable
    parameters. It's designed for functions that make external API calls or
    perform operations that may fail temporarily due to network issues,
    rate limiting, or transient errors.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds before first retry (default: 1.0)
        max_delay: Maximum delay in seconds between retries (default: 60.0)
        exponential_base: Base for exponential backoff calculation (default: 2.0)
        retryable_exceptions: Tuple of exception types to retry on. If None, retries
            on all exceptions (default: None)
        jitter: Whether to add random jitter to delay to prevent thundering herd
            (default: True)
        retry_logging: Whether to log retry attempts (default: True)
    
    Returns:
        Decorated function with retry logic
    
    Raises:
        The last exception encountered if all retries are exhausted
    
    Example:
        ```python
        @retry(max_retries=3, initial_delay=1.0)
        def call_external_api():
            response = httpx.get("https://api.example.com/data")
            return response.json()
        
        @retry(
            max_retries=5,
            retryable_exceptions=(httpx.TimeoutException, httpx.NetworkError)
        )
        def fetch_data():
            # Only retries on network/timeout errors
            pass
        ```
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Optional[Exception] = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Check if we should retry this exception
                    if retryable_exceptions is not None:
                        if not isinstance(e, retryable_exceptions):
                            if retry_logging:
                                logger.debug(
                                    f"{func.__name__}: Exception {type(e).__name__} not in "
                                    f"retryable list, raising immediately: {e}"
                                )
                            raise
                    
                    # Don't retry on last attempt
                    if attempt == max_retries - 1:
                        if retry_logging:
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
                    
                    # Add jitter if enabled (10% random variation)
                    if jitter:
                        jitter_amount = delay * 0.1 * random.random()
                        delay += jitter_amount
                    
                    if retry_logging:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}): "
                            f"{type(e).__name__}: {e}. Retrying in {delay:.2f}s..."
                        )
                    
                    time.sleep(delay)
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            
            raise RuntimeError(
                f"{func.__name__} failed after {max_retries} attempts with no exception captured"
            )
        
        return wrapper
    return decorator


def retry_on_network_error(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
):
    """
    Decorator to retry on network-related errors only.
    
    This is a convenience decorator that retries only on network-related
    exceptions such as timeouts, connection errors, and network failures.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 60.0)
    
    Returns:
        Decorated function with network error retry logic
    
    Example:
        ```python
        @retry_on_network_error(max_retries=5)
        def fetch_from_api():
            response = httpx.get("https://api.example.com/data", timeout=10.0)
            return response.json()
        ```
    """
    try:
        import httpx
        import requests
        
        network_exceptions: Tuple[type[Exception], ...] = (
            httpx.TimeoutException,
            httpx.NetworkError,
            httpx.ConnectError,
            httpx.ConnectTimeout,
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.RequestException,
            ConnectionError,
            TimeoutError,
            OSError,  # Network-related OS errors
        )
    except ImportError:
        # Fallback if httpx/requests not available
        network_exceptions = (
            ConnectionError,
            TimeoutError,
            OSError,
        )
    
    return retry(
        max_retries=max_retries,
        initial_delay=initial_delay,
        max_delay=max_delay,
        retryable_exceptions=network_exceptions,
    )


def retry_on_server_error(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
):
    """
    Decorator to retry on server errors (5xx status codes).
    
    This decorator is designed for HTTP clients and retries on server errors
    (500, 502, 503, 504) which are typically transient.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 60.0)
    
    Returns:
        Decorated function with server error retry logic
    
    Example:
        ```python
        @retry_on_server_error(max_retries=3)
        def call_api():
            response = httpx.get("https://api.example.com/data")
            if response.status_code >= 500:
                raise httpx.HTTPStatusError("Server error", request=..., response=response)
            return response.json()
        ```
    """
    try:
        import httpx
        
        server_error_exceptions: Tuple[type[Exception], ...] = (
            httpx.HTTPStatusError,
        )
    except ImportError:
        # If httpx not available, use generic exception
        server_error_exceptions = (Exception,)
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Optional[Exception] = None
            
            for attempt in range(max_retries):
                try:
                    result = func(*args, **kwargs)
                    
                    # Check if result is an HTTP response with server error
                    if hasattr(result, 'status_code'):
                        status_code = getattr(result, 'status_code')
                        if 500 <= status_code < 600:
                            raise RuntimeError(
                                f"Server error {status_code} returned from {func.__name__}"
                            )
                    
                    return result
                except Exception as e:
                    last_exception = e
                    
                    # Check if it's a server error exception
                    should_retry = False
                    if isinstance(e, server_error_exceptions):
                        should_retry = True
                    elif hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                        status_code = e.response.status_code
                        if 500 <= status_code < 600:
                            should_retry = True
                    
                    if not should_retry:
                        logger.debug(
                            f"{func.__name__}: Exception {type(e).__name__} is not a "
                            f"server error, raising immediately: {e}"
                        )
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
                        initial_delay * (2.0 ** attempt),
                        max_delay
                    )
                    
                    # Add jitter
                    jitter_amount = delay * 0.1 * random.random()
                    delay += jitter_amount
                    
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}): "
                        f"{type(e).__name__}: {e}. Retrying in {delay:.2f}s..."
                    )
                    
                    time.sleep(delay)
            
            if last_exception:
                raise last_exception
            
            raise RuntimeError(
                f"{func.__name__} failed after {max_retries} attempts with no exception captured"
            )
        
        return wrapper
    return decorator
