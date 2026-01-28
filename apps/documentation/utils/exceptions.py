"""
Custom exceptions for documentation app.

Note: S3Error, RepositoryError, and LambdaAPIError are imported from apps.core.exceptions
to avoid duplication. DocumentationError is specific to documentation services.
DocumentationNotFoundError, EndpointDocumentationNotFoundError, RelationshipNotFoundError,
and PostmanConfigurationNotFoundError map to Lambda documentation.api 404 behavior.
"""

from apps.core.exceptions import (
    S3Error,
    RepositoryError,
    LambdaAPIError,
    ServiceError,
)


class DocumentationError(ServiceError):
    """
    Exception raised for documentation service operations.

    Inherits from ServiceError for consistency with other service exceptions.
    """
    def __init__(
        self,
        message: str,
        resource_id: str = None,
        operation: str = None,
        service_name: str = "DocumentationService",
        error_code: str = None
    ):
        super().__init__(
            message=message,
            service_name=service_name,
            operation=operation,
            error_code=error_code or "documentation_error"
        )
        self.resource_id = resource_id


class DocumentationNotFoundError(DocumentationError):
    """Raised when a documentation page is not found. Maps to 404."""
    def __init__(self, message: str, resource_id: str = None, **kwargs):
        super().__init__(message=message, resource_id=resource_id, error_code="documentation_not_found", **kwargs)


class EndpointDocumentationNotFoundError(DocumentationError):
    """Raised when endpoint documentation is not found. Maps to 404."""
    def __init__(self, message: str, resource_id: str = None, **kwargs):
        super().__init__(message=message, resource_id=resource_id, error_code="endpoint_not_found", **kwargs)


class RelationshipNotFoundError(DocumentationError):
    """Raised when a relationship is not found. Maps to 404."""
    def __init__(self, message: str, resource_id: str = None, **kwargs):
        super().__init__(message=message, resource_id=resource_id, error_code="relationship_not_found", **kwargs)


class PostmanConfigurationNotFoundError(DocumentationError):
    """Raised when a Postman configuration is not found. Maps to 404."""
    def __init__(self, message: str, resource_id: str = None, **kwargs):
        super().__init__(message=message, resource_id=resource_id, error_code="postman_not_found", **kwargs)


# Backward-compatible alias used by tests and views
NotFoundError = DocumentationNotFoundError


# Re-export for backward compatibility
__all__ = [
    'S3Error',
    'RepositoryError',
    'LambdaAPIError',
    'DocumentationError',
    'DocumentationNotFoundError',
    'EndpointDocumentationNotFoundError',
    'RelationshipNotFoundError',
    'PostmanConfigurationNotFoundError',
    'NotFoundError',
]
