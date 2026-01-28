"""Operations models."""
import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class OperationLog(models.Model):
    """Model for tracking system operations."""
    
    OPERATION_TYPE_CHOICES = [
        ('documentation_sync', 'Documentation Sync'),
        ('s3_sync', 'S3 Sync'),
        ('codebase_analysis', 'Codebase Analysis'),
        ('ai_learning', 'AI Learning'),
        ('knowledge_extraction', 'Knowledge Extraction'),
        ('data_migration', 'Data Migration'),
        ('system_backup', 'System Backup'),
    ]
    
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    operation_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    operation_type = models.CharField(max_length=50, choices=OPERATION_TYPE_CHOICES)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    progress = models.IntegerField(default=0)  # 0-100
    metadata = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    started_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='started_operations')
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'operation_logs'
        verbose_name = 'Operation Log'
        verbose_name_plural = 'Operation Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['operation_id']),
            models.Index(fields=['operation_type']),
            models.Index(fields=['status']),
            models.Index(fields=['started_by', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.status}"
