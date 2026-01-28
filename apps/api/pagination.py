"""
Centralized API pagination configuration.

This module provides common pagination classes for all APIs.
"""

from apps.core.pagination import (
    StandardResultsSetPagination,
    LargeResultsSetPagination,
    SmallResultsSetPagination,
    CustomLimitOffsetPagination,
)

__all__ = [
    'StandardResultsSetPagination',
    'LargeResultsSetPagination',
    'SmallResultsSetPagination',
    'CustomLimitOffsetPagination',
]
