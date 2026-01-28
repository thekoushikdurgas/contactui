"""Django admin configuration for knowledge app."""
from django.contrib import admin
from .models import KnowledgeBase


@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    """Admin interface for KnowledgeBase model."""
    list_display = ('title', 'pattern_type', 'created_by', 'created_at', 'updated_at')
    list_filter = ('pattern_type', 'created_at', 'updated_at')
    search_fields = ('title', 'content', 'tags')
    readonly_fields = ('knowledge_id', 'created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('knowledge_id', 'pattern_type', 'title', 'content')
        }),
        ('Metadata', {
            'fields': ('tags', 'metadata')
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )
