"""Operations service."""
import logging
from typing import Optional, Dict, Any, List
from django.utils import timezone
from apps.core.services.base_service import BaseService
from .operation_storage_service import OperationStorageService

logger = logging.getLogger(__name__)


class OperationsService(BaseService):
    """Service for operations management using S3 storage."""
    
    def __init__(self):
        """Initialize operations service."""
        super().__init__('OperationsService')
        self.storage = OperationStorageService()
    
    def create_operation(
        self,
        operation_type: str,
        name: str,
        metadata: Dict[str, Any] = None,
        started_by=None
    ) -> Dict[str, Any]:
        """
        Create a new operation.
        
        Args:
            operation_type: Type of operation
            name: Operation name
            metadata: Additional metadata
            started_by: User UUID who started the operation
            
        Returns:
            Created operation data dictionary
        """
        # Convert started_by to UUID string if needed
        started_by_uuid = None
        if started_by:
            if hasattr(started_by, 'uuid'):
                started_by_uuid = str(started_by.uuid)
            elif hasattr(started_by, 'id'):
                started_by_uuid = str(started_by.id)
            else:
                started_by_uuid = str(started_by)
        
        operation = self.storage.create_operation(
            operation_type=operation_type,
            name=name,
            started_by=started_by_uuid,
            metadata=metadata
        )
        
        self.logger.info(f"Created operation: {operation.get('operation_id')}")
        return operation
    
    def get_operation(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an operation by ID.
        
        Args:
            operation_id: Operation ID (UUID string)
            
        Returns:
            Operation data dictionary, or None if not found
        """
        return self.storage.get_operation(operation_id)
    
    def update_progress(
        self,
        operation_id: str,
        progress: int,
        status: str = None,
        metadata: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update operation progress.
        
        Args:
            operation_id: Operation ID
            progress: Progress percentage (0-100)
            status: Optional status update
            metadata: Optional metadata update
            
        Returns:
            Updated operation data dictionary, or None if not found
        """
        update_data = {
            'progress': max(0, min(100, progress))
        }
        
        if status:
            update_data['status'] = status
        
        if metadata:
            existing = self.get_operation(operation_id)
            if existing:
                existing_metadata = existing.get('metadata', {})
                existing_metadata.update(metadata)
                update_data['metadata'] = existing_metadata
        
        return self.storage.update_operation(operation_id, **update_data)
    
    def list_operations(
        self,
        operation_type: Optional[str] = None,
        status: Optional[str] = None,
        started_by=None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List operations with filters.
        
        Args:
            operation_type: Filter by operation type (optional)
            status: Filter by status (optional)
            started_by: Filter by user UUID (optional)
            limit: Maximum number of operations
            offset: Offset for pagination
            
        Returns:
            List of operation data dictionaries
        """
        # Convert started_by to UUID string if needed
        started_by_uuid = None
        if started_by:
            if hasattr(started_by, 'uuid'):
                started_by_uuid = str(started_by.uuid)
            elif hasattr(started_by, 'id'):
                started_by_uuid = str(started_by.id)
            else:
                started_by_uuid = str(started_by)
        
        filters = {}
        if operation_type:
            filters['operation_type'] = operation_type
        if status:
            filters['status'] = status
        if started_by_uuid:
            filters['started_by'] = started_by_uuid
        
        result = self.storage.list(filters=filters, limit=limit, offset=offset, order_by='created_at', reverse=True)
        return result.get('items', [])
    
    def set_error(self, operation_id: str, error_message: str) -> Optional[Dict[str, Any]]:
        """
        Set operation error.
        
        Args:
            operation_id: Operation ID
            error_message: Error message
            
        Returns:
            Updated operation data dictionary, or None if not found
        """
        return self.storage.update_operation(
            operation_id,
            status='failed',
            error_message=error_message,
            completed_at=timezone.now().isoformat()
        )
