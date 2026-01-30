"""Django-side validation models matching Lambda API Pydantic schemas.

These models provide validation rules that match the Lambda API models,
allowing Django to validate data before sending to Lambda API or after receiving from it.

Over time, these helpers have evolved into a thin layer around the canonical
Pydantic models defined in ``apps.documentation.schemas.pydantic`` so that
all validation and persistence ultimately goes through a single source of
truth for JSON schemas.
"""

from typing import Any, Dict, List, Optional

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from pydantic import ValidationError as PydanticValidationError

from apps.documentation.schemas.pydantic.models import (
    EnhancedRelationship,
    EndpointDocumentation,
    PageDocumentation,
)
from apps.documentation.schemas.pydantic.postman_models import PostmanConfiguration


class LambdaModelValidator:
    """Base validator for Lambda API models."""
    
    @staticmethod
    def validate_id_format(value: str, resource_id: str) -> str:
        """Validate ID format (should be {resource_id}-001 but allow other formats)."""
        if not value:
            return f"{resource_id}-001"
        return value
    
    @staticmethod
    def validate_route(value: Any) -> str:
        """Validate and fix route to start with '/'."""
        if not isinstance(value, str):
            return "/"
        value = value.strip()
        if not value or value == "/":
            return "/"
        if not value.startswith("/"):
            # Auto-fix routes that don't start with '/'
            if len(value) > 50 or "error" in value.lower() or "boundary" in value.lower():
                return "/"
            return "/" + value.lstrip("/")
        return value
    
    @staticmethod
    def validate_method(value: str) -> str:
        """Validate and uppercase HTTP/GraphQL method."""
        valid_methods = ["QUERY", "MUTATION", "GET", "POST", "PUT", "DELETE", "PATCH"]
        if value.upper() not in valid_methods:
            raise ValidationError(_(f"method must be one of {valid_methods}, got {value}"))
        return value.upper()
    
    @staticmethod
    def validate_page_type(value: str) -> str:
        """Validate page type."""
        valid_types = ["dashboard", "marketing", "docs"]
        if value not in valid_types:
            raise ValidationError(_(f"page_type must be one of {valid_types}, got {value}"))
        return value
    
    @staticmethod
    def validate_page_state(value: str) -> str:
        """Validate page state."""
        valid_states = ["coming_soon", "published", "draft", "development", "test"]
        if value not in valid_states:
            raise ValidationError(_(f"page_state must be one of {valid_states}, got {value}"))
        return value
    
    @staticmethod
    def validate_status(value: str) -> str:
        """Validate status."""
        valid_statuses = ["draft", "published", "archived", "deleted"]
        if value not in valid_statuses:
            raise ValidationError(_(f"status must be one of {valid_statuses}, got {value}"))
        return value
    
    @staticmethod
    def validate_endpoint_state(value: str) -> str:
        """Validate endpoint state."""
        valid_states = ["coming_soon", "published", "draft", "development", "test"]
        if value not in valid_states:
            raise ValidationError(_(f"endpoint_state must be one of {valid_states}, got {value}"))
        return value
    
    @staticmethod
    def validate_usage_type(value: str) -> str:
        """Validate usage type."""
        valid_types = ["primary", "secondary", "conditional", "lazy", "prefetch"]
        if value not in valid_types:
            raise ValidationError(_(f"usage_type must be one of {valid_types}, got {value}"))
        return value
    
    @staticmethod
    def validate_usage_context(value: str) -> str:
        """Validate usage context."""
        valid_contexts = ["data_fetching", "data_mutation", "authentication", "analytics", "realtime", "background"]
        if value not in valid_contexts:
            raise ValidationError(_(f"usage_context must be one of {valid_contexts}, got {value}"))
        return value
    
    @staticmethod
    def validate_relationship_state(value: str) -> str:
        """Validate relationship state."""
        valid_states = ["coming_soon", "published", "draft", "development", "test"]
        if value not in valid_states:
            raise ValidationError(_(f"state must be one of {valid_states}, got {value}"))
        return value


