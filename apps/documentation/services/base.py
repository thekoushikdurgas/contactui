"""Base service class for documentation services.

This module provides DocumentationServiceBase which extracts common patterns
from PagesService, EndpointsService, RelationshipsService, and PostmanService
to reduce code duplication (Task 2.3.2).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, TypeVar, Generic

from apps.core.services.base_service import BaseService
from apps.documentation.repositories.unified_storage import UnifiedStorage
from apps.documentation.utils.retry import retry_on_network_error
from apps.documentation.utils.exceptions import DocumentationError

# Import cache TTL config if available
try:
    from apps.core.utils.redis_cache import CACHE_TTL_CONFIG
except ImportError:
    CACHE_TTL_CONFIG = {}

logger = logging.getLogger(__name__)

T = TypeVar('T')  # Resource type


class DocumentationServiceBase(BaseService, Generic[T]):
    """Base class for documentation services with common patterns.
    
    Provides common initialization, caching, retry logic, and CRUD operations
    for PagesService, EndpointsService, RelationshipsService, and PostmanService.
    """
    
    def __init__(
        self,
        service_name: str,
        unified_storage: Optional[UnifiedStorage] = None,
        repository: Optional[Any] = None,
        resource_name: Optional[str] = None
    ):
        """
        Initialize documentation service base.
        
        Args:
            service_name: Name of the service (e.g., "PagesService")
            unified_storage: Optional UnifiedStorage instance
            repository: Optional repository instance for write operations
            resource_name: Name of the resource (e.g., "pages", "endpoints")
        """
        super().__init__(service_name)
        self.resource_name = resource_name or service_name.lower().replace("service", "")
        
        # Initialize unified storage (shared singleton)
        if unified_storage is None:
            from apps.documentation.services import get_shared_unified_storage
            self.unified_storage = get_shared_unified_storage()
        else:
            self.unified_storage = unified_storage
        
        # Initialize repository for write operations
        self.repository = repository
        
        # Cache timeout (5 minutes default)
        self.cache_timeout = 300
    
    def _get_resource(
        self,
        resource_id: str,
        operation_name: str,
        storage_method: str,
        use_cache: bool = True,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Generic method to get a single resource with caching and retry logic.
        
        Args:
            resource_id: Resource identifier
            operation_name: Name of the operation for cache key (e.g., 'get_page')
            storage_method: Method name on unified_storage (e.g., 'get_page')
            use_cache: Whether to use cache
            **kwargs: Additional arguments to pass to storage method
            
        Returns:
            Resource data dictionary or None if not found
            
        Raises:
            DocumentationError: If retrieval fails after retries
        """
        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(operation_name, resource_id, **kwargs)
            cached = self._get_from_cache(cache_key)
            if cached is not None:
                self.logger.debug(f"Cache hit for {operation_name}: {resource_id}")
                return cached
        
        try:
            # Retry logic for external API calls
            @retry_on_network_error(max_retries=3, initial_delay=1.0)
            def _get_with_retry():
                method = getattr(self.unified_storage, storage_method)
                return method(resource_id, **kwargs)
            
            result = _get_with_retry()
            
            # Cache the result
            if use_cache and result is not None:
                cache_key = self._get_cache_key(operation_name, resource_id, **kwargs)
                self._set_cache(cache_key, result, timeout=self.cache_timeout, data_type='detail')
            
            return result
            
        except Exception as e:
            error_response = self._handle_error(
                e,
                context=f"Failed to get {self.resource_name} {resource_id}",
                record_monitoring=True
            )
            raise DocumentationError(
                f"Failed to retrieve {self.resource_name} {resource_id}: {error_response.get('error', str(e))}"
            ) from e
    
    def _list_resources(
        self,
        operation_name: str,
        storage_method: str,
        use_cache: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generic method to list resources with caching and retry logic.
        
        Args:
            operation_name: Name of the operation for cache key (e.g., 'list_pages')
            storage_method: Method name on unified_storage (e.g., 'list_pages')
            use_cache: Whether to use cache
            **kwargs: Additional arguments to pass to storage method
            
        Returns:
            Dictionary with resource list and 'total' count
            
        Raises:
            DocumentationError: If retrieval fails after retries
        """
        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(operation_name, **kwargs)
            cached = self._get_from_cache(cache_key)
            if cached is not None:
                self.logger.debug(f"Cache hit for {operation_name}")
                return cached
        
        try:
            # Retry logic for external API calls
            @retry_on_network_error(max_retries=3, initial_delay=1.0)
            def _list_with_retry():
                method = getattr(self.unified_storage, storage_method)
                return method(**kwargs)
            
            result = _list_with_retry()
            
            # Ensure consistent return format
            resource_key = f"{self.resource_name}s"  # e.g., "pages", "endpoints"
            if resource_key not in result:
                result[resource_key] = []
            if 'total' not in result:
                result['total'] = len(result.get(resource_key, []))
            
            # Cache the result (shorter TTL for list operations)
            if use_cache:
                cache_key = self._get_cache_key(operation_name, **kwargs)
                # Use dynamic TTL for list operations (2 minutes)
                self._set_cache(cache_key, result, timeout=120, data_type='list')
            
            return result
            
        except Exception as e:
            error_response = self._handle_error(
                e,
                context=f"Failed to list {self.resource_name}s",
                record_monitoring=True
            )
            raise DocumentationError(
                f"Failed to list {self.resource_name}s: {error_response.get('error', str(e))}"
            ) from e
    
    def _create_resource(
        self,
        resource_data: Dict[str, Any],
        operation_name: str,
        repository_method: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generic method to create a resource.
        
        Args:
            resource_data: Resource data dictionary
            operation_name: Name of the operation for logging
            repository_method: Optional repository method name (defaults to 'create_{resource_name}')
            
        Returns:
            Created resource data dictionary or None if failed
            
        Raises:
            DocumentationError: If creation fails
        """
        if not self.repository:
            raise DocumentationError(f"Repository not initialized for {self.name}")
        
        try:
            if repository_method:
                method = getattr(self.repository, repository_method)
            else:
                method_name = f"create_{self.resource_name.rstrip('s')}"  # e.g., "create_page"
                method = getattr(self.repository, method_name, None)
                if not method:
                    # Fallback to generic create
                    method = getattr(self.repository, 'create', None)
            
            if not method:
                raise DocumentationError("Create method not found in repository")
            
            result = method(resource_data)
            
            # Clear cache for this resource and list operations
            if result:
                resource_id = result.get('id') or result.get(f"{self.resource_name.rstrip('s')}_id")
                if resource_id:
                    self._clear_resource_cache(resource_id)
            self._clear_list_cache()
            
            self.logger.info(f"{operation_name} created successfully: {resource_data.get('id')}")
            return result
            
        except Exception as e:
            error_response = self._handle_error(
                e,
                context=f"Failed to create {self.resource_name}",
                record_monitoring=True
            )
            raise DocumentationError(
                f"Failed to create {self.resource_name}: {error_response.get('error', str(e))}"
            ) from e
    
    def _update_resource(
        self,
        resource_id: str,
        resource_data: Dict[str, Any],
        operation_name: str,
        repository_method: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generic method to update a resource.
        
        Args:
            resource_id: Resource identifier
            resource_data: Updated resource data dictionary
            operation_name: Name of the operation for logging
            repository_method: Optional repository method name
            
        Returns:
            Updated resource data dictionary or None if failed
            
        Raises:
            DocumentationError: If update fails
        """
        if not self.repository:
            raise DocumentationError(f"Repository not initialized for {self.name}")
        
        try:
            if repository_method:
                method = getattr(self.repository, repository_method)
            else:
                method_name = f"update_{self.resource_name.rstrip('s')}"  # e.g., "update_page"
                method = getattr(self.repository, method_name, None)
                if not method:
                    # Fallback to generic update
                    method = getattr(self.repository, 'update', None)
            
            if not method:
                raise DocumentationError("Update method not found in repository")
            
            result = method(resource_id, resource_data)
            
            # Clear cache for this resource and list operations
            self._clear_resource_cache(resource_id)
            self._clear_list_cache()
            
            self.logger.info(f"{operation_name} updated successfully: {resource_id}")
            return result
            
        except Exception as e:
            error_response = self._handle_error(
                e,
                context=f"Failed to update {self.resource_name} {resource_id}",
                record_monitoring=True
            )
            raise DocumentationError(
                f"Failed to update {self.resource_name} {resource_id}: {error_response.get('error', str(e))}"
            ) from e
    
    def _delete_resource(
        self,
        resource_id: str,
        operation_name: str,
        repository_method: Optional[str] = None
    ) -> bool:
        """
        Generic method to delete a resource.
        
        Args:
            resource_id: Resource identifier
            operation_name: Name of the operation for logging
            repository_method: Optional repository method name
            
        Returns:
            True if deleted successfully, False otherwise
            
        Raises:
            DocumentationError: If deletion fails
        """
        if not self.repository:
            raise DocumentationError(f"Repository not initialized for {self.name}")
        
        try:
            if repository_method:
                method = getattr(self.repository, repository_method)
            else:
                method_name = f"delete_{self.resource_name.rstrip('s')}"  # e.g., "delete_page"
                method = getattr(self.repository, method_name, None)
                if not method:
                    # Fallback to generic delete
                    method = getattr(self.repository, 'delete', None)
            
            if not method:
                raise DocumentationError("Delete method not found in repository")
            
            result = method(resource_id)
            
            # Clear cache for this resource and list operations
            self._clear_resource_cache(resource_id)
            self._clear_list_cache()
            
            self.logger.info(f"{operation_name} deleted successfully: {resource_id}")
            return result
            
        except Exception as e:
            error_response = self._handle_error(
                e,
                context=f"Failed to delete {self.resource_name} {resource_id}",
                record_monitoring=True
            )
            raise DocumentationError(
                f"Failed to delete {self.resource_name} {resource_id}: {error_response.get('error', str(e))}"
            ) from e
    
    def _clear_resource_cache(self, resource_id: str) -> None:
        """
        Clear cache for a specific resource.
        
        Uses UnifiedStorage's pattern-based cache clearing for consistency (Task 2.3.4).
        
        Args:
            resource_id: Resource identifier
        """
        try:
            # Use UnifiedStorage's pattern-based cache clearing (consistent with service methods)
            if hasattr(self, 'unified_storage') and self.unified_storage:
                self.unified_storage.clear_cache(self.resource_name, resource_id)
            else:
                # Fallback to direct cache key clearing
                cache_key = self._get_cache_key(f"get_{self.resource_name.rstrip('s')}", resource_id)
                self._clear_cache(cache_key)
        except Exception as e:
            self.logger.warning(f"Failed to clear resource cache: {e}")
    
    def _clear_list_cache(self) -> None:
        """
        Clear cache for list operations.
        
        Uses UnifiedStorage's pattern-based cache clearing for consistency (Task 2.3.4).
        """
        try:
            # Use UnifiedStorage's pattern-based cache clearing (consistent with service methods)
            if hasattr(self, 'unified_storage') and self.unified_storage:
                self.unified_storage.clear_cache(self.resource_name)
            self.logger.debug(f"List cache cleared for {self.resource_name}s")
        except Exception as e:
            self.logger.warning(f"Failed to clear list cache: {e}")
        except Exception as e:
            self.logger.warning(f"Failed to clear list cache: {e}")
