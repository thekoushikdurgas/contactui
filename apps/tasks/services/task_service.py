"""Task management service."""

import logging
from typing import Optional, Dict, Any, List
from django.utils import timezone
from .task_storage_service import TaskStorageService

logger = logging.getLogger(__name__)


class TaskService:
    """Service for managing tasks using S3 storage."""
    
    def __init__(self):
        """Initialize task service."""
        self.storage = TaskStorageService()
    
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
    ) -> Dict[str, Any]:
        """
        Create a new task.
        
        Args:
            task_type: Type of task
            title: Task title
            description: Task description
            priority: Task priority
            assigned_to: User UUID assigned to task
            created_by: User UUID who created task
            due_date: Due date (datetime or ISO string)
            metadata: Additional metadata
            
        Returns:
            Created task data dictionary
        """
        # Convert assigned_to and created_by to UUID strings if needed
        assigned_to_uuid = None
        if assigned_to:
            if hasattr(assigned_to, 'uuid'):
                assigned_to_uuid = str(assigned_to.uuid)
            elif hasattr(assigned_to, 'id'):
                assigned_to_uuid = str(assigned_to.id)
            else:
                assigned_to_uuid = str(assigned_to)
        
        created_by_uuid = None
        if created_by:
            if hasattr(created_by, 'uuid'):
                created_by_uuid = str(created_by.uuid)
            elif hasattr(created_by, 'id'):
                created_by_uuid = str(created_by.id)
            else:
                created_by_uuid = str(created_by)
        
        # Convert due_date to ISO string if datetime
        due_date_str = None
        if due_date:
            if isinstance(due_date, str):
                due_date_str = due_date
            else:
                due_date_str = due_date.isoformat()
        
        return self.storage.create_task(
            task_type=task_type,
            title=title,
            description=description,
            priority=priority,
            assigned_to=assigned_to_uuid,
            created_by=created_by_uuid,
            due_date=due_date_str,
            metadata=metadata
        )
    
    def update_task(self, task_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Update a task.
        
        Args:
            task_id: Task ID (UUID string)
            **kwargs: Fields to update
            
        Returns:
            Updated task data dictionary, or None if not found
        """
        # Convert datetime objects to ISO strings
        for key, value in kwargs.items():
            if hasattr(value, 'isoformat'):
                kwargs[key] = value.isoformat()
            elif hasattr(value, 'uuid'):  # User objects
                kwargs[key] = str(value.uuid)
            elif hasattr(value, 'id'):  # User objects
                kwargs[key] = str(value.id)
        
        return self.storage.update_task(task_id, **kwargs)
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a task by ID.
        
        Args:
            task_id: Task ID (UUID string)
            
        Returns:
            Task data dictionary, or None if not found
        """
        return self.storage.get_task(task_id)
    
    def list_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        task_type: Optional[str] = None,
        assigned_to=None,
        created_by=None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List tasks with filters.
        
        Args:
            status: Filter by status
            priority: Filter by priority
            task_type: Filter by task type
            assigned_to: Filter by assigned user (UUID or object)
            created_by: Filter by creator (UUID or object)
            limit: Optional limit
            offset: Offset for pagination
            
        Returns:
            List of task data dictionaries
        """
        # Convert user objects to UUID strings
        assigned_to_uuid = None
        if assigned_to:
            if hasattr(assigned_to, 'uuid'):
                assigned_to_uuid = str(assigned_to.uuid)
            elif hasattr(assigned_to, 'id'):
                assigned_to_uuid = str(assigned_to.id)
            else:
                assigned_to_uuid = str(assigned_to)
        
        created_by_uuid = None
        if created_by:
            if hasattr(created_by, 'uuid'):
                created_by_uuid = str(created_by.uuid)
            elif hasattr(created_by, 'id'):
                created_by_uuid = str(created_by.id)
            else:
                created_by_uuid = str(created_by)
        
        return self.storage.list_tasks(
            status=status,
            priority=priority,
            task_type=task_type,
            assigned_to=assigned_to_uuid,
            created_by=created_by_uuid,
            limit=limit,
            offset=offset
        )
    
    def add_comment(self, task_id: str, content: str, author=None) -> Optional[Dict[str, Any]]:
        """
        Add a comment to a task.
        
        Args:
            task_id: Task ID (UUID string)
            content: Comment content
            author: Comment author (UUID or object)
            
        Returns:
            Updated task data dictionary with new comment, or None if error
        """
        # Convert author to UUID string
        author_uuid = None
        if author:
            if hasattr(author, 'uuid'):
                author_uuid = str(author.uuid)
            elif hasattr(author, 'id'):
                author_uuid = str(author.id)
            else:
                author_uuid = str(author)
        
        return self.storage.add_comment(task_id, content, author_uuid)
    
    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task.
        
        Args:
            task_id: Task ID (UUID string)
            
        Returns:
            True if successful, False otherwise
        """
        return self.storage.delete_task(task_id)
