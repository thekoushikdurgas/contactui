"""
Durgasflow API Serializers
"""

from rest_framework import serializers
from ..models import (
    Workflow, WorkflowNode, WorkflowConnection,
    Execution, ExecutionLog, Credential, WorkflowTemplate
)


class WorkflowNodeSerializer(serializers.ModelSerializer):
    """Serializer for WorkflowNode"""
    
    class Meta:
        model = WorkflowNode
        fields = [
            'id', 'node_id', 'node_type', 'category', 'title',
            'position_x', 'position_y', 'config', 'inputs', 'outputs',
            'properties', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class WorkflowConnectionSerializer(serializers.ModelSerializer):
    """Serializer for WorkflowConnection"""
    source_node_id = serializers.CharField(source='source_node.node_id', read_only=True)
    target_node_id = serializers.CharField(source='target_node.node_id', read_only=True)
    
    class Meta:
        model = WorkflowConnection
        fields = [
            'id', 'source_node', 'source_node_id', 'source_output',
            'target_node', 'target_node_id', 'target_input', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class WorkflowListSerializer(serializers.ModelSerializer):
    """Serializer for Workflow list view"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Workflow
        fields = [
            'id', 'name', 'description', 'status', 'is_active',
            'trigger_type', 'tags', 'execution_count', 'success_count',
            'failure_count', 'created_by', 'created_by_name',
            'created_at', 'updated_at', 'last_executed_at'
        ]
        read_only_fields = [
            'id', 'created_by', 'execution_count', 'success_count',
            'failure_count', 'created_at', 'updated_at', 'last_executed_at'
        ]


class WorkflowDetailSerializer(serializers.ModelSerializer):
    """Serializer for Workflow detail view"""
    nodes = WorkflowNodeSerializer(many=True, read_only=True)
    connections = WorkflowConnectionSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Workflow
        fields = [
            'id', 'name', 'description', 'graph_data', 'status', 'is_active',
            'trigger_type', 'schedule_cron', 'webhook_path', 'webhook_secret',
            'tags', 'settings', 'execution_count', 'success_count',
            'failure_count', 'created_by', 'created_by_name',
            'created_at', 'updated_at', 'last_executed_at',
            'nodes', 'connections'
        ]
        read_only_fields = [
            'id', 'created_by', 'execution_count', 'success_count',
            'failure_count', 'created_at', 'updated_at', 'last_executed_at',
            'nodes', 'connections'
        ]


class WorkflowCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating workflows"""
    
    class Meta:
        model = Workflow
        fields = [
            'name', 'description', 'trigger_type', 'graph_data',
            'tags', 'settings', 'schedule_cron', 'webhook_path'
        ]


class WorkflowGraphSerializer(serializers.Serializer):
    """Serializer for workflow graph data"""
    graph_data = serializers.JSONField()


class ExecutionLogSerializer(serializers.ModelSerializer):
    """Serializer for ExecutionLog"""
    
    class Meta:
        model = ExecutionLog
        fields = [
            'id', 'node_id', 'node_type', 'node_title',
            'level', 'message', 'data', 'started_at', 'finished_at',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ExecutionListSerializer(serializers.ModelSerializer):
    """Serializer for Execution list view"""
    workflow_name = serializers.CharField(source='workflow.name', read_only=True)
    duration = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Execution
        fields = [
            'id', 'workflow', 'workflow_name', 'status', 'trigger_type',
            'started_at', 'finished_at', 'duration', 'error_message',
            'triggered_by', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'duration']


class ExecutionDetailSerializer(serializers.ModelSerializer):
    """Serializer for Execution detail view"""
    workflow_name = serializers.CharField(source='workflow.name', read_only=True)
    logs = ExecutionLogSerializer(many=True, read_only=True)
    duration = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Execution
        fields = [
            'id', 'workflow', 'workflow_name', 'status', 'trigger_type',
            'trigger_data', 'started_at', 'finished_at', 'duration',
            'result_data', 'error_message', 'error_stack', 'node_results',
            'retry_count', 'max_retries', 'triggered_by',
            'created_at', 'updated_at', 'logs'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'logs', 'duration']


class CredentialListSerializer(serializers.ModelSerializer):
    """Serializer for Credential list view (without sensitive data)"""
    
    class Meta:
        model = Credential
        fields = [
            'id', 'name', 'description', 'credential_type', 'service_name',
            'created_at', 'updated_at', 'last_used_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_used_at']


class CredentialDetailSerializer(serializers.ModelSerializer):
    """Serializer for Credential detail view"""
    
    class Meta:
        model = Credential
        fields = [
            'id', 'name', 'description', 'credential_type', 'service_name',
            'data', 'created_at', 'updated_at', 'last_used_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_used_at']
        extra_kwargs = {
            'data': {'write_only': True}  # Don't expose credential data in responses
        }


class WorkflowTemplateSerializer(serializers.ModelSerializer):
    """Serializer for WorkflowTemplate"""
    
    class Meta:
        model = WorkflowTemplate
        fields = [
            'id', 'name', 'description', 'category', 'graph_data',
            'thumbnail_url', 'tags', 'is_featured', 'use_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'use_count', 'created_at', 'updated_at']


class NodeTypeSerializer(serializers.Serializer):
    """Serializer for node type schema"""
    type = serializers.CharField()
    title = serializers.CharField()
    category = serializers.CharField()
    description = serializers.CharField()
    color = serializers.CharField()
    inputs = serializers.ListField()
    outputs = serializers.ListField()
    properties = serializers.ListField()


class StatsSerializer(serializers.Serializer):
    """Serializer for workflow statistics"""
    total_workflows = serializers.IntegerField()
    active_workflows = serializers.IntegerField()
    draft_workflows = serializers.IntegerField()
    total_executions = serializers.IntegerField()
    total_successes = serializers.IntegerField()
    total_failures = serializers.IntegerField()
