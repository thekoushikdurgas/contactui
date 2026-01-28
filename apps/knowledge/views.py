"""Knowledge base views."""
import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from apps.core.decorators.auth import require_super_admin
from .services import KnowledgeBaseService

# Pattern type choices (moved from model)
PATTERN_TYPE_CHOICES = [
    ('pattern', 'Pattern'),
    ('documentation', 'Documentation'),
    ('code_snippet', 'Code Snippet'),
    ('best_practice', 'Best Practice'),
    ('api_pattern', 'API Pattern'),
    ('architecture', 'Architecture'),
]


@require_super_admin
def knowledge_list(request):
    """List knowledge base items."""
    search_query = request.GET.get('search', '')
    pattern_type = request.GET.get('pattern_type', '')
    tags_filter = request.GET.get('tags', '')
    view_mode = request.GET.get('view', 'grid')
    
    knowledge_service = KnowledgeBaseService()
    
    # Search knowledge items
    knowledge_items = knowledge_service.search(
        query=search_query,
        pattern_type=pattern_type if pattern_type else None,
        tags=tags_filter.split(',') if tags_filter else None,
        limit=1000
    )
    
    # Paginate
    paginator = Paginator(knowledge_items, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get all unique tags for filter
    all_tags = set()
    all_items = knowledge_service.storage.list(limit=None, offset=0)
    for item in all_items.get('items', []):
        all_tags.update(item.get('tags', []) or [])
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'pattern_type': pattern_type,
        'tags_filter': tags_filter,
        'view_mode': view_mode,
        'all_tags': sorted(all_tags),
        'pattern_types': PATTERN_TYPE_CHOICES,
        'total_count': len(knowledge_items),
    }
    
    return render(request, 'knowledge/list.html', context)


@require_super_admin
def knowledge_create(request):
    """Create a new knowledge base item."""
    knowledge_service = KnowledgeBaseService()
    
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    if request.method == 'POST':
        pattern_type = request.POST.get('pattern_type', '')
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        tags_str = request.POST.get('tags', '')
        metadata_str = request.POST.get('metadata', '{}')
        
        if not pattern_type or not title or not content:
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'knowledge/create.html', {
                'pattern_types': PATTERN_TYPE_CHOICES,
            })
        
        # Parse tags
        tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
        
        # Parse metadata
        try:
            metadata = json.loads(metadata_str) if metadata_str else {}
        except json.JSONDecodeError:
            metadata = {}
        
        # Create knowledge item
        knowledge_item = knowledge_service.create(
            pattern_type=pattern_type,
            title=title,
            content=content,
            tags=tags,
            metadata=metadata,
            created_by=user_uuid
        )
        
        messages.success(request, 'Knowledge item created successfully!')
        return redirect('knowledge:detail', knowledge_id=knowledge_item.get('knowledge_id'))
    
    return render(request, 'knowledge/create.html', {
        'pattern_types': PATTERN_TYPE_CHOICES,
    })


@require_super_admin
def knowledge_detail(request, knowledge_id):
    """View knowledge base item details."""
    knowledge_service = KnowledgeBaseService()
    
    item = knowledge_service.get_by_id(str(knowledge_id))
    
    if not item:
        messages.error(request, 'Knowledge item not found.')
        return redirect('knowledge:list')
    
    # Get related items
    related_items = knowledge_service.get_related(str(knowledge_id))
    
    context = {
        'item': item,
        'related_items': related_items,
    }
    
    return render(request, 'knowledge/detail.html', context)


@require_super_admin
def knowledge_edit(request, knowledge_id):
    """Edit knowledge base item."""
    knowledge_service = KnowledgeBaseService()
    
    item = knowledge_service.get_by_id(str(knowledge_id))
    
    if not item:
        messages.error(request, 'Knowledge item not found.')
        return redirect('knowledge:list')
    
    # SuperAdmin can edit all items (no permission check needed)
    
    if request.method == 'POST':
        pattern_type = request.POST.get('pattern_type', '')
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        tags_str = request.POST.get('tags', '')
        metadata_str = request.POST.get('metadata', '{}')
        
        # Parse tags
        tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
        
        # Parse metadata
        try:
            metadata = json.loads(metadata_str) if metadata_str else {}
        except json.JSONDecodeError:
            metadata = {}
        
        # Update item
        updated_item = knowledge_service.update(
            str(knowledge_id),
            pattern_type=pattern_type,
            title=title,
            content=content,
            tags=tags,
            metadata=metadata
        )
        
        if updated_item:
            messages.success(request, 'Knowledge item updated successfully!')
            return redirect('knowledge:detail', knowledge_id=knowledge_id)
        else:
            messages.error(request, 'Failed to update knowledge item.')
    
    # Convert tags list to comma-separated string
    tags_str = ', '.join(item.get('tags', [])) if item.get('tags') else ''
    
    # Convert metadata dict to JSON string
    metadata_str = json.dumps(item.get('metadata', {}), indent=2) if item.get('metadata') else '{}'
    
    context = {
        'item': item,
        'tags_str': tags_str,
        'metadata_str': metadata_str,
        'pattern_types': PATTERN_TYPE_CHOICES,
    }
    
    return render(request, 'knowledge/edit.html', context)


@require_super_admin
def knowledge_delete(request, knowledge_id):
    """Delete knowledge base item."""
    knowledge_service = KnowledgeBaseService()
    
    item = knowledge_service.get_by_id(str(knowledge_id))
    
    if not item:
        messages.error(request, 'Knowledge item not found.')
        return redirect('knowledge:list')
    
    # SuperAdmin can delete all items (no permission check needed)
    
    if request.method == 'POST':
        success = knowledge_service.delete(str(knowledge_id))
        if success:
            messages.success(request, 'Knowledge item deleted successfully!')
        else:
            messages.error(request, 'Failed to delete knowledge item.')
        return redirect('knowledge:list')
    
    return render(request, 'knowledge/delete_confirm.html', {'item': item})


@require_super_admin
def knowledge_search(request):
    """Advanced search for knowledge base items."""
    query = request.GET.get('q', '').strip()
    pattern_type = request.GET.get('pattern_type', '')
    tags = request.GET.getlist('tags')
    
    knowledge_service = KnowledgeBaseService()
    
    items = knowledge_service.search(
        query=query,
        pattern_type=pattern_type if pattern_type else None,
        tags=tags if tags else None,
        limit=100
    )
    
    # Get all unique tags
    all_tags = set()
    all_items = knowledge_service.storage.list(limit=None, offset=0)
    for item in all_items.get('items', []):
        all_tags.update(item.get('tags', []) or [])
    
    context = {
        'items': items,
        'query': query,
        'pattern_type': pattern_type,
        'selected_tags': tags,
        'all_tags': sorted(all_tags),
        'pattern_types': PATTERN_TYPE_CHOICES,
    }
    
    return render(request, 'knowledge/search.html', context)
