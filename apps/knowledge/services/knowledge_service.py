"""Knowledge base service for managing knowledge items."""
import logging
from typing import Optional, Dict, Any, List
from apps.core.services.base_service import BaseService, log_performance
from .knowledge_storage_service import KnowledgeStorageService

logger = logging.getLogger(__name__)


class KnowledgeBaseService(BaseService):
    """Service for managing knowledge base items using S3 storage."""
    
    def __init__(self):
        """Initialize knowledge base service."""
        super().__init__('KnowledgeBaseService')
        self.storage = KnowledgeStorageService()
        self.cache_timeout = 600  # 10 minutes
    
    @log_performance
    def search(self, query: str, pattern_type: Optional[str] = None, tags: Optional[List[str]] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search knowledge base items.
        
        Args:
            query: Search query
            pattern_type: Filter by pattern type
            tags: Filter by tags
            limit: Maximum number of results
            
        Returns:
            List of knowledge item dictionaries
        """
        return self.storage.search_knowledge(
            query=query,
            pattern_type=pattern_type,
            tags=tags,
            limit=limit
        )
    
    @log_performance
    def get_by_id(self, knowledge_id: str) -> Optional[Dict[str, Any]]:
        """
        Get knowledge base item by ID.
        
        Args:
            knowledge_id: Knowledge base item ID
            
        Returns:
            Knowledge item dictionary, or None if not found
        """
        return self.storage.get_knowledge(knowledge_id)
    
    @log_performance
    def create(self, pattern_type: str, title: str, content: str, tags: List[str] = None, metadata: Dict = None, created_by=None) -> Dict[str, Any]:
        """
        Create a new knowledge base item.
        
        Args:
            pattern_type: Pattern type
            title: Title
            content: Content
            tags: List of tags
            metadata: Metadata dictionary
            created_by: User UUID who created the item
            
        Returns:
            Created knowledge item dictionary
        """
        # Validate required fields
        is_valid, error_msg = self._validate_input(
            {'pattern_type': pattern_type, 'title': title, 'content': content},
            ['pattern_type', 'title', 'content']
        )
        if not is_valid:
            raise ValueError(error_msg)
        
        # Convert created_by to UUID string if needed
        created_by_uuid = None
        if created_by:
            if hasattr(created_by, 'uuid'):
                created_by_uuid = str(created_by.uuid)
            elif hasattr(created_by, 'id'):
                created_by_uuid = str(created_by.id)
            else:
                created_by_uuid = str(created_by)
        
        return self.storage.create_knowledge(
            pattern_type=pattern_type,
            title=title,
            content=content,
            tags=tags,
            metadata=metadata,
            created_by=created_by_uuid
        )
    
    @log_performance
    def update(self, knowledge_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Update a knowledge base item.
        
        Args:
            knowledge_id: Knowledge base item ID
            **kwargs: Fields to update
            
        Returns:
            Updated knowledge item dictionary, or None if not found
        """
        return self.storage.update_knowledge(knowledge_id, **kwargs)
    
    @log_performance
    def delete(self, knowledge_id: str) -> bool:
        """
        Delete a knowledge base item.
        
        Args:
            knowledge_id: Knowledge base item ID
            
        Returns:
            True if successful, False otherwise
        """
        return self.storage.delete_knowledge(knowledge_id)
    
    @log_performance
    def get_related(self, knowledge_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get related knowledge base items.
        
        Args:
            knowledge_id: Knowledge base item ID
            limit: Maximum number of results
            
        Returns:
            List of related knowledge item dictionaries
        """
        item = self.get_by_id(knowledge_id)
        if not item:
            return []
        
        # Find items with similar tags or pattern type
        pattern_type = item.get('pattern_type')
        tags = item.get('tags', [])
        
        # Get all items with same pattern type or overlapping tags
        all_items = self.storage.list(filters={'pattern_type': pattern_type}, limit=None, offset=0)
        related_items = []
        
        for related_item in all_items.get('items', []):
            if related_item.get('knowledge_id') == knowledge_id:
                continue
            
            # Check if tags overlap
            related_tags = related_item.get('tags', [])
            if tags and related_tags and set(tags) & set(related_tags):
                related_items.append(related_item)
            elif related_item.get('pattern_type') == pattern_type:
                related_items.append(related_item)
            
            if len(related_items) >= limit:
                break
        
        return related_items[:limit]
