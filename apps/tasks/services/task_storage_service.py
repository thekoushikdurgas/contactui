"""Task storage service using S3 JSON storage."""

import logging
import uuid as uuid_lib
from typing import Optional, Dict, Any, List
from datetime import datetime

from apps.core.services.s3_model_storage import S3ModelStorage

logger = logging.getLogger(__name__)


class TaskStorageService(S3ModelStorage):
    """Storage service for tasks using S3 JSON storage."""
    
    def __init__(self):
        """Initialize task storage service."""
        super().__init__(model_name='tasks')
    
    def _extract_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata fields for task index."""
        return {
            'uuid': data.get('uuid') or data.get('task_id'),
            'task_id': data.get('task_id') or data.get('uuid'),
            'title': data.get('title', ''),
            'status': data.get('status', 'pending'),
            'priority': data.get('priority', 'medium'),
            'task_type': data.get('task_type', ''),
            'assigned_to': data.get('assigned_to'),  # UUID string
            'created_by': data.get('created_by'),  # UUID string
            'created_at': data.get('created_at', ''),
            'updated_at': data.get('updated_at', ''),
            'due_date': data.get('due_date'),
        }
    
    def create_task(
        self,
        task_type: str,
        title: str,
        description: str = '',
        priority: str = 'medium',
        assigned_to: Optional[str] = None,
        created_by: Optional[str] = None,
        due_date: Optional[str] = None,
        metadata: Optional[Dict] = None
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
            due_date: Due date (ISO format string)
            metadata: Additional metadata
            
        Returns:
            Created task data dictionary
        """
        task_id = str(uuid_lib.uuid4())
        now = datetime.utcnow().isoformat()
        
        task_data = {
            'task_id': task_id,
            'task_type': task_type,
            'title': title,
            'description': description,
            'status': 'pending',
            'priority': priority,
            'assigned_to': assigned_to,
            'created_by': created_by,
            'due_date': due_date,
            'metadata': metadata or {},
            'created_at': now,
            'updated_at': now,
            'started_at': None,
            'completed_at': None,
            'comments': [],  # Comments stored as nested list
        }
        
        return self.create(task_data, item_uuid=task_id)
    
    def update_task(self, task_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Update a task.
        
        Args:
            task_id: Task ID (UUID string)
            **kwargs: Fields to update
            
        Returns:
            Updated task data dictionary, or None if not found
        """
        # Handle status timestamp updates
        if 'status' in kwargs:
            task = self.get(task_id)
            if task:
                if kwargs['status'] == 'in_progress' and not task.get('started_at'):
                    kwargs['started_at'] = datetime.utcnow().isoformat()
                elif kwargs['status'] == 'completed' and not task.get('completed_at'):
                    kwargs['completed_at'] = datetime.utcnow().isoformat()
        
        return self.update(task_id, kwargs)
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a task by ID.
        
        Args:
            task_id: Task ID (UUID string)
            
        Returns:
            Task data dictionary, or None if not found
        """
        return self.get(task_id)
    
    def list_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        task_type: Optional[str] = None,
        assigned_to: Optional[str] = None,
        created_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List tasks with filters.
        
        Args:
            status: Filter by status
            priority: Filter by priority
            task_type: Filter by task type
            assigned_to: Filter by assigned user UUID
            created_by: Filter by creator UUID
            limit: Optional limit
            offset: Offset for pagination
            
        Returns:
            List of task data dictionaries
        """
        filters = {}
        if status:
            filters['status'] = status
        if priority:
            filters['priority'] = priority
        if task_type:
            filters['task_type'] = task_type
        if assigned_to:
            filters['assigned_to'] = assigned_to
        if created_by:
            filters['created_by'] = created_by
        
        result = self.list(filters=filters, limit=limit, offset=offset, order_by='created_at', reverse=True)
        return result.get('items', [])
    
    def add_comment(
        self,
        task_id: str,
        content: str,
        author: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Add a comment to a task.
        
        Args:
            task_id: Task ID (UUID string)
            content: Comment content
            author: Author UUID
            
        Returns:
            Updated task data dictionary with new comment, or None if task not found
        """
        task = self.get(task_id)
        if not task:
            return None
        
        comment_id = str(uuid_lib.uuid4())
        now = datetime.utcnow().isoformat()
        
        comment = {
            'comment_id': comment_id,
            'content': content,
            'author': author,
            'created_at': now,
            'updated_at': now,
        }
        
        # Add comment to task's comments list
        comments = task.get('comments', [])
        comments.append(comment)
        
        return self.update(task_id, {'comments': comments})
    
    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task.
        
        Args:
            task_id: Task ID (UUID string)
            
        Returns:
            True if successful, False otherwise
        """
        return self.delete(task_id)
    
    def get_task_comments(self, task_id: str) -> List[Dict[str, Any]]:
        """
        Get all comments for a task.
        
        Args:
            task_id: Task ID (UUID string)
            
        Returns:
            List of comment dictionaries
        """
        task = self.get(task_id)
        if not task:
            return []
        
        return task.get('comments', [])
