"""URL configuration for admin app."""
from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'admin'

urlpatterns = [
    path('', RedirectView.as_view(url='/admin/users/', permanent=False), name='index'),
    path('users/', views.users_view, name='users'),
    path('user-history/', views.user_history_view, name='user_history'),
    path('statistics/', views.statistics_view, name='statistics'),
    path('logs/', views.logs_view, name='logs'),
    path('system-status/', views.system_status_view, name='system_status'),
    path('settings/', views.settings_view, name='settings'),
]
