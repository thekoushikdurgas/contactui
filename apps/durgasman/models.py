"""Durgasman API Testing App Models."""

from django.db import models
from django.conf import settings
import json


class Collection(models.Model):
    """Groups API requests (from Postman collections)."""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    ai_docs = models.TextField(blank=True)  # AI-generated documentation

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.user.username})"


class ApiRequest(models.Model):
    """Individual API requests."""
    HTTP_METHODS = [
        ('GET', 'GET'), ('POST', 'POST'), ('PUT', 'PUT'),
        ('PATCH', 'PATCH'), ('DELETE', 'DELETE'), ('HEAD', 'HEAD'),
        ('OPTIONS', 'OPTIONS')
    ]

    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='requests')
    name = models.CharField(max_length=200)
    method = models.CharField(max_length=10, choices=HTTP_METHODS)
    url = models.TextField()
    headers = models.JSONField(default=list)  # [{"key": "Content-Type", "value": "application/json", "enabled": True}]
    params = models.JSONField(default=list)   # Query parameters
    body = models.TextField(blank=True)
    auth_type = models.CharField(max_length=50, default='None')
    response_schema = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.method} {self.name}"


class Environment(models.Model):
    """Environment variable management."""
    name = models.CharField(max_length=200)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='durgasman_environments')
    variables_list = models.JSONField(default=list)  # [{"key": "baseUrl", "value": "https://api.example.com", "enabled": True}]
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.user.username})"


class EnvVariable(models.Model):
    """Individual environment variables."""
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE, related_name='env_variables')
    key = models.CharField(max_length=200)
    value = models.TextField()
    enabled = models.BooleanField(default=True)

    class Meta:
        unique_together = ['environment', 'key']
        ordering = ['key']

    def __str__(self):
        return f"{self.key} = {self.value[:50]}{'...' if len(self.value) > 50 else ''}"


class RequestHistory(models.Model):
    """Execution history and responses."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=10)
    url = models.TextField()
    request_headers = models.JSONField(default=dict)
    request_body = models.TextField(blank=True)
    response_status = models.IntegerField()
    response_headers = models.JSONField(default=dict)
    response_body = models.TextField()
    response_time_ms = models.IntegerField()
    response_size_bytes = models.IntegerField()

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['response_status']),
        ]

    def __str__(self):
        return f"{self.method} {self.url} -> {self.response_status} ({self.response_time_ms}ms)"


class MockEndpoint(models.Model):
    """Mock server endpoints."""
    path = models.CharField(max_length=500)
    method = models.CharField(max_length=10, choices=ApiRequest.HTTP_METHODS)
    response_body = models.TextField()
    response_schema = models.TextField(blank=True)
    status_code = models.IntegerField(default=200)
    enabled = models.BooleanField(default=True)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, null=True, blank=True, related_name='mocks')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['path', 'method']
        ordering = ['path']

    def __str__(self):
        return f"{self.method} {self.path} -> {self.status_code}"