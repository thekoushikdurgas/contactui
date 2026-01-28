"""Templates models."""
import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Template(models.Model):
    """Model for documentation templates."""
    
    CATEGORY_CHOICES = [
        ('api', 'API Documentation'),
        ('guide', 'User Guide'),
        ('reference', 'Reference'),
        ('tutorial', 'Tutorial'),
        ('changelog', 'Changelog'),
    ]
    
    template_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='api')
    description = models.TextField(blank=True)
    content = models.TextField()  # Template content with variables
    variables = models.JSONField(default=dict, blank=True)  # Template variables definition
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'templates'
        verbose_name = 'Template'
        verbose_name_plural = 'Templates'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['template_id']),
            models.Index(fields=['category']),
            models.Index(fields=['created_by', '-created_at']),
        ]
    
    def __str__(self):
        return self.name
