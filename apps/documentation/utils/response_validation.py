"""
Response validation utilities using Pydantic.

Provides decorators for validating API response data before returning to clients.
This ensures API responses match expected schemas and helps catch bugs early.
"""

from __future__ import annotations

import functools
import logging
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union

from django.http import HttpRequest, JsonResponse
from pydantic import BaseModel, ValidationError as PydanticValidationError

from apps.documentation.utils.api_responses import APIResponse, server_error_response

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)
F = TypeVar("F", bound=Callable)


def validate_response(
    schema: Type[T],
    validate_data_only: bool = True,
    strict: bool = False,
) -> Callable[[F], F]:
    """
    Decorator to validate API response data against a Pydantic schema.
    
    This decorator validates that the response data matches the expected schema
    before returning it to the client. This helps catch bugs early and ensures
    API consistency.
    
    Args:
        schema: Pydantic model class to validate against
        validate_data_only: If True, validates only the 'data' field of APIResponse.
                           If False, validates the entire response structure (default: True)
        strict: If True, raises exceptions on validation errors (default: False).
                If False, logs warning and returns error response
        
    Returns:
        Decorated function with response validation
        
    Example:
        ```python
        from apps.documentation.schemas.response_schemas import PageResponseSchema
        
        @validate_response(PageResponseSchema)
        def get_page_api(request: HttpRequest) -> JsonResponse:
            page = pages_service.get_page(page_id)
            return success_response(page).to_json_response()
        ```
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
            # Call original function
            response = func(request, *args, **kwargs)
            
            # Only validate JsonResponse objects
            if not isinstance(response, JsonResponse):
                logger.warning(
                    f"{func.__name__} returned non-JsonResponse, skipping validation"
                )
                return response
            
            try:
                # Parse response content
                import json
                response_data = json.loads(response.content)
                
                # Extract data to validate
                if validate_data_only:
                    # Validate only the 'data' field
                    if not isinstance(response_data, dict):
                        raise ValueError("Response is not a dictionary")
                    
                    if 'data' not in response_data:
                        logger.debug(
                            f"{func.__name__} response has no 'data' field, skipping validation"
                        )
                        return response
                    
                    data_to_validate = response_data['data']
                else:
                    # Validate entire response structure
                    data_to_validate = response_data
                
                # Validate against schema
                try:
                    validated_data = schema(**data_to_validate) if isinstance(data_to_validate, dict) else schema(data_to_validate)
                    logger.debug(f"Response validation passed for {func.__name__}")
                except PydanticValidationError as e:
                    error_msg = f"Response validation failed for {func.__name__}: {e.errors()}"
                    
                    if strict:
                        logger.error(error_msg)
                        raise ValueError(error_msg) from e
                    else:
                        logger.warning(error_msg)
                        # Return error response instead of original response
                        return server_error_response(
                            "Response validation failed - this is a server error"
                        ).to_json_response()
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse response JSON from {func.__name__}: {e}")
                if strict:
                    raise
                return server_error_response(
                    "Invalid response format"
                ).to_json_response()
            except Exception as e:
                logger.error(
                    f"Unexpected error during response validation in {func.__name__}: {e}",
                    exc_info=True
                )
                if strict:
                    raise
                # Return original response on unexpected errors
                return response
            
            return response
        
        return wrapper  # type: ignore
    return decorator


def validate_response_list(
    item_schema: Type[T],
    validate_data_only: bool = True,
    strict: bool = False,
) -> Callable[[F], F]:
    """
    Decorator to validate API response data that is a list of items.
    
    This decorator validates that each item in the response list matches
    the expected schema.
    
    Args:
        item_schema: Pydantic model class to validate each list item against
        validate_data_only: If True, validates only the 'data' field (default: True)
        strict: If True, raises exceptions on validation errors (default: False)
        
    Returns:
        Decorated function with list response validation
        
    Example:
        ```python
        from apps.documentation.schemas.response_schemas import PageResponseSchema
        
        @validate_response_list(PageResponseSchema)
        def list_pages_api(request: HttpRequest) -> JsonResponse:
            pages = pages_service.list_pages()
            return success_response(pages).to_json_response()
        ```
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
            # Call original function
            response = func(request, *args, **kwargs)
            
            # Only validate JsonResponse objects
            if not isinstance(response, JsonResponse):
                logger.warning(
                    f"{func.__name__} returned non-JsonResponse, skipping validation"
                )
                return response
            
            try:
                # Parse response content
                import json
                response_data = json.loads(response.content)
                
                # Extract data to validate
                if validate_data_only:
                    if not isinstance(response_data, dict) or 'data' not in response_data:
                        logger.debug(
                            f"{func.__name__} response has no 'data' field, skipping validation"
                        )
                        return response
                    
                    data_to_validate = response_data['data']
                else:
                    data_to_validate = response_data
                
                # Ensure data is a list
                if not isinstance(data_to_validate, list):
                    error_msg = f"Expected list response in {func.__name__}, got {type(data_to_validate)}"
                    if strict:
                        raise ValueError(error_msg)
                    logger.warning(error_msg)
                    return server_error_response(
                        "Invalid response format - expected list"
                    ).to_json_response()
                
                # Validate each item
                validation_errors = []
                for idx, item in enumerate(data_to_validate):
                    try:
                        if isinstance(item, dict):
                            item_schema(**item)
                        else:
                            item_schema(item)
                    except PydanticValidationError as e:
                        validation_errors.append({
                            'index': idx,
                            'errors': e.errors()
                        })
                
                if validation_errors:
                    error_msg = (
                        f"Response list validation failed for {func.__name__}: "
                        f"{len(validation_errors)} items failed validation"
                    )
                    
                    if strict:
                        logger.error(error_msg)
                        raise ValueError(error_msg)
                    else:
                        logger.warning(f"{error_msg}. Errors: {validation_errors}")
                        return server_error_response(
                            "Response validation failed - this is a server error"
                        ).to_json_response()
                
                logger.debug(f"Response list validation passed for {func.__name__}")
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse response JSON from {func.__name__}: {e}")
                if strict:
                    raise
                return server_error_response(
                    "Invalid response format"
                ).to_json_response()
            except Exception as e:
                logger.error(
                    f"Unexpected error during response validation in {func.__name__}: {e}",
                    exc_info=True
                )
                if strict:
                    raise
                return response
            
            return response
        
        return wrapper  # type: ignore
    return decorator


