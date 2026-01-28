"""URL configuration for roadmap app."""
from django.urls import path
from . import views

app_name = 'roadmap'

urlpatterns = [
    path('', views.roadmap_view, name='dashboard'),
]
