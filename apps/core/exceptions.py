"""
Custom exceptions for core services and DRF API.

This module provides custom exception classes for different layers
of the application, including DRF-compatible exceptions.
"""

from rest_framework.exceptions import APIException
from rest_framework import status


class S3Error(Exception):
    """Exception raised for S3 operations."""
    
    def __init__(
        self,
        message: str,
        s3_key: str = None,
        operation: str = None,
        error_code: str = None
    ):
        self.message = message
        self.s3_key = s3_key
        self.operation = operation
        self.error_code = error_code
        super().__init__(self.message)


class LambdaAPIError(Exception):
    """Exception raised for Lambda API operations."""
    
    def __init__(
        self,
        message: str,
        endpoint: str = None,
        status_code: int = None,
        error_code: str = None
    ):
        self.message = message
        self.endpoint = endpoint
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


class GraphQLError(Exception):
    """Exception raised for GraphQL operations."""
    
    def __init__(
        self,
        message: str,
        query: str = None,
        errors: list = None,
        error_code: str = None
    ):
        self.message = message
        self.query = query
        self.errors = errors or []
        self.error_code = error_code
        super().__init__(self.message)


class RepositoryError(Exception):
    """Exception raised for repository operations."""
    
    def __init__(
        self,
        message: str,
        entity_id: str = None,
        operation: str = None,
        error_code: str = None
    ):
        self.message = message
        self.entity_id = entity_id
        self.operation = operation
        self.error_code = error_code
        super().__init__(self.message)


class ServiceError(Exception):
    """Exception raised for service layer operations."""
    
    def __init__(
        self,
        message: str,
        service_name: str = None,
        operation: str = None,
        error_code: str = None
    ):
        self.message = message
        self.service_name = service_name
        self.operation = operation
        self.error_code = error_code
        super().__init__(self.message)


# DRF-Compatible Exceptions

class ValidationError(APIException):
    """Custom validation error for DRF."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Invalid input.'
    default_code = 'invalid'
    
    def __init__(self, detail=None, code=None, field=None):
        if detail is None:
            detail = self.default_detail
        if code is None:
            code = self.default_code
        
        self.detail = detail
        self.code = code
        self.field = field


class NotFoundError(APIException):
    """Custom not found error for DRF."""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Resource not found.'
    default_code = 'not_found'


class PermissionDeniedError(APIException):
    """Custom permission denied error for DRF."""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'You do not have permission to perform this action.'
    default_code = 'permission_denied'


class AuthenticationError(APIException):
    """Custom authentication error for DRF."""
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Authentication credentials were not provided.'
    default_code = 'authentication_failed'


class ConflictError(APIException):
    """Custom conflict error for DRF (409)."""
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'A conflict occurred with the current state of the resource.'
    default_code = 'conflict'


class ServiceUnavailableError(APIException):
    """Custom service unavailable error for DRF (503)."""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'Service temporarily unavailable.'
    default_code = 'service_unavailable'
