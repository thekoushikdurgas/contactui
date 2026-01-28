"""Generic S3 model storage service for storing Django models as JSON files in S3."""

import json
import uuid as uuid_lib
import logging
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from django.conf import settings
from django.core.cache import cache

from apps.core.services.s3_service import S3Service
from apps.core.exceptions import S3Error
from apps.documentation.repositories.s3_json_storage import S3JSONStorage

logger = logging.getLogger(__name__)


class S3ModelStorageError(Exception):
    """Exception for S3 model storage errors."""
    pass


class S3ModelStorage:
    """
    Generic S3 model storage service.
    
    Stores model instances as JSON files in S3 with the following structure:
    
    s3://bucket/
      models/
        {model_name}/
          index.json          # {total: N, items: [{uuid, metadata}]}
          {uuid}.json         # Full model data
    
    Features:
    - CRUD operations (create, read, update, delete)
    - Index management for fast listing
    - Pagination support
    - Filtering/search support
    - Batch operations
    - Caching for performance
    """
    
    def __init__(self, model_name: str, s3_service: Optional[S3Service] = None):
        """
        Initialize S3 model storage.
        
        Args:
            model_name: Name of the model (e.g., 'tasks', 'knowledge')
            s3_service: Optional S3Service instance
        """
        self.model_name = model_name
        self.s3_service = s3_service or S3Service()
        self.s3_json_storage = S3JSONStorage(s3_service=self.s3_service)
        self.bucket_name = settings.S3_BUCKET_NAME
        self.models_prefix = f"models/{model_name}/"
        self.index_key = f"{self.models_prefix}index.json"
        self.cache_prefix = f"s3_model:{model_name}:"
        self.cache_ttl = 300  # 5 minutes default
    
    def _get_item_key(self, item_uuid: str) -> str:
        """Get S3 key for an item."""
        return f"{self.models_prefix}{item_uuid}.json"
    
    def _get_cache_key(self, key_type: str, *args) -> str:
        """Get cache key."""
        return f"{self.cache_prefix}{key_type}:{':'.join(str(a) for a in args)}"
    
    def _read_index(self) -> Dict[str, Any]:
        """
        Read index.json from S3.
        
        Returns:
            Index dictionary with 'total' and 'items' list
        """
        cache_key = self._get_cache_key('index')
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        index_data = self.s3_json_storage.read_json(self.index_key)
        if not index_data:
            # Initialize empty index
            index_data = {
                'total': 0,
                'items': [],
                'updated_at': datetime.utcnow().isoformat()
            }
            self._write_index(index_data)
        
        cache.set(cache_key, index_data, self.cache_ttl)
        return index_data
    
    def _write_index(self, index_data: Dict[str, Any]) -> None:
        """
        Write index.json to S3.
        
        Args:
            index_data: Index dictionary to write
        """
        index_data['updated_at'] = datetime.utcnow().isoformat()
        self.s3_json_storage.write_json(self.index_key, index_data)
        
        # Invalidate cache
        cache_key = self._get_cache_key('index')
        cache.delete(cache_key)
    
    def _update_index_item(self, item_uuid: str, metadata: Dict[str, Any], operation: str = 'update') -> None:
        """
        Update an item in the index.
        
        Args:
            item_uuid: UUID of the item
            metadata: Metadata to store in index (should include fields for filtering)
            operation: 'create', 'update', or 'delete'
        """
        index_data = self._read_index()
        items = index_data.get('items', [])
        
        if operation == 'delete':
            # Remove from index
            items = [item for item in items if item.get('uuid') != item_uuid]
            index_data['total'] = len(items)
        else:
            # Find existing item or create new
            item_found = False
            for i, item in enumerate(items):
                if item.get('uuid') == item_uuid:
                    items[i] = {**item, **metadata, 'uuid': item_uuid}
                    item_found = True
                    break
            
            if not item_found:
                items.append({**metadata, 'uuid': item_uuid})
                index_data['total'] = len(items)
        
        index_data['items'] = items
        self._write_index(index_data)
    
    def create(self, data: Dict[str, Any], item_uuid: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new model instance.
        
        Args:
            data: Model data dictionary
            item_uuid: Optional UUID (generated if not provided)
            
        Returns:
            Created model data with UUID
        """
        # Generate UUID if not provided
        if not item_uuid:
            if 'id' in data:
                item_uuid = str(data['id'])
            elif 'uuid' in data:
                item_uuid = str(data['uuid'])
            else:
                item_uuid = str(uuid_lib.uuid4())
        
        # Ensure UUID is in data
        data['uuid'] = item_uuid
        data['id'] = item_uuid  # For compatibility
        
        # Add timestamps if not present
        now = datetime.utcnow().isoformat()
        if 'created_at' not in data:
            data['created_at'] = now
        if 'updated_at' not in data:
            data['updated_at'] = now
        
        # Write to S3
        item_key = self._get_item_key(item_uuid)
        self.s3_json_storage.write_json(item_key, data)
        
        # Update index with metadata (extract key fields for filtering)
        metadata = self._extract_metadata(data)
        self._update_index_item(item_uuid, metadata, 'create')
        
        # Invalidate item cache
        cache_key = self._get_cache_key('item', item_uuid)
        cache.delete(cache_key)
        
        logger.info(f"Created {self.model_name} item: {item_uuid}")
        return data
    
    def get(self, item_uuid: str) -> Optional[Dict[str, Any]]:
        """
        Get a model instance by UUID.
        
        Args:
            item_uuid: UUID of the item
            
        Returns:
            Model data dictionary or None if not found
        """
        # Check cache
        cache_key = self._get_cache_key('item', item_uuid)
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        # Read from S3
        item_key = self._get_item_key(item_uuid)
        data = self.s3_json_storage.read_json(item_key)
        
        if data:
            cache.set(cache_key, data, self.cache_ttl)
        
        return data
    
    def update(self, item_uuid: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a model instance.
        
        Args:
            item_uuid: UUID of the item
            data: Updated data dictionary
            
        Returns:
            Updated model data or None if not found
        """
        # Get existing data
        existing = self.get(item_uuid)
        if not existing:
            return None
        
        # Merge updates
        updated_data = {**existing, **data}
        updated_data['updated_at'] = datetime.utcnow().isoformat()
        updated_data['uuid'] = item_uuid  # Ensure UUID is preserved
        
        # Write to S3
        item_key = self._get_item_key(item_uuid)
        self.s3_json_storage.write_json(item_key, updated_data)
        
        # Update index
        metadata = self._extract_metadata(updated_data)
        self._update_index_item(item_uuid, metadata, 'update')
        
        # Invalidate cache
        cache_key = self._get_cache_key('item', item_uuid)
        cache.delete(cache_key)
        
        logger.info(f"Updated {self.model_name} item: {item_uuid}")
        return updated_data
    
    def delete(self, item_uuid: str) -> bool:
        """
        Delete a model instance.
        
        Args:
            item_uuid: UUID of the item
            
        Returns:
            True if deleted, False if not found
        """
        # Check if exists
        existing = self.get(item_uuid)
        if not existing:
            return False
        
        # Delete from S3
        item_key = self._get_item_key(item_uuid)
        self.s3_json_storage.delete_json(item_key)
        
        # Update index
        self._update_index_item(item_uuid, {}, 'delete')
        
        # Invalidate cache
        cache_key = self._get_cache_key('item', item_uuid)
        cache.delete(cache_key)
        
        logger.info(f"Deleted {self.model_name} item: {item_uuid}")
        return True
    
    def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        order_by: Optional[str] = None,
        reverse: bool = False
    ) -> Dict[str, Any]:
        """
        List model instances with filtering and pagination.
        
        Args:
            filters: Dictionary of filters (e.g., {'status': 'active', 'priority': 'high'})
            limit: Maximum number of items to return
            offset: Offset for pagination
            order_by: Field to order by (default: 'created_at')
            reverse: Reverse order (default: False, newest first)
            
        Returns:
            Dictionary with 'items' list and 'total' count
        """
        # Read index
        index_data = self._read_index()
        items_metadata = index_data.get('items', [])
        
        # Apply filters
        if filters:
            filtered_items = []
            for item_meta in items_metadata:
                match = True
                for key, value in filters.items():
                    item_value = item_meta.get(key)
                    if isinstance(value, (list, tuple)):
                        if item_value not in value:
                            match = False
                            break
                    elif item_value != value:
                        match = False
                        break
                if match:
                    filtered_items.append(item_meta)
            items_metadata = filtered_items
        
        # Sort
        if order_by:
            items_metadata.sort(
                key=lambda x: x.get(order_by, ''),
                reverse=reverse
            )
        else:
            # Default: sort by created_at descending (newest first)
            items_metadata.sort(
                key=lambda x: x.get('created_at', ''),
                reverse=not reverse
            )
        
        # Paginate
        total = len(items_metadata)
        if limit:
            items_metadata = items_metadata[offset:offset + limit]
        else:
            items_metadata = items_metadata[offset:]
        
        # Load full data for returned items
        items = []
        for item_meta in items_metadata:
            item_uuid = item_meta.get('uuid')
            if item_uuid:
                item_data = self.get(item_uuid)
                if item_data:
                    items.append(item_data)
        
        return {
            'items': items,
            'total': total,
            'limit': limit,
            'offset': offset
        }
    
    def batch_create(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create multiple model instances in batch.
        
        Args:
            items: List of model data dictionaries
            
        Returns:
            List of created model data
        """
        created_items = []
        for item_data in items:
            created = self.create(item_data)
            created_items.append(created)
        
        logger.info(f"Batch created {len(created_items)} {self.model_name} items")
        return created_items
    
    def batch_delete(self, item_uuids: List[str]) -> int:
        """
        Delete multiple model instances in batch.
        
        Args:
            item_uuids: List of UUIDs to delete
            
        Returns:
            Number of items deleted
        """
        deleted_count = 0
        for item_uuid in item_uuids:
            if self.delete(item_uuid):
                deleted_count += 1
        
        logger.info(f"Batch deleted {deleted_count} {self.model_name} items")
        return deleted_count
    
    def _extract_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata fields for index.
        
        Override this method in subclasses to specify which fields
        should be stored in the index for filtering.
        
        Args:
            data: Full model data
            
        Returns:
            Metadata dictionary with key fields
        """
        # Default: extract common fields
        metadata_fields = [
            'uuid', 'id', 'title', 'name', 'status', 'priority',
            'type', 'created_at', 'updated_at', 'created_by', 'assigned_to'
        ]
        
        metadata = {}
        for field in metadata_fields:
            if field in data:
                value = data[field]
                # Convert complex types to strings for JSON
                if isinstance(value, (dict, list)):
                    continue  # Skip complex types
                metadata[field] = value
        
        return metadata
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Get count of items matching filters.
        
        Args:
            filters: Optional filters dictionary
            
        Returns:
            Count of matching items
        """
        result = self.list(filters=filters, limit=1, offset=0)
        return result.get('total', 0)
    
    def exists(self, item_uuid: str) -> bool:
        """
        Check if an item exists.
        
        Args:
            item_uuid: UUID of the item
            
        Returns:
            True if exists, False otherwise
        """
        return self.get(item_uuid) is not None
    
    def search(
        self,
        query: str,
        fields: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Search items by text query.
        
        Args:
            query: Search query string
            fields: Fields to search in (default: ['title', 'name', 'description'])
            limit: Maximum results
            offset: Offset for pagination
            
        Returns:
            Dictionary with 'items' list and 'total' count
        """
        if not fields:
            fields = ['title', 'name', 'description', 'content']
        
        query_lower = query.lower()
        matching_items = []
        
        # Get all items (could be optimized with better indexing)
        all_items = self.list(limit=None, offset=0)
        
        for item in all_items.get('items', []):
            match = False
            for field in fields:
                value = item.get(field, '')
                if isinstance(value, str) and query_lower in value.lower():
                    match = True
                    break
            
            if match:
                matching_items.append(item)
        
        # Paginate
        total = len(matching_items)
        if limit:
            matching_items = matching_items[offset:offset + limit]
        else:
            matching_items = matching_items[offset:]
        
        return {
            'items': matching_items,
            'total': total,
            'limit': limit,
            'offset': offset
        }
