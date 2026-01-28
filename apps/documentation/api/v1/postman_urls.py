"""
Postman URLconf - 14 GET routes.
"""

from django.urls import path
from . import postman_views

app_name = 'api_v1_postman'
urlpatterns = [
    path('', postman_views.postman_list, name='postman_list'),
    path('by-state/<str:state>/', postman_views.postman_by_state_list, name='postman_by_state_list'),
    path('by-state/<str:state>/count/', postman_views.postman_by_state_count, name='postman_by_state_count'),
    path('<str:config_id>/', postman_views.postman_detail, name='postman_detail'),
    path('<str:config_id>/collection/', postman_views.postman_detail_collection, name='postman_detail_collection'),
    path('<str:config_id>/environments/', postman_views.postman_detail_environments, name='postman_detail_environments'),
    path('<str:config_id>/environments/<str:env_name>/', postman_views.postman_detail_environment, name='postman_detail_environment'),
    path('<str:config_id>/mappings/', postman_views.postman_detail_mappings, name='postman_detail_mappings'),
    path('<str:config_id>/mappings/<str:mapping_id>/', postman_views.postman_detail_mapping, name='postman_detail_mapping'),
    path('<str:config_id>/test-suites/', postman_views.postman_detail_test_suites, name='postman_detail_test_suites'),
    path('<str:config_id>/test-suites/<str:suite_id>/', postman_views.postman_detail_test_suite, name='postman_detail_test_suite'),
    path('<str:config_id>/access-control/', postman_views.postman_detail_access_control, name='postman_detail_access_control'),
]
