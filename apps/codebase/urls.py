"""URL configuration for codebase app."""
from django.urls import path
from . import views

app_name = 'codebase'

urlpatterns = [
    path('', views.codebase_dashboard, name='dashboard'),
    path('scan/', views.scan_view, name='scan'),
    path('analyses/<str:analysis_id>/', views.analysis_detail_view, name='analysis_detail'),
    path('analyses/<str:analysis_id>/files/', views.file_list_view, name='file_list'),
    path('analyses/<str:analysis_id>/files/<path:file_path>/', views.file_detail_view, name='file_detail'),
    path('analyses/<str:analysis_id>/dependencies/', views.dependencies_view, name='dependencies'),
    path('analyses/<str:analysis_id>/patterns/', views.patterns_view, name='patterns'),
    # API endpoint removed - will use form views directly
]
