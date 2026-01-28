"""
URL configuration for REST API v1 - documentation GETs and dashboard.

- Health & Info: 7
- Pages: 20 GETs (pages_urls)
- Endpoints, Relationships, Postman: 28, 38, 14 GETs + Index + Dashboard
"""

from django.urls import path, include

from . import health, core, docs_meta

urlpatterns = [
    # ==========================================================================
    # Health & Info (7 endpoints)
    # ==========================================================================
    path('', health.service_info, name='root'),
    path('health/', health.health, name='health'),
    path('health/database/', health.health_database, name='health_database'),
    path('health/cache/', health.health_cache, name='health_cache'),
    path('health/storage/', health.health_storage, name='health_storage'),

    # ==========================================================================
    # Docs / meta - endpoint statistics (optional)
    # ==========================================================================
    path('docs/endpoint-stats/', docs_meta.endpoint_stats, name='docs_endpoint_stats'),

    # ==========================================================================
    # Pages API - 20 GET routes (Lambda parity)
    # ==========================================================================
    path('pages/', include('apps.documentation.api.v1.pages_urls')),

    # ==========================================================================
    # Endpoints API - 28 GET routes (Lambda parity)
    # ==========================================================================
    path('endpoints/', include('apps.documentation.api.v1.endpoints_urls')),

    # ==========================================================================
    # Relationships API - 38 GET routes (Lambda parity)
    # ==========================================================================
    path('relationships/', include('apps.documentation.api.v1.relationships_urls')),

    # ==========================================================================
    # Postman API - 14 GET routes (Lambda parity)
    # ==========================================================================
    path('postman/', include('apps.documentation.api.v1.postman_urls')),

    # ==========================================================================
    # Dashboard Pagination API (4 endpoints)
    # Used by dashboard tabs for client-side pagination and filtering
    # ==========================================================================
    path('dashboard/pages/', core.dashboard_pages, name='dashboard_pages'),
    path('dashboard/endpoints/', core.dashboard_endpoints, name='dashboard_endpoints'),
    path('dashboard/relationships/', core.dashboard_relationships, name='dashboard_relationships'),
    path('dashboard/postman/', core.dashboard_postman, name='dashboard_postman'),
]
