"""
Request validation utilities using Pydantic.

Provides decorators and schemas for validating API request data.
"""

from __future__ import annotations

import functools
import json
import logging
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union

from django.http import HttpRequest, JsonResponse
from pydantic import BaseModel, ValidationError as PydanticValidationError

from apps.documentation.utils.api_responses import validation_error_response

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)
F = TypeVar("F", bound=Callable)


def validate_request(
    schema: Type[T],
    parse_json: bool = True,
    allow_empty: bool = False,
) -> Callable[[F], F]:
    """
    Decorator to validate request body against a Pydantic schema.
    
    Args:
        schema: Pydantic model class to validate against
        parse_json: Whether to parse JSON body (default: True)
        allow_empty: Whether to allow empty body (default: False)
        
    Returns:
        Decorated function with validated data in request.validated_data
        
    Example:
        @validate_request(PageCreateSchema)
        def create_page_api(request: HttpRequest) -> JsonResponse:
            data = request.validated_data  # Validated Pydantic model
            ...
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
            # Parse JSON body if needed
            if parse_json:
                try:
                    body = request.body
                    if not body and not allow_empty:
                        return validation_error_response(
                            ["Request body is required"]
                        ).to_json_response()
                    
                    if not body:
                        data = {}
                    else:
                        data = json.loads(body)
                except json.JSONDecodeError as e:
                    logger.warning("Invalid JSON in request body: %s", e)
                    return validation_error_response(
                        [f"Invalid JSON: {str(e)}"]
                    ).to_json_response()
            else:
                # Use GET params or form data
                data = dict(request.GET) if request.method == "GET" else dict(request.POST)
            
            # Validate against schema
            try:
                validated_data = schema(**data)
                # Attach validated data to request object
                request.validated_data = validated_data
            except PydanticValidationError as e:
                logger.warning("Validation failed for %s: %s", func.__name__, e.errors())
                # Format Pydantic errors into list of strings
                errors = []
                for error in e.errors():
                    field = ".".join(str(loc) for loc in error.get("loc", []))
                    msg = error.get("msg", "Validation error")
                    errors.append(f"{field}: {msg}")
                
                return validation_error_response(errors).to_json_response()
            except Exception as e:
                logger.error("Unexpected error during validation: %s", e, exc_info=True)
                return validation_error_response(
                    [f"Validation error: {str(e)}"]
                ).to_json_response()
            
            # Call original function
            return func(request, *args, **kwargs)
        
        return wrapper  # type: ignore
    return decorator


def validate_query_params(
    schema: Type[T],
) -> Callable[[F], F]:
    """
    Decorator to validate query parameters against a Pydantic schema.
    
    Args:
        schema: Pydantic model class to validate against
        
    Returns:
        Decorated function with validated data in request.validated_params
        
    Example:
        @validate_query_params(PageListQuerySchema)
        def list_pages_api(request: HttpRequest) -> JsonResponse:
            params = request.validated_params  # Validated Pydantic model
            ...
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
            # Convert query params to dict
            query_params = dict(request.GET)
            
            # Convert string values to appropriate types where possible
            # (Pydantic will handle type conversion)
            processed_params = {}
            for key, value in query_params.items():
                # Handle multiple values (take first)
                if isinstance(value, list):
                    processed_params[key] = value[0] if value else None
                else:
                    processed_params[key] = value
            
            # Validate against schema
            try:
                validated_params = schema(**processed_params)
                # Attach validated params to request object
                request.validated_params = validated_params
            except PydanticValidationError as e:
                logger.warning("Query param validation failed for %s: %s", func.__name__, e.errors())
                errors = []
                for error in e.errors():
                    field = ".".join(str(loc) for loc in error.get("loc", []))
                    msg = error.get("msg", "Validation error")
                    errors.append(f"{field}: {msg}")
                
                return validation_error_response(errors).to_json_response()
            except Exception as e:
                logger.error("Unexpected error during query validation: %s", e, exc_info=True)
                return validation_error_response(
                    [f"Query parameter validation error: {str(e)}"]
                ).to_json_response()
            
            # Call original function
            return func(request, *args, **kwargs)
        
        return wrapper  # type: ignore
    return decorator


def validate_path_params(
    schema: Type[T],
) -> Callable[[F], F]:
    """
    Decorator to validate path parameters against a Pydantic schema.
    
    Args:
        schema: Pydantic model class to validate against
        
    Returns:
        Decorated function with validated data in request.validated_path_params
        
    Example:
        @validate_path_params(PageDetailPathSchema)
        def get_page_api(request: HttpRequest, page_id: str) -> JsonResponse:
            params = request.validated_path_params  # Validated Pydantic model
            ...
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
            # Use kwargs as path params
            path_params = kwargs.copy()
            
            # Validate against schema
            try:
                validated_params = schema(**path_params)
                # Attach validated params to request object
                request.validated_path_params = validated_params
            except PydanticValidationError as e:
                logger.warning("Path param validation failed for %s: %s", func.__name__, e.errors())
                errors = []
                for error in e.errors():
                    field = ".".join(str(loc) for loc in error.get("loc", []))
                    msg = error.get("msg", "Validation error")
                    errors.append(f"{field}: {msg}")
                
                return validation_error_response(errors).to_json_response()
            except Exception as e:
                logger.error("Unexpected error during path validation: %s", e, exc_info=True)
                return validation_error_response(
                    [f"Path parameter validation error: {str(e)}"]
                ).to_json_response()
            
            # Call original function
            return func(request, *args, **kwargs)
        
        return wrapper  # type: ignore
    return decorator
