"""
Core models for the DocsAI application.

This file is maintained for backward compatibility.
New code should import from apps.core.models directly.
"""

# Import from new structure (models package)
from .models.user import User
from .models.base import (
    TimeStampedModel,
    ActiveModel,
    SoftDeleteModel,
    UUIDModel,
    BaseModel,
)

__all__ = [
    'User',
    'TimeStampedModel',
    'ActiveModel',
    'SoftDeleteModel',
    'UUIDModel',
    'BaseModel',
]

