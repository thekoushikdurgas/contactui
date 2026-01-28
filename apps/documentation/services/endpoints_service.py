"""Endpoints Service with multi-strategy pattern (Local → S3 → Lambda)."""

import logging
from typing import Optional, Dict, Any, List
from apps.documentation.services.base import DocumentationServiceBase
from apps.documentation.repositories.unified_storage import UnifiedStorage
from apps.documentation.repositories.endpoints_repository import EndpointsRepository
from apps.documentation.utils.retry import retry_on_network_error
from apps.documentation.utils.exceptions import DocumentationError

logger = logging.getLogger(__name__)


class EndpointsService(DocumentationServiceBase):
    """Service for endpoints operations with multi-strategy pattern using UnifiedStorage."""

    def __init__(
        self,
        unified_storage: Optional[UnifiedStorage] = None,
        repository: Optional[EndpointsRepository] = None
    ):
        """Initialize endpoints service.

        Args:
            unified_storage: Optional UnifiedStorage instance. If not provided, creates new one.
            repository: Optional EndpointsRepository instance. If not provided, creates new one.
        """
        # Initialize base class with common patterns (Task 2.3.2)
        super().__init__(
            service_name="EndpointsService",
            unified_storage=unified_storage,
            repository=repository or EndpointsRepository(),
            resource_name="endpoints"
        )
    
    def get_endpoint(self, endpoint_id: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get endpoint by ID with multi-strategy:
        1. Try Local JSON files
        2. Fallback to S3
        3. Fallback to Lambda API

        Uses DocumentationServiceBase._get_resource() for common patterns (Task 2.3.2).

        Args:
            endpoint_id: Endpoint identifier
            use_cache: Whether to use cache (default True). For API compatibility;
                storage layer cache is still used when True.
        """
        return self._get_resource(
            resource_id=endpoint_id,
            operation_name='get_endpoint',
            storage_method='get_endpoint',
            use_cache=use_cache
        )

    def get_endpoints_bulk(
        self,
        endpoint_ids: List[str],
        use_cache: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """
        Fetch multiple endpoints by ID. Returns dict mapping endpoint_id -> endpoint data.
        
        Args:
            endpoint_ids: List of endpoint identifiers
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Dictionary mapping endpoint_id to endpoint data
            
        Raises:
            DocumentationError: If retrieval fails after retries
        """
        try:
            # Retry logic for external API calls
            @retry_on_network_error(max_retries=3, initial_delay=1.0)
            def _get_endpoints_bulk_with_retry():
                return self.unified_storage.get_endpoints_bulk(endpoint_ids)
            
            result = _get_endpoints_bulk_with_retry()
            return result
            
        except Exception as e:
            error_response = self._handle_error(
                e,
                context=f"Failed to get endpoints bulk (count: {len(endpoint_ids)})",
                record_monitoring=True
            )
            raise DocumentationError(
                f"Failed to retrieve endpoints: {error_response.get('error', str(e))}"
            ) from e
    
    def list_endpoints(
        self,
        api_version: Optional[str] = None,
        method: Optional[str] = None,
        endpoint_state: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        List endpoints with multi-strategy.
        
        Uses DocumentationServiceBase._list_resources() for common patterns (Task 2.3.2).
        1. Try Local JSON files
        2. Fallback to S3
        3. Fallback to Lambda API
        
        Args:
            api_version: Optional API version filter
            method: Optional HTTP method filter
            endpoint_state: Optional endpoint state filter
            limit: Maximum number of results
            offset: Number of results to skip
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Dictionary with 'endpoints' list and 'total' count
            
        Raises:
            DocumentationError: If retrieval fails after retries
        """
        return self._list_resources(
            operation_name='list_endpoints',
            storage_method='list_endpoints',
            use_cache=use_cache,
            api_version=api_version,
            method=method,
            endpoint_state=endpoint_state,
            limit=limit,
            offset=offset
        )

    def get_endpoint_by_id(self, endpoint_id: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Alias for get_endpoint for Lambda API parity."""
        return self.get_endpoint(endpoint_id, use_cache=use_cache)

    def get_endpoint_by_path(
        self, endpoint_path: str, method: str, use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Get endpoint documentation by path and method."""
        return self.unified_storage.get_endpoint_by_path_and_method(endpoint_path, method)

    def get_endpoints_by_api_version(self, api_version: str) -> List[Dict[str, Any]]:
        """Get all endpoints for a specific API version."""
        return self.unified_storage.get_endpoints_by_api_version(api_version)

    def get_endpoints_by_method(self, method: str) -> List[Dict[str, Any]]:
        """Get all endpoints for a specific HTTP/GraphQL method."""
        return self.unified_storage.get_endpoints_by_method(method)

    def count_endpoints_by_api_version(self, api_version: str) -> int:
        """Count endpoints by API version."""
        return self.unified_storage.count_endpoints_by_api_version(api_version)

    def count_endpoints_by_method(self, method: str) -> int:
        """Count endpoints by method."""
        return self.unified_storage.count_endpoints_by_method(method)

    def get_api_version_statistics(self) -> Dict[str, Any]:
        """Get statistics for all API versions."""
        return self.unified_storage.get_api_version_statistics()

    def get_method_statistics(self) -> Dict[str, Any]:
        """Get statistics for all HTTP/GraphQL methods."""
        return self.unified_storage.get_method_statistics()

    def get_pages_using_endpoint(
        self, endpoint_path: str, method: str
    ) -> List[Dict[str, Any]]:
        """Get all pages using a specific endpoint."""
        endpoint = self.unified_storage.get_endpoint_by_path_and_method(endpoint_path, method)
        if not endpoint:
            return []
        return endpoint.get("used_by_pages") or []
    
    def create_endpoint(self, endpoint_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create endpoint with data transformation (use S3 direct for writes).
        
        Uses DocumentationServiceBase._create_resource() for common patterns (Task 2.3.4).
        
        Args:
            endpoint_data: Endpoint data dictionary
            
        Returns:
            Created endpoint data dictionary or None if creation failed
            
        Raises:
            ValueError: If endpoint data is invalid
            DocumentationError: If creation fails after retries
        """
        # Validate required fields
        required_fields = ['endpoint_id', 'method', 'path']
        is_valid, error_msg = self._validate_input(endpoint_data, required_fields)
        if not is_valid:
            raise ValueError(error_msg)
        
        return self._create_resource(
            resource_data=endpoint_data,
            operation_name='create_endpoint'
        )

    def update_endpoint(self, endpoint_id: str, endpoint_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update endpoint with data transformation (use S3 direct for writes).
        
        Uses DocumentationServiceBase._update_resource() for common patterns (Task 2.3.4).
        
        Args:
            endpoint_id: Endpoint identifier
            endpoint_data: Endpoint data dictionary (partial updates supported)
            
        Returns:
            Updated endpoint data dictionary or None if update failed
            
        Raises:
            ValueError: If endpoint not found
            DocumentationError: If update fails after retries
        """
        # Check if endpoint exists (use_cache=False to avoid stale cache before update)
        existing = self.get_endpoint(endpoint_id, use_cache=False)
        if not existing:
            raise ValueError(f"Endpoint not found: {endpoint_id}")
        
        return self._update_resource(
            resource_id=endpoint_id,
            resource_data=endpoint_data,
            operation_name='update_endpoint'
        )

    def delete_endpoint(self, endpoint_id: str) -> bool:
        """
        Delete endpoint (use S3 direct for writes).
        
        Uses DocumentationServiceBase._delete_resource() for common patterns (Task 2.3.4).
        
        Args:
            endpoint_id: Endpoint identifier
            
        Returns:
            True if deletion was successful, False otherwise
            
        Raises:
            DocumentationError: If deletion fails after retries
        """
        return self._delete_resource(
            resource_id=endpoint_id,
            operation_name='delete_endpoint'
        )
    
    def _clear_cache_for_endpoint(self, endpoint_id: str) -> None:
        """
        Clear cache entries for a specific endpoint.
        
        Args:
            endpoint_id: Endpoint identifier
        """
        try:
            # Use UnifiedStorage's pattern-based cache clearing
            self.unified_storage.clear_cache('endpoints', endpoint_id)
            self.unified_storage.clear_cache('endpoints')
        except Exception as e:
            self.logger.warning(f"Failed to clear cache for endpoint {endpoint_id}: {e}")
    
    def get_endpoints_by_api_version(self, api_version: str, method: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get endpoints by API version (use S3 direct like PagesService)."""
        try:
            endpoints = self.repository.list_all(api_version=api_version, method=method)
            return endpoints
        except Exception as e:
            logger.warning(f"Repository failed for get_endpoints_by_api_version: {e}")
            # Fallback to unified storage
            result = self.unified_storage.list_endpoints(api_version=api_version, method=method)
            return result.get('endpoints', [])

    def get_endpoints_by_method(self, method: str) -> List[Dict[str, Any]]:
        """Get endpoints by method (use S3 direct like PagesService)."""
        try:
            endpoints = self.repository.list_all(method=method)
            return endpoints
        except Exception as e:
            logger.warning(f"Repository failed for get_endpoints_by_method: {e}")
            # Fallback to unified storage
            result = self.unified_storage.list_endpoints(method=method)
            return result.get('endpoints', [])

    def get_endpoints_by_version_and_method(self, api_version: str, method: str) -> List[Dict[str, Any]]:
        """Get endpoints by both API version and method (use S3 direct like PagesService)."""
        try:
            endpoints = self.repository.list_all(api_version=api_version, method=method)
            return endpoints
        except Exception as e:
            logger.warning(f"Repository failed for get_endpoints_by_version_and_method: {e}")
            return self.get_endpoints_by_api_version(api_version, method=method)
    
    def count_endpoints_by_api_version(self, api_version: str) -> int:
        """Count endpoints by API version (use S3 direct like PagesService)."""
        try:
            endpoints = self.repository.list_all(api_version=api_version)
            return len(endpoints)
        except Exception as e:
            logger.warning(f"Repository failed for count_endpoints_by_api_version: {e}")
            # Fallback
            result = self.list_endpoints(api_version=api_version, limit=1)
            return result.get('total', 0)

    def count_endpoints_by_method(self, method: str) -> int:
        """Count endpoints by method (use S3 direct like PagesService)."""
        try:
            endpoints = self.repository.list_all(method=method)
            return len(endpoints)
        except Exception as e:
            logger.warning(f"Repository failed for count_endpoints_by_method: {e}")
            # Fallback
            result = self.list_endpoints(method=method, limit=1)
            return result.get('total', 0)
    
    def get_api_version_statistics(self) -> Dict[str, Any]:
        """Get API version statistics (use S3 direct like PagesService)."""
        try:
            # Get all endpoints and calculate statistics
            all_endpoints = self.repository.list_all()
            version_counts = {}

            for endpoint in all_endpoints:
                api_version = endpoint.get('api_version', 'unknown')
                if api_version not in version_counts:
                    version_counts[api_version] = 0
                version_counts[api_version] += 1

            versions = [
                {'api_version': version, 'count': count}
                for version, count in version_counts.items()
            ]

            return {
                'versions': versions,
                'total': len(versions)
            }
        except Exception as e:
            logger.warning(f"Repository failed for get_api_version_statistics: {e}")
            # Fallback: return empty
            return {'versions': [], 'total': 0}

    def get_method_statistics(self) -> Dict[str, Any]:
        """Get method statistics (use S3 direct like PagesService)."""
        try:
            # Get all endpoints and calculate statistics
            all_endpoints = self.repository.list_all()
            method_counts = {}

            for endpoint in all_endpoints:
                method = endpoint.get('method', 'unknown')
                if method not in method_counts:
                    method_counts[method] = 0
                method_counts[method] += 1

            methods = [
                {'method': method, 'count': count}
                for method, count in method_counts.items()
            ]

            return {
                'methods': methods,
                'total': len(methods)
            }
        except Exception as e:
            logger.warning(f"Repository failed for get_method_statistics: {e}")
            # Fallback: return empty
            return {'methods': [], 'total': 0}
    
    def get_endpoint_pages(self, endpoint_id: str) -> Dict[str, Any]:
        """
        Get all pages using a specific endpoint.
        
        Uses relationships service to find pages that use this endpoint.
        
        Args:
            endpoint_id: Endpoint identifier
            
        Returns:
            Dictionary with 'pages' list
            
        Raises:
            DocumentationError: If retrieval fails after retries
        """
        try:
            # Use relationships service to find pages using this endpoint
            from apps.documentation.services import relationships_service
            
            relationships_result = relationships_service.list_relationships(
                endpoint_id=endpoint_id,
                limit=1000  # Get all relationships for this endpoint
            )
            
            if not relationships_result or not relationships_result.get('relationships'):
                return {'pages': []}
            
            # Extract unique page IDs from relationships
            page_ids = set()
            pages = []
            
            for rel in relationships_result.get('relationships', []):
                page_id = rel.get('page_id') or rel.get('page_path')
                if page_id and page_id not in page_ids:
                    page_ids.add(page_id)
                    # Get page details
                    from apps.documentation.services import pages_service
                    page = pages_service.get_page(page_id)
                    if page:
                        pages.append(page)
            
            return {'pages': pages}
            
        except Exception as e:
            error_response = self._handle_error(
                e,
                context=f"Failed to get pages for endpoint {endpoint_id}",
                record_monitoring=True
            )
            raise DocumentationError(
                f"Failed to get endpoint pages: {error_response.get('error', str(e))}"
            ) from e
    
    def get_endpoints_by_state(
        self,
        state: str,
        api_version: Optional[str] = None,
        method: Optional[str] = None,
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get all endpoints filtered by state.
        
        Args:
            state: Endpoint state filter (published, draft, coming_soon, development, test)
            api_version: Optional API version filter
            method: Optional HTTP/GraphQL method filter
            use_cache: Whether to use cache (default: True)
            
        Returns:
            List of endpoint dictionaries matching the state
        """
        result = self.list_endpoints(
            api_version=api_version,
            method=method,
            endpoint_state=state,
            limit=None,
            offset=0,
            use_cache=use_cache,
        )
        return result.get("endpoints", [])
    
    def count_endpoints_by_state(
        self,
        state: str,
        api_version: Optional[str] = None,
        method: Optional[str] = None,
    ) -> int:
        """
        Count endpoints by state.
        
        Args:
            state: Endpoint state filter
            api_version: Optional API version filter
            method: Optional HTTP/GraphQL method filter
            
        Returns:
            Number of endpoints matching the state
        """
        try:
            result = self.list_endpoints(
                api_version=api_version,
                method=method,
                endpoint_state=state,
                limit=None,
                offset=0,
                use_cache=True,
            )
            return result.get("total", 0)
        except Exception as e:
            self.logger.warning(f"count_endpoints_by_state failed: {e}")
            return 0
    
    def get_endpoints_by_lambda_service(
        self,
        service_name: str,
        api_version: Optional[str] = None,
        method: Optional[str] = None,
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get all endpoints filtered by Lambda service.
        
        Args:
            service_name: Lambda service name
            api_version: Optional API version filter
            method: Optional HTTP/GraphQL method filter
            use_cache: Whether to use cache (default: True)
            
        Returns:
            List of endpoint dictionaries for the Lambda service
        """
        # Get all endpoints and filter by lambda_service field
        result = self.list_endpoints(
            api_version=api_version,
            method=method,
            limit=None,
            offset=0,
            use_cache=use_cache,
        )
        endpoints = result.get("endpoints", [])
        
        # Filter by lambda_service
        filtered = []
        for endpoint in endpoints:
            lambda_services = endpoint.get("lambda_services", [])
            if isinstance(lambda_services, list):
                if any(ls.get("service_name") == service_name for ls in lambda_services if isinstance(ls, dict)):
                    filtered.append(endpoint)
            elif isinstance(lambda_services, str) and lambda_services == service_name:
                filtered.append(endpoint)
        
        return filtered
    
    def count_endpoints_by_lambda_service(
        self,
        service_name: str,
        api_version: Optional[str] = None,
        method: Optional[str] = None,
    ) -> int:
        """
        Count endpoints by Lambda service.
        
        Args:
            service_name: Lambda service name
            api_version: Optional API version filter
            method: Optional HTTP/GraphQL method filter
            
        Returns:
            Number of endpoints for the Lambda service
        """
        endpoints = self.get_endpoints_by_lambda_service(
            service_name=service_name,
            api_version=api_version,
            method=method,
            use_cache=True,
        )
        return len(endpoints)
    
    def get_endpoint_access_control(self, endpoint_id: str) -> Optional[Dict[str, Any]]:
        """
        Get access_control sub-resource for an endpoint.
        
        Args:
            endpoint_id: Endpoint identifier
            
        Returns:
            Access control dictionary or None if endpoint not found
        """
        endpoint = self.get_endpoint(endpoint_id)
        if not endpoint:
            return None
        return endpoint.get("access_control")
    
    def get_endpoint_lambda_services(self, endpoint_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get Lambda services for an endpoint.
        
        Args:
            endpoint_id: Endpoint identifier
            
        Returns:
            List of Lambda service dictionaries or None if endpoint not found
        """
        endpoint = self.get_endpoint(endpoint_id)
        if not endpoint:
            return None
        lambda_services = endpoint.get("lambda_services", [])
        if isinstance(lambda_services, list):
            return lambda_services
        return []
    
    def get_endpoint_files(self, endpoint_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get service/router files for an endpoint.
        
        Args:
            endpoint_id: Endpoint identifier
            
        Returns:
            List of file dictionaries or None if endpoint not found
        """
        endpoint = self.get_endpoint(endpoint_id)
        if not endpoint:
            return None
        return endpoint.get("files", [])
    
    def get_endpoint_dependencies(self, endpoint_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get endpoint dependencies.
        
        Args:
            endpoint_id: Endpoint identifier
            
        Returns:
            List of dependency dictionaries or None if endpoint not found
        """
        endpoint = self.get_endpoint(endpoint_id)
        if not endpoint:
            return None
        return endpoint.get("dependencies", [])
    
    def get_endpoint_methods(self, endpoint_id: str) -> Optional[List[str]]:
        """
        Get methods for an endpoint (usually single method, but can be multiple).
        
        Args:
            endpoint_id: Endpoint identifier
            
        Returns:
            List of method strings or None if endpoint not found
        """
        endpoint = self.get_endpoint(endpoint_id)
        if not endpoint:
            return None
        method = endpoint.get("method")
        if method:
            return [method]
        return []
    
    def get_endpoint_used_by_pages(self, endpoint_id: str) -> List[Dict[str, Any]]:
        """
        Get pages that use this endpoint (alias for get_endpoint_pages).
        
        Args:
            endpoint_id: Endpoint identifier
            
        Returns:
            List of page dictionaries
        """
        result = self.get_endpoint_pages(endpoint_id)
        return result.get("pages", [])
