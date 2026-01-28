"""
Abstract base models for the DocsAI application.

These models provide common functionality that can be inherited by other models.
"""

from typing import Optional
from django.db import models
from django.utils import timezone
import uuid


class TimeStampedModel(models.Model):
    """Abstract base model with timestamp fields (created_at, updated_at)."""
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
        get_latest_by = 'created_at'


class ActiveModel(models.Model):
    """Abstract model with is_active field for soft activation/deactivation."""
    
    is_active = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """Abstract model with soft delete functionality."""
    
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    
    class Meta:
        abstract = True
    
    def soft_delete(self) -> None:
        """Mark the object as deleted without actually deleting it."""
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])
    
    def restore(self) -> None:
        """Restore a soft-deleted object."""
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])
    
    @property
    def is_deleted(self) -> bool:
        """Check if the object is soft-deleted."""
        return self.deleted_at is not None


class UUIDModel(models.Model):
    """Abstract model with UUID primary key instead of auto-incrementing integer."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    class Meta:
        abstract = True


class BaseModel(TimeStampedModel, ActiveModel):
    """
    Complete base model combining timestamp and active functionality.
    
    Use this as the base class for most models that need timestamps and is_active.
    """
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
        get_latest_by = 'created_at'


class BaseModelWithUUID(TimeStampedModel, ActiveModel, UUIDModel):
    """
    Base model with UUID primary key, timestamps, and active status.
    
    Use this when you need UUID primary keys instead of integer IDs.
    """
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
        get_latest_by = 'created_at'
