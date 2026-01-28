"""API URLs for AI Agent app."""
from django.urls import path
from . import views

app_name = 'ai_agent_api'

urlpatterns = [
    path('chat/', views.chat_api, name='chat'),
    path('sessions/', views.sessions_api, name='sessions'),
    path('sessions/<str:session_id>/', views.session_detail_api, name='session_detail'),
]
