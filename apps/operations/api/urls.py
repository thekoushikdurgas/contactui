"""API URL configuration for operations app."""
from django.urls import path
from . import views

app_name = 'operations_api'

urlpatterns = [
    path('', views.operations_list_api, name='operations_list'),
    path('<str:operation_id>/', views.operations_detail_api, name='operations_detail'),
]
