"""Shared validation logic for scripts."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from scripts.utils.context import get_logger, is_django_context

logger = get_logger(__name__)

# Type checking
if TYPE_CHECKING:
    from apps.documentation.utils.schema_validators import (
        PageSchemaValidator,
        EndpointSchemaValidator,
        RelationshipSchemaValidator,
    )


class ValidationError:
    """Simple validation error class for scripts."""
    
    def __init__(self, field: str, message: str, value: Any = None):
        """
        Initialize validation error.
        
        Args:
            field: Field name that failed validation
            message: Error message
            value: Optional value that failed validation
        """
        self.field = field
        self.message = message
        self.value = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary."""
        return {
            "field": self.field,
            "message": self.message,
            "value": self.value,
        }
    
    def __str__(self) -> str:
        """String representation."""
        if self.value is not None:
            return f"{self.field}: {self.message} (value: {self.value})"
        return f"{self.field}: {self.message}"


def load_json_file(file_path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Load and parse JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Tuple of (parsed_data, error_message)
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        return json.loads(content), None
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON: {str(e)}"
    except Exception as e:
        return None, f"Error reading file: {str(e)}"


def validate_json_structure(data: Dict[str, Any], required_fields: List[str]) -> Tuple[bool, List[ValidationError]]:
    """
    Validate JSON structure has required fields.
    
    Args:
        data: Data dictionary to validate
        required_fields: List of required field names
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    for field in required_fields:
        if field not in data or data[field] is None:
            errors.append(ValidationError(field, f"Missing required field: {field}"))
    
    return len(errors) == 0, errors


def validate_date_consistency(created_at: Optional[str], updated_at: Optional[str]) -> Tuple[bool, List[ValidationError]]:
    """
    Validate that updated_at >= created_at.
    
    Args:
        created_at: ISO format date string
        updated_at: ISO format date string
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not created_at or not updated_at:
        return True, errors  # Can't validate if dates are missing
    
    try:
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        
        if updated < created:
            errors.append(
                ValidationError(
                    "updated_at",
                    f"updated_at ({updated_at}) must be >= created_at ({created_at})",
                )
            )
    except (ValueError, AttributeError) as e:
        errors.append(ValidationError("date", f"Invalid date format: {str(e)}"))
    
    return len(errors) == 0, errors


def validate_route(route: Any) -> Tuple[bool, List[ValidationError]]:
    """
    Validate route format (must start with '/' and be a string).
    
    Args:
        route: Route value to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not isinstance(route, str):
        errors.append(ValidationError("route", f"Route must be a string, got {type(route).__name__}", route))
    elif not route.startswith("/"):
        errors.append(ValidationError("route", f"Route must start with '/', got '{route}'", route))
    
    return len(errors) == 0, errors


def get_validator(resource_type: str):
    """
    Get validator for a resource type (works in both Django and Lambda contexts).
    
    Args:
        resource_type: Type of resource ('pages', 'endpoints', 'relationships')
        
    Returns:
        Validator instance or None if not available
    """
    is_django = is_django_context()
    
    if is_django:
        try:
            # Try Django validators first
            from apps.documentation.utils.schema_validators import (
                PageSchemaValidator,
                EndpointSchemaValidator,
                RelationshipSchemaValidator,
            )
            
            if resource_type == "pages":
                return PageSchemaValidator()
            elif resource_type == "endpoints":
                return EndpointSchemaValidator()
            elif resource_type == "relationships":
                return RelationshipSchemaValidator()
        except ImportError:
            pass
    
    # Try Lambda API validators
    try:
        from app.utils.schema_validators import (
            PageSchemaValidator,
            EndpointSchemaValidator,
            RelationshipSchemaValidator,
            ValidationError as LambdaValidationError,
        )
        
        if resource_type == "pages":
            return PageSchemaValidator()
        elif resource_type == "endpoints":
            return EndpointSchemaValidator()
        elif resource_type == "relationships":
            return RelationshipSchemaValidator()
    except ImportError:
        pass
    
    # Fallback: return None (validation will be skipped)
    logger.warning(f"Validators not available for {resource_type}, validation will be skipped")
    return None


def validate_with_schema(
    data: Dict[str, Any],
    resource_type: str,
    validator: Optional[Any] = None,
) -> Tuple[bool, List[ValidationError]]:
    """
    Validate data using schema validator.
    
    Args:
        data: Data to validate
        resource_type: Type of resource ('pages', 'endpoints', 'relationships')
        validator: Optional validator instance (will be fetched if not provided)
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    if validator is None:
        validator = get_validator(resource_type)
    
    if validator is None:
        # No validator available, skip validation
        return True, []
    
    try:
        # Try to call validate method
        if hasattr(validator, "validate"):
            validation_result = validator.validate(data)
            
            # Handle different return formats
            if isinstance(validation_result, tuple) and len(validation_result) == 2:
                is_valid, validation_errors = validation_result
                
                # Convert errors to ValidationError objects
                converted_errors = []
                if validation_errors:
                    for error in validation_errors:
                        if isinstance(error, ValidationError):
                            converted_errors.append(error)
                        elif isinstance(error, dict):
                            converted_errors.append(
                                ValidationError(
                                    error.get("field", "unknown"),
                                    error.get("message", str(error)),
                                    error.get("value"),
                                )
                            )
                        elif isinstance(error, str):
                            converted_errors.append(ValidationError("validation", error))
                        else:
                            # Try to extract field and message
                            error_str = str(error)
                            if ":" in error_str:
                                field, message = error_str.split(":", 1)
                                converted_errors.append(ValidationError(field.strip(), message.strip()))
                            else:
                                converted_errors.append(ValidationError("validation", error_str))
                
                return is_valid, converted_errors
            else:
                # Unexpected return format, assume valid
                return True, []
        else:
            # Validator doesn't have validate method
            return True, []
    except Exception as e:
        # Validation failed with exception
        logger.error(f"Validation error for {resource_type}: {e}", exc_info=True)
        return False, [ValidationError("validation", f"Validation error: {str(e)}")]


def validate_relationship_by_page(data: Dict[str, Any]) -> Tuple[bool, List[ValidationError]]:
    """
    Validate by-page relationship data.
    
    Args:
        data: Relationship data dictionary
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Required fields
    required_fields = ["page_path", "endpoints", "created_at", "updated_at"]
    is_valid, field_errors = validate_json_structure(data, required_fields)
    errors.extend(field_errors)
    
    # Validate endpoints array
    if "endpoints" in data:
        if not isinstance(data["endpoints"], list):
            errors.append(ValidationError("endpoints", "endpoints must be an array"))
        else:
            for idx, endpoint in enumerate(data["endpoints"]):
                endpoint_required = [
                    "page_path",
                    "endpoint_path",
                    "method",
                    "api_version",
                    "via_service",
                    "usage_type",
                    "usage_context",
                    "updated_at",
                ]
                is_ep_valid, ep_errors = validate_json_structure(endpoint, endpoint_required)
                errors.extend(
                    ValidationError(f"endpoints[{idx}].{e.field}", e.message) for e in ep_errors
                )
                
                # Check date consistency
                if "created_at" in endpoint and "updated_at" in endpoint:
                    is_date_valid, date_errors = validate_date_consistency(
                        endpoint.get("created_at"), endpoint.get("updated_at")
                    )
                    errors.extend(
                        ValidationError(f"endpoints[{idx}].{e.field}", e.message) for e in date_errors
                    )
    
    # Check file-level date consistency
    if "created_at" in data and "updated_at" in data:
        is_date_valid, date_errors = validate_date_consistency(data.get("created_at"), data.get("updated_at"))
        errors.extend(date_errors)
    
    return len(errors) == 0, errors


def validate_relationship_by_endpoint(data: Dict[str, Any]) -> Tuple[bool, List[ValidationError]]:
    """
    Validate by-endpoint relationship data.
    
    Args:
        data: Relationship data dictionary
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Required fields
    required_fields = ["endpoint_path", "method", "pages", "created_at", "updated_at"]
    is_valid, field_errors = validate_json_structure(data, required_fields)
    errors.extend(field_errors)
    
    # Validate pages array
    if "pages" in data:
        if not isinstance(data["pages"], list):
            errors.append(ValidationError("pages", "pages must be an array"))
        else:
            for idx, page in enumerate(data["pages"]):
                page_required = ["page_path", "via_service", "usage_type", "usage_context"]
                is_page_valid, page_errors = validate_json_structure(page, page_required)
                errors.extend(
                    ValidationError(f"pages[{idx}].{e.field}", e.message) for e in page_errors
                )
                
                # Check date consistency
                if "updated_at" in page and "created_at" in data:
                    is_date_valid, date_errors = validate_date_consistency(
                        data.get("created_at"), page.get("updated_at")
                    )
                    errors.extend(
                        ValidationError(f"pages[{idx}].{e.field}", e.message) for e in date_errors
                    )
    
    # Check file-level date consistency
    if "created_at" in data and "updated_at" in data:
        is_date_valid, date_errors = validate_date_consistency(data.get("created_at"), data.get("updated_at"))
        errors.extend(date_errors)
    
    return len(errors) == 0, errors
