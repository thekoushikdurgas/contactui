"""API URL configuration for codebase app."""
from django.urls import path
from . import views

app_name = 'codebase_api'

urlpatterns = [
    path('scan/', views.codebase_scan_api, name='codebase_scan'),
    path('analysis/<str:analysis_id>/', views.codebase_analysis_detail_api, name='codebase_analysis_detail'),
    path('analysis/<str:analysis_id>/files/', views.codebase_analysis_files_api, name='codebase_analysis_files'),
    path('analysis/<str:analysis_id>/dependencies/', views.codebase_analysis_dependencies_api, name='codebase_analysis_dependencies'),
    path('analysis/<str:analysis_id>/patterns/', views.codebase_analysis_patterns_api, name='codebase_analysis_patterns'),
]
