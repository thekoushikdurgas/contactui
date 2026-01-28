"""URL configuration for accessibility app."""
from django.urls import path
from . import views

app_name = 'accessibility'

urlpatterns = [
    path('', views.accessibility_view, name='dashboard'),
]
