from django.contrib import admin
from .models import (
    Workflow, WorkflowNode, WorkflowConnection,
    Execution, ExecutionLog, Credential, WorkflowTemplate
)


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'trigger_type', 'is_active', 'execution_count', 'created_by', 'updated_at']
    list_filter = ['status', 'trigger_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_executed_at', 'execution_count', 'success_count', 'failure_count']
    ordering = ['-updated_at']


@admin.register(WorkflowNode)
class WorkflowNodeAdmin(admin.ModelAdmin):
    list_display = ['title', 'node_type', 'category', 'workflow', 'created_at']
    list_filter = ['category', 'node_type']
    search_fields = ['title', 'node_type', 'workflow__name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(WorkflowConnection)
class WorkflowConnectionAdmin(admin.ModelAdmin):
    list_display = ['workflow', 'source_node', 'target_node', 'created_at']
    list_filter = ['workflow']
    readonly_fields = ['id', 'created_at']


@admin.register(Execution)
class ExecutionAdmin(admin.ModelAdmin):
    list_display = ['id', 'workflow', 'status', 'trigger_type', 'started_at', 'finished_at', 'triggered_by']
    list_filter = ['status', 'trigger_type', 'created_at']
    search_fields = ['workflow__name', 'error_message']
    readonly_fields = ['id', 'created_at', 'updated_at', 'duration']
    ordering = ['-created_at']


@admin.register(ExecutionLog)
class ExecutionLogAdmin(admin.ModelAdmin):
    list_display = ['execution', 'node_title', 'level', 'message', 'created_at']
    list_filter = ['level', 'created_at']
    search_fields = ['message', 'node_title']
    readonly_fields = ['id', 'created_at']


@admin.register(Credential)
class CredentialAdmin(admin.ModelAdmin):
    list_display = ['name', 'credential_type', 'service_name', 'created_by', 'last_used_at']
    list_filter = ['credential_type', 'service_name']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_used_at']


@admin.register(WorkflowTemplate)
class WorkflowTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_featured', 'use_count', 'created_at']
    list_filter = ['category', 'is_featured']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at', 'use_count']
