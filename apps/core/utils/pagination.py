"""
Pagination utilities for API responses.
"""

from typing import Dict, Any, List, Optional
from django.http import JsonResponse


class PaginationHelper:
    """
    Helper class for consistent pagination across API endpoints.
    """
    
    @staticmethod
    def get_pagination_params(request) -> Dict[str, int]:
        """
        Extract pagination parameters from request.
        
        Args:
            request: Django request object
            
        Returns:
            Dictionary with 'limit' and 'offset'
        """
        try:
            limit = int(request.GET.get('limit', 20))
            offset = int(request.GET.get('offset', 0))
        except (ValueError, TypeError):
            limit = 20
            offset = 0
        
        # Enforce reasonable limits
        if limit < 1:
            limit = 20
        if limit > 100:
            limit = 100
        if offset < 0:
            offset = 0
        
        return {
            'limit': limit,
            'offset': offset
        }
    
    @staticmethod
    def paginate_list(
        items: List[Any],
        limit: int,
        offset: int
    ) -> Dict[str, Any]:
        """
        Paginate a list of items.
        
        Args:
            items: List of items to paginate
            limit: Maximum number of items per page
            offset: Number of items to skip
            
        Returns:
            Dictionary with paginated results and metadata
        """
        total = len(items)
        paginated_items = items[offset:offset + limit]
        
        return {
            'items': paginated_items,
            'total': total,
            'limit': limit,
            'offset': offset,
            'has_next': (offset + limit) < total,
            'has_previous': offset > 0,
            'page': (offset // limit) + 1 if limit > 0 else 1,
            'total_pages': (total + limit - 1) // limit if limit > 0 else 1
        }
    
    @staticmethod
    def create_paginated_response(
        items: List[Any],
        limit: int,
        offset: int,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> JsonResponse:
        """
        Create a paginated JSON response.
        
        Args:
            items: List of items to paginate
            limit: Maximum number of items per page
            offset: Number of items to skip
            additional_data: Optional additional data to include in response
            
        Returns:
            JsonResponse with paginated data
        """
        paginated = PaginationHelper.paginate_list(items, limit, offset)
        
        response_data = {
            'success': True,
            **paginated
        }
        
        if additional_data:
            response_data.update(additional_data)
        
        return JsonResponse(response_data)
    
    @staticmethod
    def get_page_number(request) -> int:
        """
        Get page number from request (1-based).
        
        Args:
            request: Django request object
            
        Returns:
            Page number (default: 1)
        """
        try:
            page = int(request.GET.get('page', 1))
            return max(1, page)
        except (ValueError, TypeError):
            return 1
    
    @staticmethod
    def page_to_offset(page: int, limit: int) -> int:
        """
        Convert page number to offset.
        
        Args:
            page: Page number (1-based)
            limit: Items per page
            
        Returns:
            Offset value
        """
        return (page - 1) * limit
