"""JSON Store models."""
import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class JSONStore(models.Model):
    """Model for storing JSON data."""
    
    TYPE_CHOICES = [
        ('postman_environment', 'Postman Environment'),
        ('config', 'Configuration'),
        ('data', 'Data'),
        ('custom', 'Custom'),
    ]
    
    store_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=255, unique=True, db_index=True)
    data = models.JSONField(default=dict)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='custom')
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='json_stores')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'json_store'
        verbose_name = 'JSON Store'
        verbose_name_plural = 'JSON Stores'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['store_id']),
            models.Index(fields=['key']),
            models.Index(fields=['type']),
            models.Index(fields=['created_by', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.key} ({self.type})"
