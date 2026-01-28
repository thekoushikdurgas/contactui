"""URL configuration for database app."""
from django.urls import path
from . import views

app_name = 'database'

urlpatterns = [
    path('', views.database_view, name='schema'),
]
