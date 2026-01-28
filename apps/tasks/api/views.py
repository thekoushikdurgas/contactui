"""Task DRF API views."""
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.tasks.models import Task
from apps.tasks.services import TaskService
from .serializers import TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    """List, create, retrieve, update, delete tasks via DRF."""

    queryset = Task.objects.all().select_related('assigned_to', 'created_by').order_by('-created_at')
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'task_id'
    lookup_field = 'task_id'

    def get_queryset(self):
        qs = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        priority = self.request.query_params.get('priority')
        task_type = self.request.query_params.get('task_type')
        if status_filter:
            qs = qs.filter(status=status_filter)
        if priority:
            qs = qs.filter(priority=priority)
        if task_type:
            qs = qs.filter(task_type=task_type)
        qs = (qs.filter(created_by=self.request.user) | qs.filter(assigned_to=self.request.user)).distinct()
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        svc = TaskService()
        task = svc.create_task(
            task_type=serializer.validated_data['task_type'],
            title=serializer.validated_data['title'],
            description=serializer.validated_data.get('description', ''),
            priority=serializer.validated_data.get('priority', 'medium'),
            assigned_to=serializer.validated_data.get('assigned_to'),
            created_by=request.user,
            due_date=serializer.validated_data.get('due_date'),
            metadata=serializer.validated_data.get('metadata') or {},
        )
        return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        svc = TaskService()
        allowed = {'title', 'description', 'status', 'priority', 'assigned_to', 'due_date', 'metadata'}
        update_data = {k: v for k, v in serializer.validated_data.items() if k in allowed}
        updated = svc.update_task(str(instance.task_id), **update_data)
        if not updated:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(TaskSerializer(updated).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        svc = TaskService()
        if svc.delete_task(str(instance.task_id)):
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'detail': 'Delete failed.'}, status=status.HTTP_400_BAD_REQUEST)
