"""Validation rule definitions for Lambda API model compatibility."""

from typing import Any, Dict, List, Optional
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


# ============= VALIDATION RULE DEFINITIONS =============

class ValidationRules:
    """Centralized validation rules matching Lambda API schemas."""
    
    # Enum Values
    PAGE_TYPES = ["dashboard", "marketing", "docs"]
    PAGE_STATES = ["coming_soon", "published", "draft", "development", "test"]
    PAGE_STATUSES = ["draft", "published", "archived", "deleted"]
    HTTP_METHODS = ["QUERY", "MUTATION", "GET", "POST", "PUT", "DELETE", "PATCH"]
    USAGE_TYPES = ["primary", "secondary", "conditional", "lazy", "prefetch"]
    USAGE_CONTEXTS = ["data_fetching", "data_mutation", "authentication", "analytics", "realtime", "background"]
    INVOCATION_PATTERNS = ["on_mount", "on_click", "on_submit", "polling"]
    ERROR_HANDLING_STRATEGIES = ["console", "toast", "modal"]
    LOADING_STATES = ["spinner", "skeleton", "none"]
    POSTMAN_STATES = ["coming_soon", "published", "draft", "development", "test"]
    
    # Field Validation Rules
    @staticmethod
    def validate_id_format(value: str, resource_id: str) -> str:
        """Validate ID format."""
        if not value:
            return f"{resource_id}-001"
        return value
    
    @staticmethod
    def validate_route(value: Any) -> str:
        """Validate route - must start with '/'."""
        if not isinstance(value, str):
            return "/"
        value = value.strip()
        if not value or value == "/":
            return "/"
        if not value.startswith("/"):
            if len(value) > 50 or "error" in value.lower():
                return "/"
            return "/" + value.lstrip("/")
        return value
    
    @staticmethod
    def validate_page_type(value: str) -> str:
        """Validate page type."""
        if value not in ValidationRules.PAGE_TYPES:
            raise ValidationError(_(f"page_type must be one of {ValidationRules.PAGE_TYPES}"))
        return value
    
    @staticmethod
    def validate_page_state(value: str) -> str:
        """Validate page state."""
        if value not in ValidationRules.PAGE_STATES:
            raise ValidationError(_(f"page_state must be one of {ValidationRules.PAGE_STATES}"))
        return value
    
    @staticmethod
    def validate_status(value: str) -> str:
        """Validate status."""
        if value not in ValidationRules.PAGE_STATUSES:
            raise ValidationError(_(f"status must be one of {ValidationRules.PAGE_STATUSES}"))
        return value
    
    @staticmethod
    def validate_method(value: str) -> str:
        """Validate HTTP/GraphQL method."""
        if value.upper() not in ValidationRules.HTTP_METHODS:
            raise ValidationError(_(f"method must be one of {ValidationRules.HTTP_METHODS}"))
        return value.upper()
    
    @staticmethod
    def validate_usage_type(value: str) -> str:
        """Validate usage type."""
        if value not in ValidationRules.USAGE_TYPES:
            raise ValidationError(_(f"usage_type must be one of {ValidationRules.USAGE_TYPES}"))
        return value
    
    @staticmethod
    def validate_usage_context(value: str) -> str:
        """Validate usage context."""
        if value not in ValidationRules.USAGE_CONTEXTS:
            raise ValidationError(_(f"usage_context must be one of {ValidationRules.USAGE_CONTEXTS}"))
        return value
    
    @staticmethod
    def validate_invocation_pattern(value: str) -> str:
        """Validate invocation pattern."""
        if value not in ValidationRules.INVOCATION_PATTERNS:
            raise ValidationError(_(f"invocation_pattern must be one of {ValidationRules.INVOCATION_PATTERNS}"))
        return value
    
    @staticmethod
    def validate_error_handling(value: str) -> str:
        """Validate error handling strategy."""
        if value not in ValidationRules.ERROR_HANDLING_STRATEGIES:
            raise ValidationError(_(f"error_handling must be one of {ValidationRules.ERROR_HANDLING_STRATEGIES}"))
        return value
    
    @staticmethod
    def validate_loading_state(value: str) -> str:
        """Validate loading state."""
        if value not in ValidationRules.LOADING_STATES:
            raise ValidationError(_(f"loading_state must be one of {ValidationRules.LOADING_STATES}"))
        return value
    
    @staticmethod
    def validate_heading_level(value: int) -> int:
        """Validate heading level (1-6)."""
        if not isinstance(value, int) or value < 1 or value > 6:
            raise ValidationError(_("heading level must be between 1 and 6"))
        return value
    
    @staticmethod
    def validate_retry_count(value: int) -> int:
        """Validate retry count (0-10)."""
        if not isinstance(value, int) or value < 0 or value > 10:
            raise ValidationError(_("max_retries must be between 0 and 10"))
        return value
    
    @staticmethod
    def validate_backoff_ms(value: int) -> int:
        """Validate backoff milliseconds (min 100)."""
        if not isinstance(value, int) or value < 100:
            raise ValidationError(_("backoff_ms must be at least 100"))
        return value
    
    @staticmethod
    def validate_timeout_ms(value: int) -> int:
        """Validate timeout milliseconds (min 1000)."""
        if not isinstance(value, int) or value < 1000:
            raise ValidationError(_("timeout_ms must be at least 1000"))
        return value


