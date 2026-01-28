"""Operations views."""
from django.shortcuts import render
from apps.core.decorators.auth import require_super_admin


@require_super_admin
def operations_view(request):
    """Operations hub: stats and links to analyze/validate/generate/upload/workflow."""
    stats = {'total_operations': 0, 'successful': 0, 'failed': 0, 'uptime': '99.9%'}
    try:
        from apps.documentation.services.pages_service import PagesService
        from apps.documentation.services.endpoints_service import EndpointsService
        ps = PagesService()
        es = EndpointsService()
        pr = ps.list_pages(limit=1, offset=0)
        er = es.list_endpoints(limit=1, offset=0)
        stats['total_pages'] = pr.get('total', 0)
        stats['total_endpoints'] = er.get('total', 0)
    except Exception:
        stats['total_pages'] = 0
        stats['total_endpoints'] = 0
    context = {
        'system_status': {
            's3': 'operational',
            'lambda': 'operational',
            'graphql': 'operational',
            'database': 'operational',
        },
        'recent_operations': [],
        'stats': stats,
    }
    return render(request, 'operations/dashboard.html', context)
