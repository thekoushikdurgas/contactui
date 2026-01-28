"""URL configuration for documentation app."""
from django.urls import path, include
from django.shortcuts import redirect
from django.http import HttpResponsePermanentRedirect
from .views import dashboard

def create_redirect_view(target_name):
    """Create a redirect view function for a given URL name."""
    def redirect_view(request):
        from django.urls import reverse
        try:
            target_url = reverse(f'documentation:{target_name}')
            # Preserve query parameters
            query_string = request.GET.urlencode()
            if query_string:
                target_url = f"{target_url}?{query_string}"
            return HttpResponsePermanentRedirect(target_url)
        except Exception:
            # Fallback to dashboard if route doesn't exist
            return redirect('documentation:dashboard')
    return redirect_view
# Removed: api_router, api_urls_versioned (API routes removed)
# Import legacy views directly from views.py file (not from views package)
# Use importlib to avoid package/directory conflict
import importlib.util
import os
views_file_path = os.path.join(os.path.dirname(__file__), 'views.py')
spec = importlib.util.spec_from_file_location("legacy_views", views_file_path)
legacy_views = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy_views)
from .views.pages_views import (
    page_list_view,
    page_detail_view,
    page_form_view,
    page_create_api,
    page_draft_api,
    page_update_api,
    page_delete_api,
)
from .views.endpoints_views import (
    endpoint_list_view,
    endpoint_detail_view,
    endpoint_form_view,
    endpoint_create_api,
    endpoint_draft_api,
    endpoint_update_api,
    endpoint_delete_api,
    endpoint_delete_view,
)
from .views.relationships_views import (
    relationship_list_view,
    relationship_detail_view,
    relationship_form_view,
    relationship_create_api,
    relationship_update_api,
    relationship_delete_api,
)
from .views.postman_views import (
    postman_detail_view,
    postman_form_view,
)
from .views import operations
from .views import media_views
from .views import media_manager_dashboard
from .api import dashboard_api
from .api.dashboard_api_bulk import dashboard_bulk_delete_api
from .api import statistics_api
from .api import views as api_views
from .api import media_manager_api

app_name = 'documentation'

