"""URL configuration for knowledge base API."""

from django.urls import path
from . import views

app_name = 'knowledge_api'

urlpatterns = [
    path('', views.knowledge_list_api, name='list'),
    path('search/', views.knowledge_search_api, name='search'),
    path('<uuid:knowledge_id>/', views.knowledge_detail_api, name='detail'),
    path('<uuid:knowledge_id>/update/', views.knowledge_update_api, name='update'),
    path('<uuid:knowledge_id>/delete/', views.knowledge_delete_api, name='delete'),
    path('create/', views.knowledge_create_api, name='create'),
]
