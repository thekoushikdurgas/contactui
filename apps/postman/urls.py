"""URL configuration for postman app."""
from django.urls import path
from . import views

app_name = 'postman'

urlpatterns = [
    path('', views.postman_homepage, name='homepage'),
    path('dashboard/', views.postman_dashboard, name='dashboard'),
]
