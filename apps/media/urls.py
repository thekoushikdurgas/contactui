"""URL configuration for media app."""
from django.urls import path
from . import views

app_name = 'media'

urlpatterns = [
    path('', views.list_media_view, name='list'),
]
