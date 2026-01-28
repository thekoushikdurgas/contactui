"""Accessibility views."""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def accessibility_view(request):
    """Accessibility testing dashboard."""
    context = {
        'scans': [],
        'issues': [],
        'stats': {
            'total_issues': 0,
            'critical': 0,
            'warning': 0,
            'info': 0,
            'compliance_score': '0%'
        }
    }
    return render(request, 'accessibility/dashboard.html', context)
