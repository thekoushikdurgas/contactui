"""Test Runner views."""
from django.shortcuts import render
from apps.core.decorators.auth import require_super_admin
from .services.test_storage_service import TestSuiteStorageService


@require_super_admin
def test_runner_view(request):
    """Test runner dashboard."""
    storage = TestSuiteStorageService()
    
    # Get test suites
    suites_result = storage.list(limit=50, offset=0, order_by='created_at', reverse=True)
    test_suites = suites_result.get('items', [])
    
    # Get recent runs from all suites
    recent_runs = []
    for suite in test_suites[:10]:  # Limit to 10 most recent suites
        runs = storage.get_runs(suite.get('suite_id'))
        recent_runs.extend(runs[:5])  # Get 5 most recent runs per suite
    
    # Sort runs by created_at descending
    recent_runs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    recent_runs = recent_runs[:20]  # Limit to 20 most recent runs
    
    # Calculate stats
    total_tests = sum(run.get('total', 0) for run in recent_runs)
    passed = sum(run.get('passed', 0) for run in recent_runs)
    failed = sum(run.get('failed', 0) for run in recent_runs)
    skipped = sum(run.get('skipped', 0) for run in recent_runs)
    success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
    
    context = {
        'test_suites': test_suites,
        'recent_runs': recent_runs,
        'stats': {
            'total_tests': total_tests,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'success_rate': f'{success_rate:.1f}%'
        }
    }
    return render(request, 'test_runner/dashboard.html', context)
