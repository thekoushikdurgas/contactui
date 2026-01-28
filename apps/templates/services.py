"""Templates service."""
import logging
from typing import Optional, Dict, Any, List
from apps.core.services.base_service import BaseService
from .models import Template

logger = logging.getLogger(__name__)


class TemplateService(BaseService):
    """Service for template operations."""
    
    def __init__(self):
        """Initialize template service."""
        super().__init__('TemplateService')
    
    def create_template(
        self,
        name: str,
        category: str,
        content: str,
        variables: Dict[str, Any] = None,
        description: str = '',
        created_by=None
    ) -> Template:
        """
        Create a new template.
        
        Args:
            name: Template name
            category: Template category
            content: Template content
            variables: Template variables definition
            description: Template description
            created_by: User creating the template
            
        Returns:
            Created Template instance
        """
        template = Template.objects.create(
            name=name,
            category=category,
            content=content,
            variables=variables or {},
            description=description,
            created_by=created_by
        )
        
        self.logger.info(f"Created template: {template.template_id}")
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
        try:
            import uuid
            template_uuid = uuid.UUID(template_id) if isinstance(template_id, str) else template_id
            template = Template.objects.get(template_id=template_uuid)
            
            # Simple template rendering (replace {{variable}} with values)
            content = template.content
            for key, value in variable_values.items():
                content = content.replace(f'{{{{{key}}}}}', str(value))
            
            return content
        except Template.DoesNotExist:
            raise ValueError(f"Template not found: {template_id}")
    
    def list_templates(
        self,
        category: Optional[str] = None,
        user=None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Template]:
        """
        List templates.
        
        Args:
            category: Filter by category (optional)
            user: Filter by user (optional)
            limit: Maximum number of templates
            offset: Offset for pagination
            
        Returns:
            List of Template instances
        """
        queryset = Template.objects.all()
        
        if category:
            queryset = queryset.filter(category=category)
        if user:
            queryset = queryset.filter(created_by=user)
        
        queryset = queryset.select_related('created_by')
        queryset = queryset.order_by('-created_at')
        
        return list(queryset[offset:offset + limit])
