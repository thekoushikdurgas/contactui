"""URL configuration for architecture app."""
from django.urls import path
from . import views

app_name = 'architecture'

urlpatterns = [
    path('', views.architecture_view, name='blueprint'),
]
