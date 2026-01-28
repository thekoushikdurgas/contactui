"""Task DRF API views."""
from rest_framework import viewsets, status
from rest_framework.response import Response

from apps.core.decorators.auth import require_super_admin
from apps.tasks.services import TaskService
from apps.tasks.services.task_storage_service import TaskStorageService
from .serializers import TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    """List, create, retrieve, update, delete tasks via DRF."""

    serializer_class = TaskSerializer
    lookup_url_kwarg = 'task_id'
    lookup_field = 'task_id'
    
    def get_permissions(self):
        """Use SuperAdmin decorator instead of IsAuthenticated"""
        return []  # Permission handled by decorator
    
    def dispatch(self, request, *args, **kwargs):
        """Apply SuperAdmin decorator to all methods"""
        return require_super_admin(super().dispatch)(request, *args, **kwargs)

    def get_queryset(self):
        # Get user UUID from token
        user_uuid = None
        if hasattr(self.request, 'appointment360_user'):
            user_uuid = self.request.appointment360_user.get('uuid')
        
        storage = TaskStorageService()
        
        filters = {}
        status_filter = self.request.query_params.get('status')
        priority = self.request.query_params.get('priority')
        task_type = self.request.query_params.get('task_type')
        
        if status_filter:
            filters['status'] = status_filter
        if priority:
            filters['priority'] = priority
        if task_type:
            filters['task_type'] = task_type
        
        # Get all tasks and filter by user
        result = storage.list(filters=filters, limit=None, offset=0)
        all_tasks = result.get('items', [])
        
        # Filter by user (created_by or assigned_to)
        user_tasks = [
            task for task in all_tasks
            if task.get('created_by') == user_uuid or task.get('assigned_to') == user_uuid
        ]
        
        # Sort by created_at descending
        user_tasks.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return user_tasks

    def get_object(self):
        """Get a single task object"""
        task_id = self.kwargs.get(self.lookup_field)
        storage = TaskStorageService()
        task = storage.get_task(task_id)
        
        if not task:
            from rest_framework.exceptions import NotFound
            raise NotFound('Task not found')
        
        return task

    def create(self, request, *args, **kwargs):
        # Get user UUID from token
        user_uuid = None
        if hasattr(request, 'appointment360_user'):
            user_uuid = request.appointment360_user.get('uuid')
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        svc = TaskService()
        
        # Convert assigned_to to UUID string if provided
        assigned_to_uuid = None
        assigned_to = serializer.validated_data.get('assigned_to')
        if assigned_to:
            if hasattr(assigned_to, 'uuid'):
                assigned_to_uuid = str(assigned_to.uuid)
            elif hasattr(assigned_to, 'id'):
                assigned_to_uuid = str(assigned_to.id)
            else:
                assigned_to_uuid = str(assigned_to)
        
        task = svc.create_task(
            task_type=serializer.validated_data['task_type'],
            title=serializer.validated_data['title'],
            description=serializer.validated_data.get('description', ''),
            priority=serializer.validated_data.get('priority', 'medium'),
            assigned_to=assigned_to_uuid,
            created_by=user_uuid,
            due_date=serializer.validated_data.get('due_date'),
            metadata=serializer.validated_data.get('metadata') or {},
        )
        return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        task_id = self.kwargs.get(self.lookup_field)
        partial = kwargs.pop('partial', False)
        task = self.get_object()
        
        serializer = self.get_serializer(task, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        svc = TaskService()
        
        allowed = {'title', 'description', 'status', 'priority', 'assigned_to', 'due_date', 'metadata'}
        update_data = {k: v for k, v in serializer.validated_data.items() if k in allowed}
        
        # Convert assigned_to to UUID string if provided
        if 'assigned_to' in update_data and update_data['assigned_to']:
            assigned_to = update_data['assigned_to']
            if hasattr(assigned_to, 'uuid'):
                update_data['assigned_to'] = str(assigned_to.uuid)
            elif hasattr(assigned_to, 'id'):
                update_data['assigned_to'] = str(assigned_to.id)
            else:
                update_data['assigned_to'] = str(assigned_to)
        
        updated = svc.update_task(task_id, **update_data)
        if not updated:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(TaskSerializer(updated).data)

    def destroy(self, request, *args, **kwargs):
        task_id = self.kwargs.get(self.lookup_field)
        svc = TaskService()
        if svc.delete_task(task_id):
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'detail': 'Delete failed.'}, status=status.HTTP_400_BAD_REQUEST)
