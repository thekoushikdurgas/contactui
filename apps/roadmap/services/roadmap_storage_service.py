"""Roadmap storage service using S3 JSON storage."""

import logging
import uuid as uuid_lib
from typing import Optional, Dict, Any
from datetime import datetime

from apps.core.services.s3_model_storage import S3ModelStorage

logger = logging.getLogger(__name__)


class RoadmapStorageService(S3ModelStorage):
    """Storage service for roadmap items using S3 JSON storage."""
    
    def __init__(self):
        """Initialize roadmap storage service."""
        super().__init__(model_name='roadmap')
    
    def _extract_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata fields for roadmap index."""
        return {
            'uuid': data.get('uuid') or data.get('item_id'),
            'item_id': data.get('item_id') or data.get('uuid'),
            'title': data.get('title', ''),
            'status': data.get('status', 'planned'),
            'progress': data.get('progress', 0),
            'due_date': data.get('due_date'),
            'created_by': data.get('created_by'),  # UUID string
            'created_at': data.get('created_at', ''),
            'updated_at': data.get('updated_at', ''),
        }
    
    def create_item(
        self,
        title: str,
        description: str = '',
        status: str = 'planned',
        progress: int = 0,
        due_date: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new roadmap item."""
        item_id = str(uuid_lib.uuid4())
        now = datetime.utcnow().isoformat()
        
        item_data = {
            'item_id': item_id,
            'title': title,
            'description': description,
            'status': status,
            'progress': progress,
            'due_date': due_date,
            'created_by': created_by,
            'created_at': now,
            'updated_at': now,
        }
        
        return self.create(item_data, item_uuid=item_id)
    
    def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get roadmap item by ID."""
        return self.get(item_id)
    
    def update_item(self, item_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Update a roadmap item."""
        return self.update(item_id, kwargs)
    
    def delete_item(self, item_id: str) -> bool:
        """Delete a roadmap item."""
        return self.delete(item_id)