def validate_response_type(
    expected_type: type,
    validate_data_only: bool = True,
    strict: bool = False,
) -> Callable[[F], F]:
    """
    Decorator to validate API response data type (simple type checking).
    
    This decorator performs basic type validation on response data.
    For more complex validation, use @validate_response with a Pydantic schema.
    
    Args:
        expected_type: Python type to validate against (e.g., dict, list, str, int)
        validate_data_only: If True, validates only the 'data' field (default: True)
        strict: If True, raises exceptions on validation errors (default: False)
        
    Returns:
        Decorated function with type validation
        
    Example:
        ```python
        @validate_response_type(dict)
        def get_page_api(request: HttpRequest) -> JsonResponse:
            page = pages_service.get_page(page_id)
            return success_response(page).to_json_response()
        ```
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
            # Call original function
            response = func(request, *args, **kwargs)
            
            # Only validate JsonResponse objects
            if not isinstance(response, JsonResponse):
                logger.warning(
                    f"{func.__name__} returned non-JsonResponse, skipping validation"
                )
                return response
            
            try:
                # Parse response content
                import json
                response_data = json.loads(response.content)
                
                # Extract data to validate
                if validate_data_only:
                    if not isinstance(response_data, dict) or 'data' not in response_data:
                        logger.debug(
                            f"{func.__name__} response has no 'data' field, skipping validation"
                        )
                        return response
                    
                    data_to_validate = response_data['data']
                else:
                    data_to_validate = response_data
                
                # Validate type
                if not isinstance(data_to_validate, expected_type):
                    error_msg = (
                        f"Response type validation failed for {func.__name__}: "
                        f"expected {expected_type.__name__}, got {type(data_to_validate).__name__}"
                    )
                    
                    if strict:
                        logger.error(error_msg)
                        raise TypeError(error_msg)
                    else:
                        logger.warning(error_msg)
                        return server_error_response(
                            "Response type validation failed - this is a server error"
                        ).to_json_response()
                
                logger.debug(f"Response type validation passed for {func.__name__}")
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse response JSON from {func.__name__}: {e}")
                if strict:
                    raise
                return server_error_response(
                    "Invalid response format"
                ).to_json_response()
            except Exception as e:
                logger.error(
                    f"Unexpected error during response validation in {func.__name__}: {e}",
                    exc_info=True
                )
                if strict:
                    raise
                return response
            
            return response
        
        return wrapper  # type: ignore
    return decorator
