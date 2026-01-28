"""Accessibility models."""
import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class AccessibilityScan(models.Model):
    """Model for accessibility scans."""
    
    SEVERITY_CHOICES = [
        ('critical', 'Critical'),
        ('serious', 'Serious'),
        ('moderate', 'Moderate'),
        ('minor', 'Minor'),
    ]
    
    scan_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.URLField()
    issues = models.JSONField(default=list, blank=True)  # List of accessibility issues
    score = models.IntegerField(default=0)  # Accessibility score (0-100)
    total_issues = models.IntegerField(default=0)
    critical_issues = models.IntegerField(default=0)
    warning_issues = models.IntegerField(default=0)
    info_issues = models.IntegerField(default=0)
    scanned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='accessibility_scans')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'accessibility_scans'
        verbose_name = 'Accessibility Scan'
        verbose_name_plural = 'Accessibility Scans'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['scan_id']),
            models.Index(fields=['url']),
            models.Index(fields=['scanned_by', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.url} - Score: {self.score}"
