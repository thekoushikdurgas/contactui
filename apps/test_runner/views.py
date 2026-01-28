"""Test Runner views."""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def test_runner_view(request):
    """Test runner dashboard."""
    context = {
        'test_suites': [],
        'recent_runs': [],
        'stats': {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'success_rate': '0%'
        }
    }
    return render(request, 'test_runner/dashboard.html', context)
