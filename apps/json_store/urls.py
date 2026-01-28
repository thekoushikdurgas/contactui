"""URL configuration for json_store app."""
from django.urls import path
from . import views

app_name = 'json_store'

urlpatterns = [
    path('', views.list_json_view, name='list'),
]
