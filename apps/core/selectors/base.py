"""
Base selector class for query optimization and data retrieval.

Selectors encapsulate complex database queries and provide a clean interface
for retrieving data. They help separate query logic from views and services.
"""

from typing import Optional, List, Any, Dict, TypeVar
from django.db import models
from django.core.cache import cache
import logging

# Type variable for model instances
ModelType = TypeVar('ModelType', bound=models.Model)


class BaseSelector:
    """
    Base selector class that provides common query patterns.
    
    Selectors should be used to:
    - Encapsulate complex queries
    - Optimize database access (select_related, prefetch_related)
    - Provide reusable query methods
    - Cache frequently accessed data
    """
    
    def __init__(self, model: type[models.Model]) -> None:
        """
        Initialize selector with a model.
        
        Args:
            model: Django model class
        """
        self.model = model
        self.logger = logging.getLogger(f"{__name__}.{model.__name__}")
    
    def get_by_id(
        self, 
        pk: Any, 
        use_cache: bool = True,
        select_related: Optional[List[str]] = None,
        prefetch_related: Optional[List[str]] = None
    ) -> Optional[ModelType]:
        """
        Get a single object by primary key with optional relationship loading.
        
        Args:
            pk: Primary key value
            use_cache: Whether to use cache
            select_related: List of ForeignKey/OneToOne fields to prefetch
            prefetch_related: List of ManyToMany/reverse FK fields to prefetch
            
        Returns:
            Model instance or None
        """
        cache_key = f"{self.model.__name__}:{pk}" if use_cache else None
        
        if use_cache and cache_key:
            cached = cache.get(cache_key)
            if cached:
                return cached
        
        try:
            queryset = self.model.objects.all()
            
            if select_related:
                queryset = queryset.select_related(*select_related)
            if prefetch_related:
                queryset = queryset.prefetch_related(*prefetch_related)
                
            obj = queryset.get(pk=pk)
            
            if use_cache and cache_key:
                cache.set(cache_key, obj, 300)  # 5 minutes
            return obj
        except self.model.DoesNotExist:
            return None
    
    def get_all(
        self, 
        filters: Optional[Dict] = None, 
        order_by: Optional[List[str]] = None,
        select_related: Optional[List[str]] = None,
        prefetch_related: Optional[List[str]] = None
    ) -> models.QuerySet:
        """
        Get all objects with optional filtering, ordering, and relationship loading.
        
        Args:
            filters: Dictionary of field filters
            order_by: List of fields to order by
            select_related: List of ForeignKey/OneToOne fields to prefetch
            prefetch_related: List of ManyToMany/reverse FK fields to prefetch
            
        Returns:
            QuerySet
        """
        queryset = self.model.objects.all()
        
        if select_related:
            queryset = queryset.select_related(*select_related)
        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)
        
        if filters:
            queryset = queryset.filter(**filters)
        
        if order_by:
            queryset = queryset.order_by(*order_by)
        
        return queryset
    
    def get_active(self) -> models.QuerySet:
        """
        Get all active objects (if model has is_active field).
        
        Returns:
            QuerySet of active objects
        """
        if hasattr(self.model, 'is_active'):
            return self.model.objects.filter(is_active=True)
        return self.model.objects.all()
    
    def get_recent(self, days: int = 7, limit: Optional[int] = None) -> models.QuerySet:
        """
        Get recently created objects.
        
        Args:
            days: Number of days to look back
            limit: Optional limit on number of results
            
        Returns:
            QuerySet of recent objects
        """
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff = timezone.now() - timedelta(days=days)
        queryset = self.model.objects.filter(created_at__gte=cutoff)
        
        if limit:
            queryset = queryset[:limit]
        
        return queryset
    
    def count(self, filters: Optional[Dict] = None) -> int:
        """
        Count objects matching filters.
        
        Args:
            filters: Optional dictionary of field filters
            
        Returns:
            Count of matching objects
        """
        queryset = self.model.objects.all()
        if filters:
            queryset = queryset.filter(**filters)
        return queryset.count()
    
    def exists(self, filters: Dict) -> bool:
        """
        Check if objects matching filters exist.
        
        Args:
            filters: Dictionary of field filters
            
        Returns:
            True if objects exist, False otherwise
        """
        return self.model.objects.filter(**filters).exists()
