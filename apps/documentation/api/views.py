"""API views for documentation app."""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from apps.documentation.services import (
    get_pages_service,
    get_endpoints_service,
    get_relationships_service
)
from apps.documentation.services.schema_service import SchemaService
from django.views.decorators.csrf import csrf_exempt
import json
from apps.documentation.utils.list_projectors import (
    should_expand_full,
    to_page_list_item,
    to_endpoint_list_item,
    to_relationship_list_item,
)


@login_required
@require_http_methods(["GET"])
def pages_list_api(request):
    """API endpoint to list pages."""
    service = get_pages_service()
    result = service.list_pages(
        page_type=request.GET.get('page_type'),
        status=request.GET.get('status'),
        limit=int(request.GET.get('limit', 20)),
        offset=int(request.GET.get('offset', 0))
    )
    items = result.get('pages', [])
    if not should_expand_full(request.GET):
        items = [to_page_list_item(p) for p in items]
    return JsonResponse({
        'success': True,
        'items': items,
        'total': result.get('total', 0)
    })


@login_required
@csrf_exempt
def pages_api(request):
    """
    Unified API endpoint for pages list (GET) and create (POST).
    Handles: GET /api/v2/pages/ (list) and POST /api/v2/pages/ (create)
    """
    if request.method == 'GET':
        return pages_list_api(request)
    elif request.method == 'POST':
        return pages_create_api(request)
    else:
        return JsonResponse({
            'success': False,
            'error': 'Method not allowed'
        }, status=405)


@login_required
@csrf_exempt
def page_api(request, page_id):
    """
    Unified API endpoint for page detail (GET), update (PUT/PATCH), and delete (DELETE).
    Handles: GET, PUT, PATCH, DELETE /api/v2/pages/<page_id>/
    """
    if request.method == 'GET':
        return pages_detail_api(request, page_id)
    elif request.method in ['PUT', 'PATCH']:
        return pages_update_api(request, page_id)
    elif request.method == 'DELETE':
        return pages_delete_api(request, page_id)
    else:
        return JsonResponse({
            'success': False,
            'error': 'Method not allowed'
        }, status=405)


@login_required
@require_http_methods(["GET"])
def pages_detail_api(request, page_id):
    """API endpoint to get single page."""
    service = PagesService()
    page = service.get_page(page_id)
    if page:
        return JsonResponse({
            'success': True,
            'data': page
        })
    return JsonResponse({
        'success': False,
        'error': 'Page not found'
    }, status=404)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def pages_create_api(request):
    """API endpoint to create page."""
    try:
        data = json.loads(request.body)
        service = get_pages_service()
        page = service.create_page(data)
        if page:
            return JsonResponse({
                'success': True,
                'data': page
            }, status=201)
        return JsonResponse({
            'success': False,
            'error': 'Failed to create page'
        }, status=400)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["PUT", "PATCH"])
@csrf_exempt
def pages_update_api(request, page_id):
    """API endpoint to update page."""
    try:
        data = json.loads(request.body)
        service = get_pages_service()
        page = service.update_page(page_id, data)
        if page:
            return JsonResponse({
                'success': True,
                'data': page
            })
        return JsonResponse({
            'success': False,
            'error': 'Page not found or update failed'
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["DELETE"])
@csrf_exempt
def pages_delete_api(request, page_id):
    """API endpoint to delete page."""
    service = get_pages_service()
    success = service.delete_page(page_id)
    if success:
        return JsonResponse({
            'success': True,
            'message': 'Page deleted'
        })
    return JsonResponse({
        'success': False,
        'error': 'Page not found or delete failed'
    }, status=404)


# Endpoints API - Unified views for multiple HTTP methods

@login_required
@csrf_exempt
def endpoints_api(request):
    """
    Unified API endpoint for endpoints list (GET) and create (POST).
    Handles: GET /api/v2/endpoints/ (list) and POST /api/v2/endpoints/ (create)
    """
    if request.method == 'GET':
        return endpoints_list_api(request)
    elif request.method == 'POST':
        return endpoints_create_api(request)
    else:
        return JsonResponse({
            'success': False,
            'error': 'Method not allowed'
        }, status=405)


@login_required
@csrf_exempt
def endpoint_api(request, endpoint_id):
    """
    Unified API endpoint for endpoint detail (GET), update (PUT/PATCH), and delete (DELETE).
    Handles: GET, PUT, PATCH, DELETE /api/v2/endpoints/<endpoint_id>/
    """
    if request.method == 'GET':
        return endpoints_detail_api(request, endpoint_id)
    elif request.method in ['PUT', 'PATCH']:
        return endpoints_update_api(request, endpoint_id)
    elif request.method == 'DELETE':
        return endpoints_delete_api(request, endpoint_id)
    else:
        return JsonResponse({
            'success': False,
            'error': 'Method not allowed'
        }, status=405)


# Individual endpoint views (kept for backward compatibility if needed)

@login_required
@require_http_methods(["GET"])
def endpoints_list_api(request):
    """API endpoint to list endpoints."""
    service = EndpointsService()
    result = service.list_endpoints(
        method=request.GET.get('method'),
        limit=int(request.GET.get('limit', 20)),
        offset=int(request.GET.get('offset', 0))
    )
    items = result.get('endpoints', [])
    if not should_expand_full(request.GET):
        items = [to_endpoint_list_item(ep) for ep in items]
    return JsonResponse({
        'success': True,
        'items': items,
        'total': result.get('total', 0)
    })


@login_required
@require_http_methods(["GET"])
def endpoints_detail_api(request, endpoint_id):
    """API endpoint to get single endpoint."""
    service = get_endpoints_service()
    endpoint = service.get_endpoint(endpoint_id)
    if endpoint:
        return JsonResponse({
            'success': True,
            'data': endpoint
        })
    return JsonResponse({
        'success': False,
        'error': 'Endpoint not found'
    }, status=404)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def endpoints_create_api(request):
    """API endpoint to create endpoint."""
    try:
        data = json.loads(request.body)
        service = EndpointsService()
        endpoint = service.create_endpoint(data)
        if endpoint:
            return JsonResponse({
                'success': True,
                'data': endpoint
            }, status=201)
        return JsonResponse({
            'success': False,
            'error': 'Failed to create endpoint'
        }, status=400)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)