# ============= VALIDATION ERROR CODES =============

class ValidationErrorCodes:
    """Standard validation error codes."""
    
    # Field Errors
    REQUIRED_FIELD = "REQUIRED_FIELD"
    INVALID_TYPE = "INVALID_TYPE"
    INVALID_VALUE = "INVALID_VALUE"
    INVALID_FORMAT = "INVALID_FORMAT"
    OUT_OF_RANGE = "OUT_OF_RANGE"
    
    # Model Errors
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FIELD_COMBINATION = "INVALID_FIELD_COMBINATION"
    COMPUTED_FIELD_MISMATCH = "COMPUTED_FIELD_MISMATCH"
    
    # Specific Field Errors
    INVALID_ROUTE = "INVALID_ROUTE"
    INVALID_METHOD = "INVALID_METHOD"
    INVALID_PAGE_TYPE = "INVALID_PAGE_TYPE"
    INVALID_PAGE_STATE = "INVALID_PAGE_STATE"
    INVALID_STATUS = "INVALID_STATUS"
    INVALID_USAGE_TYPE = "INVALID_USAGE_TYPE"
    INVALID_USAGE_CONTEXT = "INVALID_USAGE_CONTEXT"
    MISSING_FILE_REFERENCE = "MISSING_FILE_REFERENCE"
    
    # Error Messages
    ERROR_MESSAGES = {
        REQUIRED_FIELD: "This field is required",
        INVALID_TYPE: "Invalid data type",
        INVALID_VALUE: "Invalid value",
        INVALID_FORMAT: "Invalid format",
        OUT_OF_RANGE: "Value out of allowed range",
        MISSING_REQUIRED_FIELD: "Required field is missing",
        INVALID_FIELD_COMBINATION: "Invalid combination of fields",
        COMPUTED_FIELD_MISMATCH: "Computed field value does not match actual data",
        INVALID_ROUTE: "Route must start with '/'",
        INVALID_METHOD: "Method must be one of: QUERY, MUTATION, GET, POST, PUT, DELETE, PATCH",
        INVALID_PAGE_TYPE: "Page type must be one of: dashboard, marketing, docs",
        INVALID_PAGE_STATE: "Page state must be one of: coming_soon, published, draft, development, test",
        INVALID_STATUS: "Status must be one of: draft, published, archived, deleted",
        INVALID_USAGE_TYPE: "Usage type must be one of: primary, secondary, conditional, lazy, prefetch",
        INVALID_USAGE_CONTEXT: "Usage context must be one of: data_fetching, data_mutation, authentication, analytics, realtime, background",
        MISSING_FILE_REFERENCE: "At least one of 'service_file' or 'router_file' must be provided",
    }
    
    @classmethod
    def get_message(cls, code: str) -> str:
        """Get error message for error code."""
        return cls.ERROR_MESSAGES.get(code, "Validation error")


