"""Durgasman API Testing App Views."""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import os
from django.conf import settings

from apps.core.decorators.auth import require_super_admin
from .services.durgasman_storage_service import (
    CollectionStorageService,
    EnvironmentStorageService,
    RequestHistoryStorageService
)


@require_super_admin
def dashboard(request):
    """Main Durgasman dashboard."""
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    collection_storage = CollectionStorageService()
    history_storage = RequestHistoryStorageService()
    environment_storage = EnvironmentStorageService()
    
    collections_result = collection_storage.list(
        filters={'user': user_uuid},
        limit=10,
        offset=0,
        order_by='created_at',
        reverse=True
    )
    collections = collections_result.get('items', [])
    
    history_result = history_storage.list(
        filters={'user': user_uuid},
        limit=5,
        offset=0,
        order_by='timestamp',
        reverse=True
    )
    recent_history = history_result.get('items', [])
    
    environments_result = environment_storage.list(
        filters={'user': user_uuid},
        limit=5,
        offset=0,
        order_by='created_at',
        reverse=True
    )
    environments = environments_result.get('items', [])
    
    context = {
        'collections': collections,
        'recent_history': recent_history,
        'environments': environments,
    }
    return render(request, 'durgasman/dashboard.html', context)


@require_super_admin
def collection_detail(request, collection_id):
    """View collection details and requests."""
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    collection_storage = CollectionStorageService()
    collection = collection_storage.get_collection(collection_id)
    
    if not collection or collection.get('user') != user_uuid:
        messages.error(request, 'Collection not found or unauthorized.')
        return redirect('durgasman:dashboard')
    
    # Get requests from collection (stored as nested data)
    requests = collection.get('requests', [])

    context = {
        'collection': collection,
        'requests': requests,
    }
    return render(request, 'durgasman/collection_detail.html', context)


@require_super_admin
def import_view(request):
    """Handle import from media manager."""
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    import_type = request.GET.get('type')
    file_path = request.GET.get('file')

    if not import_type or not file_path:
        return redirect('durgasman:dashboard')

    # Security check - only allow media/ paths
    if not file_path.startswith('media/'):
        raise Http404

    full_path = os.path.join(settings.MEDIA_ROOT, file_path)

    if not os.path.exists(full_path):
        messages.error(request, f'File not found: {file_path}')
        return redirect('documentation:media_manager_dashboard')

    try:
        if import_type == 'postman':
            from .services.postman_importer import import_postman_collection
            collection = import_postman_collection(full_path, user_uuid)
            messages.success(request, f'Successfully imported Postman collection: {collection.get("name")}')
        elif import_type == 'endpoints':
            from .services.endpoint_importer import import_endpoint_json
            collection = import_endpoint_json(full_path, user_uuid)
            messages.success(request, f'Successfully imported endpoint: {collection.get("name")}')
        else:
            messages.error(request, f'Unknown import type: {import_type}')
            return redirect('documentation:media_manager_dashboard')

        return redirect('durgasman:collection_detail', collection_id=collection.get('collection_id') or collection.get('id'))

    except Exception as e:
        messages.error(request, f'Import failed: {str(e)}')
        return redirect('documentation:media_manager_dashboard')


# API Views

@require_super_admin
@require_http_methods(["GET"])
def api_collections(request):
    """API endpoint for collections."""
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    collection_storage = CollectionStorageService()
    
    collections_result = collection_storage.list(
        filters={'user': user_uuid},
        limit=None,
        offset=0
    )
    collections = collections_result.get('items', [])

    # Add request count for each collection
    for collection in collections:
        collection_id = collection.get('collection_id') or collection.get('id')
        requests = collection.get('requests', [])
        collection['requests_count'] = len(requests) if requests else 0

    return JsonResponse({
        'collections': collections,
        'total': len(collections)
    })


@require_super_admin
@require_http_methods(["GET"])
def api_collection_requests(request, collection_id):
    """API endpoint for collection requests."""
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    collection_storage = CollectionStorageService()
    collection = collection_storage.get_collection(collection_id)
    
    if not collection or collection.get('user') != user_uuid:
        return JsonResponse({'error': 'Collection not found or unauthorized'}, status=404)
    
    # Get requests from collection (stored as nested data)
    requests = collection.get('requests', [])
    
    # Format requests
    formatted_requests = []
    for req in requests:
        formatted_requests.append({
            'id': req.get('request_id') or req.get('id'),
            'name': req.get('name'),
            'method': req.get('method'),
            'url': req.get('url'),
            'headers': req.get('headers', []),
            'params': req.get('params', []),
            'body': req.get('body'),
            'auth_type': req.get('auth_type'),
            'response_schema': req.get('response_schema'),
            'created_at': req.get('created_at'),
            'updated_at': req.get('updated_at'),
        })

    return JsonResponse({
        'collection': {
            'id': collection.get('collection_id') or collection.get('id'),
            'name': collection.get('name'),
            'description': collection.get('description'),
        },
        'requests': formatted_requests,
        'total': len(formatted_requests)
    })


