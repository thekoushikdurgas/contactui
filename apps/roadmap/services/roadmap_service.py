"""Roadmap service."""
import logging
from typing import Optional, Dict, Any, List
from apps.core.services.base_service import BaseService
from .roadmap_storage_service import RoadmapStorageService

logger = logging.getLogger(__name__)


class RoadmapService(BaseService):
    """Service for roadmap operations using S3 storage."""
    
    def __init__(self):
        """Initialize roadmap service."""
        super().__init__('RoadmapService')
        self.storage = RoadmapStorageService()
    
    def create_item(
        self,
        title: str,
        description: str = '',
        status: str = 'planned',
        due_date=None,
        created_by=None
    ) -> Dict[str, Any]:
        """
        Create a roadmap item.
        
        Args:
            title: Item title
            description: Item description
            status: Item status
            due_date: Due date (datetime or ISO string)
            created_by: User UUID creating the item
            
        Returns:
            Created roadmap item data dictionary
        """
        # Convert created_by to UUID string if needed
        created_by_uuid = None
        if created_by:
            if hasattr(created_by, 'uuid'):
                created_by_uuid = str(created_by.uuid)
            elif hasattr(created_by, 'id'):
                created_by_uuid = str(created_by.id)
            else:
                created_by_uuid = str(created_by)
        
        # Convert due_date to ISO string if datetime
        due_date_str = None
        if due_date:
            if isinstance(due_date, str):
                due_date_str = due_date
            else:
                due_date_str = due_date.isoformat()
        
        item = self.storage.create_item(
            title=title,
            description=description,
            status=status,
            due_date=due_date_str,
            created_by=created_by_uuid
        )
        
        self.logger.info(f"Created roadmap item: {item.get('item_id')}")
        return item
    
    def update_progress(
        self,
        item_id: str,
        progress: int,
        status: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update roadmap item progress.
        
        Args:
            item_id: Item ID
            progress: Progress percentage (0-100)
            status: Optional status update
            
        Returns:
            Updated roadmap item data dictionary, or None if not found
        """
        update_data = {
            'progress': max(0, min(100, progress))
        }
        if status:
            update_data['status'] = status
        
        return self.storage.update_item(item_id, **update_data)
    
    def list_items(
        self,
        status: Optional[str] = None,
        user=None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List roadmap items.
        
        Args:
            status: Filter by status (optional)
            user: Filter by user UUID (optional)
            limit: Maximum number of items
            offset: Offset for pagination
            
        Returns:
            List of roadmap item data dictionaries
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
        
        filters = {}
        if status:
            filters['status'] = status
        if user_uuid:
            filters['created_by'] = user_uuid
        
        result = self.storage.list(filters=filters, limit=limit, offset=offset, order_by='due_date', reverse=False)
        return result.get('items', [])
