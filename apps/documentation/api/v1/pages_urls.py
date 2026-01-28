"""
Pages URLconf - 20 GET routes in correct order (static before parameterized).
Mount at: path('pages/', include('apps.documentation.api.v1.pages_urls'))
"""

from django.urls import path
from . import pages_views

app_name = 'api_v1_pages'
urlpatterns = [
    path('', pages_views.pages_list, name='pages_list'),
    path('by-type/docs/', pages_views.pages_by_type_docs, name='pages_by_type_docs'),
    path('by-type/marketing/', pages_views.pages_by_type_marketing, name='pages_by_type_marketing'),
    path('by-type/dashboard/', pages_views.pages_by_type_dashboard, name='pages_by_type_dashboard'),
    path('by-type/<str:page_type>/count/', pages_views.pages_by_type_count, name='pages_by_type_count'),
    path('by-type/<str:page_type>/published/', pages_views.pages_by_type_published, name='pages_by_type_published'),
    path('by-type/<str:page_type>/draft/', pages_views.pages_by_type_draft, name='pages_by_type_draft'),
    path('by-type/<str:page_type>/stats/', pages_views.pages_by_type_stats, name='pages_by_type_stats'),
    path('by-state/<str:state>/', pages_views.pages_by_state_list, name='pages_by_state_list'),
    path('by-state/<str:state>/count/', pages_views.pages_by_state_count, name='pages_by_state_count'),
    path('<str:page_id>/access-control/', pages_views.pages_detail_access_control, name='pages_detail_access_control'),
    path('<str:page_id>/sections/', pages_views.pages_detail_sections, name='pages_detail_sections'),
    path('<str:page_id>/components/', pages_views.pages_detail_components, name='pages_detail_components'),
    path('<str:page_id>/endpoints/', pages_views.pages_detail_endpoints, name='pages_detail_endpoints'),
    path('<str:page_id>/versions/', pages_views.pages_detail_versions, name='pages_detail_versions'),
    path('<str:segment>/', pages_views.pages_by_user_type_or_page_detail, name='pages_user_type_or_detail'),
]
