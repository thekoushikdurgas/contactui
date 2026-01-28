"""Knowledge base service for managing knowledge items."""
import logging
from typing import Optional, Dict, Any, List
from django.db.models import Q
from apps.core.services.base_service import BaseService, log_performance
from .models import KnowledgeBase

logger = logging.getLogger(__name__)


class KnowledgeBaseService(BaseService):
    """Service for managing knowledge base items."""
    
    def __init__(self):
        """Initialize knowledge base service."""
        super().__init__('KnowledgeBaseService')
        self.cache_timeout = 600  # 10 minutes
    
    @log_performance
    def search(self, query: str, pattern_type: Optional[str] = None, tags: Optional[List[str]] = None, limit: int = 20) -> List[KnowledgeBase]:
        """
        Search knowledge base items.
        
        Args:
            query: Search query
            pattern_type: Filter by pattern type
            tags: Filter by tags
            limit: Maximum number of results
            
        Returns:
            List of KnowledgeBase instances
        """
        # Check cache first
        cache_key = self._get_cache_key('search', query=query, pattern_type=pattern_type, tags=tags, limit=limit)
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result
        
        queryset = KnowledgeBase.objects.all()
        
        # Text search
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query)
            )
        
        # Filter by pattern type
        if pattern_type:
            queryset = queryset.filter(pattern_type=pattern_type)
        
        # Filter by tags
        if tags:
            for tag in tags:
                queryset = queryset.filter(tags__contains=[tag])
        
        results = list(queryset[:limit])
        
        # Cache results
        self._set_cache(cache_key, results, self.cache_timeout)
        
        return results
    
    @log_performance
    def get_by_id(self, knowledge_id: str) -> Optional[KnowledgeBase]:
        """
        Get knowledge base item by ID.
        
        Args:
            knowledge_id: Knowledge base item ID
            
        Returns:
            KnowledgeBase instance, or None if not found
        """
        cache_key = self._get_cache_key('get_by_id', knowledge_id=knowledge_id)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            item = KnowledgeBase.objects.get(knowledge_id=knowledge_id)
            self._set_cache(cache_key, item, self.cache_timeout)
            return item
        except KnowledgeBase.DoesNotExist:
            return None
    
    @log_performance
    def create(self, pattern_type: str, title: str, content: str, tags: List[str] = None, metadata: Dict = None, created_by=None) -> KnowledgeBase:
        """
        Create a new knowledge base item.
        
        Args:
            pattern_type: Pattern type
            title: Title
            content: Content
            tags: List of tags
            metadata: Metadata dictionary
            created_by: User who created the item
            
        Returns:
            Created KnowledgeBase instance
        """
        # Validate required fields
        is_valid, error_msg = self._validate_input(
            {'pattern_type': pattern_type, 'title': title, 'content': content},
            ['pattern_type', 'title', 'content']
        )
        if not is_valid:
            raise ValueError(error_msg)
        
        item = KnowledgeBase.objects.create(
            pattern_type=pattern_type,
            title=title,
            content=content,
            tags=tags or [],
            metadata=metadata or {},
            created_by=created_by
        )
        
        # Invalidate cache
        self._clear_cache()
        
        return item
    
    @log_performance
    def update(self, knowledge_id: str, **kwargs) -> Optional[KnowledgeBase]:
        """
        Update a knowledge base item.
        
        Args:
            knowledge_id: Knowledge base item ID
            **kwargs: Fields to update
            
        Returns:
            Updated KnowledgeBase instance, or None if not found
        """
        try:
            item = KnowledgeBase.objects.get(knowledge_id=knowledge_id)
            for key, value in kwargs.items():
                if hasattr(item, key):
                    setattr(item, key, value)
            item.save()
            
            # Invalidate cache
            cache_key = self._get_cache_key('get_by_id', knowledge_id=knowledge_id)
            self._clear_cache(cache_key)
            self._clear_cache()  # Clear search cache too
            
            return item
        except KnowledgeBase.DoesNotExist:
            return None
    
    @log_performance
    def delete(self, knowledge_id: str) -> bool:
        """
        Delete a knowledge base item.
        
        Args:
            knowledge_id: Knowledge base item ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            item = KnowledgeBase.objects.get(knowledge_id=knowledge_id)
            item.delete()
            
            # Invalidate cache
            cache_key = self._get_cache_key('get_by_id', knowledge_id=knowledge_id)
            self._clear_cache(cache_key)
            self._clear_cache()  # Clear search cache too
            
            return True
        except KnowledgeBase.DoesNotExist:
            return False
    
    @log_performance
    def get_related(self, knowledge_id: str, limit: int = 5) -> List[KnowledgeBase]:
        """
        Get related knowledge base items.
        
        Args:
            knowledge_id: Knowledge base item ID
            limit: Maximum number of results
            
        Returns:
            List of related KnowledgeBase instances
        """
        try:
            item = KnowledgeBase.objects.get(knowledge_id=knowledge_id)
            
            # Find items with similar tags or pattern type
            related = KnowledgeBase.objects.filter(
                Q(pattern_type=item.pattern_type) |
                Q(tags__overlap=item.tags)
            ).exclude(knowledge_id=knowledge_id)
            
            return list(related[:limit])
        except KnowledgeBase.DoesNotExist:
            return []
