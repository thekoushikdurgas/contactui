"""Task API URL configuration."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'', views.TaskViewSet, basename='task')

app_name = 'tasks_api'
urlpatterns = [
    path('', include(router.urls)),
]
