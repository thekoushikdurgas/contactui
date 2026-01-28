"""Task management service."""

import logging
from typing import Optional, Dict, Any, List
from django.utils import timezone
from .models import Task, TaskComment

logger = logging.getLogger(__name__)


class TaskService:
    """Service for managing tasks."""
    
    def __init__(self):
        """Initialize task service."""
        pass
    
    def create_task(
        self,
        task_type: str,
        title: str,
        description: str = '',
        priority: str = 'medium',
        assigned_to=None,
        created_by=None,
        due_date=None,
        metadata: Dict = None
    ) -> Task:
        """
        Create a new task.
        
        Args:
            task_type: Type of task
            title: Task title
            description: Task description
            priority: Task priority
            assigned_to: User assigned to task
            created_by: User who created task
            due_date: Due date
            metadata: Additional metadata
            
        Returns:
            Created Task instance
        """
        task = Task.objects.create(
            task_type=task_type,
            title=title,
            description=description,
            priority=priority,
            assigned_to=assigned_to,
            created_by=created_by,
            due_date=due_date,
            metadata=metadata or {},
            status='pending'
        )
        
        logger.info(f"Created task: {task.task_id}")
        return task
    
    def update_task(self, task_id: str, **kwargs) -> Optional[Task]:
        """
        Update a task.
        
        Args:
            task_id: Task ID (UUID string)
            **kwargs: Fields to update
            
        Returns:
            Updated Task instance, or None if not found
        """
        try:
            import uuid
            task_uuid = uuid.UUID(task_id) if isinstance(task_id, str) else task_id
            task = Task.objects.get(task_id=task_uuid)
            
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            
            # Update status timestamps
            if 'status' in kwargs:
                if kwargs['status'] == 'in_progress' and not task.started_at:
                    task.started_at = timezone.now()
                elif kwargs['status'] == 'completed' and not task.completed_at:
                    task.completed_at = timezone.now()
            
            task.save()
            logger.info(f"Updated task: {task.task_id}")
            return task
        except (Task.DoesNotExist, ValueError) as e:
            logger.error(f"Error updating task {task_id}: {e}")
            return None
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get a task by ID.
        
        Args:
            task_id: Task ID (UUID string)
            
        Returns:
            Task instance, or None if not found
        """
        try:
            import uuid
            task_uuid = uuid.UUID(task_id) if isinstance(task_id, str) else task_id
            return Task.objects.get(task_id=task_uuid)
        except (Task.DoesNotExist, ValueError):
            return None
    
    def list_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        task_type: Optional[str] = None,
        assigned_to=None,
        created_by=None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Task]:
        """
        List tasks with filters.
        
        Args:
            status: Filter by status
            priority: Filter by priority
            task_type: Filter by task type
            assigned_to: Filter by assigned user
            created_by: Filter by creator
            limit: Optional limit
            offset: Offset for pagination
            
        Returns:
            List of Task instances
        """
        queryset = Task.objects.all()
        
        if status:
            queryset = queryset.filter(status=status)
        if priority:
            queryset = queryset.filter(priority=priority)
        if task_type:
            queryset = queryset.filter(task_type=task_type)
        if assigned_to:
            queryset = queryset.filter(assigned_to=assigned_to)
        if created_by:
            queryset = queryset.filter(created_by=created_by)
        
        # Add eager loading to avoid N+1 queries
        queryset = queryset.select_related('assigned_to', 'created_by')
        
        # Order and paginate
        queryset = queryset.order_by('-created_at')
        
        if limit:
            queryset = queryset[offset:offset + limit]
        else:
            queryset = queryset[offset:]
        
        return list(queryset)
    
    def add_comment(self, task_id: str, content: str, author=None) -> Optional[TaskComment]:
        """
        Add a comment to a task.
        
        Args:
            task_id: Task ID (UUID string)
            content: Comment content
            author: Comment author
            
        Returns:
            Created TaskComment instance, or None if error
        """
        try:
            import uuid
            task_uuid = uuid.UUID(task_id) if isinstance(task_id, str) else task_id
            task = Task.objects.get(task_id=task_uuid)
            comment = TaskComment.objects.create(
                task=task,
                content=content,
                author=author
            )
            logger.info(f"Added comment to task: {task_id}")
            return comment
        except (Task.DoesNotExist, ValueError) as e:
            logger.error(f"Error adding comment to task {task_id}: {e}")
            return None
    
    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task.
        
        Args:
            task_id: Task ID (UUID string)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import uuid
            task_uuid = uuid.UUID(task_id) if isinstance(task_id, str) else task_id
            task = Task.objects.get(task_id=task_uuid)
            task.delete()
            logger.info(f"Deleted task: {task_id}")
            return True
        except (Task.DoesNotExist, ValueError) as e:
            logger.error(f"Error deleting task {task_id}: {e}")
            return False
