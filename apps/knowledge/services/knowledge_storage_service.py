"""Knowledge storage service using S3 JSON storage."""

import logging
import uuid as uuid_lib
from typing import Optional, Dict, Any, List
from datetime import datetime

from apps.core.services.s3_model_storage import S3ModelStorage

logger = logging.getLogger(__name__)


class KnowledgeStorageService(S3ModelStorage):
    """Storage service for knowledge base items using S3 JSON storage."""
    
    def __init__(self):
        """Initialize knowledge storage service."""
        super().__init__(model_name='knowledge')
    
    def _extract_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata fields for knowledge index."""
        return {
            'uuid': data.get('uuid') or data.get('knowledge_id'),
            'knowledge_id': data.get('knowledge_id') or data.get('uuid'),
            'title': data.get('title', ''),
            'pattern_type': data.get('pattern_type', ''),
            'created_by': data.get('created_by'),  # UUID string
            'created_at': data.get('created_at', ''),
            'updated_at': data.get('updated_at', ''),
            'tags': data.get('tags', []),  # Store tags for filtering
        }
    
    def create_knowledge(
        self,
        pattern_type: str,
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
        created_by: Optional[str] = None
    ) -> Dict[str, Any]:
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
            Created knowledge item data dictionary
        """
        knowledge_id = str(uuid_lib.uuid4())
        now = datetime.utcnow().isoformat()
        
        knowledge_data = {
            'knowledge_id': knowledge_id,
            'pattern_type': pattern_type,
            'title': title,
            'content': content,
            'tags': tags or [],
            'metadata': metadata or {},
            'created_by': created_by,
            'created_at': now,
            'updated_at': now,
        }
        
        return self.create(knowledge_data, item_uuid=knowledge_id)
    
    def get_knowledge(self, knowledge_id: str) -> Optional[Dict[str, Any]]:
        """Get knowledge item by ID."""
        return self.get(knowledge_id)
    
    def update_knowledge(self, knowledge_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Update a knowledge item."""
        return self.update(knowledge_id, kwargs)
    
    def delete_knowledge(self, knowledge_id: str) -> bool:
        """Delete a knowledge item."""
        return self.delete(knowledge_id)
    
    def search_knowledge(
        self,
        query: Optional[str] = None,
        pattern_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge base items.
        
        Args:
            query: Search query string
            pattern_type: Filter by pattern type
            tags: Filter by tags
            limit: Maximum results
            
        Returns:
            List of knowledge item dictionaries
        """
        filters = {}
        if pattern_type:
            filters['pattern_type'] = pattern_type
        
        # Get all items matching filters
        result = self.list(filters=filters, limit=None, offset=0)
        items = result.get('items', [])
        
        # Apply text search if query provided
        if query:
            query_lower = query.lower()
            items = [
                item for item in items
                if query_lower in item.get('title', '').lower() or
                   query_lower in item.get('content', '').lower()
            ]
        
        # Apply tag filter
        if tags:
            filtered_items = []
            for item in items:
                item_tags = item.get('tags', [])
                if any(tag in item_tags for tag in tags):
                    filtered_items.append(item)
            items = filtered_items
        
        return items[:limit]
