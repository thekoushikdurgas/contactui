"""Template storage service using S3 JSON storage."""

import logging
import uuid as uuid_lib
from typing import Optional, Dict, Any
from datetime import datetime

from apps.core.services.s3_model_storage import S3ModelStorage

logger = logging.getLogger(__name__)


class TemplateStorageService(S3ModelStorage):
    """Storage service for templates using S3 JSON storage."""
    
    def __init__(self):
        """Initialize template storage service."""
        super().__init__(model_name='templates')
    
    def _extract_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata fields for template index."""
        return {
            'uuid': data.get('uuid') or data.get('template_id'),
            'template_id': data.get('template_id') or data.get('uuid'),
            'name': data.get('name', ''),
            'category': data.get('category', 'api'),
            'created_by': data.get('created_by'),  # UUID string
            'created_at': data.get('created_at', ''),
            'updated_at': data.get('updated_at', ''),
        }
    
    def create_template(
        self,
        name: str,
        category: str = 'api',
        description: str = '',
        content: str = '',
        variables: Optional[Dict] = None,
        created_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new template."""
        template_id = str(uuid_lib.uuid4())
        now = datetime.utcnow().isoformat()
        
        template_data = {
            'template_id': template_id,
            'name': name,
            'category': category,
            'description': description,
            'content': content,
            'variables': variables or {},
            'created_by': created_by,
            'created_at': now,
            'updated_at': now,
        }
        
        return self.create(template_data, item_uuid=template_id)
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get template by ID."""
        return self.get(template_id)
    
    def update_template(self, template_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Update a template."""
        return self.update(template_id, kwargs)
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a template."""
        return self.delete(template_id)
