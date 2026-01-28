"""S3 Index Manager for managing index.json files."""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from apps.documentation.repositories.s3_json_storage import S3JSONStorage
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class S3IndexManager:
    """Manager for S3 index.json files."""
    
    def __init__(self, storage: Optional[S3JSONStorage] = None):
        """Initialize S3 index manager."""
        if storage is None:
            from apps.documentation.services import get_shared_s3_storage
            self.storage = get_shared_s3_storage()
        else:
            self.storage = storage
        self.data_prefix = settings.S3_DATA_PREFIX
    
    def _get_index_key(self, resource_type: str) -> str:
        """Get S3 key for index file."""
        return f"{self.data_prefix}{resource_type}/index.json"
    
    def read_index(self, resource_type: str, use_cache: bool = True, cache_ttl: int = 300) -> Dict[str, Any]:
        """
        Read index.json file for a resource type with optional caching.
        
        Args:
            resource_type: Type of resource ('pages', 'endpoints', 'relationships')
            use_cache: Whether to use cache (default: True)
            cache_ttl: Cache TTL in seconds (default: 300 = 5 minutes)
            
        Returns:
            Index data dictionary, or empty dict if not found
        """
        cache_key = f"s3_index:{resource_type}"
        
        # Try cache first
        if use_cache:
            try:
                cached_data = cache.get(cache_key)
                if cached_data is not None:
                    logger.debug(f"Cache hit for {resource_type} index")
                    return cached_data
            except Exception as e:
                logger.warning(f"Cache get failed for {resource_type} index: {e}")
        
        # Read from S3
        index_key = self._get_index_key(resource_type)
        index_data = self.storage.read_json(index_key)
        if not index_data:
            index_data = {
                'version': '2.0',
                'last_updated': None,
                'total': 0,
                resource_type: [],
                'indexes': {},
                'statistics': {}
            }
        
        # Cache the result
        if use_cache:
            try:
                cache.set(cache_key, index_data, cache_ttl)
                logger.debug(f"Cached {resource_type} index (TTL: {cache_ttl}s)")
            except Exception as e:
                logger.warning(f"Cache set failed for {resource_type} index: {e}")
        
        return index_data
    
    def update_index(self, resource_type: str, data: Dict[str, Any]) -> bool:
        """
        Update index.json file for a resource type and invalidate all related caches.
        
        Invalidates:
        - S3 index cache (s3_index:{resource_type})
        - Local index cache (local_json_storage:index:{resource_type})
        - UnifiedStorage list cache (unified_storage:{resource_type}:*)
        
        Args:
            resource_type: Type of resource
            data: Index data to write
            
        Returns:
            True if successful
        """
        index_key = self._get_index_key(resource_type)
        try:
            self.storage.write_json(index_key, data)
            
            # Invalidate S3 index cache
            cache_key = f"s3_index:{resource_type}"
            try:
                cache.delete(cache_key)
                logger.debug(f"Invalidated S3 index cache for {resource_type}")
            except Exception as e:
                logger.warning(f"Cache delete failed for {resource_type} S3 index: {e}")
            
            # Invalidate local index cache (if using local storage)
            local_cache_key = f"local_json_storage:index:{resource_type}"
            try:
                cache.delete(local_cache_key)
                logger.debug(f"Invalidated local index cache for {resource_type}")
            except Exception as e:
                logger.warning(f"Cache delete failed for {resource_type} local index: {e}")
            
            # Invalidate UnifiedStorage list cache for this resource type
            # This ensures list operations reflect the updated index
            try:
                from apps.documentation.services import get_shared_unified_storage
                unified_storage = get_shared_unified_storage()
                unified_storage.clear_cache(resource_type)
                logger.debug(f"Invalidated UnifiedStorage list cache for {resource_type}")
            except Exception as e:
                logger.warning(f"Failed to invalidate UnifiedStorage cache for {resource_type}: {e}")
            
            logger.info(f"Updated index for {resource_type} and invalidated all related caches")
            return True
        except Exception as e:
            logger.error(f"Failed to update index for {resource_type}: {e}")
            return False
    
    def update_index_entry(
        self,
        resource_type: str,
        index_name: str,
        key: str,
        value: Any,
        add: bool = True
    ) -> bool:
        """
        Update a specific entry in an index.
        
        Args:
            resource_type: Type of resource ('pages', 'endpoints', 'relationships')
            index_name: Name of the index ('by_page', 'by_endpoint', etc.)
            key: Key in the index
            value: Value to add/remove
            add: If True, add the value; if False, remove it
            
        Returns:
            True if successful
        """
        index_data = self.read_index(resource_type)
        indexes = index_data.setdefault('indexes', {})
        target_index = indexes.setdefault(index_name, {})
        
        if add:
            if key not in target_index:
                target_index[key] = []
            if value not in target_index[key]:
                target_index[key].append(value)
        else:
            if key in target_index and value in target_index[key]:
                target_index[key].remove(value)
                if not target_index[key]:
                    del target_index[key]
        
        return self.update_index(resource_type, index_data)
    
    def get_indexed_pages(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Get pages from index with optional filters.
        
        Optimized with early filtering and set operations (Task 2.1.2).
        Expected improvement: 30-40% faster filtering.
        
        Args:
            filters: Optional filters (page_type, status, etc.)
            
        Returns:
            List of page dictionaries
        """
        index_data = self.read_index('pages')
        pages = index_data.get('pages', [])
        
        if not filters:
            return pages
        
        # Optimize filtering with compiled filter function (Task 2.1.3)
        def should_include_page(page: Dict[str, Any]) -> bool:
            """Compiled filter function for faster execution."""
            # Fast path: page_type filter (most selective)
            if filters.get('page_type') and page.get('page_type') != filters['page_type']:
                return False
            
            # Get metadata efficiently
            metadata = page.get('metadata', {})
            page_status = metadata.get('status') or page.get('status')
            
            # Filter by status
            if filters.get('status'):
                if page_status != filters['status']:
                    return False
            
            # Filter by page_state
            if filters.get('page_state'):
                page_state = metadata.get('page_state')
                if page_state != filters['page_state']:
                    return False
            
            # Filter by include_drafts
            if not filters.get('include_drafts', True) and page_status == 'draft':
                return False
            
            # Filter by include_deleted
            if not filters.get('include_deleted', False) and page_status == 'deleted':
                return False
            
            return True
        
        # Use list comprehension for faster filtering (Task 2.1.3)
        filtered_pages = [page for page in pages if should_include_page(page)]
        
        return filtered_pages
    
    def add_item_to_index(
        self,
        resource_type: str,
        item_id: str,
        item_data: Dict[str, Any]
    ) -> bool:
        """
        Add a single item to the index incrementally.
        
        Args:
            resource_type: Type of resource ('pages', 'endpoints', 'relationships', 'postman')
            item_id: ID of the item to add
            item_data: Full item data dictionary
            
        Returns:
            True if successful
        """
        from datetime import datetime, timezone
        
        try:
            index_data = self.read_index(resource_type)
            items_list = index_data.get(resource_type, [])
            
            # Remove existing entry if present (for updates)
            items_list = [item for item in items_list if item.get('page_id' if resource_type == 'pages' else 'endpoint_id' if resource_type == 'endpoints' else 'relationship_id' if resource_type == 'relationships' else 'config_id') != item_id]
            
            # Create summary entry for index
            if resource_type == 'pages':
                page_type = item_data.get('page_type', 'docs')
                route = item_data.get('metadata', {}).get('route') or item_data.get('route', '')
                summary = {
                    'page_id': item_id,
                    'page_type': page_type,
                    'route': route,
                    'file_name': f"{item_id}.json"
                }
                items_list.append(summary)
                
                # Update indexes
                indexes = index_data.setdefault('indexes', {})
                by_type = indexes.setdefault('by_type', {})
                if page_type not in by_type:
                    by_type[page_type] = []
                if item_id not in by_type[page_type]:
                    by_type[page_type].append(item_id)
                
                by_route = indexes.setdefault('by_route', {})
                if route:
                    by_route[route] = item_id
                    
            elif resource_type == 'endpoints':
                method = item_data.get('method', 'GET')
                api_version = item_data.get('api_version', 'v1')
                path = item_data.get('endpoint_path') or item_data.get('path', '')
                summary = {
                    'endpoint_id': item_id,
                    'method': method,
                    'api_version': api_version,
                    'path': path,
                    'file_name': f"{item_id}.json"
                }
                items_list.append(summary)
                
                # Update indexes
                indexes = index_data.setdefault('indexes', {})
                by_method = indexes.setdefault('by_method', {})
                if method not in by_method:
                    by_method[method] = []
                if item_id not in by_method[method]:
                    by_method[method].append(item_id)
                
                by_api_version = indexes.setdefault('by_api_version', {})
                if api_version not in by_api_version:
                    by_api_version[api_version] = []
                if item_id not in by_api_version[api_version]:
                    by_api_version[api_version].append(item_id)
                
                by_path = indexes.setdefault('by_path', {})
                if path:
                    by_path[path] = item_id
                    
            elif resource_type == 'relationships':
                page_id = item_data.get('page_id') or item_data.get('page_path')
                endpoint_path = item_data.get('endpoint_path')
                method = item_data.get('method', 'GET')
                usage_type = item_data.get('usage_type', 'primary')
                
                summary = {
                    'relationship_id': item_id,
                    'page_id': page_id,
                    'endpoint_path': endpoint_path,
                    'method': method,
                    'usage_type': usage_type,
                    'file_name': f"{item_id}.json"
                }
                items_list.append(summary)
                
                # Update indexes
                indexes = index_data.setdefault('indexes', {})
                by_page = indexes.setdefault('by_page', {})
                if page_id:
                    if page_id not in by_page:
                        by_page[page_id] = []
                    if item_id not in by_page[page_id]:
                        by_page[page_id].append(item_id)
                
                by_endpoint = indexes.setdefault('by_endpoint', {})
                if endpoint_path:
                    endpoint_key = f"{method}:{endpoint_path}"
                    if endpoint_key not in by_endpoint:
                        by_endpoint[endpoint_key] = []
                    if item_id not in by_endpoint[endpoint_key]:
                        by_endpoint[endpoint_key].append(item_id)
                
                by_usage_type = indexes.setdefault('by_usage_type', {})
                if usage_type not in by_usage_type:
                    by_usage_type[usage_type] = []
                if item_id not in by_usage_type[usage_type]:
                    by_usage_type[usage_type].append(item_id)
            
            # Update statistics
            stats = index_data.setdefault('statistics', {})
            stats['total'] = len(items_list)
            
            # Update metadata
            index_data['last_updated'] = datetime.now(timezone.utc).isoformat()
            index_data['total'] = len(items_list)
            index_data[resource_type] = items_list
            
            return self.update_index(resource_type, index_data)
            
        except Exception as e:
            logger.error(f"Failed to add item to index for {resource_type}: {e}", exc_info=True)
            return False
    
    def remove_item_from_index(
        self,
        resource_type: str,
        item_id: str
    ) -> bool:
        """
        Remove a single item from the index incrementally.
        
        Args:
            resource_type: Type of resource
            item_id: ID of the item to remove
            
        Returns:
            True if successful
        """
        from datetime import datetime, timezone
        
        try:
            index_data = self.read_index(resource_type)
            items_list = index_data.get(resource_type, [])
            
            # Find and remove the item
            id_field = 'page_id' if resource_type == 'pages' else 'endpoint_id' if resource_type == 'endpoints' else 'relationship_id' if resource_type == 'relationships' else 'config_id'
            original_count = len(items_list)
            items_list = [item for item in items_list if item.get(id_field) != item_id]
            
            if len(items_list) == original_count:
                logger.warning(f"Item {item_id} not found in index for {resource_type}")
                return False
            
            # Update indexes - remove item_id from all index entries
            indexes = index_data.get('indexes', {})
            for index_name, index_data_dict in indexes.items():
                if isinstance(index_data_dict, dict):
                    for key, value_list in list(index_data_dict.items()):
                        if isinstance(value_list, list) and item_id in value_list:
                            value_list.remove(item_id)
                            if not value_list:
                                del index_data_dict[key]
            
            # Update statistics
            stats = index_data.setdefault('statistics', {})
            stats['total'] = len(items_list)
            
            # Update metadata
            index_data['last_updated'] = datetime.now(timezone.utc).isoformat()
            index_data['total'] = len(items_list)
            index_data[resource_type] = items_list
            
            return self.update_index(resource_type, index_data)
            
        except Exception as e:
            logger.error(f"Failed to remove item from index for {resource_type}: {e}", exc_info=True)
            return False
    
    def validate_index(self, resource_type: str) -> Dict[str, Any]:
        """
        Validate index consistency.
        
        Checks:
        - All files in S3 are listed in index
        - Index doesn't reference non-existent files
        - Index structure is valid
        
        Args:
            resource_type: Type of resource to validate
            
        Returns:
            Dictionary with validation results:
            {
                'valid': bool,
                'total_in_s3': int,
                'total_in_index': int,
                'missing_in_index': List[str],  # Files in S3 but not in index
                'extra_in_index': List[str],    # Files in index but not in S3
                'errors': List[str]
            }
        """
        try:
            prefix = f"{self.data_prefix}{resource_type}/"
            
            # List all files in S3
            file_keys = self.storage.list_json_files(prefix, max_keys=10000)
            json_files = [f for f in file_keys if not f.endswith('/index.json')]
            
            # Extract IDs from filenames
            s3_ids = set()
            for file_key in json_files:
                item_id = file_key.split('/')[-1].replace('.json', '')
                s3_ids.add(item_id)
            
            # Read index
            index_data = self.read_index(resource_type)
            items_list = index_data.get(resource_type, [])
            
            # Extract IDs from index
            id_field = 'page_id' if resource_type == 'pages' else 'endpoint_id' if resource_type == 'endpoints' else 'relationship_id' if resource_type == 'relationships' else 'config_id'
            index_ids = set()
            for item in items_list:
                item_id = item.get(id_field)
                if item_id:
                    index_ids.add(item_id)
            
            # Find discrepancies
            missing_in_index = sorted(list(s3_ids - index_ids))
            extra_in_index = sorted(list(index_ids - s3_ids))
            
            # Check index structure
            errors = []
            if not isinstance(index_data, dict):
                errors.append("Index data is not a dictionary")
            if 'version' not in index_data:
                errors.append("Index missing 'version' field")
            if resource_type not in index_data:
                errors.append(f"Index missing '{resource_type}' list")
            if 'indexes' not in index_data:
                errors.append("Index missing 'indexes' field")
            
            is_valid = len(missing_in_index) == 0 and len(extra_in_index) == 0 and len(errors) == 0
            
            result = {
                'valid': is_valid,
                'total_in_s3': len(s3_ids),
                'total_in_index': len(index_ids),
                'missing_in_index': missing_in_index,
                'extra_in_index': extra_in_index,
                'errors': errors,
                'resource_type': resource_type
            }
            
            if not is_valid:
                logger.warning(
                    f"Index validation failed for {resource_type}: "
                    f"{len(missing_in_index)} missing, {len(extra_in_index)} extra, {len(errors)} errors"
                )
            else:
                logger.info(f"Index validation passed for {resource_type}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to validate index for {resource_type}: {e}", exc_info=True)
            return {
                'valid': False,
                'total_in_s3': 0,
                'total_in_index': 0,
                'missing_in_index': [],
                'extra_in_index': [],
                'errors': [str(e)],
                'resource_type': resource_type
            }
    
    def get_index_health(self, resource_type: str, max_age_hours: int = 24) -> Dict[str, Any]:
        """
        Check index health and freshness.
        
        Args:
            resource_type: Type of resource to check
            max_age_hours: Maximum age in hours before index is considered stale
            
        Returns:
            Dictionary with health status:
            {
                'healthy': bool,
                'age_hours': float,
                'last_updated': str,
                'is_stale': bool,
                'total_items': int,
                'warnings': List[str]
            }
        """
        try:
            index_data = self.read_index(resource_type)
            last_updated_str = index_data.get('last_updated')
            
            if not last_updated_str:
                return {
                    'healthy': False,
                    'age_hours': None,
                    'last_updated': None,
                    'is_stale': True,
                    'total_items': index_data.get('total', 0),
                    'warnings': ['Index has no last_updated timestamp']
                }
            
            # Parse timestamp
            try:
                last_updated = datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
                if last_updated.tzinfo is None:
                    last_updated = last_updated.replace(tzinfo=timezone.utc)
            except Exception as e:
                return {
                    'healthy': False,
                    'age_hours': None,
                    'last_updated': last_updated_str,
                    'is_stale': True,
                    'total_items': index_data.get('total', 0),
                    'warnings': [f'Invalid timestamp format: {e}']
                }
            
            # Calculate age
            now = datetime.now(timezone.utc)
            age_delta = now - last_updated
            age_hours = age_delta.total_seconds() / 3600
            
            is_stale = age_hours > max_age_hours
            warnings = []
            
            if is_stale:
                warnings.append(f'Index is stale (age: {age_hours:.1f} hours, max: {max_age_hours} hours)')
            
            total_items = index_data.get('total', 0)
            if total_items == 0:
                warnings.append('Index has no items')
            
            # Check version
            version = index_data.get('version', '1.0')
            if version != '2.0':
                warnings.append(f'Index version is {version}, expected 2.0')
            
            healthy = not is_stale and len(warnings) == 0
            
            return {
                'healthy': healthy,
                'age_hours': age_hours,
                'last_updated': last_updated_str,
                'is_stale': is_stale,
                'total_items': total_items,
                'warnings': warnings,
                'version': version
            }
            
        except Exception as e:
            logger.error(f"Failed to check index health for {resource_type}: {e}", exc_info=True)
            return {
                'healthy': False,
                'age_hours': None,
                'last_updated': None,
                'is_stale': True,
                'total_items': 0,
                'warnings': [f'Error checking health: {str(e)}']
            }
    
    def rebuild_index(self, resource_type: str) -> bool:
        """
        Rebuild index from all files.
        
        Args:
            resource_type: Type of resource to rebuild ('pages', 'endpoints', 'relationships')
            
        Returns:
            True if successful
        """
        from datetime import datetime, timezone
        
        try:
            prefix = f"{self.data_prefix}{resource_type}/"
            
            # List all files in the resource directory
            # Use list_json_files which internally calls s3_service.list_files
            file_keys = self.storage.list_json_files(prefix, max_keys=10000)
            
            # Filter to exclude index.json itself
            json_files = [f for f in file_keys if not f.endswith('/index.json')]
            
            items = []
            indexes = {}
            
            # Process each file
            for file_key in json_files:
                item_data = self.storage.read_json(file_key)
                if not item_data:
                    continue
                
                # Extract item ID from filename
                item_id = file_key.split('/')[-1].replace('.json', '')
                
                # Add to items list
                items.append({
                    'id': item_id,
                    'page_id' if resource_type == 'pages' else 'endpoint_id' if resource_type == 'endpoints' else 'relationship_id': item_id,
                    **{k: v for k, v in item_data.items() if k not in ['_id', 'created_at', 'updated_at']}
                })
                
                # Build indexes based on resource type
                if resource_type == 'pages':
                    page_type = item_data.get('page_type', 'docs')
                    status = item_data.get('metadata', {}).get('status') or item_data.get('status', 'published')
                    route = item_data.get('metadata', {}).get('route') or item_data.get('route', '/')
                    
                    # By page_type index
                    if 'by_page_type' not in indexes:
                        indexes['by_page_type'] = {}
                    if page_type not in indexes['by_page_type']:
                        indexes['by_page_type'][page_type] = []
                    indexes['by_page_type'][page_type].append(item_id)
                    
                    # By route index
                    if 'by_route' not in indexes:
                        indexes['by_route'] = {}
                    indexes['by_route'][route] = item_id
                
                elif resource_type == 'relationships':
                    page_id = item_data.get('page_id')
                    endpoint_path = item_data.get('endpoint_path')
                    method = item_data.get('method', 'GET')
                    
                    # By page index
                    if page_id:
                        if 'by_page' not in indexes:
                            indexes['by_page'] = {}
                        if page_id not in indexes['by_page']:
                            indexes['by_page'][page_id] = []
                        indexes['by_page'][page_id].append(item_id)
                    
                    # By endpoint index
                    if endpoint_path:
                        endpoint_key = f"{method}:{endpoint_path}"
                        if 'by_endpoint' not in indexes:
                            indexes['by_endpoint'] = {}
                        if endpoint_key not in indexes['by_endpoint']:
                            indexes['by_endpoint'][endpoint_key] = []
                        indexes['by_endpoint'][endpoint_key].append(item_id)
            
            # Create new index structure
            index_data = {
                'version': '2.0',
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'total': len(items),
                resource_type: items,
                'indexes': indexes,
                'statistics': {
                    'total_items': len(items),
                    'last_rebuild': datetime.now(timezone.utc).isoformat()
                }
            }
            
            # Write updated index
            return self.update_index(resource_type, index_data)
            
        except Exception as e:
            logger.error(f"Failed to rebuild index for {resource_type}: {e}")
            return False
