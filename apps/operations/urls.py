"""URL configuration for operations app."""
from django.urls import path
from . import views

app_name = 'operations'

urlpatterns = [
    path('', views.operations_view, name='dashboard'),
]
