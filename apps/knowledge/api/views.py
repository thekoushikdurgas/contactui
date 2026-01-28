"""API views for Knowledge Base."""

import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from apps.core.decorators.auth import require_super_admin
from apps.knowledge.services import KnowledgeBaseService

logger = logging.getLogger(__name__)
knowledge_service = KnowledgeBaseService()


@require_super_admin
@require_http_methods(["GET"])
def knowledge_list_api(request):
    """List knowledge base items."""
    try:
        search_query = request.GET.get('search', '')
        pattern_type = request.GET.get('pattern_type')
        tags = request.GET.getlist('tags')
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 20))
        
        if search_query:
            items = knowledge_service.search(
                query=search_query,
                pattern_type=pattern_type,
                tags=tags if tags else None,
                limit=limit * 2  # Get more for pagination
            )
        else:
            # Use storage service to list items
            filters = {}
            if pattern_type:
                filters['pattern_type'] = pattern_type
            if tags:
                # Filter by tags (would need to be done in memory or storage service)
                pass
            
            all_items = knowledge_service.storage.list(filters=filters, limit=None, offset=0)
            items = all_items.get('items', [])
            
            # Filter by tags in memory
            if tags:
                items = [
                    item for item in items
                    if any(tag in item.get('tags', []) for tag in tags)
                ]
            
            # Sort by updated_at descending
            items.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        
        paginator = Paginator(items, limit)
        page_obj = paginator.get_page(page)
        
        items_data = [
            {
                'knowledge_id': item.get('knowledge_id') or item.get('id'),
                'pattern_type': item.get('pattern_type'),
                'title': item.get('title'),
                'content': (item.get('content', '')[:200] + '...' 
                           if len(item.get('content', '')) > 200 
                           else item.get('content', '')),
                'tags': item.get('tags', []),
                'metadata': item.get('metadata', {}),
                'created_at': item.get('created_at', ''),
                'updated_at': item.get('updated_at', ''),
                'created_by': item.get('created_by')  # UUID string
            }
            for item in page_obj
        ]
        
        return JsonResponse({
            'items': items_data,
            'pagination': {
                'page': page,
                'pages': paginator.num_pages,
                'total': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        })
    except Exception as e:
        logger.error(f"Knowledge list API error: {e}", exc_info=True)
        return JsonResponse({'error': 'Internal server error'}, status=500)


@require_super_admin
@require_http_methods(["GET"])
def knowledge_detail_api(request, knowledge_id):
    """Get knowledge base item detail."""
    try:
        item = knowledge_service.get_by_id(knowledge_id)
        if not item:
            return JsonResponse({'error': 'Knowledge item not found'}, status=404)
        
        related_items = knowledge_service.get_related(knowledge_id, limit=5)
        
        return JsonResponse({
            'item': {
                'knowledge_id': item.get('knowledge_id') or item.get('id'),
                'pattern_type': item.get('pattern_type'),
                'title': item.get('title'),
                'content': item.get('content'),
                'tags': item.get('tags', []),
                'metadata': item.get('metadata', {}),
                'created_at': item.get('created_at', ''),
                'updated_at': item.get('updated_at', ''),
                'created_by': item.get('created_by')  # UUID string
            },
            'related_items': [
                {
                    'knowledge_id': rel.get('knowledge_id') or rel.get('id'),
                    'title': rel.get('title'),
                    'pattern_type': rel.get('pattern_type')
                }
                for rel in related_items
            ]
        })
    except Exception as e:
        logger.error(f"Knowledge detail API error: {e}", exc_info=True)
        return JsonResponse({'error': 'Internal server error'}, status=500)


@require_super_admin
@csrf_exempt
@require_http_methods(["POST"])
def knowledge_create_api(request):
    """Create knowledge base item."""
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    try:
        data = json.loads(request.body)
        
        pattern_type = data.get('pattern_type')
        title = data.get('title')
        content = data.get('content')
        tags = data.get('tags', [])
        metadata = data.get('metadata', {})
        
        if not pattern_type or not title or not content:
            return JsonResponse({'error': 'pattern_type, title, and content are required'}, status=400)
        
        item = knowledge_service.create(
            pattern_type=pattern_type,
            title=title,
            content=content,
            tags=tags,
            metadata=metadata,
            created_by=user_uuid
        )
        
        return JsonResponse({
            'success': True,
            'item': {
                'knowledge_id': item.get('knowledge_id') or item.get('id'),
                'pattern_type': item.get('pattern_type'),
                'title': item.get('title'),
                'content': item.get('content'),
                'tags': item.get('tags', []),
                'metadata': item.get('metadata', {}),
                'created_at': item.get('created_at', '')
            }
        }, status=201)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Knowledge create API error: {e}", exc_info=True)
        return JsonResponse({'error': 'Internal server error'}, status=500)


@require_super_admin
@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def knowledge_update_api(request, knowledge_id):
    """Update knowledge base item."""
    try:
        data = json.loads(request.body)
        
        item = knowledge_service.update(knowledge_id, **data)
        if not item:
            return JsonResponse({'error': 'Knowledge item not found'}, status=404)
        
        return JsonResponse({
            'success': True,
            'item': {
                'knowledge_id': item.get('knowledge_id') or item.get('id'),
                'pattern_type': item.get('pattern_type'),
                'title': item.get('title'),
                'content': item.get('content'),
                'tags': item.get('tags', []),
                'metadata': item.get('metadata', {}),
                'updated_at': item.get('updated_at', '')
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Knowledge update API error: {e}", exc_info=True)
        return JsonResponse({'error': 'Internal server error'}, status=500)


@require_super_admin
@csrf_exempt
@require_http_methods(["DELETE"])
def knowledge_delete_api(request, knowledge_id):
    """Delete knowledge base item."""
    try:
        success = knowledge_service.delete(knowledge_id)
        if not success:
            return JsonResponse({'error': 'Knowledge item not found'}, status=404)
        
        return JsonResponse({'success': True})
    except Exception as e:
        logger.error(f"Knowledge delete API error: {e}", exc_info=True)
        return JsonResponse({'error': 'Internal server error'}, status=500)


@require_super_admin
@require_http_methods(["GET"])
def knowledge_search_api(request):
    """Search knowledge base items."""
    try:
        query = request.GET.get('q', '')
        pattern_type = request.GET.get('pattern_type')
        tags = request.GET.getlist('tags')
        limit = int(request.GET.get('limit', 20))
        
        if not query:
            return JsonResponse({'error': 'Search query is required'}, status=400)
        
        items = knowledge_service.search(
            query=query,
            pattern_type=pattern_type,
            tags=tags if tags else None,
            limit=limit
        )
        
        items_data = [
            {
                'knowledge_id': item.get('knowledge_id') or item.get('id'),
                'pattern_type': item.get('pattern_type'),
                'title': item.get('title'),
                'content': (item.get('content', '')[:200] + '...' 
                           if len(item.get('content', '')) > 200 
                           else item.get('content', '')),
                'tags': item.get('tags', []),
                'updated_at': item.get('updated_at', '')
            }
            for item in items
        ]
        
        return JsonResponse({
            'results': items_data,
            'total': len(items_data)
        })
    except Exception as e:
        logger.error(f"Knowledge search API error: {e}", exc_info=True)
        return JsonResponse({'error': 'Internal server error'}, status=500)
