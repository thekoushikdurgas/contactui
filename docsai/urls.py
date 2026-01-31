"""
URL configuration for docsai project.
"""
from pathlib import Path
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.documentation.views.api_docs import api_docs_index

BASE_DIR = Path(__file__).resolve().parent.parent

urlpatterns = [
    path('', include('apps.core.urls')),
    path('docs/', include('apps.documentation.urls')),
    path('durgasman/', include('apps.durgasman.urls')),
    path('analytics/', include('apps.analytics.urls')),
    path('ai/', include('apps.ai_agent.urls')),
    path('codebase/', include('apps.codebase.urls')),
    path('tasks/', include('apps.tasks.urls')),
    path('media/', include('apps.media.urls')),
    path('graph/', include('apps.graph.urls')),
    path('tests/', include('apps.test_runner.urls')),
    path('accessibility/', include('apps.accessibility.urls')),
    path('roadmap/', include('apps.roadmap.urls')),
    path('postman/', include('apps.postman.urls')),
    path('templates/', include('apps.templates.urls')),
    path('architecture/', include('apps.architecture.urls')),
    path('database/', include('apps.database.urls')),
    path('json-store/', include('apps.json_store.urls')),
    path('operations/', include('apps.operations.urls')),
    path('page-builder/', include('apps.page_builder.urls')),
    path('knowledge/', include('apps.knowledge.urls')),
    path('admin/', include('apps.admin.urls')),
    # REST API v1 - documentation GETs + health + dashboard
    path('api/v1/', include('apps.documentation.api.v1.urls')),
    # OpenAPI schema and interactive API docs (Swagger UI, ReDoc)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', api_docs_index, name='swagger-ui'),
    path('api/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui-raw'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    # Durgasflow - Workflow Automation (keeping non-API routes)
    path('durgasflow/', include('apps.durgasflow.urls')),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Serve static files from static directory (source files)
    urlpatterns += static(settings.STATIC_URL, document_root=BASE_DIR / 'static')
