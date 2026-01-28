"""URL configuration for test_runner app."""
from django.urls import path
from . import views

app_name = 'test_runner'

urlpatterns = [
    path('', views.test_runner_view, name='dashboard'),
]
