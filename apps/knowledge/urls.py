"""URL configuration for knowledge app."""
from django.urls import path
from . import views

app_name = 'knowledge'

urlpatterns = [
    path('', views.knowledge_list, name='list'),
    path('create/', views.knowledge_create, name='create'),
    path('<uuid:knowledge_id>/', views.knowledge_detail, name='detail'),
    path('<uuid:knowledge_id>/edit/', views.knowledge_edit, name='edit'),
    path('<uuid:knowledge_id>/delete/', views.knowledge_delete, name='delete'),
    path('search/', views.knowledge_search, name='search'),
]
