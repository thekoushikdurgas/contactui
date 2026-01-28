"""GraphQL Client Service for appointment360 GraphQL API."""

import json
import logging
import time
from typing import Optional, Dict, Any
from django.conf import settings
from django.core.cache import cache
import httpx

logger = logging.getLogger(__name__)


class GraphQLError(Exception):
    """Custom exception for GraphQL errors."""
    pass


class GraphQLClient:
    """Client for executing GraphQL queries and mutations."""
    
    def __init__(self, endpoint_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize GraphQL client.
        
        Args:
            endpoint_url: GraphQL endpoint URL (defaults to settings)
            api_key: API key for authentication (defaults to settings)
        """
        self.endpoint = endpoint_url or getattr(settings, 'APPOINTMENT360_GRAPHQL_URL', 'http://localhost:8000/graphql')
        self.api_key = api_key or getattr(settings, 'APPOINTMENT360_GRAPHQL_API_KEY', None)
        self.timeout = getattr(settings, 'GRAPHQL_TIMEOUT', 30)
        self.max_retries = getattr(settings, 'GRAPHQL_MAX_RETRIES', 3)
        self.retry_delay = getattr(settings, 'GRAPHQL_RETRY_DELAY', 1)  # seconds
        self.client = httpx.Client(timeout=self.timeout)
        
        logger.info(f"GraphQLClient initialized with endpoint: {self.endpoint}")
        logger.debug(f"API Key configured: {bool(self.api_key)}")
        logger.debug(f"Retry settings: max_retries={self.max_retries}, retry_delay={self.retry_delay}s")
    
    def _get_headers(self, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Get default headers for GraphQL requests."""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        if additional_headers:
            headers.update(additional_headers)
        
        return headers
    
    def _get_cache_key(self, query: str, variables: Optional[Dict] = None) -> str:
        """Generate cache key for query."""
        cache_data = {
            'query': query,
            'variables': variables or {}
        }
        return f"graphql:{hash(json.dumps(cache_data, sort_keys=True))}"
    
    def execute_query(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        use_cache: bool = True,
        cache_timeout: int = 300
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a GraphQL query with retry logic and caching.
        
        Args:
            query: GraphQL query string
            variables: Query variables
            headers: Additional headers
            use_cache: Whether to use response caching
            cache_timeout: Cache timeout in seconds
            
        Returns:
            Response data dictionary, or None if error
        """
        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(query, variables)
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                logger.debug(f"Cache hit for query: {query[:50]}...")
                return cached_response
        
        payload = {
            'query': query,
        }
        
        if variables:
            payload['variables'] = variables
        
        # Retry logic with exponential backoff
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    delay = self.retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                    logger.warning(f"Retrying GraphQL query (attempt {attempt + 1}/{self.max_retries}) after {delay}s delay...")
                    time.sleep(delay)
                
                logger.debug(f"Executing GraphQL query (attempt {attempt + 1}): {query[:100]}...")
                
                response = self.client.post(
                    self.endpoint,
                    headers=self._get_headers(headers),
                    json=payload
                )
                
                response.raise_for_status()
                result = response.json()
                
                # Validate response structure
                if not isinstance(result, dict):
                    raise GraphQLError(f"Invalid response format: expected dict, got {type(result)}")
                
                if 'errors' in result:
                    error_messages = [err.get('message', str(err)) for err in result['errors']]
                    error_details = [err.get('extensions', {}) for err in result['errors']]
                    logger.error(f"GraphQL errors: {error_messages}")
                    logger.debug(f"GraphQL error details: {error_details}")
                    raise GraphQLError(f"GraphQL query failed: {', '.join(error_messages)}")
                
                # Cache successful response
                if use_cache and 'data' in result:
                    cache_key = self._get_cache_key(query, variables)
                    cache.set(cache_key, result, cache_timeout)
                    logger.debug(f"Cached response for query: {query[:50]}...")
                
                return result.get('data')
                
            except httpx.TimeoutException as e:
                last_exception = e
                logger.warning(f"GraphQL query timeout (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt == self.max_retries - 1:
                    logger.error(f"GraphQL query failed after {self.max_retries} attempts due to timeout")
                    return None
                    
            except httpx.HTTPStatusError as e:
                last_exception = e
                status_code = e.response.status_code
                # Retry on 5xx errors, but not on 4xx errors
                if status_code >= 500 and attempt < self.max_retries - 1:
                    logger.warning(f"GraphQL server error {status_code} (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                    continue
                else:
                    logger.error(f"GraphQL HTTP error {status_code}: {str(e)}")
                    return None
                    
            except httpx.HTTPError as e:
                last_exception = e
                logger.warning(f"GraphQL HTTP error (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt == self.max_retries - 1:
                    logger.error(f"GraphQL query failed after {self.max_retries} attempts")
                    return None
                    
            except GraphQLError:
                # Don't retry on GraphQL errors (client errors)
                raise
                
            except Exception as e:
                last_exception = e
                logger.warning(f"Unexpected error executing GraphQL query (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt == self.max_retries - 1:
                    logger.error(f"GraphQL query failed after {self.max_retries} attempts", exc_info=True)
                    return None
        
        # If we get here, all retries failed
        if last_exception:
            logger.error(f"GraphQL query failed after {self.max_retries} attempts. Last error: {str(last_exception)}")
        return None
    
    def execute_mutation(
        self,
        mutation: str,
        variables: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a GraphQL mutation with retry logic.
        
        Args:
            mutation: GraphQL mutation string
            variables: Mutation variables
            headers: Additional headers
            
        Returns:
            Response data dictionary, or None if error
        """
        payload = {
            'query': mutation,
        }
        
        if variables:
            payload['variables'] = variables
        
        # Retry logic for mutations (fewer retries, mutations should be idempotent)
        max_mutation_retries = min(self.max_retries, 2)  # Max 2 retries for mutations
        last_exception = None
        
        for attempt in range(max_mutation_retries):
            try:
                if attempt > 0:
                    delay = self.retry_delay * (2 ** (attempt - 1))
                    logger.warning(f"Retrying GraphQL mutation (attempt {attempt + 1}/{max_mutation_retries}) after {delay}s delay...")
                    time.sleep(delay)
                
                logger.debug(f"Executing GraphQL mutation (attempt {attempt + 1}): {mutation[:100]}...")
                
                response = self.client.post(
                    self.endpoint,
                    headers=self._get_headers(headers),
                    json=payload
                )
                
                response.raise_for_status()
                result = response.json()
                
                # Validate response structure
                if not isinstance(result, dict):
                    raise GraphQLError(f"Invalid response format: expected dict, got {type(result)}")
                
                if 'errors' in result:
                    error_messages = [err.get('message', str(err)) for err in result['errors']]
                    error_details = [err.get('extensions', {}) for err in result['errors']]
                    logger.error(f"GraphQL errors: {error_messages}")
                    logger.debug(f"GraphQL error details: {error_details}")
                    raise GraphQLError(f"GraphQL mutation failed: {', '.join(error_messages)}")
                
                return result.get('data')
                
            except httpx.TimeoutException as e:
                last_exception = e
                logger.warning(f"GraphQL mutation timeout (attempt {attempt + 1}/{max_mutation_retries}): {str(e)}")
                if attempt == max_mutation_retries - 1:
                    logger.error(f"GraphQL mutation failed after {max_mutation_retries} attempts due to timeout")
                    return None
                    
            except httpx.HTTPStatusError as e:
                last_exception = e
                status_code = e.response.status_code
                # Retry on 5xx errors, but not on 4xx errors
                if status_code >= 500 and attempt < max_mutation_retries - 1:
                    logger.warning(f"GraphQL server error {status_code} (attempt {attempt + 1}/{max_mutation_retries}): {str(e)}")
                    continue
                else:
                    logger.error(f"GraphQL HTTP error {status_code}: {str(e)}")
                    return None
                    
            except httpx.HTTPError as e:
                last_exception = e
                logger.warning(f"GraphQL HTTP error (attempt {attempt + 1}/{max_mutation_retries}): {str(e)}")
                if attempt == max_mutation_retries - 1:
                    logger.error(f"GraphQL mutation failed after {max_mutation_retries} attempts")
                    return None
                    
            except GraphQLError:
                # Don't retry on GraphQL errors (client errors)
                raise
                
            except Exception as e:
                last_exception = e
                logger.warning(f"Unexpected error executing GraphQL mutation (attempt {attempt + 1}/{max_mutation_retries}): {str(e)}")
                if attempt == max_mutation_retries - 1:
                    logger.error(f"GraphQL mutation failed after {max_mutation_retries} attempts", exc_info=True)
                    return None
        
        # If we get here, all retries failed
        if last_exception:
            logger.error(f"GraphQL mutation failed after {max_mutation_retries} attempts. Last error: {str(last_exception)}")
        return None
    
    def clear_cache(self, query: Optional[str] = None, variables: Optional[Dict] = None):
        """Clear cache for a specific query or all queries."""
        if query:
            cache_key = self._get_cache_key(query, variables)
            cache.delete(cache_key)
            logger.debug(f"Cleared cache for query: {query[:50]}...")
        else:
            logger.warning("Clearing all GraphQL cache - this may affect other queries")
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
