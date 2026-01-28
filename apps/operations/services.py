"""Operations service."""
import logging
from typing import Optional, Dict, Any, List
from django.utils import timezone
from apps.core.services.base_service import BaseService
from .models import OperationLog

logger = logging.getLogger(__name__)


class OperationsService(BaseService):
    """Service for operations management."""
    
    def __init__(self):
        """Initialize operations service."""
        super().__init__('OperationsService')
    
    def create_operation(
        self,
        operation_type: str,
        name: str,
        metadata: Dict[str, Any] = None,
        started_by=None
    ) -> OperationLog:
        """
        Create a new operation.
        
        Args:
            operation_type: Type of operation
            name: Operation name
            metadata: Additional metadata
            started_by: User who started the operation
            
        Returns:
            Created OperationLog instance
        """
        operation = OperationLog.objects.create(
            operation_type=operation_type,
            name=name,
            metadata=metadata or {},
            started_by=started_by,
            status='queued'
        )
        
        self.logger.info(f"Created operation: {operation.operation_id}")
        return operation
    
    def get_operation(self, operation_id: str) -> Optional[OperationLog]:
        """
        Get an operation by ID.
        
        Args:
            operation_id: Operation ID (UUID string)
            
        Returns:
            OperationLog instance, or None if not found
        """
        try:
            import uuid
            operation_uuid = uuid.UUID(operation_id) if isinstance(operation_id, str) else operation_id
            return OperationLog.objects.get(operation_id=operation_uuid)
        except (OperationLog.DoesNotExist, ValueError):
            return None
    
    def update_progress(
        self,
        operation_id: str,
        progress: int,
        status: str = None,
        metadata: Dict[str, Any] = None
    ) -> Optional[OperationLog]:
        """
        Update operation progress.
        
        Args:
            operation_id: Operation ID
            progress: Progress percentage (0-100)
            status: Optional status update
            metadata: Optional metadata update
            
        Returns:
            Updated OperationLog instance, or None if not found
        """
        try:
            import uuid
            operation_uuid = uuid.UUID(operation_id) if isinstance(operation_id, str) else operation_id
            operation = OperationLog.objects.get(operation_id=operation_uuid)
            
            operation.progress = max(0, min(100, progress))
            
            if status:
                operation.status = status
                if status == 'running' and not operation.started_at:
                    operation.started_at = timezone.now()
                elif status in ['completed', 'failed', 'cancelled'] and not operation.completed_at:
                    operation.completed_at = timezone.now()
            
            if metadata:
                operation.metadata.update(metadata)
            
            operation.save()
            self.logger.info(f"Updated operation {operation_id}: {progress}% - {status or operation.status}")
            return operation
        except (OperationLog.DoesNotExist, ValueError) as e:
            self.logger.error(f"Error updating operation {operation_id}: {e}")
            return None
    
    def list_operations(
        self,
        operation_type: Optional[str] = None,
        status: Optional[str] = None,
        started_by=None,
        limit: int = 50,
        offset: int = 0
    ) -> List[OperationLog]:
        """
        List operations with filters.
        
        Args:
            operation_type: Filter by operation type (optional)
            status: Filter by status (optional)
            started_by: Filter by user (optional)
            limit: Maximum number of operations
            offset: Offset for pagination
            
        Returns:
            List of OperationLog instances
        """
        queryset = OperationLog.objects.all()
        
        if operation_type:
            queryset = queryset.filter(operation_type=operation_type)
        if status:
            queryset = queryset.filter(status=status)
        if started_by:
            queryset = queryset.filter(started_by=started_by)
        
        queryset = queryset.select_related('started_by')
        queryset = queryset.order_by('-created_at')
        
        return list(queryset[offset:offset + limit])
    
    def set_error(self, operation_id: str, error_message: str) -> Optional[OperationLog]:
        """
        Set operation error.
        
        Args:
            operation_id: Operation ID
            error_message: Error message
            
        Returns:
            Updated OperationLog instance, or None if not found
        """
        try:
            import uuid
            operation_uuid = uuid.UUID(operation_id) if isinstance(operation_id, str) else operation_id
            operation = OperationLog.objects.get(operation_id=operation_uuid)
            
            operation.status = 'failed'
            operation.error_message = error_message
            operation.completed_at = timezone.now()
            operation.save()
            
            self.logger.error(f"Operation {operation_id} failed: {error_message}")
            return operation
        except (OperationLog.DoesNotExist, ValueError):
            return None
