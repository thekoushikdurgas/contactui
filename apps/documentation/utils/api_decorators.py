"""Utility decorators for API endpoints to reduce code duplication."""

import json
import logging
from functools import wraps
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)


def api_endpoint(operation_name, success_status=200, not_found_error=None):
    """
    Decorator factory for standard CRUD API endpoints.
    
    Reduces code duplication in create/update/delete API views by handling:
    - JSON parsing
    - Error handling
    - Standard response format
    - Logging
    
    Args:
        operation_name: Name of the operation (e.g., 'create page', 'update endpoint')
        success_status: HTTP status code for success (default: 200, use 201 for create)
        not_found_error: Error message when resource not found (default: '{resource} not found')
    
    Usage:
        @api_endpoint('create page', success_status=201)
        def page_create_api(request):
            data = request.json_data  # Already parsed
            result = pages_service.create_page(data)
            if not result:
                return None  # Will return 500 error
            return result  # Will return success response
    """
    def decorator(func):
        @login_required
        @require_http_methods(["POST", "PUT", "PATCH", "DELETE"])
        @csrf_exempt
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            try:
                # Parse JSON body if present
                if request.body:
                    try:
                        request.json_data = json.loads(request.body)
                    except json.JSONDecodeError:
                        return JsonResponse({
                            'success': False,
                            'error': 'Invalid JSON'
                        }, status=400)
                else:
                    request.json_data = {}
                
                # Call the view function
                result = func(request, *args, **kwargs)
                
                # Handle None result (operation failed)
                if result is None:
                    error_msg = not_found_error or f'{operation_name.split()[0].title()} not found'
                    return JsonResponse({
                        'success': False,
                        'error': error_msg
                    }, status=404)
                
                # Handle tuple result (result, status_code)
                if isinstance(result, tuple):
                    result, status = result
                    return JsonResponse({
                        'success': True,
                        'data': result
                    }, status=status)
                
                # Handle dict result (already formatted)
                if isinstance(result, dict) and 'success' in result:
                    status = result.pop('status', success_status)
                    return JsonResponse(result, status=status)
                
                # Default: return result as data
                return JsonResponse({
                    'success': True,
                    'data': result
                }, status=success_status)
                
            except Exception as e:
                logger.error(f"Error in {operation_name}: {e}", exc_info=True)
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=500)
        
        return wrapper
    return decorator


def create_api_endpoint(resource_name, create_func):
    """
    Create a standard create API endpoint.
    
    Args:
        resource_name: Name of the resource (e.g., 'page', 'endpoint')
        create_func: Function to call for creation (e.g., pages_service.create_page)
    
    Returns:
        Decorated view function
    """
    @api_endpoint(f'create {resource_name}', success_status=201)
    def create_view(request):
        result = create_func(request.json_data)
        if not result:
            return None  # Will trigger 500 error
        return result
    
    return create_view


def update_api_endpoint(resource_name, update_func):
    """
    Create a standard update API endpoint.
    
    Args:
        resource_name: Name of the resource (e.g., 'page', 'endpoint')
        update_func: Function to call for update (e.g., lambda id, data: pages_service.update_page(id, data))
    
    Returns:
        Decorated view function
    """
    @api_endpoint(f'update {resource_name}', not_found_error=f'{resource_name.title()} not found')
    def update_view(request, resource_id):
        result = update_func(resource_id, request.json_data)
        return result  # None if not found, data if updated
    
    return update_view


def delete_api_endpoint(resource_name, delete_func):
    """
    Create a standard delete API endpoint.
    
    Args:
        resource_name: Name of the resource (e.g., 'page', 'endpoint')
        delete_func: Function to call for deletion (e.g., lambda id: pages_service.delete_page(id))
    
    Returns:
        Decorated view function
    """
    @api_endpoint(f'delete {resource_name}', not_found_error=f'{resource_name.title()} not found')
    def delete_view(request, resource_id):
        result = delete_func(resource_id)
        if result:
            return {'message': f'{resource_name.title()} deleted successfully'}
        return None  # Will trigger 404
    
    return delete_view
