"""
Endpoints URLconf - 28 GET routes (static before parameterized).
Mount at: path('endpoints/', include('apps.documentation.api.v1.endpoints_urls'))
"""

from django.urls import path
from . import endpoints_views

app_name = 'api_v1_endpoints'
urlpatterns = [
    path('', endpoints_views.endpoints_list, name='endpoints_list'),
    path('by-api-version/v1/', endpoints_views.endpoints_by_api_version_v1, name='endpoints_by_api_version_v1'),
    path('by-api-version/v4/', endpoints_views.endpoints_by_api_version_v4, name='endpoints_by_api_version_v4'),
    path('by-api-version/graphql/', endpoints_views.endpoints_by_api_version_graphql, name='endpoints_by_api_version_graphql'),
    path('by-api-version/<str:api_version>/count/', endpoints_views.endpoints_by_api_version_count, name='endpoints_by_api_version_count'),
    path('by-api-version/<str:api_version>/stats/', endpoints_views.endpoints_by_api_version_stats, name='endpoints_by_api_version_stats'),
    path('by-api-version/<str:api_version>/by-method/<str:method>/', endpoints_views.endpoints_by_api_version_by_method, name='endpoints_by_api_version_by_method'),
    path('by-method/GET/', endpoints_views.endpoints_by_method_get, name='endpoints_by_method_get'),
    path('by-method/POST/', endpoints_views.endpoints_by_method_post, name='endpoints_by_method_post'),
    path('by-method/QUERY/', endpoints_views.endpoints_by_method_query, name='endpoints_by_method_query'),
    path('by-method/MUTATION/', endpoints_views.endpoints_by_method_mutation, name='endpoints_by_method_mutation'),
    path('by-method/<str:method>/count/', endpoints_views.endpoints_by_method_count, name='endpoints_by_method_count'),
    path('by-method/<str:method>/stats/', endpoints_views.endpoints_by_method_stats, name='endpoints_by_method_stats'),
    path('by-state/<str:state>/', endpoints_views.endpoints_by_state_list, name='endpoints_by_state_list'),
    path('by-state/<str:state>/count/', endpoints_views.endpoints_by_state_count, name='endpoints_by_state_count'),
    path('by-lambda/<str:service_name>/', endpoints_views.endpoints_by_lambda_list, name='endpoints_by_lambda_list'),
    path('by-lambda/<str:service_name>/count/', endpoints_views.endpoints_by_lambda_count, name='endpoints_by_lambda_count'),
    path('<str:endpoint_id>/', endpoints_views.endpoints_detail, name='endpoints_detail'),
    path('<str:endpoint_id>/pages/', endpoints_views.endpoints_detail_pages, name='endpoints_detail_pages'),
    path('<str:endpoint_id>/access-control/', endpoints_views.endpoints_detail_access_control, name='endpoints_detail_access_control'),
    path('<str:endpoint_id>/lambda-services/', endpoints_views.endpoints_detail_lambda_services, name='endpoints_detail_lambda_services'),
    path('<str:endpoint_id>/files/', endpoints_views.endpoints_detail_files, name='endpoints_detail_files'),
    path('<str:endpoint_id>/methods/', endpoints_views.endpoints_detail_methods, name='endpoints_detail_methods'),
    path('<str:endpoint_id>/used-by-pages/', endpoints_views.endpoints_detail_used_by_pages, name='endpoints_detail_used_by_pages'),
    path('<str:endpoint_id>/dependencies/', endpoints_views.endpoints_detail_dependencies, name='endpoints_detail_dependencies'),
]