@require_super_admin
@require_http_methods(["GET", "PUT", "DELETE"])
def api_request_detail(request, request_id):
    """API endpoint for individual request CRUD."""
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    collection_storage = CollectionStorageService()
    
    # Find request in collections
    collections_result = collection_storage.list(
        filters={'user': user_uuid},
        limit=None,
        offset=0
    )
    
    api_request = None
    collection = None
    collection_id = None
    
    for coll in collections_result.get('items', []):
        requests = coll.get('requests', [])
        for req in requests:
            if req.get('request_id') == request_id or req.get('id') == request_id:
                api_request = req
                collection = coll
                collection_id = coll.get('collection_id') or coll.get('id')
                break
        if api_request:
            break
    
    if not api_request:
        return JsonResponse({'error': 'Request not found or unauthorized'}, status=404)

    if request.method == 'GET':
        return JsonResponse({
            'id': api_request.get('request_id') or api_request.get('id'),
            'name': api_request.get('name'),
            'method': api_request.get('method'),
            'url': api_request.get('url'),
            'headers': api_request.get('headers', []),
            'params': api_request.get('params', []),
            'body': api_request.get('body', ''),
            'auth_type': api_request.get('auth_type'),
            'response_schema': api_request.get('response_schema', ''),
        })

    elif request.method == 'PUT':
        data = json.loads(request.body)
        
        # Update request in collection
        requests = collection.get('requests', [])
        for i, req in enumerate(requests):
            if req.get('request_id') == request_id or req.get('id') == request_id:
                # Update fields
                for field in ['name', 'method', 'url', 'headers', 'params', 'body', 'auth_type', 'response_schema']:
                    if field in data:
                        requests[i][field] = data[field]
                break
        
        # Update collection
        collection_storage.update_collection(collection_id, requests=requests)
        return JsonResponse({'success': True})

    elif request.method == 'DELETE':
        # Remove request from collection
        requests = collection.get('requests', [])
        requests = [req for req in requests if req.get('request_id') != request_id and req.get('id') != request_id]
        
        # Update collection
        collection_storage.update_collection(collection_id, requests=requests)
        return JsonResponse({'success': True})


@require_super_admin
@require_http_methods(["GET"])
def api_environments(request):
    """API endpoint for environments."""
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    environment_storage = EnvironmentStorageService()
    environments_result = environment_storage.list(
        filters={'user': user_uuid},
        limit=None,
        offset=0
    )
    environments = environments_result.get('items', [])
    
    formatted_environments = [
        {
            'id': env.get('environment_id') or env.get('id'),
            'name': env.get('name'),
            'created_at': env.get('created_at'),
        }
        for env in environments
    ]

    return JsonResponse({
        'environments': formatted_environments,
        'total': len(formatted_environments)
    })


@require_super_admin
@require_http_methods(["GET"])
def api_history(request):
    """API endpoint for request history."""
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    limit = int(request.GET.get('limit', 50))
    
    history_storage = RequestHistoryStorageService()
    history_result = history_storage.list(
        filters={'user': user_uuid},
        limit=limit,
        offset=0
    )
    history = history_result.get('items', [])

    # Format history items
    formatted_history = [
        {
            'id': h.get('history_id') or h.get('id'),
            'timestamp': h.get('timestamp') or h.get('created_at'),
            'method': h.get('method'),
            'url': h.get('url'),
            'response_status': h.get('response_status'),
            'response_time_ms': h.get('response_time_ms'),
            'response_size_bytes': h.get('response_size_bytes')
        }
        for h in history
    ]

    return JsonResponse({
        'history': formatted_history,
        'total': len(formatted_history)
    })


@require_super_admin
@require_http_methods(["GET"])
def api_mocks(request):
    """API endpoint for mock endpoints."""
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    collection_storage = CollectionStorageService()
    collections_result = collection_storage.list(
        filters={'user': user_uuid},
        limit=None,
        offset=0
    )
    
    # Collect mock endpoints from collections
    mocks = []
    for collection in collections_result.get('items', []):
        mock_endpoints = collection.get('mock_endpoints', [])
        for mock in mock_endpoints:
            mocks.append({
                'id': mock.get('mock_id') or mock.get('id'),
                'path': mock.get('path'),
                'method': mock.get('method'),
                'status_code': mock.get('status_code'),
                'enabled': mock.get('enabled', True),
                'created_at': mock.get('created_at'),
            })

    return JsonResponse({
        'mocks': mocks,
        'total': len(mocks)
    })


@require_super_admin
@csrf_exempt
@require_http_methods(["POST"])
def api_analyze_response(request):
    """API endpoint for AI response analysis."""
    try:
        data = json.loads(request.body)
        request_data = data.get('request', {})
        response_data = data.get('response', {})

        from .services.ai_service import ai_service
        analysis = ai_service.analyze_response(request_data, response_data)

        return JsonResponse({
            'analysis': analysis,
            'status': 'success'
        })

    except Exception as e:
        return JsonResponse({
            'analysis': f'Analysis failed: {str(e)}',
            'status': 'error'
        }, status=500)