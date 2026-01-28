"""User model for the DocsAI application."""

from django.contrib.auth.models import AbstractUser
from django.db import models
from .base import TimeStampedModel
from ..managers import BaseManager


class User(AbstractUser, TimeStampedModel):
    """Extended user model with additional fields."""
    
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    theme_preference = models.CharField(
        max_length=10,
        choices=[('light', 'Light'), ('dark', 'Dark')],
        default='light',
        db_index=True
    )
    api_keys = models.JSONField(default=dict, blank=True)
    
    # Use custom manager
    objects = BaseManager()
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['email']),
            models.Index(fields=['is_active', '-created_at']),
        ]
    
    def __str__(self):
        return self.username
