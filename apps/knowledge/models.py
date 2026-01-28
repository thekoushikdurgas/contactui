"""Knowledge base models."""
import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class KnowledgeBase(models.Model):
    """Knowledge base model."""
    
    PATTERN_TYPE_CHOICES = [
        ('pattern', 'Pattern'),
        ('documentation', 'Documentation'),
        ('code_snippet', 'Code Snippet'),
        ('best_practice', 'Best Practice'),
        ('api_pattern', 'API Pattern'),
        ('architecture', 'Architecture'),
    ]
    
    knowledge_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pattern_type = models.CharField(max_length=50, choices=PATTERN_TYPE_CHOICES)
    title = models.CharField(max_length=500)
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    tags = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='knowledge_items')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'knowledge_base'
        verbose_name = 'Knowledge Base Item'
        verbose_name_plural = 'Knowledge Base Items'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['knowledge_id']),
            models.Index(fields=['pattern_type']),
            models.Index(fields=['-updated_at']),
        ]
    
    def __str__(self):
        return self.title
