"""URL configuration for tasks app."""
from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.list_tasks_view, name='list'),
    path('create/', views.task_form_view, name='create'),
    path('<str:task_id>/', views.task_detail_view, name='detail'),
    path('<str:task_id>/start/', views.task_start_view, name='start'),
    path('<str:task_id>/complete/', views.task_complete_view, name='complete'),
    path('<str:task_id>/edit/', views.task_form_view, name='edit'),
    # API endpoints removed - services used directly in views
]
