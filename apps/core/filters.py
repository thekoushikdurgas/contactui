"""
Base filter classes for Django REST Framework.
"""

from rest_framework.filters import BaseFilterBackend
from django_filters.rest_framework import DjangoFilterBackend


class IsActiveFilterBackend(BaseFilterBackend):
    """
    Filter backend that allows filtering by is_active field.
    Usage: Add ?is_active=true or ?is_active=false to the URL
    """
    
    def filter_queryset(self, request, queryset, view):
        is_active = request.query_params.get('is_active', None)
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        return queryset


class TimestampFilterBackend(BaseFilterBackend):
    """
    Filter backend for timestamp-based filtering.
    Usage: ?created_after=2024-01-01&created_before=2024-12-31
    """
    
    def filter_queryset(self, request, queryset, view):
        created_after = request.query_params.get('created_after', None)
        created_before = request.query_params.get('created_before', None)
        
        if created_after:
            queryset = queryset.filter(created_at__gte=created_after)
        if created_before:
            queryset = queryset.filter(created_at__lte=created_before)
        
        return queryset