urlpatterns = [
    # Dashboard
    path('', dashboard.documentation_dashboard, name='dashboard'),
    path('pages/', dashboard.documentation_dashboard, name='dashboard_pages'),
    path('endpoints/', dashboard.documentation_dashboard, name='dashboard_endpoints'),
    path('relationships/', dashboard.documentation_dashboard, name='dashboard_relationships'),
    
    # Dashboard API endpoints (for pagination)
    path('api/dashboard/pages/', dashboard_api.dashboard_pages_api, name='api_dashboard_pages'),
    path('api/dashboard/endpoints/', dashboard_api.dashboard_endpoints_api, name='api_dashboard_endpoints'),
    path('api/dashboard/relationships/', dashboard_api.dashboard_relationships_api, name='api_dashboard_relationships'),
    path('api/dashboard/postman/', dashboard_api.dashboard_postman_api, name='api_dashboard_postman'),
    path('api/dashboard/graph/', dashboard.dashboard_graph_api, name='api_dashboard_graph'),
    
    # Statistics API endpoints (replaces API v1 statistics endpoints)
    path('api/statistics/pages/statistics/', statistics_api.statistics_pages_statistics, name='api_statistics_pages_statistics'),
    path('api/statistics/pages/types/', statistics_api.statistics_pages_types, name='api_statistics_pages_types'),
    path('api/statistics/endpoints/api-versions/', statistics_api.statistics_endpoints_api_versions, name='api_statistics_endpoints_api_versions'),
    path('api/statistics/endpoints/methods/', statistics_api.statistics_endpoints_methods, name='api_statistics_endpoints_methods'),
    path('api/statistics/relationships/statistics/', statistics_api.statistics_relationships_statistics, name='api_statistics_relationships_statistics'),
    path('api/statistics/postman/statistics/', statistics_api.statistics_postman_statistics, name='api_statistics_postman_statistics'),
    
    # Bulk operations
    path('api/dashboard/bulk-delete/', dashboard_bulk_delete_api, name='api_dashboard_bulk_delete'),
    
    # API endpoints - REMOVED (most APIs removed)
    # Removed: /api/versions/, /api/v2/, /api/health/, /api/stats/, /api/schemas/
    # Services are now used directly in views and minimal dashboard/media APIs
    # Note: /api/v1/ is included at root level in docsai/urls.py for statistics endpoints
    
    # ============================================================================
    # Unified Dashboard Routes - Migrated from /docs/media-manager/
    # All 119 endpoints integrated into /docs/ dashboard
    # ============================================================================
    
    # Health & Service Info Routes (7 routes)
    path('service-info/', media_manager_dashboard.media_manager_service_info, name='service_info'),
    path('docs/endpoint-stats/', media_manager_dashboard.media_manager_docs_endpoint_stats, name='docs_endpoint_stats'),
    path('health/database/', media_manager_dashboard.media_manager_health_database, name='health_database'),
    path('health/cache/', media_manager_dashboard.media_manager_health_cache, name='health_cache'),
    path('health/storage/', media_manager_dashboard.media_manager_health_storage, name='health_storage'),
    path('health/', media_manager_dashboard.media_manager_health, name='health'),
    
    # Statistics Route
    path('statistics/', media_manager_dashboard.media_manager_statistics, name='statistics'),
    
    # Pages API Routes (static routes before parameterized) - 20 routes
    path('pages/statistics/', media_manager_dashboard.media_manager_pages_statistics, name='pages_statistics'),
    path('pages/format/', media_manager_dashboard.media_manager_pages_format, name='pages_format'),
    path('pages/types/', media_manager_dashboard.media_manager_pages_types, name='pages_types'),
    path('pages/by-type/docs/', media_manager_dashboard.media_manager_pages_by_type_docs, name='pages_by_type_docs'),
    path('pages/by-type/marketing/', media_manager_dashboard.media_manager_pages_by_type_marketing, name='pages_by_type_marketing'),
    path('pages/by-type/dashboard/', media_manager_dashboard.media_manager_pages_by_type_dashboard, name='pages_by_type_dashboard'),
    # Generic pages by type route (must be after specific routes)
    path('pages/by-type/<str:page_type>/', media_manager_dashboard.media_manager_pages_by_type, name='pages_by_type'),
    path('pages/by-type/<str:page_type>/published/', media_manager_dashboard.media_manager_pages_by_type_published, name='pages_by_type_published'),
    path('pages/by-type/<str:page_type>/draft/', media_manager_dashboard.media_manager_pages_by_type_draft, name='pages_by_type_draft'),
    path('pages/by-type/<str:page_type>/stats/', media_manager_dashboard.media_manager_pages_by_type_stats, name='pages_by_type_stats'),
    path('pages/by-type/<str:page_type>/count/', media_manager_dashboard.media_manager_pages_by_type_count, name='pages_by_type_count'),
    path('pages/by-state/<str:state>/count/', media_manager_dashboard.media_manager_pages_by_state_count, name='pages_by_state_count'),
    path('pages/by-state/<str:state>/', media_manager_dashboard.media_manager_pages_by_state, name='pages_by_state'),
    path('pages/by-user-type/<str:user_type>/', media_manager_dashboard.media_manager_pages_by_user_type, name='pages_by_user_type'),
    # Page sub-resource routes (must be before page detail route)
    path('pages/<str:page_id>/sections/', media_manager_dashboard.media_manager_page_sections, name='page_sections'),
    path('pages/<str:page_id>/components/', media_manager_dashboard.media_manager_page_components, name='page_components'),
    path('pages/<str:page_id>/endpoints/', media_manager_dashboard.media_manager_page_endpoints, name='page_endpoints'),
    path('pages/<str:page_id>/versions/', media_manager_dashboard.media_manager_page_versions, name='page_versions'),
    path('pages/<str:page_id>/access-control/', media_manager_dashboard.media_manager_page_access_control, name='page_access_control'),
    # Page detail route (after sub-resources)
    path('pages/<str:page_id>/detail/', media_manager_dashboard.media_manager_page_detail, name='page_detail_enhanced'),
    
    # Endpoints API Routes (static routes before parameterized) - 28 routes
    path('endpoints/statistics/', media_manager_dashboard.media_manager_endpoints_statistics, name='endpoints_statistics'),
    path('endpoints/format/', media_manager_dashboard.media_manager_endpoints_format, name='endpoints_format'),
    path('endpoints/api-versions/', media_manager_dashboard.media_manager_endpoints_api_versions, name='endpoints_api_versions'),
    path('endpoints/methods/', media_manager_dashboard.media_manager_endpoints_methods, name='endpoints_methods'),
    path('endpoints/by-api-version/v1/', media_manager_dashboard.media_manager_endpoints_by_api_version_v1, name='endpoints_by_api_version_v1'),
    path('endpoints/by-api-version/v4/', media_manager_dashboard.media_manager_endpoints_by_api_version_v4, name='endpoints_by_api_version_v4'),
    path('endpoints/by-api-version/graphql/', media_manager_dashboard.media_manager_endpoints_by_api_version_graphql, name='endpoints_by_api_version_graphql'),
    # Generic endpoints by API version route (must be after specific routes)
    path('endpoints/by-api-version/<str:api_version>/', media_manager_dashboard.media_manager_endpoints_by_api_version, name='endpoints_by_api_version'),
    path('endpoints/by-api-version/<str:api_version>/count/', media_manager_dashboard.media_manager_endpoints_by_api_version_count, name='endpoints_by_api_version_count'),
    path('endpoints/by-api-version/<str:api_version>/stats/', media_manager_dashboard.media_manager_endpoints_by_api_version_stats, name='endpoints_by_api_version_stats'),
    path('endpoints/by-api-version/<str:api_version>/by-method/<str:method>/', media_manager_dashboard.media_manager_endpoints_by_api_version_by_method, name='endpoints_by_api_version_by_method'),
    path('endpoints/by-method/GET/', media_manager_dashboard.media_manager_endpoints_by_method_get, name='endpoints_by_method_get'),
    path('endpoints/by-method/POST/', media_manager_dashboard.media_manager_endpoints_by_method_post, name='endpoints_by_method_post'),
    path('endpoints/by-method/QUERY/', media_manager_dashboard.media_manager_endpoints_by_method_query, name='endpoints_by_method_query'),
    path('endpoints/by-method/MUTATION/', media_manager_dashboard.media_manager_endpoints_by_method_mutation, name='endpoints_by_method_mutation'),
    # Generic endpoints by method route (must be after specific routes)
    path('endpoints/by-method/<str:method>/', media_manager_dashboard.media_manager_endpoints_by_method, name='endpoints_by_method'),
    path('endpoints/by-method/<str:method>/count/', media_manager_dashboard.media_manager_endpoints_by_method_count, name='endpoints_by_method_count'),
    path('endpoints/by-method/<str:method>/stats/', media_manager_dashboard.media_manager_endpoints_by_method_stats, name='endpoints_by_method_stats'),
    path('endpoints/by-state/<str:state>/count/', media_manager_dashboard.media_manager_endpoints_by_state_count, name='endpoints_by_state_count'),
    path('endpoints/by-state/<str:state>/', media_manager_dashboard.media_manager_endpoints_by_state, name='endpoints_by_state'),
    path('endpoints/by-lambda/<str:service_name>/count/', media_manager_dashboard.media_manager_endpoints_by_lambda_count, name='endpoints_by_lambda_count'),
    path('endpoints/by-lambda/<str:service_name>/', media_manager_dashboard.media_manager_endpoints_by_lambda, name='endpoints_by_lambda'),
    # Endpoint sub-resource routes (must be before endpoint detail route)
    path('endpoints/<str:endpoint_id>/pages/', media_manager_dashboard.media_manager_endpoint_pages, name='endpoint_pages'),
    path('endpoints/<str:endpoint_id>/access-control/', media_manager_dashboard.media_manager_endpoint_access_control, name='endpoint_access_control'),
    path('endpoints/<str:endpoint_id>/lambda-services/', media_manager_dashboard.media_manager_endpoint_lambda_services, name='endpoint_lambda_services'),
    path('endpoints/<str:endpoint_id>/files/', media_manager_dashboard.media_manager_endpoint_files, name='endpoint_files'),
    path('endpoints/<str:endpoint_id>/methods/', media_manager_dashboard.media_manager_endpoint_methods, name='endpoint_methods'),
    path('endpoints/<str:endpoint_id>/used-by-pages/', media_manager_dashboard.media_manager_endpoint_used_by_pages, name='endpoint_used_by_pages'),
    path('endpoints/<str:endpoint_id>/dependencies/', media_manager_dashboard.media_manager_endpoint_dependencies, name='endpoint_dependencies'),
    # Endpoint detail route (after sub-resources)
    path('endpoints/<str:endpoint_id>/detail/', media_manager_dashboard.media_manager_endpoint_detail, name='endpoint_detail_enhanced'),
    
    # Relationships API Routes (static routes before parameterized) - 38 routes
    path('relationships/statistics/', media_manager_dashboard.media_manager_relationships_statistics, name='relationships_statistics'),
    path('relationships/format/', media_manager_dashboard.media_manager_relationships_format, name='relationships_format'),
    path('relationships/graph/', media_manager_dashboard.media_manager_relationships_graph, name='relationships_graph'),
    path('relationships/usage-types/', media_manager_dashboard.media_manager_relationships_usage_types, name='relationships_usage_types'),
    path('relationships/usage-contexts/', media_manager_dashboard.media_manager_relationships_usage_contexts, name='relationships_usage_contexts'),
    path('relationships/by-page/<str:page_id>/primary/', media_manager_dashboard.media_manager_relationships_by_page_primary, name='relationships_by_page_primary'),
    path('relationships/by-page/<str:page_id>/secondary/', media_manager_dashboard.media_manager_relationships_by_page_secondary, name='relationships_by_page_secondary'),
    path('relationships/by-page/<str:page_id>/count/', media_manager_dashboard.media_manager_relationships_by_page_count, name='relationships_by_page_count'),
    path('relationships/by-page/<str:page_id>/by-usage-type/<str:usage_type>/', media_manager_dashboard.media_manager_relationships_by_page_by_usage_type, name='relationships_by_page_by_usage_type'),
    path('relationships/by-page/<str:page_id>/', media_manager_dashboard.media_manager_relationships_by_page, name='relationships_by_page'),
    path('relationships/by-endpoint/<str:endpoint_id>/pages/', media_manager_dashboard.media_manager_relationships_by_endpoint_pages, name='relationships_by_endpoint_pages'),
    path('relationships/by-endpoint/<str:endpoint_id>/count/', media_manager_dashboard.media_manager_relationships_by_endpoint_count, name='relationships_by_endpoint_count'),
    path('relationships/by-endpoint/<str:endpoint_id>/by-usage-context/<str:usage_context>/', media_manager_dashboard.media_manager_relationships_by_endpoint_by_usage_context, name='relationships_by_endpoint_by_usage_context'),
    path('relationships/by-endpoint/<str:endpoint_id>/', media_manager_dashboard.media_manager_relationships_by_endpoint, name='relationships_by_endpoint'),
    path('relationships/by-usage-type/primary/', media_manager_dashboard.media_manager_relationships_by_usage_type_primary, name='relationships_by_usage_type_primary'),
    path('relationships/by-usage-type/secondary/', media_manager_dashboard.media_manager_relationships_by_usage_type_secondary, name='relationships_by_usage_type_secondary'),
    path('relationships/by-usage-type/conditional/', media_manager_dashboard.media_manager_relationships_by_usage_type_conditional, name='relationships_by_usage_type_conditional'),
    # Generic relationships by usage type route (must be after specific routes)
    path('relationships/by-usage-type/<str:usage_type>/', media_manager_dashboard.media_manager_relationships_by_usage_type, name='relationships_by_usage_type'),
    path('relationships/by-usage-type/<str:usage_type>/count/', media_manager_dashboard.media_manager_relationships_by_usage_type_count, name='relationships_by_usage_type_count'),
    path('relationships/by-usage-type/<str:usage_type>/by-usage-context/<str:usage_context>/', media_manager_dashboard.media_manager_relationships_by_usage_type_by_usage_context, name='relationships_by_usage_type_by_usage_context'),
    path('relationships/by-usage-context/data_fetching/', media_manager_dashboard.media_manager_relationships_by_usage_context_data_fetching, name='relationships_by_usage_context_data_fetching'),
    path('relationships/by-usage-context/data_mutation/', media_manager_dashboard.media_manager_relationships_by_usage_context_data_mutation, name='relationships_by_usage_context_data_mutation'),
    path('relationships/by-usage-context/authentication/', media_manager_dashboard.media_manager_relationships_by_usage_context_authentication, name='relationships_by_usage_context_authentication'),
    path('relationships/by-usage-context/analytics/', media_manager_dashboard.media_manager_relationships_by_usage_context_analytics, name='relationships_by_usage_context_analytics'),
    # Generic relationships by usage context route (must be after specific routes)
    path('relationships/by-usage-context/<str:usage_context>/', media_manager_dashboard.media_manager_relationships_by_usage_context, name='relationships_by_usage_context'),
    path('relationships/by-usage-context/<str:usage_context>/count/', media_manager_dashboard.media_manager_relationships_by_usage_context_count, name='relationships_by_usage_context_count'),
    path('relationships/by-state/<str:state>/count/', media_manager_dashboard.media_manager_relationships_by_state_count, name='relationships_by_state_count'),
    path('relationships/by-state/<str:state>/', media_manager_dashboard.media_manager_relationships_by_state, name='relationships_by_state'),
    path('relationships/by-lambda/<str:service_name>/', media_manager_dashboard.media_manager_relationships_by_lambda, name='relationships_by_lambda'),
    path('relationships/by-invocation-pattern/<str:pattern>/', media_manager_dashboard.media_manager_relationships_by_invocation_pattern, name='relationships_by_invocation_pattern'),
    path('relationships/by-postman-config/<str:config_id>/', media_manager_dashboard.media_manager_relationships_by_postman_config, name='relationships_by_postman_config'),
    path('relationships/performance/slow/', media_manager_dashboard.media_manager_relationships_performance_slow, name='relationships_performance_slow'),
    path('relationships/performance/errors/', media_manager_dashboard.media_manager_relationships_performance_errors, name='relationships_performance_errors'),
    # Relationship sub-resource routes (must be before relationship detail route)
    path('relationships/<str:relationship_id>/access-control/', media_manager_dashboard.media_manager_relationship_access_control, name='relationship_access_control'),
    path('relationships/<str:relationship_id>/data-flow/', media_manager_dashboard.media_manager_relationship_data_flow, name='relationship_data_flow'),
    path('relationships/<str:relationship_id>/performance/', media_manager_dashboard.media_manager_relationship_performance, name='relationship_performance'),
    path('relationships/<str:relationship_id>/dependencies/', media_manager_dashboard.media_manager_relationship_dependencies, name='relationship_dependencies'),
    path('relationships/<str:relationship_id>/postman/', media_manager_dashboard.media_manager_relationship_postman, name='relationship_postman'),
    # Relationship detail route (after sub-resources)
    path('relationships/<str:relationship_id>/detail/', media_manager_dashboard.media_manager_relationship_detail, name='relationship_detail_enhanced'),
    
    # Postman API Routes (static routes before parameterized) - 14 routes
    path('postman/statistics/', media_manager_dashboard.media_manager_postman_statistics, name='postman_statistics'),
    path('postman/format/', media_manager_dashboard.media_manager_postman_format, name='postman_format'),
    path('postman/by-state/<str:state>/count/', media_manager_dashboard.media_manager_postman_by_state_count, name='postman_by_state_count'),
    path('postman/by-state/<str:state>/', media_manager_dashboard.media_manager_postman_by_state, name='postman_by_state'),
    # Postman sub-resource routes (must be before postman detail route)
    path('postman/<str:config_id>/collection/', media_manager_dashboard.media_manager_postman_collection, name='postman_collection'),
    path('postman/<str:config_id>/environments/<str:env_name>/', media_manager_dashboard.media_manager_postman_environment, name='postman_environment'),
    path('postman/<str:config_id>/environments/', media_manager_dashboard.media_manager_postman_environments, name='postman_environments'),
    path('postman/<str:config_id>/mappings/<str:mapping_id>/', media_manager_dashboard.media_manager_postman_mapping, name='postman_mapping'),
    path('postman/<str:config_id>/mappings/', media_manager_dashboard.media_manager_postman_mappings, name='postman_mappings'),
    path('postman/<str:config_id>/test-suites/<str:suite_id>/', media_manager_dashboard.media_manager_postman_test_suite, name='postman_test_suite'),
    path('postman/<str:config_id>/test-suites/', media_manager_dashboard.media_manager_postman_test_suites, name='postman_test_suites'),
    path('postman/<str:config_id>/access-control/', media_manager_dashboard.media_manager_postman_access_control, name='postman_access_control'),
    # Postman detail route (after sub-resources)
    path('postman/<str:config_id>/detail/', media_manager_dashboard.media_manager_postman_detail, name='postman_detail_enhanced'),
    
    # Index API Routes (8 routes)
    path('index/pages/validate/', media_manager_dashboard.media_manager_index_pages_validate, name='index_pages_validate'),
    path('index/endpoints/validate/', media_manager_dashboard.media_manager_index_endpoints_validate, name='index_endpoints_validate'),
    path('index/relationships/validate/', media_manager_dashboard.media_manager_index_relationships_validate, name='index_relationships_validate'),
    path('index/postman/validate/', media_manager_dashboard.media_manager_index_postman_validate, name='index_postman_validate'),
    path('index/pages/', media_manager_dashboard.media_manager_index_pages, name='index_pages'),
    path('index/endpoints/', media_manager_dashboard.media_manager_index_endpoints, name='index_endpoints'),
    path('index/relationships/', media_manager_dashboard.media_manager_index_relationships, name='index_relationships'),
    path('index/postman/', media_manager_dashboard.media_manager_index_postman, name='index_postman'),
    
    # Dashboard API Routes (4 routes)
    path('dashboard/pages/', media_manager_dashboard.media_manager_dashboard_pages, name='dashboard_pages_enhanced'),
    path('dashboard/endpoints/', media_manager_dashboard.media_manager_dashboard_endpoints, name='dashboard_endpoints_enhanced'),
    path('dashboard/relationships/', media_manager_dashboard.media_manager_dashboard_relationships, name='dashboard_relationships_enhanced'),
    path('dashboard/postman/', media_manager_dashboard.media_manager_dashboard_postman, name='dashboard_postman_enhanced'),
    
    # ============================================================================
    # End of Unified Dashboard Routes
    # ============================================================================
    
    # Pages CRUD (form views use services directly - no API endpoints)
    path('pages/list/', page_list_view, name='pages_list'),
    path('pages/<str:page_id>/', page_detail_view, name='page_detail'),
    path('pages/create/', page_form_view, name='page_create'),
    path('pages/<str:page_id>/edit/', page_form_view, name='page_edit'),
    path('pages/<str:page_id>/update/', legacy_views.update_page_view, name='page_update'),
    path('pages/<str:page_id>/delete/', legacy_views.delete_page_view, name='page_delete'),
    
    # Endpoints CRUD (form views use services directly - no API endpoints)
    path('endpoints/list/', endpoint_list_view, name='endpoints_list'),
    path('endpoints/<str:endpoint_id>/', endpoint_detail_view, name='endpoint_detail'),
    path('endpoints/create/', endpoint_form_view, name='endpoint_create'),
    path('endpoints/<str:endpoint_id>/edit/', endpoint_form_view, name='endpoint_edit'),
    path('endpoints/<str:endpoint_id>/delete/', endpoint_delete_view, name='endpoint_delete'),
    
    # API endpoints (for form auto-save and AJAX operations)
    path('api/endpoints/draft/', endpoint_draft_api, name='api_endpoint_draft'),
    path('api/pages/draft/', page_draft_api, name='api_page_draft'),
    
    # Relationships CRUD and API (form + create/update/delete API for AJAX)
    path('relationships/list/', relationship_list_view, name='relationships_list'),
    path('relationships/<str:relationship_id>/', relationship_detail_view, name='relationship_detail'),
    path('relationships/create/', relationship_form_view, name='relationship_create'),
    path('relationships/<str:relationship_id>/edit/', relationship_form_view, name='relationship_edit'),
    path('api/relationships/create/', relationship_create_api, name='api_relationship_create'),
    path('api/relationships/<str:relationship_id>/update/', relationship_update_api, name='api_relationship_update'),
    path('api/relationships/<str:relationship_id>/delete/', relationship_delete_api, name='api_relationship_delete'),
    
    # Postman CRUD (create before detail so /postman/create/ is not captured as postman_id)
    path('postman/create/', postman_form_view, name='postman_create'),
    path('postman/<str:postman_id>/edit/', postman_form_view, name='postman_edit'),
    path('postman/<str:postman_id>/', postman_detail_view, name='postman_detail'),
    
    # ============================================================================
    # Redirects from old /docs/media-manager/* routes to new /docs/* routes
    # These redirects will be removed after migration period (30 days)
    # ============================================================================
    # Main dashboard redirect
    path('media-manager/', lambda r: redirect('documentation:dashboard'), name='media_manager_dashboard_redirect'),
    path('media-manager/pages/', lambda r: redirect('documentation:dashboard_pages'), name='media_manager_pages_redirect'),
    path('media-manager/endpoints/', lambda r: redirect('documentation:dashboard_endpoints'), name='media_manager_endpoints_redirect'),
    path('media-manager/relationships/', lambda r: redirect('documentation:dashboard_relationships'), name='media_manager_relationships_redirect'),
    path('media-manager/postman/', lambda r: redirect('documentation:dashboard'), name='media_manager_postman_redirect'),
    
    # Service Info & Health redirects
    path('media-manager/service-info/', lambda r: redirect('documentation:service_info'), name='media_manager_service_info_redirect'),
    path('media-manager/docs/endpoint-stats/', lambda r: redirect('documentation:docs_endpoint_stats'), name='media_manager_docs_endpoint_stats_redirect'),
    path('media-manager/health/', lambda r: redirect('documentation:health'), name='media_manager_health_redirect'),
    path('media-manager/health/database/', lambda r: redirect('documentation:health_database'), name='media_manager_health_database_redirect'),
    path('media-manager/health/cache/', lambda r: redirect('documentation:health_cache'), name='media_manager_health_cache_redirect'),
    path('media-manager/health/storage/', lambda r: redirect('documentation:health_storage'), name='media_manager_health_storage_redirect'),
    path('media-manager/statistics/', lambda r: redirect('documentation:statistics'), name='media_manager_statistics_redirect'),
    
    # Pages redirects (using create_redirect_view helper for parameterized routes)
    path('media-manager/pages/statistics/', create_redirect_view('pages_statistics'), name='media_manager_pages_statistics_redirect'),
    path('media-manager/pages/format/', create_redirect_view('pages_format'), name='media_manager_pages_format_redirect'),
    path('media-manager/pages/types/', create_redirect_view('pages_types'), name='media_manager_pages_types_redirect'),
    path('media-manager/pages/by-type/docs/', create_redirect_view('pages_by_type_docs'), name='media_manager_pages_by_type_docs_redirect'),
    path('media-manager/pages/by-type/marketing/', create_redirect_view('pages_by_type_marketing'), name='media_manager_pages_by_type_marketing_redirect'),
    path('media-manager/pages/by-type/dashboard/', create_redirect_view('pages_by_type_dashboard'), name='media_manager_pages_by_type_dashboard_redirect'),
    path('media-manager/pages/by-type/<str:page_type>/published/', create_redirect_view('pages_by_type_published'), name='media_manager_pages_by_type_published_redirect'),
    path('media-manager/pages/by-type/<str:page_type>/draft/', create_redirect_view('pages_by_type_draft'), name='media_manager_pages_by_type_draft_redirect'),
    path('media-manager/pages/by-type/<str:page_type>/stats/', create_redirect_view('pages_by_type_stats'), name='media_manager_pages_by_type_stats_redirect'),
    path('media-manager/pages/by-type/<str:page_type>/count/', create_redirect_view('pages_by_type_count'), name='media_manager_pages_by_type_count_redirect'),
    path('media-manager/pages/by-state/<str:state>/count/', create_redirect_view('pages_by_state_count'), name='media_manager_pages_by_state_count_redirect'),
    path('media-manager/pages/by-state/<str:state>/', create_redirect_view('pages_by_state'), name='media_manager_pages_by_state_redirect'),
    path('media-manager/pages/by-user-type/<str:user_type>/', create_redirect_view('pages_by_user_type'), name='media_manager_pages_by_user_type_redirect'),
    path('media-manager/pages/<str:page_id>/sections/', create_redirect_view('page_sections'), name='media_manager_page_sections_redirect'),
    path('media-manager/pages/<str:page_id>/components/', create_redirect_view('page_components'), name='media_manager_page_components_redirect'),
    path('media-manager/pages/<str:page_id>/endpoints/', create_redirect_view('page_endpoints'), name='media_manager_page_endpoints_redirect'),
    path('media-manager/pages/<str:page_id>/versions/', create_redirect_view('page_versions'), name='media_manager_page_versions_redirect'),
    path('media-manager/pages/<str:page_id>/access-control/', create_redirect_view('page_access_control'), name='media_manager_page_access_control_redirect'),
    path('media-manager/pages/<str:page_id>/', create_redirect_view('page_detail_enhanced'), name='media_manager_page_detail_redirect'),
    
    # Endpoints redirects
    path('media-manager/endpoints/statistics/', create_redirect_view('endpoints_statistics'), name='media_manager_endpoints_statistics_redirect'),
    path('media-manager/endpoints/format/', create_redirect_view('endpoints_format'), name='media_manager_endpoints_format_redirect'),
    path('media-manager/endpoints/api-versions/', create_redirect_view('endpoints_api_versions'), name='media_manager_endpoints_api_versions_redirect'),
    path('media-manager/endpoints/methods/', create_redirect_view('endpoints_methods'), name='media_manager_endpoints_methods_redirect'),
    path('media-manager/endpoints/by-api-version/v1/', create_redirect_view('endpoints_by_api_version_v1'), name='media_manager_endpoints_by_api_version_v1_redirect'),
    path('media-manager/endpoints/by-api-version/v4/', create_redirect_view('endpoints_by_api_version_v4'), name='media_manager_endpoints_by_api_version_v4_redirect'),
    path('media-manager/endpoints/by-api-version/graphql/', create_redirect_view('endpoints_by_api_version_graphql'), name='media_manager_endpoints_by_api_version_graphql_redirect'),
    path('media-manager/endpoints/by-api-version/<str:api_version>/count/', create_redirect_view('endpoints_by_api_version_count'), name='media_manager_endpoints_by_api_version_count_redirect'),
    path('media-manager/endpoints/by-api-version/<str:api_version>/stats/', create_redirect_view('endpoints_by_api_version_stats'), name='media_manager_endpoints_by_api_version_stats_redirect'),
    path('media-manager/endpoints/by-api-version/<str:api_version>/by-method/<str:method>/', create_redirect_view('endpoints_by_api_version_by_method'), name='media_manager_endpoints_by_api_version_by_method_redirect'),
    path('media-manager/endpoints/by-method/GET/', create_redirect_view('endpoints_by_method_get'), name='media_manager_endpoints_by_method_get_redirect'),
    path('media-manager/endpoints/by-method/POST/', create_redirect_view('endpoints_by_method_post'), name='media_manager_endpoints_by_method_post_redirect'),
    path('media-manager/endpoints/by-method/QUERY/', create_redirect_view('endpoints_by_method_query'), name='media_manager_endpoints_by_method_query_redirect'),
    path('media-manager/endpoints/by-method/MUTATION/', create_redirect_view('endpoints_by_method_mutation'), name='media_manager_endpoints_by_method_mutation_redirect'),
    # Generic endpoints by method redirect (must be after specific routes)
    path('media-manager/endpoints/by-method/<str:method>/', create_redirect_view('endpoints_by_method'), name='media_manager_endpoints_by_method_redirect'),
    path('media-manager/endpoints/by-method/<str:method>/count/', create_redirect_view('endpoints_by_method_count'), name='media_manager_endpoints_by_method_count_redirect'),
    path('media-manager/endpoints/by-method/<str:method>/stats/', create_redirect_view('endpoints_by_method_stats'), name='media_manager_endpoints_by_method_stats_redirect'),
    path('media-manager/endpoints/by-state/<str:state>/count/', create_redirect_view('endpoints_by_state_count'), name='media_manager_endpoints_by_state_count_redirect'),
    path('media-manager/endpoints/by-state/<str:state>/', create_redirect_view('endpoints_by_state'), name='media_manager_endpoints_by_state_redirect'),
    path('media-manager/endpoints/by-lambda/<str:service_name>/count/', create_redirect_view('endpoints_by_lambda_count'), name='media_manager_endpoints_by_lambda_count_redirect'),
    path('media-manager/endpoints/by-lambda/<str:service_name>/', create_redirect_view('endpoints_by_lambda'), name='media_manager_endpoints_by_lambda_redirect'),
    path('media-manager/endpoints/<str:endpoint_id>/pages/', create_redirect_view('endpoint_pages'), name='media_manager_endpoint_pages_redirect'),
    path('media-manager/endpoints/<str:endpoint_id>/access-control/', create_redirect_view('endpoint_access_control'), name='media_manager_endpoint_access_control_redirect'),
    path('media-manager/endpoints/<str:endpoint_id>/lambda-services/', create_redirect_view('endpoint_lambda_services'), name='media_manager_endpoint_lambda_services_redirect'),
    path('media-manager/endpoints/<str:endpoint_id>/files/', create_redirect_view('endpoint_files'), name='media_manager_endpoint_files_redirect'),
    path('media-manager/endpoints/<str:endpoint_id>/methods/', create_redirect_view('endpoint_methods'), name='media_manager_endpoint_methods_redirect'),
    path('media-manager/endpoints/<str:endpoint_id>/used-by-pages/', create_redirect_view('endpoint_used_by_pages'), name='media_manager_endpoint_used_by_pages_redirect'),
    path('media-manager/endpoints/<str:endpoint_id>/dependencies/', create_redirect_view('endpoint_dependencies'), name='media_manager_endpoint_dependencies_redirect'),
    path('media-manager/endpoints/<str:endpoint_id>/', create_redirect_view('endpoint_detail_enhanced'), name='media_manager_endpoint_detail_redirect'),
    
    # Relationships redirects
    path('media-manager/relationships/statistics/', create_redirect_view('relationships_statistics'), name='media_manager_relationships_statistics_redirect'),
    path('media-manager/relationships/format/', create_redirect_view('relationships_format'), name='media_manager_relationships_format_redirect'),
    path('media-manager/relationships/graph/', create_redirect_view('relationships_graph'), name='media_manager_relationships_graph_redirect'),
    path('media-manager/relationships/usage-types/', create_redirect_view('relationships_usage_types'), name='media_manager_relationships_usage_types_redirect'),
    path('media-manager/relationships/usage-contexts/', create_redirect_view('relationships_usage_contexts'), name='media_manager_relationships_usage_contexts_redirect'),
    path('media-manager/relationships/by-page/<str:page_id>/primary/', create_redirect_view('relationships_by_page_primary'), name='media_manager_relationships_by_page_primary_redirect'),
    path('media-manager/relationships/by-page/<str:page_id>/secondary/', create_redirect_view('relationships_by_page_secondary'), name='media_manager_relationships_by_page_secondary_redirect'),
    path('media-manager/relationships/by-page/<str:page_id>/count/', create_redirect_view('relationships_by_page_count'), name='media_manager_relationships_by_page_count_redirect'),
    path('media-manager/relationships/by-page/<str:page_id>/by-usage-type/<str:usage_type>/', create_redirect_view('relationships_by_page_by_usage_type'), name='media_manager_relationships_by_page_by_usage_type_redirect'),
    path('media-manager/relationships/by-page/<str:page_id>/', create_redirect_view('relationships_by_page'), name='media_manager_relationships_by_page_redirect'),
    path('media-manager/relationships/by-endpoint/<str:endpoint_id>/pages/', create_redirect_view('relationships_by_endpoint_pages'), name='media_manager_relationships_by_endpoint_pages_redirect'),
    path('media-manager/relationships/by-endpoint/<str:endpoint_id>/count/', create_redirect_view('relationships_by_endpoint_count'), name='media_manager_relationships_by_endpoint_count_redirect'),
    path('media-manager/relationships/by-endpoint/<str:endpoint_id>/by-usage-context/<str:usage_context>/', create_redirect_view('relationships_by_endpoint_by_usage_context'), name='media_manager_relationships_by_endpoint_by_usage_context_redirect'),
    path('media-manager/relationships/by-endpoint/<str:endpoint_id>/', create_redirect_view('relationships_by_endpoint'), name='media_manager_relationships_by_endpoint_redirect'),
    path('media-manager/relationships/by-usage-type/primary/', create_redirect_view('relationships_by_usage_type_primary'), name='media_manager_relationships_by_usage_type_primary_redirect'),
    path('media-manager/relationships/by-usage-type/secondary/', create_redirect_view('relationships_by_usage_type_secondary'), name='media_manager_relationships_by_usage_type_secondary_redirect'),
    path('media-manager/relationships/by-usage-type/conditional/', create_redirect_view('relationships_by_usage_type_conditional'), name='media_manager_relationships_by_usage_type_conditional_redirect'),
    path('media-manager/relationships/by-usage-type/<str:usage_type>/count/', create_redirect_view('relationships_by_usage_type_count'), name='media_manager_relationships_by_usage_type_count_redirect'),
    path('media-manager/relationships/by-usage-type/<str:usage_type>/by-usage-context/<str:usage_context>/', create_redirect_view('relationships_by_usage_type_by_usage_context'), name='media_manager_relationships_by_usage_type_by_usage_context_redirect'),
    path('media-manager/relationships/by-usage-context/data_fetching/', create_redirect_view('relationships_by_usage_context_data_fetching'), name='media_manager_relationships_by_usage_context_data_fetching_redirect'),
    path('media-manager/relationships/by-usage-context/data_mutation/', create_redirect_view('relationships_by_usage_context_data_mutation'), name='media_manager_relationships_by_usage_context_data_mutation_redirect'),
    path('media-manager/relationships/by-usage-context/authentication/', create_redirect_view('relationships_by_usage_context_authentication'), name='media_manager_relationships_by_usage_context_authentication_redirect'),
    path('media-manager/relationships/by-usage-context/analytics/', create_redirect_view('relationships_by_usage_context_analytics'), name='media_manager_relationships_by_usage_context_analytics_redirect'),
    path('media-manager/relationships/by-usage-context/<str:usage_context>/count/', create_redirect_view('relationships_by_usage_context_count'), name='media_manager_relationships_by_usage_context_count_redirect'),
    path('media-manager/relationships/by-state/<str:state>/count/', create_redirect_view('relationships_by_state_count'), name='media_manager_relationships_by_state_count_redirect'),
    path('media-manager/relationships/by-state/<str:state>/', create_redirect_view('relationships_by_state'), name='media_manager_relationships_by_state_redirect'),
    path('media-manager/relationships/by-lambda/<str:service_name>/', create_redirect_view('relationships_by_lambda'), name='media_manager_relationships_by_lambda_redirect'),
    path('media-manager/relationships/by-invocation-pattern/<str:pattern>/', create_redirect_view('relationships_by_invocation_pattern'), name='media_manager_relationships_by_invocation_pattern_redirect'),
    path('media-manager/relationships/by-postman-config/<str:config_id>/', create_redirect_view('relationships_by_postman_config'), name='media_manager_relationships_by_postman_config_redirect'),
    path('media-manager/relationships/performance/slow/', create_redirect_view('relationships_performance_slow'), name='media_manager_relationships_performance_slow_redirect'),
    path('media-manager/relationships/performance/errors/', create_redirect_view('relationships_performance_errors'), name='media_manager_relationships_performance_errors_redirect'),
    path('media-manager/relationships/<str:relationship_id>/access-control/', create_redirect_view('relationship_access_control'), name='media_manager_relationship_access_control_redirect'),
    path('media-manager/relationships/<str:relationship_id>/data-flow/', create_redirect_view('relationship_data_flow'), name='media_manager_relationship_data_flow_redirect'),
    path('media-manager/relationships/<str:relationship_id>/performance/', create_redirect_view('relationship_performance'), name='media_manager_relationship_performance_redirect'),
    path('media-manager/relationships/<str:relationship_id>/dependencies/', create_redirect_view('relationship_dependencies'), name='media_manager_relationship_dependencies_redirect'),
    path('media-manager/relationships/<str:relationship_id>/postman/', create_redirect_view('relationship_postman'), name='media_manager_relationship_postman_redirect'),
    path('media-manager/relationships/<str:relationship_id>/', create_redirect_view('relationship_detail_enhanced'), name='media_manager_relationship_detail_redirect'),
    
    # Postman redirects
    path('media-manager/postman/statistics/', create_redirect_view('postman_statistics'), name='media_manager_postman_statistics_redirect'),
    path('media-manager/postman/format/', create_redirect_view('postman_format'), name='media_manager_postman_format_redirect'),
    path('media-manager/postman/by-state/<str:state>/count/', create_redirect_view('postman_by_state_count'), name='media_manager_postman_by_state_count_redirect'),
    path('media-manager/postman/by-state/<str:state>/', create_redirect_view('postman_by_state'), name='media_manager_postman_by_state_redirect'),
    path('media-manager/postman/<str:config_id>/collection/', create_redirect_view('postman_collection'), name='media_manager_postman_collection_redirect'),
    path('media-manager/postman/<str:config_id>/environments/<str:env_name>/', create_redirect_view('postman_environment'), name='media_manager_postman_environment_redirect'),
    path('media-manager/postman/<str:config_id>/environments/', create_redirect_view('postman_environments'), name='media_manager_postman_environments_redirect'),
    path('media-manager/postman/<str:config_id>/mappings/<str:mapping_id>/', create_redirect_view('postman_mapping'), name='media_manager_postman_mapping_redirect'),
    path('media-manager/postman/<str:config_id>/mappings/', create_redirect_view('postman_mappings'), name='media_manager_postman_mappings_redirect'),
    path('media-manager/postman/<str:config_id>/test-suites/<str:suite_id>/', create_redirect_view('postman_test_suite'), name='media_manager_postman_test_suite_redirect'),
    path('media-manager/postman/<str:config_id>/test-suites/', create_redirect_view('postman_test_suites'), name='media_manager_postman_test_suites_redirect'),
    path('media-manager/postman/<str:config_id>/access-control/', create_redirect_view('postman_access_control'), name='media_manager_postman_access_control_redirect'),
    path('media-manager/postman/<str:config_id>/', create_redirect_view('postman_detail_enhanced'), name='media_manager_postman_detail_redirect'),
    
    # Index redirects
    path('media-manager/index/pages/validate/', create_redirect_view('index_pages_validate'), name='media_manager_index_pages_validate_redirect'),
    path('media-manager/index/endpoints/validate/', create_redirect_view('index_endpoints_validate'), name='media_manager_index_endpoints_validate_redirect'),
    path('media-manager/index/relationships/validate/', create_redirect_view('index_relationships_validate'), name='media_manager_index_relationships_validate_redirect'),
    path('media-manager/index/postman/validate/', create_redirect_view('index_postman_validate'), name='media_manager_index_postman_validate_redirect'),
    path('media-manager/index/pages/', create_redirect_view('index_pages'), name='media_manager_index_pages_redirect'),
    path('media-manager/index/endpoints/', create_redirect_view('index_endpoints'), name='media_manager_index_endpoints_redirect'),
    path('media-manager/index/relationships/', create_redirect_view('index_relationships'), name='media_manager_index_relationships_redirect'),
    path('media-manager/index/postman/', create_redirect_view('index_postman'), name='media_manager_index_postman_redirect'),
    
    # Dashboard API redirects
    path('media-manager/dashboard/pages/', create_redirect_view('dashboard_pages_enhanced'), name='media_manager_dashboard_pages_redirect'),
    path('media-manager/dashboard/endpoints/', create_redirect_view('dashboard_endpoints_enhanced'), name='media_manager_dashboard_endpoints_redirect'),
    path('media-manager/dashboard/relationships/', create_redirect_view('dashboard_relationships_enhanced'), name='media_manager_dashboard_relationships_redirect'),
    path('media-manager/dashboard/postman/', create_redirect_view('dashboard_postman_enhanced'), name='media_manager_dashboard_postman_redirect'),
    
    # ============================================================================
    # OLD ROUTES REMOVED - All routes above now redirect to new unified routes
    # The following old routes have been migrated to /docs/* (without media-manager prefix)
    # and redirects have been added above. Old routes removed to avoid conflicts.
    # ============================================================================
    
    # Media Manager Dashboard AJAX API endpoints
    path('api/media-manager/pages/', media_manager_api.get_pages_list_api, name='api_media_manager_pages'),
    path('api/media-manager/endpoints/', media_manager_api.get_endpoints_list_api, name='api_media_manager_endpoints'),
    path('api/media-manager/relationships/', media_manager_api.get_relationships_list_api, name='api_media_manager_relationships'),
    path('api/media-manager/postman/', media_manager_api.get_postman_list_api, name='api_media_manager_postman'),
    path('api/media-manager/statistics/', media_manager_api.get_statistics_api, name='api_media_manager_statistics'),
    path('api/media-manager/health/', media_manager_api.get_health_api, name='api_media_manager_health'),

    # Media file preview, viewer, form, delete
    path('media/preview/<path:file_path>', media_views.media_file_preview, name='media_file_preview'),
    path('media/viewer/<path:file_path>', media_views.media_file_viewer, name='media_file_viewer'),
    path('media/form/create/', media_views.media_file_form, name='media_file_form'),
    path('media/form/edit/<path:file_path>', media_views.media_file_form, name='media_file_form_edit'),
    path('media/delete/<path:file_path>', media_views.media_file_delete_confirm, name='media_file_delete_confirm'),
    path('media/file/<path:file_path>/analyze/', media_views.analyze_file_view, name='media_file_analyze'),
    path('media/file/<path:file_path>/validate/', media_views.validate_file_view, name='media_file_validate'),
    path('media/file/<path:file_path>/generate-json/', media_views.generate_json_file_view, name='media_file_generate_json'),
    path('media/file/<path:file_path>/upload-s3/', media_views.upload_file_to_s3_view, name='media_file_upload_s3'),

    # Media API (specific routes first)
    path('api/media/files/', media_views.list_files_api, name='api_media_files'),
    path('api/media/files/create/', media_views.create_file_api, name='api_media_file_create'),
    path('api/media/sync-status/', media_views.sync_status_api, name='api_media_sync_status'),
    path('api/media/bulk-sync/', media_views.bulk_sync_api, name='api_media_bulk_sync'),
    path('api/media/indexes/regenerate/pages/', media_views.regenerate_pages_index_api, name='api_media_regenerate_pages_index'),
    path('api/media/indexes/regenerate/endpoints/', media_views.regenerate_endpoints_index_api, name='api_media_regenerate_endpoints_index'),
    path('api/media/indexes/regenerate/postman/', media_views.regenerate_postman_index_api, name='api_media_regenerate_postman_index'),
    path('api/media/indexes/regenerate/relationships/', media_views.regenerate_relationships_index_api, name='api_media_regenerate_relationships_index'),
    path('api/media/indexes/regenerate/all/', media_views.regenerate_all_indexes_api, name='api_media_regenerate_all_indexes'),
    path('api/media/files/<path:file_path>/', media_views.get_file_api, name='api_media_file'),
    path('api/media/files/<path:file_path>/update/', media_views.update_file_api, name='api_media_file_update'),
    path('api/media/files/<path:file_path>/delete/', media_views.delete_file_api, name='api_media_file_delete'),
    path('api/media/sync/<path:file_path>/', media_views.sync_file_api, name='api_media_sync_file'),

    # Operations
    path('operations/', operations.operations_dashboard, name='operations_dashboard'),
    path('operations/analyze/', operations.analyze_docs_view, name='operations_analyze'),
    path('operations/validate/', operations.validate_docs_view, name='operations_validate'),
    path('operations/generate-json/', operations.generate_json_view, name='operations_generate_json'),
    path('operations/generate-postman/', operations.generate_postman_view, name='operations_generate_postman'),
    path('operations/upload/', operations.upload_docs_view, name='operations_upload'),
    path('operations/seed/', operations.seed_documentation_view, name='operations_seed'),
    path('operations/workflow/', operations.workflow_view, name='operations_workflow'),
    path('operations/status/', operations.docs_status_view, name='operations_status'),
    path('operations/tasks/', operations.task_list_view, name='operations_tasks'),
    path('operations/tasks/<str:task_id>/', operations.task_detail_view, name='operations_task_detail'),
    
    # Legacy URLs for backward compatibility
    path('list/', legacy_views.list_pages_view, name='list'),
    path('<str:page_id>/', legacy_views.get_page_view, name='detail'),
    path('create/', legacy_views.create_page_view, name='create'),
    path('<str:page_id>/update/', legacy_views.update_page_view, name='update'),
    path('<str:page_id>/delete/', legacy_views.delete_page_view, name='delete'),
]
