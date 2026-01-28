"""Task API serializers."""
from rest_framework import serializers

from apps.tasks.models import Task


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for Task model."""

    class Meta:
        model = Task
        fields = [
            'task_id', 'task_type', 'title', 'description', 'status', 'priority',
            'assigned_to', 'created_by', 'due_date', 'metadata',
            'created_at', 'updated_at', 'started_at', 'completed_at',
        ]
        read_only_fields = [
            'task_id', 'created_by', 'created_at', 'updated_at', 'started_at', 'completed_at'
        ]
