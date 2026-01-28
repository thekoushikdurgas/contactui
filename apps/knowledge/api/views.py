"""API views for Knowledge Base."""

import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from apps.knowledge.models import KnowledgeBase
from apps.knowledge.services import KnowledgeBaseService

logger = logging.getLogger(__name__)
knowledge_service = KnowledgeBaseService()


@login_required
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
            queryset = KnowledgeBase.objects.all()
            if pattern_type:
                queryset = queryset.filter(pattern_type=pattern_type)
            if tags:
                for tag in tags:
                    queryset = queryset.filter(tags__contains=[tag])
            items = list(queryset.order_by('-updated_at'))
        
        paginator = Paginator(items, limit)
        page_obj = paginator.get_page(page)
        
        items_data = [
            {
                'knowledge_id': str(item.knowledge_id),
                'pattern_type': item.pattern_type,
                'title': item.title,
                'content': item.content[:200] + '...' if len(item.content) > 200 else item.content,
                'tags': item.tags,
                'metadata': item.metadata,
                'created_at': item.created_at.isoformat(),
                'updated_at': item.updated_at.isoformat(),
                'created_by': item.created_by.username if item.created_by else None
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


@login_required
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
                'knowledge_id': str(item.knowledge_id),
                'pattern_type': item.pattern_type,
                'title': item.title,
                'content': item.content,
                'tags': item.tags,
                'metadata': item.metadata,
                'created_at': item.created_at.isoformat(),
                'updated_at': item.updated_at.isoformat(),
                'created_by': item.created_by.username if item.created_by else None
            },
            'related_items': [
                {
                    'knowledge_id': str(rel.knowledge_id),
                    'title': rel.title,
                    'pattern_type': rel.pattern_type
                }
                for rel in related_items
            ]
        })
    except Exception as e:
        logger.error(f"Knowledge detail API error: {e}", exc_info=True)
        return JsonResponse({'error': 'Internal server error'}, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def knowledge_create_api(request):
    """Create knowledge base item."""
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
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'item': {
                'knowledge_id': str(item.knowledge_id),
                'pattern_type': item.pattern_type,
                'title': item.title,
                'content': item.content,
                'tags': item.tags,
                'metadata': item.metadata,
                'created_at': item.created_at.isoformat()
            }
        }, status=201)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Knowledge create API error: {e}", exc_info=True)
        return JsonResponse({'error': 'Internal server error'}, status=500)


@login_required
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
                'knowledge_id': str(item.knowledge_id),
                'pattern_type': item.pattern_type,
                'title': item.title,
                'content': item.content,
                'tags': item.tags,
                'metadata': item.metadata,
                'updated_at': item.updated_at.isoformat()
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Knowledge update API error: {e}", exc_info=True)
        return JsonResponse({'error': 'Internal server error'}, status=500)


@login_required
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


@login_required
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
                'knowledge_id': str(item.knowledge_id),
                'pattern_type': item.pattern_type,
                'title': item.title,
                'content': item.content[:200] + '...' if len(item.content) > 200 else item.content,
                'tags': item.tags,
                'updated_at': item.updated_at.isoformat()
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
