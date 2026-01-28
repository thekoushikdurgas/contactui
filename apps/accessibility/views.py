"""Accessibility views."""
from django.shortcuts import render
from apps.core.decorators.auth import require_super_admin
from .services.scan_storage_service import AccessibilityScanStorageService


@require_super_admin
def accessibility_view(request):
    """Accessibility testing dashboard."""
    storage = AccessibilityScanStorageService()
    
    # Get recent scans
    scans_result = storage.list(limit=10, offset=0, order_by='created_at', reverse=True)
    scans = scans_result.get('items', [])
    
    # Calculate stats from all scans
    all_scans = storage.list(limit=None, offset=0)
    total_issues = sum(scan.get('total_issues', 0) for scan in all_scans.get('items', []))
    critical = sum(scan.get('critical_issues', 0) for scan in all_scans.get('items', []))
    warning = sum(scan.get('warning_issues', 0) for scan in all_scans.get('items', []))
    info = sum(scan.get('info_issues', 0) for scan in all_scans.get('items', []))
    
    # Calculate compliance score (average of all scan scores)
    scan_scores = [scan.get('score', 0) for scan in all_scans.get('items', [])]
    compliance_score = sum(scan_scores) / len(scan_scores) if scan_scores else 0
    
    # Collect all issues
    issues = []
    for scan in scans:
        issues.extend(scan.get('issues', []))
    
    context = {
        'scans': scans,
        'issues': issues[:50],  # Limit to 50 most recent issues
        'stats': {
            'total_issues': total_issues,
            'critical': critical,
            'warning': warning,
            'info': info,
            'compliance_score': f'{compliance_score:.1f}%'
        }
    }
    return render(request, 'accessibility/dashboard.html', context)