@login_required
@require_http_methods(["PUT", "PATCH"])
@csrf_exempt
def endpoints_update_api(request, endpoint_id):
    """API endpoint to update endpoint."""
    try:
        data = json.loads(request.body)
        service = get_endpoints_service()
        endpoint = service.update_endpoint(endpoint_id, data)
        if endpoint:
            return JsonResponse({
                'success': True,
                'data': endpoint
            })
        return JsonResponse({
            'success': False,
            'error': 'Endpoint not found or update failed'
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)


@login_required
@require_http_methods(["DELETE"])
@csrf_exempt
def endpoints_delete_api(request, endpoint_id):
    """API endpoint to delete endpoint."""
    service = get_endpoints_service()
    success = service.delete_endpoint(endpoint_id)
    if success:
        return JsonResponse({
            'success': True,
            'message': 'Endpoint deleted'
        })
    return JsonResponse({
        'success': False,
        'error': 'Endpoint not found or delete failed'
    }, status=404)


# Relationships API - Unified views for multiple HTTP methods

@login_required
@csrf_exempt
def relationships_api(request):
    """
    Unified API endpoint for relationships list (GET) and create (POST).
    Handles: GET /api/v2/relationships/ (list) and POST /api/v2/relationships/ (create)
    """
    if request.method == 'GET':
        return relationships_list_api(request)
    elif request.method == 'POST':
        return relationships_create_api(request)
    else:
        return JsonResponse({
            'success': False,
            'error': 'Method not allowed'
        }, status=405)


@login_required
@csrf_exempt
def relationship_api(request, relationship_id):
    """
    Unified API endpoint for relationship detail (GET) and delete (DELETE).
    Handles: GET, DELETE /api/v2/relationships/<relationship_id>/
    """
    if request.method == 'GET':
        return relationships_detail_api(request, relationship_id)
    elif request.method == 'DELETE':
        return relationships_delete_api(request, relationship_id)
    else:
        return JsonResponse({
            'success': False,
            'error': 'Method not allowed'
        }, status=405)


# Individual relationship views (kept for backward compatibility if needed)

@login_required
@require_http_methods(["GET"])
def relationships_list_api(request):
    """API endpoint to list relationships."""
    service = RelationshipsService()
    result = service.list_relationships(
        page_id=request.GET.get('page_id'),
        endpoint_id=request.GET.get('endpoint_id'),
        limit=int(request.GET.get('limit', 20)),
        offset=int(request.GET.get('offset', 0))
    )
    items = result.get('relationships', [])
    if not should_expand_full(request.GET):
        items = [to_relationship_list_item(r) for r in items]
    return JsonResponse({
        'success': True,
        'items': items,
        'total': result.get('total', 0)
    })


@login_required
@require_http_methods(["GET"])
def relationships_detail_api(request, relationship_id):
    """API endpoint to get single relationship."""
    service = get_relationships_service()
    relationship = service.get_relationship(relationship_id)
    if relationship:
        return JsonResponse({
            'success': True,
            'data': relationship
        })
    return JsonResponse({
        'success': False,
        'error': 'Relationship not found'
    }, status=404)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def relationships_create_api(request):
    """API endpoint to create relationship."""
    try:
        data = json.loads(request.body)
        service = RelationshipsService()
        relationship = service.create_relationship(data)
        if relationship:
            return JsonResponse({
                'success': True,
                'data': relationship
            }, status=201)
        return JsonResponse({
            'success': False,
            'error': 'Failed to create relationship'
        }, status=400)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)


@login_required
@require_http_methods(["DELETE"])
@csrf_exempt
def relationships_delete_api(request, relationship_id):
    """API endpoint to delete relationship."""
    service = get_relationships_service()
    success = service.delete_relationship(relationship_id)
    if success:
        return JsonResponse({
            'success': True,
            'message': 'Relationship deleted'
        })
    return JsonResponse({
        'success': False,
        'error': 'Relationship not found or delete failed'
    }, status=404)


# Schema API endpoints

@login_required
@require_http_methods(["GET"])
def schemas_api(request, resource_type=None):
    """
    API endpoint to get schema for a resource type.
    Handles: GET /docs/api/schemas/ or GET /docs/api/schemas/{resource_type}/
    
    Resource types: pages, endpoints, relationships, postman
    """
    schema_service = SchemaService()
    
    # If no resource_type specified, return list of available schemas
    if not resource_type:
        return JsonResponse({
            'success': True,
            'available_schemas': ['pages', 'endpoints', 'relationships', 'postman'],
            'message': 'Specify a resource type: /docs/api/schemas/{resource_type}/'
        })
    
    # Get schema for the specified resource type
    schema = schema_service.get_schema(resource_type.lower())
    
    if schema:
        return JsonResponse({
            'success': True,
            'schema': schema
        })
    
    return JsonResponse({
        'success': False,
        'error': f'Schema not found for resource type: {resource_type}'
    }, status=404)
