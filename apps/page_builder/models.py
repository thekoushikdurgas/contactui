"""Page Builder models."""
import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class PageComponent(models.Model):
    """Model for page builder components."""
    
    COMPONENT_TYPE_CHOICES = [
        ('text', 'Text Block'),
        ('image', 'Image'),
        ('code', 'Code Block'),
        ('table', 'Table'),
        ('heading', 'Heading'),
        ('list', 'List'),
        ('link', 'Link'),
        ('divider', 'Divider'),
    ]
    
    component_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    page_id = models.CharField(max_length=255, db_index=True)  # Reference to page
    component_type = models.CharField(max_length=50, choices=COMPONENT_TYPE_CHOICES)
    properties = models.JSONField(default=dict, blank=True)  # Component properties
    order = models.IntegerField(default=0)  # Display order
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='page_components')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'page_components'
        verbose_name = 'Page Component'
        verbose_name_plural = 'Page Components'
        ordering = ['page_id', 'order']
        indexes = [
            models.Index(fields=['component_id']),
            models.Index(fields=['page_id', 'order']),
            models.Index(fields=['component_type']),
        ]
    
    def __str__(self):
        return f"{self.component_type} - {self.page_id}"
