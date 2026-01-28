"""JSON Store service."""
import logging
from typing import Optional, Dict, Any, List
from apps.core.services.base_service import BaseService
from .models import JSONStore

logger = logging.getLogger(__name__)


class JSONStoreService(BaseService):
    """Service for JSON store operations."""
    
    def __init__(self):
        """Initialize JSON store service."""
        super().__init__('JSONStoreService')
    
    def save(
        self,
        key: str,
        data: Dict[str, Any],
        store_type: str = 'custom',
        description: str = '',
        user=None
    ) -> JSONStore:
        """
        Save JSON data.
        
        Args:
            key: Store key
            data: JSON data to store
            store_type: Type of store
            description: Optional description
            user: User saving the data
            
        Returns:
            Created or updated JSONStore instance
        """
        store, created = JSONStore.objects.update_or_create(
            key=key,
            defaults={
                'data': data,
                'type': store_type,
                'description': description,
                'created_by': user
            }
        )
        
        action = 'Created' if created else 'Updated'
        self.logger.info(f"{action} JSON store: {key}")
        return store
    
    def get(self, key: str) -> Optional[JSONStore]:
        """
        Get JSON data by key.
        
        Args:
            key: Store key
            
        Returns:
            JSONStore instance, or None if not found
        """
        try:
            return JSONStore.objects.get(key=key)
        except JSONStore.DoesNotExist:
            return None
    
    def delete(self, key: str) -> bool:
        """
        Delete JSON data.
        
        Args:
            key: Store key
            
        Returns:
            True if successful, False if not found
        """
        try:
            store = JSONStore.objects.get(key=key)
            store.delete()
            self.logger.info(f"Deleted JSON store: {key}")
            return True
        except JSONStore.DoesNotExist:
            return False
    
    def list(
        self,
        store_type: Optional[str] = None,
        user=None,
        limit: int = 100,
        offset: int = 0
    ) -> List[JSONStore]:
        """
        List JSON stores.
        
        Args:
            store_type: Filter by type (optional)
            user: Filter by user (optional)
            limit: Maximum number of stores
            offset: Offset for pagination
            
        Returns:
            List of JSONStore instances
        """
        queryset = JSONStore.objects.all()
        
        if store_type:
            queryset = queryset.filter(type=store_type)
        if user:
            queryset = queryset.filter(created_by=user)
        
        queryset = queryset.select_related('created_by')
        queryset = queryset.order_by('-created_at')
        
        return list(queryset[offset:offset + limit])
    
    def search(
        self,
        query: str,
        store_type: Optional[str] = None,
        limit: int = 50
    ) -> List[JSONStore]:
        """
        Search JSON stores by key or description.
        
        Args:
            query: Search query
            store_type: Filter by type (optional)
            limit: Maximum number of results
            
        Returns:
            List of matching JSONStore instances
        """
        queryset = JSONStore.objects.filter(
            models.Q(key__icontains=query) | models.Q(description__icontains=query)
        )
        
        if store_type:
            queryset = queryset.filter(type=store_type)
        
        queryset = queryset.select_related('created_by')
        queryset = queryset.order_by('-created_at')
        
        return list(queryset[:limit])
