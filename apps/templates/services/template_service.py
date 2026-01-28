"""Templates service."""
import logging
from typing import Optional, Dict, Any, List
from apps.core.services.base_service import BaseService
from .template_storage_service import TemplateStorageService

logger = logging.getLogger(__name__)


class TemplateService(BaseService):
    """Service for template operations using S3 storage."""
    
    def __init__(self):
        """Initialize template service."""
        super().__init__('TemplateService')
        self.storage = TemplateStorageService()
    
    def create_template(
        self,
        name: str,
        category: str,
        content: str,
        variables: Dict[str, Any] = None,
        description: str = '',
        created_by=None
    ) -> Dict[str, Any]:
        """
        Create a new template.
        
        Args:
            name: Template name
            category: Template category
            content: Template content
            variables: Template variables definition
            description: Template description
            created_by: User UUID creating the template
            
        Returns:
            Created template data dictionary
        """
        # Convert created_by to UUID string if needed
        created_by_uuid = None
        if created_by:
            if hasattr(created_by, 'uuid'):
                created_by_uuid = str(created_by.uuid)
            elif hasattr(created_by, 'id'):
                created_by_uuid = str(created_by.id)
            else:
                created_by_uuid = str(created_by)
        
        template = self.storage.create_template(
            name=name,
            category=category,
            content=content,
            variables=variables,
            description=description,
            created_by=created_by_uuid
        )
        
        self.logger.info(f"Created template: {template.get('template_id')}")
        return template
    
    def apply_template(
        self,
        template_id: str,
        variable_values: Dict[str, Any]
    ) -> str:
        """
        Apply template with variable values.
        
        Args:
            template_id: Template ID
            variable_values: Values for template variables
            
        Returns:
            Rendered template content
        """
        template = self.storage.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        # Simple template rendering (replace {{variable}} with values)
        content = template.get('content', '')
        for key, value in variable_values.items():
            content = content.replace(f'{{{{{key}}}}}', str(value))
        
        return content
    
    def list_templates(
        self,
        category: Optional[str] = None,
        user=None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List templates.
        
        Args:
            category: Filter by category (optional)
            user: Filter by user UUID (optional)
            limit: Maximum number of templates
            offset: Offset for pagination
            
        Returns:
            List of template data dictionaries
        """
        # Convert user to UUID string if needed
        user_uuid = None
        if user:
            if hasattr(user, 'uuid'):
                user_uuid = str(user.uuid)
            elif hasattr(user, 'id'):
                user_uuid = str(user.id)
            else:
                user_uuid = str(user)
        
        filters = {}
        if category:
            filters['category'] = category
        if user_uuid:
            filters['created_by'] = user_uuid
        
        result = self.storage.list(filters=filters, limit=limit, offset=offset, order_by='created_at', reverse=True)
        return result.get('items', [])
