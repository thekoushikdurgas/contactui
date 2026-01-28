"""Backend schema validation service for Lambda API models."""

import logging
from typing import Any, Dict, List, Optional, Tuple
from django.core.exceptions import ValidationError

from apps.documentation.services.schema_service import SchemaService
from apps.documentation.schemas.lambda_models import (
    validate_page_data,
    validate_endpoint_data,
    validate_relationship_data
)

logger = logging.getLogger(__name__)


class SchemaValidator:
    """Backend schema validator for Lambda API models."""
    
    def __init__(self, schema_service: Optional[SchemaService] = None):
        """Initialize schema validator.
        
        Args:
            schema_service: Optional SchemaService instance
        """
        self.schema_service = schema_service or SchemaService()
    
    def validate_page(self, page_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate page data against Lambda API schema.
        
        Args:
            page_data: Page data dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        try:
            validate_page_data(page_data)
            return True, []
        except ValidationError as e:
            errors = []
            if hasattr(e, 'error_dict'):
                for field, field_errors in e.error_dict.items():
                    for error in field_errors:
                        errors.append(f"{field}: {error.message}")
            else:
                errors.append(str(e))
            return False, errors
        except Exception as e:
            logger.error(f"Validation error for page: {e}", exc_info=True)
            return False, [str(e)]
    
    def validate_endpoint(self, endpoint_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate endpoint data against Lambda API schema.
        
        Args:
            endpoint_data: Endpoint data dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        try:
            validate_endpoint_data(endpoint_data)
            return True, []
        except ValidationError as e:
            errors = []
            if hasattr(e, 'error_dict'):
                for field, field_errors in e.error_dict.items():
                    for error in field_errors:
                        errors.append(f"{field}: {error.message}")
            else:
                errors.append(str(e))
            return False, errors
        except Exception as e:
            logger.error(f"Validation error for endpoint: {e}", exc_info=True)
            return False, [str(e)]
    
    def validate_relationship(self, relationship_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate relationship data against Lambda API schema.
        
        Args:
            relationship_data: Relationship data dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        try:
            validate_relationship_data(relationship_data)
            return True, []
        except ValidationError as e:
            errors = []
            if hasattr(e, 'error_dict'):
                for field, field_errors in e.error_dict.items():
                    for error in field_errors:
                        errors.append(f"{field}: {error.message}")
            else:
                errors.append(str(e))
            return False, errors
        except Exception as e:
            logger.error(f"Validation error for relationship: {e}", exc_info=True)
            return False, [str(e)]
    
    def validate(self, data: Dict[str, Any], resource_type: str) -> Tuple[bool, List[str]]:
        """Validate data for a resource type.
        
        Args:
            data: Resource data dictionary
            resource_type: Type of resource ('pages', 'endpoints', 'relationships')
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        if resource_type == 'pages':
            return self.validate_page(data)
        elif resource_type == 'endpoints':
            return self.validate_endpoint(data)
        elif resource_type == 'relationships':
            return self.validate_relationship(data)
        else:
            return False, [f"Unknown resource type: {resource_type}"]
    
    def validate_field(self, field_path: str, value: Any, resource_type: str) -> Tuple[bool, Optional[str]]:
        """Validate a single field.
        
        Args:
            field_path: Dot-separated field path (e.g., 'metadata.route')
            value: Field value
            resource_type: Type of resource
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        from apps.documentation.utils.validation_rules import ValidationRules
        
        rules = ValidationRules()
        
        # Extract field name
        field_name = field_path.split('.')[-1]
        
        try:
            if field_name == 'route':
                rules.validate_route(value)
            elif field_name == 'method':
                rules.validate_method(value)
            elif field_name == 'page_type':
                rules.validate_page_type(value)
            elif field_name == 'page_state':
                rules.validate_page_state(value)
            elif field_name == 'status':
                rules.validate_status(value)
            elif field_name == 'usage_type':
                rules.validate_usage_type(value)
            elif field_name == 'usage_context':
                rules.validate_usage_context(value)
            # Add more field validations as needed
            
            return True, None
        except ValidationError as e:
            return False, str(e)
        except Exception as e:
            return False, str(e)
