"""Operation log storage service using S3 JSON storage."""

import logging
import uuid as uuid_lib
from typing import Optional, Dict, Any
from datetime import datetime

from apps.core.services.s3_model_storage import S3ModelStorage

logger = logging.getLogger(__name__)


class OperationStorageService(S3ModelStorage):
    """Storage service for operation logs using S3 JSON storage."""
    
    def __init__(self):
        """Initialize operation storage service."""
        super().__init__(model_name='operations')
    
    def _extract_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata fields for operation index."""
        return {
            'uuid': data.get('uuid') or data.get('operation_id'),
            'operation_id': data.get('operation_id') or data.get('uuid'),
            'name': data.get('name', ''),
            'operation_type': data.get('operation_type', ''),
            'status': data.get('status', 'queued'),
            'progress': data.get('progress', 0),
            'started_by': data.get('started_by'),  # UUID string
            'created_at': data.get('created_at', ''),
            'started_at': data.get('started_at'),
            'completed_at': data.get('completed_at'),
        }
    
    def create_operation(
        self,
        operation_type: str,
        name: str,
        started_by: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create a new operation log."""
        operation_id = str(uuid_lib.uuid4())
        now = datetime.utcnow().isoformat()
        
        operation_data = {
            'operation_id': operation_id,
            'operation_type': operation_type,
            'name': name,
            'status': 'queued',
            'progress': 0,
            'metadata': metadata or {},
            'error_message': '',
            'started_by': started_by,
            'created_at': now,
            'started_at': None,
            'completed_at': None,
        }
        
        return self.create(operation_data, item_uuid=operation_id)
    
    def get_operation(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get operation by ID."""
        return self.get(operation_id)
    
    def update_operation(self, operation_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Update an operation."""
        # Handle status timestamp updates
        if 'status' in kwargs:
            operation = self.get(operation_id)
            if operation:
                if kwargs['status'] == 'running' and not operation.get('started_at'):
                    kwargs['started_at'] = datetime.utcnow().isoformat()
                elif kwargs['status'] in ['completed', 'failed', 'cancelled'] and not operation.get('completed_at'):
                    kwargs['completed_at'] = datetime.utcnow().isoformat()
        
        return self.update(operation_id, kwargs)
    
    def delete_operation(self, operation_id: str) -> bool:
        """Delete an operation."""
        return self.delete(operation_id)
