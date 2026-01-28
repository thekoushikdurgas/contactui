"""JSON Store service."""
import logging
from typing import Optional, Dict, Any, List
from apps.core.services.base_service import BaseService
from .json_store_storage_service import JSONStoreStorageService

logger = logging.getLogger(__name__)


class JSONStoreService(BaseService):
    """Service for JSON store operations using S3 storage."""
    
    def __init__(self):
        """Initialize JSON store service."""
        super().__init__('JSONStoreService')
        self.storage = JSONStoreStorageService()
    
    def save(
        self,
        key: str,
        data: Dict[str, Any],
        store_type: str = 'custom',
        description: str = '',
        user=None
    ) -> Dict[str, Any]:
        """
        Save JSON data.
        
        Args:
            key: Store key
            data: JSON data to store
            store_type: Type of store
            description: Optional description
            user: User UUID string saving the data
            
        Returns:
            Created or updated JSON store dictionary
        """
        # Convert user to UUID string if needed
        user_uuid = None
        if user:
            if hasattr(user, 'uuid'):
                user_uuid = str(user.uuid)
            elif hasattr(user, 'id'):
                user_uuid = str(user.id)
            else:
                user_uuid = str(user)
        
        # Check if store with this key already exists
        existing = self.storage.get_by_key(key)
        
        if existing:
            # Update existing store
            store = self.storage.update_by_key(
                key,
                data=data,
                type=store_type,
                description=description,
                created_by=user_uuid
            )
            action = 'Updated'
        else:
            # Create new store
            store = self.storage.create_store(
                key=key,
                data=data,
                store_type=store_type,
                description=description,
                created_by=user_uuid
            )
            action = 'Created'
        
        self.logger.info(f"{action} JSON store: {key}")
        return store
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get JSON data by key.
        
        Args:
            key: Store key
            
        Returns:
            JSON store dictionary, or None if not found
        """
        return self.storage.get_by_key(key)
    
    def delete(self, key: str) -> bool:
        """
        Delete JSON data.
        
        Args:
            key: Store key
            
        Returns:
            True if successful, False if not found
        """
        deleted = self.storage.delete_by_key(key)
        if deleted:
            self.logger.info(f"Deleted JSON store: {key}")
        return deleted
    
    def list(
        self,
        store_type: Optional[str] = None,
        user=None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List JSON stores.
        
        Args:
            store_type: Filter by type (optional)
            user: Filter by user UUID (optional)
            limit: Maximum number of stores
            offset: Offset for pagination
            
        Returns:
            List of JSON store dictionaries
        """
        # Convert user to UUID string if needed
        user_uuid = None
        if user:
            if hasattr(user, 'uuid'):
                user_uuid = str(user.uuid)
            elif hasattr(user, 'id'):
                user_uuid = str(user.id)
            else:
                user_uuid = str(user)
        
        result = self.storage.list_stores(
            store_type=store_type,
            created_by=user_uuid,
            limit=limit,
            offset=offset
        )
        
        return result.get('items', [])
    
    def search(
        self,
        query: str,
        store_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search JSON stores by key or description.
        
        Args:
            query: Search query
            store_type: Filter by type (optional)
            limit: Maximum number of results
            
        Returns:
            List of matching JSON store dictionaries
        """
        return self.storage.search_stores(
            query=query,
            store_type=store_type,
            limit=limit
        )