# ============= VALIDATION HELPERS =============

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """Validate that all required fields are present."""
    missing = [field for field in required_fields if field not in data or data[field] is None]
    if missing:
        raise ValidationError({
            field: ValidationErrorCodes.get_message(ValidationErrorCodes.REQUIRED_FIELD)
            for field in missing
        })


def validate_enum_field(value: Any, valid_values: List[str], field_name: str) -> str:
    """Validate enum field value."""
    if value not in valid_values:
        raise ValidationError({
            field_name: f"{field_name} must be one of {valid_values}, got {value}"
        })
    return value


def validate_computed_fields(data: Dict[str, Any], computed_fields: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and auto-calculate computed fields."""
    for field_name, calculation_func in computed_fields.items():
        calculated_value = calculation_func(data)
        if field_name in data and data[field_name] != calculated_value:
            # Auto-correct computed field
            data[field_name] = calculated_value
        elif field_name not in data:
            # Set computed field
            data[field_name] = calculated_value
    return data


def calculate_endpoint_count(data: Dict[str, Any]) -> int:
    """Calculate endpoint_count from uses_endpoints."""
    uses_endpoints = data.get('metadata', {}).get('uses_endpoints', [])
    if isinstance(uses_endpoints, list):
        return len(uses_endpoints)
    return 0


def calculate_api_versions(data: Dict[str, Any]) -> List[str]:
    """Calculate api_versions from uses_endpoints."""
    uses_endpoints = data.get('metadata', {}).get('uses_endpoints', [])
    if not isinstance(uses_endpoints, list):
        return []
    
    api_versions_set = set()
    for endpoint in uses_endpoints:
        if isinstance(endpoint, dict) and 'api_version' in endpoint:
            api_versions_set.add(endpoint['api_version'])
    
    return sorted(list(api_versions_set))


def calculate_page_count(data: Dict[str, Any]) -> int:
    """Calculate page_count from used_by_pages."""
    used_by_pages = data.get('used_by_pages', [])
    if isinstance(used_by_pages, list):
        return len(used_by_pages)
    return 0


# ============= FIELD-SPECIFIC VALIDATORS =============

def validate_page_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate PageMetadata structure."""
    rules = ValidationRules()
    
    # Validate required fields
    validate_required_fields(data, ['route', 'file_path', 'purpose', 's3_key', 'last_updated'])
    
    # Validate and normalize route
    data['route'] = rules.validate_route(data.get('route', '/'))
    
    # Validate optional fields with defaults
    if 'status' not in data:
        data['status'] = 'published'
    else:
        data['status'] = rules.validate_status(data['status'])
    
    if 'page_state' not in data:
        data['page_state'] = 'development'
    else:
        data['page_state'] = rules.validate_page_state(data['page_state'])
    
    if 'authentication' not in data or not data['authentication']:
        data['authentication'] = 'Not required'
    
    # Validate uses_endpoints
    if 'uses_endpoints' in data and isinstance(data['uses_endpoints'], list):
        for endpoint in data['uses_endpoints']:
            if isinstance(endpoint, dict):
                if 'method' in endpoint:
                    endpoint['method'] = rules.validate_method(endpoint['method'])
                if 'usage_type' in endpoint:
                    endpoint['usage_type'] = rules.validate_usage_type(endpoint['usage_type'])
                if 'usage_context' in endpoint:
                    endpoint['usage_context'] = rules.validate_usage_context(endpoint['usage_context'])
    
    # Auto-calculate computed fields
    computed_fields = {
        'endpoint_count': calculate_endpoint_count,
        'api_versions': lambda d: calculate_api_versions(d)
    }
    data = validate_computed_fields({'metadata': data}, computed_fields)
    if 'metadata' in data:
        data = data['metadata']
    
    return data


def validate_endpoint_documentation(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate EndpointDocumentation structure."""
    rules = ValidationRules()
    
    # Validate required fields
    validate_required_fields(data, ['endpoint_id', 'endpoint_path', 'method', 'api_version', 'description'])
    
    # Validate method
    if 'method' in data:
        data['method'] = rules.validate_method(data['method'])
    
    # Validate endpoint_state
    if 'endpoint_state' not in data:
        data['endpoint_state'] = 'development'
    else:
        data['endpoint_state'] = rules.validate_page_state(data['endpoint_state'])  # Same values
    
    # Validate file reference requirement
    has_legacy_file = data.get('service_file') or data.get('router_file')
    files = data.get('files', {})
    has_files_object = files and (files.get('service_file') or files.get('router_file'))
    if not (has_legacy_file or has_files_object):
        raise ValidationError({
            'service_file': ValidationErrorCodes.get_message(ValidationErrorCodes.MISSING_FILE_REFERENCE),
            'router_file': ValidationErrorCodes.get_message(ValidationErrorCodes.MISSING_FILE_REFERENCE)
        })
    
    # Validate used_by_pages
    if 'used_by_pages' in data and isinstance(data['used_by_pages'], list):
        for page_usage in data['used_by_pages']:
            if isinstance(page_usage, dict):
                if 'usage_type' in page_usage:
                    page_usage['usage_type'] = rules.validate_usage_type(page_usage['usage_type'])
                if 'usage_context' in page_usage:
                    page_usage['usage_context'] = rules.validate_usage_context(page_usage['usage_context'])
    
    # Auto-calculate page_count
    data['page_count'] = calculate_page_count(data)
    
    return data


def validate_relationship_connection(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate RelationshipConnection structure."""
    rules = ValidationRules()
    
    # Validate required fields
    validate_required_fields(data, ['via_service', 'usage_type', 'usage_context'])
    
    # Validate optional fields with defaults
    if 'usage_type' not in data:
        data['usage_type'] = 'primary'
    else:
        data['usage_type'] = rules.validate_usage_type(data['usage_type'])
    
    if 'usage_context' not in data:
        data['usage_context'] = 'data_fetching'
    else:
        data['usage_context'] = rules.validate_usage_context(data['usage_context'])
    
    if 'invocation_pattern' not in data:
        data['invocation_pattern'] = 'on_mount'
    elif 'invocation_pattern' in data:
        data['invocation_pattern'] = rules.validate_invocation_pattern(data['invocation_pattern'])
    
    # Validate retry_policy if present
    if 'retry_policy' in data and isinstance(data['retry_policy'], dict):
        retry = data['retry_policy']
        if 'max_retries' in retry:
            retry['max_retries'] = rules.validate_retry_count(retry['max_retries'])
        if 'backoff_ms' in retry:
            retry['backoff_ms'] = rules.validate_backoff_ms(retry['backoff_ms'])
        if 'timeout_ms' in retry:
            retry['timeout_ms'] = rules.validate_timeout_ms(retry['timeout_ms'])
    
    return data


def validate_data_flow_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate DataFlowResponse structure."""
    rules = ValidationRules()
    
    # Set defaults
    if 'error_handling' not in data:
        data['error_handling'] = 'console'
    else:
        data['error_handling'] = rules.validate_error_handling(data['error_handling'])
    
    if 'loading_state' not in data:
        data['loading_state'] = 'spinner'
    else:
        data['loading_state'] = rules.validate_loading_state(data['loading_state'])
    
    # Ensure data_fields is a list
    if 'data_fields' not in data:
        data['data_fields'] = []
    elif not isinstance(data['data_fields'], list):
        data['data_fields'] = []
    
    return data
