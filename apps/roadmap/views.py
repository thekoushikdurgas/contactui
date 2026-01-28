"""Roadmap views."""
from django.shortcuts import render
from apps.core.decorators.auth import require_super_admin


@require_super_admin
def roadmap_view(request):
    """Development roadmap view."""
    from django.utils import timezone
    from datetime import timedelta
    
    context = {
        'milestones': [
            {
                'id': '1',
                'title': 'Documentation System',
                'status': 'completed',
                'due_date': timezone.now() - timedelta(days=30),
                'progress': 100
            },
            {
                'id': '2',
                'title': 'AI Integration',
                'status': 'in_progress',
                'due_date': timezone.now() + timedelta(days=30),
                'progress': 75
            },
            {
                'id': '3',
                'title': 'Analytics Dashboard',
                'status': 'planned',
                'due_date': timezone.now() + timedelta(days=60),
                'progress': 0
            }
        ],
        'features': []
    }
    return render(request, 'roadmap/dashboard.html', context)
