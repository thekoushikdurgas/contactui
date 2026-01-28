"""Analytics views."""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def analytics_view(request):
    """Analytics dashboard view."""
    from django.utils import timezone
    from datetime import timedelta
    from apps.documentation.services.pages_service import PagesService
    
    pages_service = PagesService()
    
    # Get basic statistics
    try:
        pages_result = pages_service.list_pages(limit=1000)
        total_pages = pages_result.get('total', 0)
        pages = pages_result.get('pages', [])
        
        # Calculate statistics
        published_pages = sum(1 for p in pages if p.get('metadata', {}).get('status') == 'published')
        draft_pages = sum(1 for p in pages if p.get('metadata', {}).get('status') == 'draft')
        
        # Page types distribution
        page_types = {}
        for page in pages:
            page_type = page.get('page_type', 'docs')
            page_types[page_type] = page_types.get(page_type, 0) + 1
        
        # Recent activity (last 7 days)
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_pages = [
            p for p in pages 
            if p.get('created_at') and 
            timezone.datetime.fromisoformat(p['created_at'].replace('Z', '+00:00')) > seven_days_ago
        ]
        
    except Exception as e:
        total_pages = 0
        published_pages = 0
        draft_pages = 0
        page_types = {}
        recent_pages = []
    
    context = {
        'total_pages': total_pages,
        'published_pages': published_pages,
        'draft_pages': draft_pages,
        'page_types': page_types,
        'recent_pages_count': len(recent_pages),
        'stats': {
            'total': total_pages,
            'published': published_pages,
            'drafts': draft_pages,
            'recent': len(recent_pages)
        }
    }
    return render(request, 'analytics/dashboard.html', context)
