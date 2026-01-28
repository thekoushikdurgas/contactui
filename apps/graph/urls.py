"""URL configuration for graph app."""
from django.urls import path
from . import views

app_name = 'graph'

urlpatterns = [
    path('', views.graph_view, name='visualization'),
]
