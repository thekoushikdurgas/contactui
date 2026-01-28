"""AI agent admin."""

from django.contrib import admin
from .models import AILearningSession, ChatMessage


@admin.register(AILearningSession)
class AILearningSessionAdmin(admin.ModelAdmin):
    """Admin for AI Learning Session."""
    list_display = ('session_name', 'status', 'created_by', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('session_name', 'session_id')
    readonly_fields = ('session_id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    """Admin for Chat Message."""
    list_display = ('role', 'content_preview', 'session', 'created_by', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('content', 'session__session_name')
    readonly_fields = ('message_id', 'created_at')
    date_hierarchy = 'created_at'
    
    def content_preview(self, obj):
        """Preview of message content."""
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content'
