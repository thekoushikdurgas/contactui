"""
Custom exception handlers for DRF.

This module provides centralized exception handling for all API endpoints.
"""

from rest_framework.views import exception_handler
from rest_framework import status
from rest_framework.response import Response
from apps.core.exceptions import (
    ValidationError,
    NotFoundError,
    PermissionDeniedError,
    AuthenticationError,
    ConflictError,
    ServiceUnavailableError,
    ServiceError,
    RepositoryError,
)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF.
    
    Provides consistent error response format across all APIs.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Handle custom exceptions
    if isinstance(exc, (ValidationError, NotFoundError, PermissionDeniedError,
                       AuthenticationError, ConflictError, ServiceUnavailableError)):
        return Response(
            {
                'success': False,
                'error': exc.detail,
                'error_code': exc.code,
                'field': getattr(exc, 'field', None),
            },
            status=exc.status_code
        )
    
    # Handle service layer exceptions
    if isinstance(exc, (ServiceError, RepositoryError)):
        return Response(
            {
                'success': False,
                'error': str(exc),
                'error_code': getattr(exc, 'error_code', 'service_error'),
                'service': getattr(exc, 'service_name', None),
                'operation': getattr(exc, 'operation', None),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Customize the response for default handler
    if response is not None:
        custom_response_data = {
            'success': False,
            'error': response.data.get('detail', 'An error occurred'),
            'error_code': response.data.get('code', 'error'),
        }
        
        # Add field errors if present
        if 'non_field_errors' in response.data:
            custom_response_data['non_field_errors'] = response.data['non_field_errors']
        
        # Add field-specific errors
        field_errors = {
            k: v for k, v in response.data.items()
            if k not in ('detail', 'code', 'non_field_errors')
        }
        if field_errors:
            custom_response_data['field_errors'] = field_errors
        
        response.data = custom_response_data
    
    return response
