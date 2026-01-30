"""Documentation views."""
import logging
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from apps.documentation.services import get_pages_service

logger = logging.getLogger(__name__)


@login_required
def list_pages_view(request):
    """List all documentation pages."""
    try:
        from django.core.paginator import Paginator
        
        # Get filter parameters
        page_type = request.GET.get('page_type', '').strip() or None
        status = request.GET.get('status', '').strip() or None
        search_query = request.GET.get('search', '').strip() or None
        
        # Pagination
        page_number = request.GET.get('page', 1)
        try:
            page_number = int(page_number)
            if page_number < 1:
                page_number = 1
        except (ValueError, TypeError):
            page_number = 1
        
        service = get_pages_service()
        result = service.list_pages(
            page_type=page_type,
            status=status,
            limit=100,  # Get more for pagination
            offset=0
        )
        
        pages = result.get('pages', [])
        # Normalize: ensure each page has top-level status for list.html (status is under metadata in storage)
        for p in pages:
            if isinstance(p, dict) and "status" not in p:
                p["status"] = (p.get("metadata") or {}).get("status", "draft")
        # Filter by search query if provided
        if search_query:
            pages = [
                p for p in pages
                if search_query.lower() in (p.get('title', '') or '').lower() or
                   search_query.lower() in (p.get('page_id', '') or '').lower()
            ]
        
        # Paginate
        paginator = Paginator(pages, 20)
        page_obj = paginator.get_page(page_number)
        
        context = {
            'pages': page_obj,
            'total': paginator.count,
            'page_type': page_type,
            'status': status,
            'search_query': search_query,
            'empty_state_create_url': reverse('documentation:create'),
        }
        return render(request, 'documentation/list.html', context)
    except Exception as e:
        logger.error(f"Error listing pages: {e}", exc_info=True)
        messages.error(request, 'An error occurred while loading pages.')
        context = {
            'pages': [], 'total': 0, 'page_obj': None,
            'empty_state_create_url': reverse('documentation:create'),
        }
        return render(request, 'documentation/list.html', context)


@login_required
def get_page_view(request, page_id):
    """Get single documentation page."""
    service = get_pages_service()
    page = service.get_page(page_id)
    if not page:
        messages.error(request, 'Page not found.')
        return redirect('documentation:list')
    # Normalize: ensure top-level content for detail.html (content may be missing or only under metadata)
    if isinstance(page, dict):
        page['content'] = page.get('content') or (page.get('metadata') or {}).get('content', '') or ''
    context = {
        'page': page,
    }
    return render(request, 'documentation/detail.html', context)


@login_required
def create_page_view(request):
    """Create new documentation page."""
    if request.method == 'POST':
        try:
            # Validate required fields
            page_id = request.POST.get('page_id', '').strip()
            title = request.POST.get('title', '').strip()
            
            if not page_id:
                messages.error(request, 'Page ID is required.')
                return render(request, 'documentation/create.html')
            
            if not title:
                messages.error(request, 'Title is required.')
                return render(request, 'documentation/create.html')
            
            service = get_pages_service()
            page_data = {
                'page_id': page_id,
                'title': title,
                'page_type': request.POST.get('page_type', 'docs'),
                'content': request.POST.get('content', ''),
                'metadata': {
                    'title': title,
                    'route': request.POST.get('route', '/'),
                    'status': request.POST.get('status', 'draft'),
                }
            }
            created = service.create_page(page_data)
            if created:
                messages.success(request, 'Page created successfully!')
                return redirect('documentation:list')
            else:
                messages.error(request, 'Failed to create page.')
        except Exception as e:
            logger.error(f"Error creating page: {e}", exc_info=True)
            messages.error(request, 'An error occurred while creating the page.')
    
    return render(request, 'documentation/create.html')


@login_required
def update_page_view(request, page_id):
    """Update documentation page."""
    if not page_id:
        messages.error(request, 'Invalid page ID.')
        return redirect('documentation:list')
    
    service = get_pages_service()
    
    if request.method == 'POST':
        try:
            title = request.POST.get('title', '').strip()
            if not title:
                messages.error(request, 'Title is required.')
                page = service.get_page(page_id)
                if not page:
                    return redirect('documentation:list')
                return render(request, 'documentation/edit.html', {'page': page})
            
            page_data = {
                'page_id': page_id,
                'title': title,
                'page_type': request.POST.get('page_type', 'docs'),
                'content': request.POST.get('content', ''),
                'metadata': {
                    'title': title,
                    'route': request.POST.get('route', '/'),
                    'status': request.POST.get('status', 'draft'),
                }
            }
            updated = service.update_page(page_id, page_data)
            if updated:
                messages.success(request, 'Page updated successfully!')
                return redirect('documentation:detail', page_id=page_id)
            else:
                messages.error(request, 'Failed to update page.')
                return redirect('documentation:update', page_id=page_id)
        except Exception as e:
            logger.error(f"Error updating page {page_id}: {e}", exc_info=True)
            messages.error(request, 'An error occurred while updating the page.')
            return redirect('documentation:update', page_id=page_id)
    
    # Load page data for editing
    try:
        page = service.get_page(page_id)
        if not page:
            messages.error(request, 'Page not found.')
            return redirect('documentation:list')
        
        context = {'page': page}
        return render(request, 'documentation/edit.html', context)
    except Exception as e:
        logger.error(f"Error loading page {page_id}: {e}", exc_info=True)
        messages.error(request, 'An error occurred while loading the page.')
        return redirect('documentation:list')


def _safe_redirect_url(request, default_name='documentation:list'):
    """Return redirect target: return_url if present and safe, else default."""
    return_url = request.GET.get('return_url') or request.POST.get('return_url', '')
    if return_url and return_url.startswith('/') and '//' not in return_url:
        from django.utils.http import url_has_allowed_host_and_scheme
        if url_has_allowed_host_and_scheme(return_url, allowed_hosts={request.get_host(), None}):
            return return_url
    return reverse(default_name)


@login_required
def delete_page_view(request, page_id):
    """Delete documentation page."""
    if not page_id:
        messages.error(request, 'Invalid page ID.')
        return redirect(_safe_redirect_url(request))
    
    service = get_pages_service()
    
    if request.method == 'POST':
        try:
            success = service.delete_page(page_id)
            if success:
                messages.success(request, 'Page deleted successfully!')
            else:
                messages.error(request, 'Failed to delete page.')
        except Exception as e:
            logger.error(f"Error deleting page {page_id}: {e}", exc_info=True)
            messages.error(request, 'An error occurred while deleting the page.')
        return redirect(_safe_redirect_url(request))
    
    try:
        page = service.get_page(page_id)
        if not page:
            messages.error(request, 'Page not found.')
            return redirect(_safe_redirect_url(request))
        if isinstance(page, dict) and 'status' not in page:
            page['status'] = (page.get('metadata') or {}).get('status', 'draft')
        return_url = request.GET.get('return_url', '')
        context = {'page': page, 'return_url': return_url}
        return render(request, 'documentation/delete_confirm.html', context)
    except Exception as e:
        logger.error(f"Error loading page {page_id} for deletion: {e}", exc_info=True)
        messages.error(request, 'An error occurred while loading the page.')
        return redirect(_safe_redirect_url(request))
