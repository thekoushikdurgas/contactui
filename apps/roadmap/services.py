"""Roadmap service."""
import logging
from typing import Optional, Dict, Any, List
from apps.core.services.base_service import BaseService
from .models import RoadmapItem

logger = logging.getLogger(__name__)


class RoadmapService(BaseService):
    """Service for roadmap operations."""
    
    def __init__(self):
        """Initialize roadmap service."""
        super().__init__('RoadmapService')
    
    def create_item(
        self,
        title: str,
        description: str = '',
        status: str = 'planned',
        due_date=None,
        created_by=None
    ) -> RoadmapItem:
        """
        Create a roadmap item.
        
        Args:
            title: Item title
            description: Item description
            status: Item status
            due_date: Due date
            created_by: User creating the item
            
        Returns:
            Created RoadmapItem instance
        """
        item = RoadmapItem.objects.create(
            title=title,
            description=description,
            status=status,
            due_date=due_date,
            created_by=created_by
        )
        
        self.logger.info(f"Created roadmap item: {item.item_id}")
        return item
    
    def update_progress(
        self,
        item_id: str,
        progress: int,
        status: str = None
    ) -> Optional[RoadmapItem]:
        """
        Update roadmap item progress.
        
        Args:
            item_id: Item ID
            progress: Progress percentage (0-100)
            status: Optional status update
            
        Returns:
            Updated RoadmapItem instance, or None if not found
        """
        try:
            import uuid
            item_uuid = uuid.UUID(item_id) if isinstance(item_id, str) else item_id
            item = RoadmapItem.objects.get(item_id=item_uuid)
            
            item.progress = max(0, min(100, progress))
            if status:
                item.status = status
            item.save()
            
            self.logger.info(f"Updated roadmap item {item_id}: {progress}%")
            return item
        except (RoadmapItem.DoesNotExist, ValueError):
            return None
    
    def list_items(
        self,
        status: Optional[str] = None,
        user=None,
        limit: int = 50,
        offset: int = 0
    ) -> List[RoadmapItem]:
        """
        List roadmap items.
        
        Args:
            status: Filter by status (optional)
            user: Filter by user (optional)
            limit: Maximum number of items
            offset: Offset for pagination
            
        Returns:
            List of RoadmapItem instances
        """
        queryset = RoadmapItem.objects.all()
        
        if status:
            queryset = queryset.filter(status=status)
        if user:
            queryset = queryset.filter(created_by=user)
        
        queryset = queryset.select_related('created_by')
        queryset = queryset.order_by('due_date', '-created_at')
        
        return list(queryset[offset:offset + limit])
