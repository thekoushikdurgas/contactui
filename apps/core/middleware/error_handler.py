"""
Error Handling Middleware for consistent error responses.
"""

from __future__ import annotations

import logging
import traceback
from typing import Callable, Optional
from django.http import HttpRequest, JsonResponse, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

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
from apps.documentation.utils.exceptions import (
    DocumentationError,
    DocumentationNotFoundError,
    EndpointDocumentationNotFoundError,
    RelationshipNotFoundError,
    PostmanConfigurationNotFoundError,
)
from apps.documentation.utils.api_responses import (
    error_response,
    server_error_response,
    validation_error_response,
    not_found_response,
    forbidden_response,
    unauthorized_response,
)

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(MiddlewareMixin):
    """
    Middleware to handle exceptions and return consistent error responses.
    
    Provides:
    - Consistent error format across all endpoints
    - Proper error logging
    - Error categorization
    - Safe error messages (hide sensitive info in production)
    """
    
    def process_exception(
        self,
        request: HttpRequest,
        exception: Exception
    ) -> Optional[JsonResponse]:
        """
        Process exceptions and return standardized error responses.
        
        Args:
            request: Django request object
            exception: Exception that was raised
            
        Returns:
            JsonResponse with standardized error format, or None to let Django handle it
        """
        # Log the exception
        error_type = type(exception).__name__
        error_message = str(exception)
        
        # Get full traceback for logging
        tb = traceback.format_exc()
        
        # Log error with context
        logger.error(
            "Unhandled exception in %s: %s - %s",
            request.path,
            error_type,
            error_message,
            exc_info=True,
            extra={
                'request_path': request.path,
                'request_method': request.method,
                'user': str(request.user) if hasattr(request, 'user') else 'anonymous',
                'error_type': error_type,
                'error_message': error_message
            }
        )
        
        # Determine if this is an API request
        is_api_request = (
            request.path.startswith('/api/') or
            request.path.startswith('/docs/api/') or
            request.content_type == 'application/json' or
            'application/json' in request.META.get('HTTP_ACCEPT', '')
        )
        
        # For API requests, return JSON error response using api_responses
        if is_api_request:
            # Handle specific exception types
            if isinstance(exception, ValidationError):
                errors = []
                if hasattr(exception, 'field') and exception.field:
                    errors.append(f"{exception.field}: {error_message}")
                else:
                    errors.append(error_message)
                response = validation_error_response(errors)
                if settings.DEBUG:
                    response.meta['traceback'] = tb.split('\n')
                return response.to_json_response()
            
            elif isinstance(exception, NotFoundError):
                response = not_found_response("Resource")
                if settings.DEBUG:
                    response.meta['traceback'] = tb.split('\n')
                    response.meta['error_type'] = error_type
                return response.to_json_response()

            elif isinstance(
                exception,
                (
                    DocumentationNotFoundError,
                    EndpointDocumentationNotFoundError,
                    RelationshipNotFoundError,
                    PostmanConfigurationNotFoundError,
                ),
            ):
                response = not_found_response("Resource")
                if settings.DEBUG:
                    response.meta['traceback'] = tb.split('\n')
                    response.meta['error_type'] = error_type
                return response.to_json_response()

            elif isinstance(exception, PermissionDeniedError):
                response = forbidden_response(error_message)
                if settings.DEBUG:
                    response.meta['traceback'] = tb.split('\n')
                return response.to_json_response()
            
            elif isinstance(exception, AuthenticationError):
                response = unauthorized_response(error_message)
                if settings.DEBUG:
                    response.meta['traceback'] = tb.split('\n')
                return response.to_json_response()
            
            elif isinstance(exception, ConflictError):
                response = error_response(
                    message=error_message,
                    status_code=409
                )
                if settings.DEBUG:
                    response.meta['traceback'] = tb.split('\n')
                return response.to_json_response()
            
            elif isinstance(exception, ServiceUnavailableError):
                response = error_response(
                    message=error_message,
                    status_code=503
                )
                if settings.DEBUG:
                    response.meta['traceback'] = tb.split('\n')
                return response.to_json_response()
            
            elif isinstance(exception, (ServiceError, RepositoryError, DocumentationError)):
                # Service layer errors
                safe_message = self._get_safe_error_message(error_message, 500)
                response = server_error_response(safe_message)
                if settings.DEBUG:
                    response.meta['traceback'] = tb.split('\n')
                    response.meta['error_type'] = error_type
                    response.meta['original_message'] = error_message
                return response.to_json_response()
            
            else:
                # Generic exception - determine status code
                status_code = 500
                if hasattr(exception, 'status_code'):
                    status_code = exception.status_code
                elif 'not found' in error_message.lower() or 'does not exist' in error_message.lower():
                    status_code = 404
                elif 'permission' in error_message.lower() or 'forbidden' in error_message.lower():
                    status_code = 403
                elif 'validation' in error_message.lower() or 'invalid' in error_message.lower():
                    status_code = 400
                
                safe_message = self._get_safe_error_message(error_message, status_code)
                response = error_response(
                    message=safe_message,
                    status_code=status_code
                )
                if settings.DEBUG:
                    response.meta['traceback'] = tb.split('\n')
                    response.meta['error_type'] = error_type
                    response.meta['original_message'] = error_message
                return response.to_json_response()
        
        # For non-API requests, let Django handle it (will show error page)
        return None
    
    def _get_safe_error_message(self, error_message: str, status_code: int) -> str:
        """
        Get safe error message for production.
        
        Hides sensitive information in production mode.
        
        Args:
            error_message: Original error message
            status_code: HTTP status code
            
        Returns:
            Safe error message
        """
        if settings.DEBUG:
            return error_message
        
        # In production, hide sensitive details
        if status_code == 500:
            return "An internal server error occurred. Please try again later."
        elif status_code == 404:
            return "The requested resource was not found."
        elif status_code == 403:
            return "You don't have permission to access this resource."
        elif status_code == 400:
            return "Invalid request. Please check your input."
        else:
            return "An error occurred processing your request."
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
