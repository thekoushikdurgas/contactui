"""
Relationships URLconf - 38 GET routes (static before parameterized).
"""

from django.urls import path
from . import relationships_views

app_name = 'api_v1_relationships'
urlpatterns = [
    path('', relationships_views.relationships_list, name='relationships_list'),
    path('usage-types/', relationships_views.relationships_usage_types, name='relationships_usage_types'),
    path('usage-contexts/', relationships_views.relationships_usage_contexts, name='relationships_usage_contexts'),
    path('by-page/<str:page_id>/', relationships_views.relationships_by_page, name='relationships_by_page'),
    path('by-page/<str:page_id>/count/', relationships_views.relationships_by_page_count, name='relationships_by_page_count'),
    path('by-page/<str:page_id>/primary/', relationships_views.relationships_by_page_primary, name='relationships_by_page_primary'),
    path('by-page/<str:page_id>/secondary/', relationships_views.relationships_by_page_secondary, name='relationships_by_page_secondary'),
    path('by-page/<str:page_id>/by-usage-type/<str:usage_type>/', relationships_views.relationships_by_page_by_usage_type, name='relationships_by_page_by_usage_type'),
    path('by-endpoint/<str:endpoint_id>/', relationships_views.relationships_by_endpoint, name='relationships_by_endpoint'),
    path('by-endpoint/<str:endpoint_id>/count/', relationships_views.relationships_by_endpoint_count, name='relationships_by_endpoint_count'),
    path('by-endpoint/<str:endpoint_id>/pages/', relationships_views.relationships_by_endpoint_pages, name='relationships_by_endpoint_pages'),
    path('by-endpoint/<str:endpoint_id>/by-usage-context/<str:usage_context>/', relationships_views.relationships_by_endpoint_by_usage_context, name='relationships_by_endpoint_by_usage_context'),
    path('by-usage-type/primary/', relationships_views.relationships_by_usage_type_primary, name='relationships_by_usage_type_primary'),
    path('by-usage-type/secondary/', relationships_views.relationships_by_usage_type_secondary, name='relationships_by_usage_type_secondary'),
    path('by-usage-type/conditional/', relationships_views.relationships_by_usage_type_conditional, name='relationships_by_usage_type_conditional'),
    path('by-usage-type/<str:usage_type>/count/', relationships_views.relationships_by_usage_type_count, name='relationships_by_usage_type_count'),
    path('by-usage-type/<str:usage_type>/by-usage-context/<str:usage_context>/', relationships_views.relationships_by_usage_type_by_usage_context, name='relationships_by_usage_type_by_usage_context'),
    path('by-usage-context/data_fetching/', relationships_views.relationships_by_usage_context_data_fetching, name='relationships_by_usage_context_data_fetching'),
    path('by-usage-context/data_mutation/', relationships_views.relationships_by_usage_context_data_mutation, name='relationships_by_usage_context_data_mutation'),
    path('by-usage-context/authentication/', relationships_views.relationships_by_usage_context_authentication, name='relationships_by_usage_context_authentication'),
    path('by-usage-context/analytics/', relationships_views.relationships_by_usage_context_analytics, name='relationships_by_usage_context_analytics'),
    path('by-usage-context/<str:usage_context>/count/', relationships_views.relationships_by_usage_context_count, name='relationships_by_usage_context_count'),
    path('by-state/<str:state>/', relationships_views.relationships_by_state_list, name='relationships_by_state_list'),
    path('by-state/<str:state>/count/', relationships_views.relationships_by_state_count, name='relationships_by_state_count'),
    path('by-lambda/<str:service_name>/', relationships_views.relationships_by_lambda, name='relationships_by_lambda'),
    path('by-invocation-pattern/<str:pattern>/', relationships_views.relationships_by_invocation_pattern, name='relationships_by_invocation_pattern'),
    path('by-postman-config/<str:config_id>/', relationships_views.relationships_by_postman_config, name='relationships_by_postman_config'),
    path('performance/slow/', relationships_views.relationships_performance_slow, name='relationships_performance_slow'),
    path('performance/errors/', relationships_views.relationships_performance_errors, name='relationships_performance_errors'),
    path('<str:relationship_id>/', relationships_views.relationships_detail, name='relationships_detail'),
    path('<str:relationship_id>/access-control/', relationships_views.relationships_detail_access_control, name='relationships_detail_access_control'),
    path('<str:relationship_id>/data-flow/', relationships_views.relationships_detail_data_flow, name='relationships_detail_data_flow'),
    path('<str:relationship_id>/performance/', relationships_views.relationships_detail_performance, name='relationships_detail_performance'),
    path('<str:relationship_id>/dependencies/', relationships_views.relationships_detail_dependencies, name='relationships_detail_dependencies'),
    path('<str:relationship_id>/postman/', relationships_views.relationships_detail_postman, name='relationships_detail_postman'),
]
