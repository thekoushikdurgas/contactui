"""Roadmap models."""
import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class RoadmapItem(models.Model):
    """Model for roadmap items."""
    
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    item_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    progress = models.IntegerField(default=0)  # 0-100
    due_date = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='roadmap_items')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'roadmap_items'
        verbose_name = 'Roadmap Item'
        verbose_name_plural = 'Roadmap Items'
        ordering = ['due_date', '-created_at']
        indexes = [
            models.Index(fields=['item_id']),
            models.Index(fields=['status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['created_by', '-created_at']),
        ]
    
    def __str__(self):
        return self.title
