"""
Central API gateway URL configuration.

This module provides centralized routing for all API versions.
"""

from django.urls import path, include

app_name = 'api'

urlpatterns = [
    # API v1 - Documentation API
    path('v1/', include('apps.documentation.api.v1.urls', namespace='v1')),
    
    # API v2 - Alternative version (if exists)
    path('v2/', include('apps.documentation.api.urls', namespace='v2')),
    
    # App-specific APIs
    path('ai/', include('apps.ai_agent.api.urls', namespace='ai')),
    path('knowledge/', include('apps.knowledge.api.urls', namespace='knowledge')),
    path('tasks/', include('apps.tasks.api.urls', namespace='tasks')),
    path('durgasflow/', include('apps.durgasflow.api.urls', namespace='durgasflow')),
]
