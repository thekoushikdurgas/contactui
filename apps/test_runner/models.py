"""Test Runner models."""
import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class TestSuite(models.Model):
    """Model for test suites."""
    
    suite_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    test_files = models.JSONField(default=list, blank=True)  # List of test file paths
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ])
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='test_suites')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'test_suites'
        verbose_name = 'Test Suite'
        verbose_name_plural = 'Test Suites'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['suite_id']),
            models.Index(fields=['status']),
            models.Index(fields=['created_by', '-created_at']),
        ]
    
    def __str__(self):
        return self.name


class TestRun(models.Model):
    """Model for test run executions."""
    
    run_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    suite = models.ForeignKey(TestSuite, on_delete=models.CASCADE, related_name='runs')
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ])
    results = models.JSONField(default=dict, blank=True)  # Test results data
    passed = models.IntegerField(default=0)
    failed = models.IntegerField(default=0)
    skipped = models.IntegerField(default=0)
    total = models.IntegerField(default=0)
    started_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='test_runs')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'test_runs'
        verbose_name = 'Test Run'
        verbose_name_plural = 'Test Runs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['run_id']),
            models.Index(fields=['suite', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.suite.name} - {self.status}"
