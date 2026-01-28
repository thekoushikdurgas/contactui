"""
Centralized API permissions.

This module provides common permission classes for all APIs.
"""

from rest_framework import permissions
from apps.core.permissions import (
    IsOwnerOrReadOnly,
    IsAuthenticatedOrReadOnly,
    IsStaffOrReadOnly,
)

__all__ = [
    'IsOwnerOrReadOnly',
    'IsAuthenticatedOrReadOnly',
    'IsStaffOrReadOnly',
    'IsAPIAuthenticated',
]


class IsAPIAuthenticated(permissions.IsAuthenticated):
    """
    Permission class that requires authentication for API access.
    Used as default for all API endpoints.
    """
    message = 'Authentication required to access this API endpoint.'


class IsAPIAdmin(permissions.IsAdminUser):
    """
    Permission class that requires admin access for API endpoints.
    """
    message = 'Admin access required for this operation.'