class PageMetadataValidator:
    """Validator for PageMetadata model."""
    
    @staticmethod
    def validate(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize PageMetadata data."""
        validator = LambdaModelValidator()
        
        # Validate required fields
        if 'route' not in data:
            raise ValidationError(_("route is required"))
        data['route'] = validator.validate_route(data.get('route', '/'))
        
        if 'file_path' not in data:
            data['file_path'] = ''
        if not isinstance(data['file_path'], str):
            data['file_path'] = str(data['file_path']) if data['file_path'] else ''
        
        if 'purpose' not in data:
            data['purpose'] = ''
        if not isinstance(data['purpose'], str):
            data['purpose'] = str(data['purpose']) if data['purpose'] else ''
        
        # Validate optional fields
        if 'status' in data:
            data['status'] = validator.validate_status(data['status'])
        else:
            data['status'] = 'published'
        
        if 'page_state' in data:
            data['page_state'] = validator.validate_page_state(data['page_state'])
        else:
            data['page_state'] = 'development'
        
        if 'authentication' not in data or not data['authentication']:
            data['authentication'] = 'Not required'
        
        # Auto-calculate computed fields
        uses_endpoints = data.get('uses_endpoints', [])
        data['endpoint_count'] = len(uses_endpoints)
        
        # Derive api_versions from uses_endpoints
        api_versions_set = set()
        for endpoint in uses_endpoints:
            if isinstance(endpoint, dict) and 'api_version' in endpoint:
                api_versions_set.add(endpoint['api_version'])
        data['api_versions'] = sorted(list(api_versions_set))
        
        # Ensure s3_key is set
        if 's3_key' not in data:
            page_id = data.get('page_id', 'unknown')
            data['s3_key'] = f"data/pages/{page_id}.json"
        
        # Ensure last_updated is set
        if 'last_updated' not in data:
            from datetime import datetime, timezone
            data['last_updated'] = datetime.now(timezone.utc).isoformat()
        
        return data


class PageEndpointUsageValidator:
    """Validator for PageEndpointUsage model."""
    
    @staticmethod
    def validate(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize PageEndpointUsage data."""
        validator = LambdaModelValidator()
        
        # Validate required fields
        required_fields = ['endpoint_path', 'method', 'api_version', 'via_service', 'usage_type', 'usage_context']
        for field in required_fields:
            if field not in data:
                raise ValidationError(_(f"{field} is required"))
        
        # Validate and normalize
        data['method'] = validator.validate_method(data['method'])
        data['usage_type'] = validator.validate_usage_type(data['usage_type'])
        data['usage_context'] = validator.validate_usage_context(data['usage_context'])
        
        return data


class EndpointDocumentationValidator:
    """Validator for EndpointDocumentation model."""
    
    @staticmethod
    def validate(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize EndpointDocumentation data."""
        validator = LambdaModelValidator()
        
        # Validate required fields
        required_fields = ['endpoint_id', 'endpoint_path', 'method', 'api_version', 'description']
        for field in required_fields:
            if field not in data:
                raise ValidationError(_(f"{field} is required"))
        
        # Validate method
        data['method'] = validator.validate_method(data['method'])
        
        # Validate endpoint_state
        if 'endpoint_state' in data:
            data['endpoint_state'] = validator.validate_endpoint_state(data['endpoint_state'])
        else:
            data['endpoint_state'] = 'development'
        
        # Validate file reference (at least one required)
        has_legacy_file = data.get('service_file') or data.get('router_file')
        files = data.get('files', {})
        has_files_object = files and (files.get('service_file') or files.get('router_file'))
        if not (has_legacy_file or has_files_object):
            raise ValidationError(_("At least one of 'service_file' or 'router_file' must be provided"))
        
        # Auto-calculate page_count
        used_by_pages = data.get('used_by_pages', [])
        data['page_count'] = len(used_by_pages)
        
        # Ensure timestamps
        if 'created_at' not in data:
            from datetime import datetime, timezone
            data['created_at'] = datetime.now(timezone.utc).isoformat()
        if 'updated_at' not in data:
            from datetime import datetime, timezone
            data['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        return data


class RelationshipValidator:
    """Validator for EnhancedRelationship model."""
    
    @staticmethod
    def validate(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize EnhancedRelationship data."""
        validator = LambdaModelValidator()
        
        # Validate state if present
        if 'state' in data:
            data['state'] = validator.validate_relationship_state(data['state'])
        else:
            data['state'] = 'development'
        
        # Validate legacy fields if present
        if 'method' in data:
            data['method'] = validator.validate_method(data['method'])
        
        if 'usage_type' in data:
            data['usage_type'] = validator.validate_usage_type(data['usage_type'])
        
        if 'usage_context' in data:
            data['usage_context'] = validator.validate_usage_context(data['usage_context'])
        
        return data


class PostmanConfigurationValidator:
    """Validator for PostmanConfiguration model."""
    
    @staticmethod
    def validate(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize PostmanConfiguration data."""
        validator = LambdaModelValidator()
        
        # Validate required fields
        required_fields = ['config_id', 'name', 'collection', 'metadata']
        for field in required_fields:
            if field not in data:
                raise ValidationError(_(f"{field} is required"))
        
        # Validate state
        if 'state' in data:
            # Use endpoint_state validator (same values)
            data['state'] = validator.validate_endpoint_state(data['state'])
        else:
            data['state'] = 'development'
        
        return data


def validate_page_data(page_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate complete PageDocumentation data.

    This first applies the legacy Django-side normalization rules to preserve
    backward-compatible behaviour, and then validates the result against the
    canonical Pydantic PageDocumentation model. The returned dict matches the
    JSON representation used in media/S3 (e.g. includes ``_id``).
    """
    validator = LambdaModelValidator()

    # Legacy normalization/validation
    if 'page_type' not in page_data:
        raise ValidationError(_("page_type is required"))
    page_data['page_type'] = validator.validate_page_type(page_data['page_type'])

    if 'metadata' in page_data:
        page_data['metadata'] = PageMetadataValidator.validate(page_data['metadata'])

    if 'metadata' in page_data and 'uses_endpoints' in page_data['metadata']:
        validated_endpoints = []
        for endpoint in page_data['metadata']['uses_endpoints']:
            validated_endpoints.append(PageEndpointUsageValidator.validate(endpoint))
        page_data['metadata']['uses_endpoints'] = validated_endpoints

    if '_id' not in page_data and 'id' not in page_data:
        page_id = page_data.get('page_id', 'unknown')
        page_data['_id'] = f"{page_id}-001"

    if 'created_at' not in page_data:
        from datetime import datetime, timezone
        page_data['created_at'] = datetime.now(timezone.utc).isoformat()

    # Canonical Pydantic validation
    try:
        model = PageDocumentation.model_validate(page_data)
    except PydanticValidationError as e:
        raise ValidationError(_("Invalid page data: %(error)s") % {"error": str(e)}) from e

    return model.model_dump(by_alias=True, exclude_none=False)


def validate_endpoint_data(endpoint_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate complete EndpointDocumentation data.

    Applies the legacy EndpointDocumentationValidator for normalization and then
    validates against the canonical Pydantic EndpointDocumentation model.
    """
    endpoint_data = EndpointDocumentationValidator.validate(endpoint_data)

    if '_id' not in endpoint_data and 'id' not in endpoint_data:
        endpoint_id = endpoint_data.get('endpoint_id', 'unknown')
        endpoint_data['_id'] = f"{endpoint_id}-001"

    try:
        model = EndpointDocumentation.model_validate(endpoint_data)
    except PydanticValidationError as e:
        raise ValidationError(_("Invalid endpoint data: %(error)s") % {"error": str(e)}) from e

    return model.model_dump(by_alias=True, exclude_none=False)


def validate_relationship_data(relationship_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate complete EnhancedRelationship data.

    Applies the legacy RelationshipValidator for normalization and then
    validates against the canonical Pydantic EnhancedRelationship model.
    """
    relationship_data = RelationshipValidator.validate(relationship_data)

    if '_id' not in relationship_data and 'id' not in relationship_data:
        relationship_id = relationship_data.get('relationship_id')
        if relationship_id:
            relationship_data['_id'] = relationship_id

    try:
        model = EnhancedRelationship.model_validate(relationship_data)
    except PydanticValidationError as e:
        raise ValidationError(_("Invalid relationship data: %(error)s") % {"error": str(e)}) from e

    return model.model_dump(by_alias=True, exclude_none=False)


def validate_postman_configuration_data(config_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate complete PostmanConfiguration data using the canonical Pydantic model.
    """
    config_data = PostmanConfigurationValidator.validate(config_data)

    if '_id' not in config_data and 'id' not in config_data:
        config_id = config_data.get('config_id', 'unknown')
        config_data['_id'] = config_id

    try:
        model = PostmanConfiguration.model_validate(config_data)
    except PydanticValidationError as e:
        raise ValidationError(_("Invalid Postman configuration data: %(error)s") % {"error": str(e)}) from e

    return model.model_dump(by_alias=True, exclude_none=False)
