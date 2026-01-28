"""URL configuration for page_builder app."""
from django.urls import path
from . import views

app_name = 'page_builder'

urlpatterns = [
    path('', views.page_builder_view, name='editor'),
]
