"""
Bulk operations API endpoints for dashboard.

Provides bulk delete functionality for dashboard resources.
"""

import json
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from apps.documentation.services import (
    get_pages_service,
    get_endpoints_service,
    get_relationships_service
)

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["POST", "DELETE"])
@csrf_exempt
def dashboard_bulk_delete_api(request):
    """
    API endpoint for bulk delete operations.
    
    Request body (JSON):
    {
        "resource_type": "pages|endpoints|relationships|postman",
        "ids": ["id1", "id2", ...]
    }
    
    Returns:
    {
        "success": true,
        "deleted_count": 2,
        "failed_count": 0,
        "errors": []
    }
    """
    try:
        data = json.loads(request.body)
        resource_type = data.get('resource_type')
        ids = data.get('ids', [])
        
        if not resource_type:
            return JsonResponse({
                'success': False,
                'error': 'resource_type is required'
            }, status=400)
        
        if not ids or not isinstance(ids, list):
            return JsonResponse({
                'success': False,
                'error': 'ids must be a non-empty array'
            }, status=400)
        
        deleted_count = 0
        failed_count = 0
        errors = []
        
        if resource_type == 'pages':
            service = get_pages_service()
            for page_id in ids:
                try:
                    success = service.delete_page(page_id)
                    if success:
                        deleted_count += 1
                    else:
                        failed_count += 1
                        errors.append({
                            'id': page_id,
                            'error': 'Failed to delete page'
                        })
                except Exception as e:
                    failed_count += 1
                    errors.append({
                        'id': page_id,
                        'error': str(e)
                    })
        
        elif resource_type == 'endpoints':
            service = get_endpoints_service()
            for endpoint_id in ids:
                try:
                    success = service.delete_endpoint(endpoint_id)
                    if success:
                        deleted_count += 1
                    else:
                        failed_count += 1
                        errors.append({
                            'id': endpoint_id,
                            'error': 'Failed to delete endpoint'
                        })
                except Exception as e:
                    failed_count += 1
                    errors.append({
                        'id': endpoint_id,
                        'error': str(e)
                    })
        
        elif resource_type == 'relationships':
            service = get_relationships_service()
            for relationship_id in ids:
                try:
                    success = service.delete_relationship(relationship_id)
                    if success:
                        deleted_count += 1
                    else:
                        failed_count += 1
                        errors.append({
                            'id': relationship_id,
                            'error': 'Failed to delete relationship'
                        })
                except Exception as e:
                    failed_count += 1
                    errors.append({
                        'id': relationship_id,
                        'error': str(e)
                    })
        
        elif resource_type == 'postman':
            # Postman delete would need to be implemented in PostmanService
            return JsonResponse({
                'success': False,
                'error': 'Bulk delete for Postman configurations not yet implemented'
            }, status=501)
        
        else:
            return JsonResponse({
                'success': False,
                'error': f'Invalid resource_type: {resource_type}'
            }, status=400)
        
        return JsonResponse({
            'success': True,
            'deleted_count': deleted_count,
            'failed_count': failed_count,
            'errors': errors,
            'total_requested': len(ids)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        logger.error(f"Error in dashboard_bulk_delete_api: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
