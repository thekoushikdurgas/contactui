"""URL configuration for templates app."""
from django.urls import path
from . import views

app_name = 'templates'

urlpatterns = [
    path('', views.list_templates_view, name='list'),
]
