"""URL configuration for ai_agent app."""
from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = 'ai_agent'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='ai_agent:chat', permanent=False), name='index'),
    path('chat/', views.chat_view, name='chat'),
    path('sessions/', views.list_sessions_view, name='sessions'),
    path('sessions/<str:session_id>/', views.session_detail_view, name='session_detail'),
    path('api/chat/', views.chat_completion_api, name='chat_completion_api'),
]
