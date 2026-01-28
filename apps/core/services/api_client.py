"""Base HTTP API client with retry logic, request validation, and error handling."""

from __future__ import annotations

import functools
import logging
import time
from enum import Enum
from typing import Any, Callable, Dict, Optional, TypeVar, Union
import httpx
from apps.core.exceptions import LambdaAPIError

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryStrategy(Enum):
    """Retry backoff strategies."""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"


def retry_request(
    max_retries: int = 3,
    retry_delay: float = 1.0,
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    retry_on: tuple[type[Exception], ...] = (httpx.HTTPStatusError, httpx.RequestError),
    retry_on_status: tuple[int, ...] = (429, 500, 502, 503, 504),
):
    """
    Decorator for retrying API requests with configurable backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Base delay between retries in seconds
        retry_strategy: Retry backoff strategy
        retry_on: Exception types to retry on
        retry_on_status: HTTP status codes to retry on
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Optional[Exception] = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except retry_on as e:
                    last_exception = e
                    
                    # Check if we should retry based on status code
                    if isinstance(e, httpx.HTTPStatusError):
                        status_code = e.response.status_code
                        if status_code not in retry_on_status:
                            # Don't retry on this status code
                            raise
                    
                    if attempt < max_retries - 1:
                        # Calculate backoff delay
                        if retry_strategy == RetryStrategy.EXPONENTIAL:
                            delay = retry_delay * (2 ** attempt)
                        elif retry_strategy == RetryStrategy.LINEAR:
                            delay = retry_delay * (attempt + 1)
                        else:  # FIXED
                            delay = retry_delay
                        
                        logger.warning(
                            "Retrying %s after %.2fs (attempt %d/%d): %s",
                            func.__name__,
                            delay,
                            attempt + 1,
                            max_retries,
                            str(e),
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            "%s failed after %d attempts: %s",
                            func.__name__,
                            max_retries,
                            str(e),
                        )
                        raise
            
            # Should not reach here
            if last_exception:
                raise last_exception
            raise RuntimeError(f"{func.__name__} failed after {max_retries} attempts")
        
        return wrapper
    return decorator


class APIClient:
    """Base HTTP client for API requests with retry logic."""
    
    def __init__(
        self,
        base_url: str,
        api_key: str = '',
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """Initialize API client.
        
        Args:
            base_url: Base URL for API
            api_key: API key for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries (exponential backoff)
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.client = httpx.Client(timeout=timeout)
        
        logger.info(f"APIClient initialized for {self.base_url}")
    
    def _validate_endpoint(self, endpoint: str) -> str:
        """
        Validate and normalize endpoint path.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            Normalized endpoint path
            
        Raises:
            ValueError: If endpoint is invalid
        """
        if not endpoint or not isinstance(endpoint, str):
            raise ValueError("endpoint must be a non-empty string")
        
        # Ensure endpoint starts with /
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"
        
        # Basic security: prevent path traversal
        if ".." in endpoint or "//" in endpoint:
            raise ValueError(f"Invalid endpoint path: {endpoint}")
        
        return endpoint
    
    def _validate_request_data(self, data: Optional[Dict[str, Any]], method: str) -> Optional[Dict[str, Any]]:
        """
        Validate request data based on method.
        
        Args:
            data: Request data dictionary
            method: HTTP method
            
        Returns:
            Validated data dictionary
            
        Raises:
            ValueError: If data is invalid
        """
        if method.upper() in ("POST", "PUT", "PATCH"):
            if data is None:
                logger.warning("%s request without data", method.upper())
                return {}
            if not isinstance(data, dict):
                raise ValueError(f"Request data must be a dictionary for {method.upper()} requests")
        
        return data
    
    def _get_headers(self, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Get default headers for API requests.
        
        Args:
            additional_headers: Optional additional headers to include
            
        Returns:
            Headers dictionary
        """
        headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "APIClient/1.0",
        }
        
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        
        if additional_headers:
            headers.update(additional_headers)
        
        return headers
    
    def _calculate_backoff(self, attempt: int) -> float:
        """Calculate backoff wait time based on retry strategy."""
        if self.retry_strategy == RetryStrategy.EXPONENTIAL:
            wait_time = self.retry_delay * (2 ** attempt)
        elif self.retry_strategy == RetryStrategy.LINEAR:
            wait_time = self.retry_delay * (attempt + 1)
        else:  # FIXED
            wait_time = self.retry_delay
        
        return wait_time
    
    def _log_request(
        self,
        method: str,
        endpoint: str,
        status_code: Optional[int] = None,
        response_time: Optional[float] = None,
        attempt: int = 1,
        error: Optional[str] = None,
    ) -> None:
        """Enhanced logging for API requests."""
        log_data: Dict[str, Any] = {
            "method": method,
            "endpoint": endpoint,
            "url": f"{self.base_url}{endpoint}",
            "attempt": attempt,
        }
        
        if status_code:
            log_data["status_code"] = status_code
        
        if response_time is not None:
            log_data["response_time_ms"] = round(response_time * 1000, 2)
        
        if error:
            log_data["error"] = error
            logger.error("API request failed: %s", log_data, extra=log_data)
        elif status_code and status_code >= 400:
            logger.warning("API request returned error: %s", log_data, extra=log_data)
        else:
            logger.info("API request successful: %s", log_data, extra=log_data)
    
    def _retry_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Any:
        """Execute request with retry logic.
        
        Args:
            method: HTTP method ('get', 'post', 'put', 'delete', 'patch')
            endpoint: API endpoint path
            **kwargs: Additional arguments for request
            
        Returns:
            Response data
            
        Raises:
            LambdaAPIError: If request fails after retries
        """
        url = f"{self.base_url}{endpoint}"
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"{method.upper()} {url} (attempt {attempt + 1}/{self.max_retries})")
                
                response = getattr(self.client, method.lower())(
                    url,
                    headers=self._get_headers(kwargs.pop('headers', None)),
                    **kwargs
                )
                
                response.raise_for_status()
                return response.json() if response.content else {}
                
            except httpx.HTTPStatusError as e:
                last_exception = e
                status_code = e.response.status_code
                
                # Don't retry on client errors (4xx) except 429 (rate limit)
                if 400 <= status_code < 500 and status_code != 429:
                    logger.error(f"Client error {status_code} for {method.upper()} {url}: {e}")
                    raise LambdaAPIError(
                        f"{method.upper()} request failed with status {status_code}: {str(e)}",
                        endpoint=endpoint,
                        status_code=status_code,
                        error_code=f'HTTP_{status_code}'
                    )
                
                # Retry on server errors (5xx) and rate limits (429)
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        f"Request failed (status {status_code}), retrying in {delay}s: {e}"
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"Request failed after {self.max_retries} attempts: {e}")
                    raise LambdaAPIError(
                        f"{method.upper()} request failed after {self.max_retries} attempts: {str(e)}",
                        endpoint=endpoint,
                        status_code=status_code,
                        error_code='MAX_RETRIES_EXCEEDED'
                    )
                    
            except httpx.RequestError as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Request error, retrying in {delay}s: {e}")
                    time.sleep(delay)
                else:
                    logger.error(f"Request error after {self.max_retries} attempts: {e}")
                    raise LambdaAPIError(
                        f"{method.upper()} request error: {str(e)}",
                        endpoint=endpoint,
                        error_code='REQUEST_ERROR'
                    )
        
        # Should not reach here, but just in case
        raise LambdaAPIError(
            f"{method.upper()} request failed: {str(last_exception)}",
            endpoint=endpoint,
            error_code='UNKNOWN_ERROR'
        )
    
    def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Make GET request with validation and retry logic.
        
        Args:
            endpoint: API endpoint path
            params: Optional query parameters
            **kwargs: Additional request arguments
            
        Returns:
            Response data dictionary
        """
        return self._retry_request("get", endpoint, params=params, **kwargs)
    
    def post(
        self, endpoint: str, json_data: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Make POST request with validation and retry logic.
        
        Args:
            endpoint: API endpoint path
            json_data: Optional JSON data to send
            **kwargs: Additional request arguments
            
        Returns:
            Response data dictionary
        """
        return self._retry_request("post", endpoint, json=json_data, **kwargs)
    
    def put(
        self, endpoint: str, json_data: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Make PUT request with validation and retry logic.
        
        Args:
            endpoint: API endpoint path
            json_data: Optional JSON data to send
            **kwargs: Additional request arguments
            
        Returns:
            Response data dictionary
        """
        return self._retry_request("put", endpoint, json=json_data, **kwargs)
    
    def patch(
        self, endpoint: str, json_data: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Make PATCH request with validation and retry logic.
        
        Args:
            endpoint: API endpoint path
            json_data: Optional JSON data to send
            **kwargs: Additional request arguments
            
        Returns:
            Response data dictionary
        """
        return self._retry_request("patch", endpoint, json=json_data, **kwargs)
    
    def delete(self, endpoint: str, **kwargs: Any) -> bool:
        """
        Make DELETE request with validation and retry logic.
        
        Args:
            endpoint: API endpoint path
            **kwargs: Additional request arguments
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._retry_request("delete", endpoint, **kwargs)
            return True
        except LambdaAPIError:
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics."""
        avg_response_time = (
            (self.total_response_time / self.request_count * 1000) if self.request_count > 0 else 0.0
        )
        return {
            "request_count": self.request_count,
            "error_count": self.error_count,
            "retry_count": self.retry_count,
            "success_rate": (
                ((self.request_count - self.error_count) / self.request_count * 100)
                if self.request_count > 0
                else 0.0
            ),
            "average_response_time_ms": round(avg_response_time, 2),
            "total_response_time_ms": round(self.total_response_time * 1000, 2),
        }
    
    def close(self) -> None:
        """Close the HTTP client and release resources."""
        if hasattr(self, "client"):
            self.client.close()
            logger.debug("APIClient closed")
    
    def __enter__(self) -> APIClient:
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
