"""URL configuration for Durgasman app."""

from django.urls import path, include
from . import views
from .api import execute

app_name = 'durgasman'

urlpatterns = [
    # Main views
    path('', views.dashboard, name='dashboard'),
    path('collection/<int:collection_id>/', views.collection_detail, name='collection_detail'),
    path('import/', views.import_view, name='import'),

    # API endpoints removed - services used directly in views
    # Removed: /durgasman/api/* endpoints
]