"""JSON Store storage service using S3 JSON storage."""

import logging
import uuid as uuid_lib
from typing import Optional, Dict, Any, List
from datetime import datetime

from apps.core.services.s3_model_storage import S3ModelStorage

logger = logging.getLogger(__name__)


class JSONStoreStorageService(S3ModelStorage):
    """Storage service for JSON store using S3 JSON storage."""
    
    def __init__(self):
        """Initialize JSON store storage service."""
        super().__init__(model_name='json_store')
    
    def _extract_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata fields for JSON store index."""
        return {
            'uuid': data.get('uuid') or data.get('store_id'),
            'store_id': data.get('store_id') or data.get('uuid'),
            'key': data.get('key', ''),
            'type': data.get('type', 'custom'),
            'description': data.get('description', ''),
            'created_by': data.get('created_by'),  # UUID string
            'created_at': data.get('created_at', ''),
            'updated_at': data.get('updated_at', ''),
        }
    
    def create_store(
        self,
        key: str,
        data: Dict[str, Any],
        store_type: str = 'custom',
        description: str = '',
        created_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new JSON store entry."""
        store_id = str(uuid_lib.uuid4())
        now = datetime.utcnow().isoformat()
        
        store_data = {
            'store_id': store_id,
            'uuid': store_id,
            'id': store_id,  # For compatibility
            'key': key,
            'data': data,
            'type': store_type,
            'description': description,
            'created_by': created_by,
            'created_at': now,
            'updated_at': now,
        }
        
        return self.create(store_data, item_uuid=store_id)
    
    def get_store(self, store_id: str) -> Optional[Dict[str, Any]]:
        """Get JSON store by store_id."""
        return self.get(store_id)
    
    def get_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get JSON store by key.
        
        This method searches through the index to find the store with the given key,
        then loads the full data.
        """
        # Read index and find by key
        index_data = self._read_index()
        items_metadata = index_data.get('items', [])
        
        for item_meta in items_metadata:
            if item_meta.get('key') == key:
                store_id = item_meta.get('uuid') or item_meta.get('store_id')
                if store_id:
                    return self.get(store_id)
        
        return None
    
    def update_store(self, store_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Update JSON store entry."""
        # Get existing data
        existing = self.get(store_id)
        if not existing:
            return None
        
        # Prepare update data
        update_data = {}
        if 'key' in kwargs:
            update_data['key'] = kwargs['key']
        if 'data' in kwargs:
            update_data['data'] = kwargs['data']
        if 'type' in kwargs:
            update_data['type'] = kwargs['type']
        if 'description' in kwargs:
            update_data['description'] = kwargs['description']
        if 'created_by' in kwargs:
            update_data['created_by'] = kwargs['created_by']
        
        return self.update(store_id, update_data)
    
    def update_by_key(self, key: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Update JSON store entry by key."""
        store = self.get_by_key(key)
        if not store:
            return None
        
        store_id = store.get('store_id') or store.get('uuid')
        return self.update_store(store_id, **kwargs)
    
    def delete_store(self, store_id: str) -> bool:
        """Delete JSON store entry."""
        return self.delete(store_id)
    
    def delete_by_key(self, key: str) -> bool:
        """Delete JSON store entry by key."""
        store = self.get_by_key(key)
        if not store:
            return False
        
        store_id = store.get('store_id') or store.get('uuid')
        return self.delete(store_id)
    
    def list_stores(
        self,
        store_type: Optional[str] = None,
        created_by: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List JSON stores with filtering.
        
        Args:
            store_type: Filter by type (optional)
            created_by: Filter by user UUID (optional)
            limit: Maximum number of stores
            offset: Offset for pagination
            
        Returns:
            Dictionary with 'items' list and 'total' count
        """
        filters = {}
        if store_type:
            filters['type'] = store_type
        if created_by:
            filters['created_by'] = created_by
        
        return self.list(
            filters=filters if filters else None,
            limit=limit,
            offset=offset,
            order_by='created_at',
            reverse=True  # Newest first
        )
    
    def search_stores(
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
        # Get all stores (or filtered by type)
        filters = {}
        if store_type:
            filters['type'] = store_type
        
        result = self.list(filters=filters if filters else None, limit=None)
        all_stores = result.get('items', [])
        
        # Filter by query in key or description
        query_lower = query.lower()
        matching_stores = []
        for store in all_stores:
            key = store.get('key', '').lower()
            description = store.get('description', '').lower()
            if query_lower in key or query_lower in description:
                matching_stores.append(store)
                if len(matching_stores) >= limit:
                    break
        
        return matching_stores
