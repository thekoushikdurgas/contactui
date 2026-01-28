"""API URL configuration for documentation app."""
from django.urls import path
from . import views

app_name = 'documentation_api'

urlpatterns = [
    # Pages API - Using unified views to handle multiple HTTP methods
    path('pages/', views.pages_api, name='pages_api'),
    path('pages/<str:page_id>/', views.page_api, name='page_api'),
    
    # Endpoints API - Using unified views to handle multiple HTTP methods
    path('endpoints/', views.endpoints_api, name='endpoints_api'),
    path('endpoints/<str:endpoint_id>/', views.endpoint_api, name='endpoint_api'),
    
    # Relationships API - Using unified views to handle multiple HTTP methods
    path('relationships/', views.relationships_api, name='relationships_api'),
    path('relationships/<str:relationship_id>/', views.relationship_api, name='relationship_api'),
]
