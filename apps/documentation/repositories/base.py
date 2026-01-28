"""Base repository class for documentation repositories.

This module provides a base class that extracts common patterns from
PagesRepository, EndpointsRepository, RelationshipsRepository, and PostmanRepository.
"""

import logging
from typing import Any, Dict, List, Optional
from django.conf import settings
from apps.documentation.repositories.s3_json_storage import S3JSONStorage
from apps.documentation.utils.s3_index_manager import S3IndexManager
from apps.core.exceptions import RepositoryError

logger = logging.getLogger(__name__)


class BaseRepository:
    """Base repository class for documentation operations using S3 JSON storage.
    
    Provides common initialization patterns, error handling, and helper methods
    that are shared across all documentation repositories.
    
    Subclasses should:
    1. Set `resource_name` (e.g., "pages", "endpoints")
    2. Implement `_get_resource_key()` method
    3. Optionally override `_get_resource_id_field()` if ID field name differs
    """
    
    def __init__(
        self,
        resource_name: str,
        storage: Optional[S3JSONStorage] = None,
        index_manager: Optional[S3IndexManager] = None,
    ):
        """
        Initialize base repository.
        
        Args:
            resource_name: Name of the resource (e.g., "pages", "endpoints")
            storage: Optional S3JSONStorage instance. If not provided, uses shared instance.
            index_manager: Optional S3IndexManager instance. If not provided, uses shared instance.
        """
        self.resource_name = resource_name
        
        # Initialize storage
        if storage is None:
            from apps.documentation.services import get_shared_s3_storage
            self.storage = get_shared_s3_storage()
        else:
            self.storage = storage
        
        # Initialize index manager
        if index_manager is None:
            from apps.documentation.services import get_shared_s3_index_manager
            self.index_manager = get_shared_s3_index_manager()
        else:
            self.index_manager = index_manager
        
        # Set up prefixes
        self.data_prefix = settings.S3_DATA_PREFIX
        self.resource_prefix = f"{self.data_prefix}{resource_name}/"
        
        # Set up logger
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def _get_resource_key(self, resource_id: str) -> str:
        """
        Get S3 key for resource JSON file.
        
        Subclasses should override this if they have a different key pattern.
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            S3 key string
        """
        return f"{self.resource_prefix}{resource_id}.json"
    
    def _get_resource_id_field(self) -> str:
        """
        Get the field name used for resource ID in the data dictionary.
        
        Subclasses can override this if they use a different field name.
        Defaults to "{resource_name}_id" (e.g., "page_id", "endpoint_id").
        
        Returns:
            Field name string
        """
        return f"{self.resource_name.rstrip('s')}_id"  # e.g., "page_id", "endpoint_id"
    
    def _ensure_id_field(self, resource_data: Dict[str, Any], resource_id: str) -> Dict[str, Any]:
        """
        Ensure the resource data has an _id field for MongoDB compatibility.
        
        Args:
            resource_data: Resource data dictionary
            resource_id: Resource identifier
            
        Returns:
            Resource data dictionary with _id field ensured
        """
        if "_id" not in resource_data:
            id_field = self._get_resource_id_field()
            resource_data["_id"] = resource_data.get(id_field, resource_id)
        return resource_data
    
    def get_by_id(
        self,
        resource_id: str,
        **filters
    ) -> Optional[Dict[str, Any]]:
        """
        Generic method to get a resource by ID.
        
        Args:
            resource_id: Resource identifier
            **filters: Additional filters (e.g., page_type, api_version)
            
        Returns:
            Resource data dictionary or None if not found
            
        Raises:
            ValueError: If resource_id is not provided
            RepositoryError: If retrieval fails
        """
        if not resource_id:
            raise ValueError(f"{self.resource_name.rstrip('s')}_id is required")
        
        try:
            resource_key = self._get_resource_key(resource_id)
            resource_data = self.storage.read_json(resource_key)
            if not resource_data:
                return None
            
            # Apply filters if provided
            for filter_key, filter_value in filters.items():
                if resource_data.get(filter_key) != filter_value:
                    return None
            
            # Ensure _id field exists
            resource_data = self._ensure_id_field(resource_data, resource_id)
            
            return resource_data
            
        except Exception as e:
            error_msg = f"Failed to get {self.resource_name.rstrip('s')} {resource_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            # RepositoryError can accept message as positional or keyword argument
            try:
                raise RepositoryError(
                    message=error_msg,
                    entity_id=resource_id,
                    operation=f"get_by_id",
                    error_code="GET_FAILED"
                ) from e
            except TypeError:
                # Fallback for older RepositoryError signature
                raise RepositoryError(error_msg) from e
    
    def list_all(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        **filters
    ) -> List[Dict[str, Any]]:
        """
        Generic method to list all resources with optional filters.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            **filters: Filter criteria (e.g., api_version, method, status)
            
        Returns:
            List of resource data dictionaries
        """
        try:
            index_data = self.index_manager.read_index(self.resource_name)
            resources = index_data.get(self.resource_name, [])
            
            # Apply filters
            filtered = []
            for resource in resources:
                match = True
                for filter_key, filter_value in filters.items():
                    resource_value = resource.get(filter_key)
                    # Handle case-insensitive string comparison for method fields
                    if isinstance(resource_value, str) and isinstance(filter_value, str):
                        if resource_value.upper() != filter_value.upper():
                            match = False
                            break
                    elif resource_value != filter_value:
                        match = False
                        break
                
                if match:
                    filtered.append(resource)
            
            # Apply pagination
            if limit is not None:
                filtered = filtered[offset:offset + limit]
            else:
                filtered = filtered[offset:]
            
            return filtered
            
        except Exception as e:
            error_msg = f"Failed to list {self.resource_name}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise RepositoryError(error_msg) from e
