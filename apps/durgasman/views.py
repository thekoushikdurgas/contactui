"""Durgasman API Testing App Views."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import models
import json
import os
from django.conf import settings

from .models import Collection, ApiRequest, Environment, RequestHistory, MockEndpoint


@login_required
def dashboard(request):
    """Main Durgasman dashboard."""
    context = {
        'collections': Collection.objects.filter(user=request.user).select_related('user')[:10],
        'recent_history': RequestHistory.objects.filter(user=request.user).select_related('user', 'collection')[:5],
        'environments': Environment.objects.filter(user=request.user).select_related('user')[:5],
    }
    return render(request, 'durgasman/dashboard.html', context)


@login_required
def collection_detail(request, collection_id):
    """View collection details and requests."""
    collection = get_object_or_404(Collection, id=collection_id, user=request.user)
    requests = collection.requests.all()

    context = {
        'collection': collection,
        'requests': requests,
    }
    return render(request, 'durgasman/collection_detail.html', context)


@login_required
def import_view(request):
    """Handle import from media manager."""
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
            collection = import_postman_collection(full_path, request.user)
            messages.success(request, f'Successfully imported Postman collection: {collection.name}')
        elif import_type == 'endpoints':
            from .services.endpoint_importer import import_endpoint_json
            collection = import_endpoint_json(full_path, request.user)
            messages.success(request, f'Successfully imported endpoint: {collection.name}')
        else:
            messages.error(request, f'Unknown import type: {import_type}')
            return redirect('documentation:media_manager_dashboard')

        return redirect('durgasman:collection_detail', collection_id=collection.id)

    except Exception as e:
        messages.error(request, f'Import failed: {str(e)}')
        return redirect('documentation:media_manager_dashboard')


# API Views

@login_required
@require_http_methods(["GET"])
def api_collections(request):
    """API endpoint for collections."""
    collections = Collection.objects.filter(user=request.user).select_related('user').values(
        'id', 'name', 'description', 'created_at'
    )

    # Add request count for each collection
    for collection in collections:
        # Use prefetch_related for better performance when counting
        collection['requests_count'] = ApiRequest.objects.filter(collection_id=collection['id']).count()

    return JsonResponse({
        'collections': list(collections),
        'total': len(collections)
    })


@login_required
@require_http_methods(["GET"])
def api_collection_requests(request, collection_id):
    """API endpoint for collection requests."""
    collection = get_object_or_404(Collection, id=collection_id, user=request.user)
    requests = collection.requests.all().values(
        'id', 'name', 'method', 'url', 'headers', 'params', 'body',
        'auth_type', 'response_schema', 'created_at', 'updated_at'
    )

    return JsonResponse({
        'collection': {
            'id': collection.id,
            'name': collection.name,
            'description': collection.description,
        },
        'requests': list(requests),
        'total': len(requests)
    })


@login_required
@require_http_methods(["GET", "PUT", "DELETE"])
def api_request_detail(request, request_id):
    """API endpoint for individual request CRUD."""
    api_request = get_object_or_404(ApiRequest, id=request_id, collection__user=request.user)

    if request.method == 'GET':
        return JsonResponse({
            'id': api_request.id,
            'name': api_request.name,
            'method': api_request.method,
            'url': api_request.url,
            'headers': api_request.headers,
            'params': api_request.params,
            'body': api_request.body,
            'auth_type': api_request.auth_type,
            'response_schema': api_request.response_schema,
        })

    elif request.method == 'PUT':
        data = json.loads(request.body)
        for field in ['name', 'method', 'url', 'headers', 'params', 'body', 'auth_type', 'response_schema']:
            if field in data:
                setattr(api_request, field, data[field])
        api_request.save()
        return JsonResponse({'success': True})

    elif request.method == 'DELETE':
        api_request.delete()
        return JsonResponse({'success': True})


@login_required
@require_http_methods(["GET"])
def api_environments(request):
    """API endpoint for environments."""
    environments = Environment.objects.filter(user=request.user).values(
        'id', 'name', 'created_at'
    )

    return JsonResponse({
        'environments': list(environments),
        'total': len(environments)
    })


@login_required
@require_http_methods(["GET"])
def api_history(request):
    """API endpoint for request history."""
    limit = int(request.GET.get('limit', 50))
    history = RequestHistory.objects.filter(user=request.user)[:limit].values(
        'id', 'timestamp', 'method', 'url', 'response_status',
        'response_time_ms', 'response_size_bytes'
    )

    return JsonResponse({
        'history': list(history),
        'total': len(history)
    })


@login_required
@require_http_methods(["GET"])
def api_mocks(request):
    """API endpoint for mock endpoints."""
    mocks = MockEndpoint.objects.filter(
        models.Q(collection__user=request.user) | models.Q(collection__isnull=True)
    ).values(
        'id', 'path', 'method', 'status_code', 'enabled', 'created_at'
    )

    return JsonResponse({
        'mocks': list(mocks),
        'total': len(mocks)
    })


@login_required
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