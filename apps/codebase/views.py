"""Codebase views."""
import logging
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

from apps.codebase.services import CodebaseAnalysisService

logger = logging.getLogger(__name__)


@login_required
def codebase_dashboard(request):
    """Codebase analysis dashboard."""
    service = CodebaseAnalysisService()
    
    # Get recent analyses (would be from database in full implementation)
    context = {
        'analyses': [],
        'recent_files': [],
        'total_files': 0,
        'total_lines': 0,
        'languages': {},
        'dependencies': [],
        'empty_state_scan_url': reverse('codebase:scan'),
    }
    
    return render(request, 'codebase/dashboard.html', context)


@login_required
def scan_view(request):
    """Scan directory view."""
    if request.method == 'POST':
        target_path = request.POST.get('target_path')
        analysis_type = request.POST.get('analysis_type', 'full_scan')
        
        if not target_path:
            messages.error(request, 'Target path is required.')
            return render(request, 'codebase/scan.html')
        
        try:
            service = CodebaseAnalysisService()
            results = service.scan_directory(target_path, analysis_type)
            
            context = {
                'results': results,
                'target_path': target_path,
                'analysis_type': analysis_type
            }
            return render(request, 'codebase/scan_results.html', context)
        except Exception as e:
            logger.error(f"Error scanning directory: {e}", exc_info=True)
            messages.error(request, f'Error scanning directory: {str(e)}')
    
    return render(request, 'codebase/scan.html')


@login_required
def analysis_detail_view(request, analysis_id):
    """Analysis detail view."""
    # Placeholder - would load from database
    context = {
        'analysis_id': analysis_id,
        'analysis': None
    }
    return render(request, 'codebase/detail.html', context)


@login_required
def file_list_view(request, analysis_id):
    """File list view for an analysis."""
    context = {
        'analysis_id': analysis_id,
        'files': []
    }
    return render(request, 'codebase/file_list.html', context)


@login_required
def file_detail_view(request, analysis_id, file_path):
    """File detail view."""
    context = {
        'analysis_id': analysis_id,
        'file_path': file_path,
        'file_data': None
    }
    return render(request, 'codebase/file_detail.html', context)


@login_required
def dependencies_view(request, analysis_id):
    """Dependencies view."""
    context = {
        'analysis_id': analysis_id,
        'dependencies': []
    }
    return render(request, 'codebase/dependencies.html', context)


@login_required
def patterns_view(request, analysis_id):
    """Patterns view."""
    context = {
        'analysis_id': analysis_id,
        'patterns': []
    }
    return render(request, 'codebase/patterns.html', context)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def scan_api(request):
    """API endpoint to scan a directory."""
    try:
        data = json.loads(request.body)
        target_path = data.get('target_path')
        analysis_type = data.get('analysis_type', 'full_scan')
        
        if not target_path:
            return JsonResponse({'error': 'target_path is required'}, status=400)
        
        service = CodebaseAnalysisService()
        results = service.scan_directory(target_path, analysis_type)
        
        return JsonResponse({
            'success': True,
            'results': results
        })
    except Exception as e:
        logger.error(f"Error in scan API: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)
