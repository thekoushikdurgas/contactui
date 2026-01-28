"""API views for codebase app."""
import json
import logging
import uuid
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from apps.codebase.services import CodebaseAnalysisService

logger = logging.getLogger(__name__)

# In-memory storage for analyses (in production, use database)
_analyses_store = {}


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def codebase_scan_api(request):
    """API endpoint to start a codebase scan."""
    try:
        data = json.loads(request.body)
        target_path = data.get('target_path')
        analysis_type = data.get('analysis_type', 'full_scan')
        name = data.get('name', f'Scan {target_path}')
        
        if not target_path:
            return JsonResponse({
                'success': False,
                'error': 'target_path is required'
            }, status=400)
        
        service = CodebaseAnalysisService()
        results = service.scan_directory(target_path, analysis_type)
        
        # Store analysis with ID
        analysis_id = str(uuid.uuid4())
        analysis_data = {
            'analysis_id': analysis_id,
            'name': name,
            'target_path': target_path,
            'analysis_type': analysis_type,
            'status': 'completed',
            'results': results,
            'created_at': results.get('created_at')
        }
        _analyses_store[analysis_id] = analysis_data
        
        return JsonResponse({
            'success': True,
            'data': {
                'analysis_id': analysis_id,
                'name': name,
                'status': 'completed',
                'results': {
                    'total_files': results.get('total_files', 0),
                    'total_lines': results.get('total_lines', 0),
                    'languages': results.get('languages', {}),
                    'dependencies_count': len(results.get('dependencies', [])),
                    'patterns_count': len(results.get('patterns', []))
                }
            }
        }, status=201)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        logger.error(f"Error in codebase scan API: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def codebase_analysis_detail_api(request, analysis_id):
    """API endpoint to get analysis details."""
    try:
        analysis = _analyses_store.get(analysis_id)
        
        if not analysis:
            return JsonResponse({
                'success': False,
                'error': 'Analysis not found'
            }, status=404)
        
        return JsonResponse({
            'success': True,
            'data': {
                'analysis_id': analysis['analysis_id'],
                'name': analysis['name'],
                'target_path': analysis['target_path'],
                'analysis_type': analysis['analysis_type'],
                'status': analysis['status'],
                'results': {
                    'total_files': analysis['results'].get('total_files', 0),
                    'total_lines': analysis['results'].get('total_lines', 0),
                    'languages': analysis['results'].get('languages', {}),
                    'dependencies': analysis['results'].get('dependencies', []),
                    'patterns': analysis['results'].get('patterns', [])
                }
            }
        })
    except Exception as e:
        logger.error(f"Error getting analysis {analysis_id}: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def codebase_analysis_files_api(request, analysis_id):
    """API endpoint to get files from an analysis."""
    try:
        analysis = _analyses_store.get(analysis_id)
        
        if not analysis:
            return JsonResponse({
                'success': False,
                'error': 'Analysis not found'
            }, status=404)
        
        files = analysis['results'].get('files', [])
        
        # Apply filters
        language = request.GET.get('language')
        if language:
            files = [f for f in files if f.get('language') == language]
        
        limit = int(request.GET.get('limit', 100))
        offset = int(request.GET.get('offset', 0))
        
        paginated_files = files[offset:offset + limit]
        
        return JsonResponse({
            'success': True,
            'items': paginated_files,
            'total': len(files),
            'limit': limit,
            'offset': offset
        })
    except Exception as e:
        logger.error(f"Error getting analysis files {analysis_id}: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def codebase_analysis_dependencies_api(request, analysis_id):
    """API endpoint to get dependencies from an analysis."""
    try:
        analysis = _analyses_store.get(analysis_id)
        
        if not analysis:
            return JsonResponse({
                'success': False,
                'error': 'Analysis not found'
            }, status=404)
        
        dependencies = analysis['results'].get('dependencies', [])
        
        return JsonResponse({
            'success': True,
            'data': dependencies,
            'total': len(dependencies)
        })
    except Exception as e:
        logger.error(f"Error getting analysis dependencies {analysis_id}: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def codebase_analysis_patterns_api(request, analysis_id):
    """API endpoint to get patterns from an analysis."""
    try:
        analysis = _analyses_store.get(analysis_id)
        
        if not analysis:
            return JsonResponse({
                'success': False,
                'error': 'Analysis not found'
            }, status=404)
        
        patterns = analysis['results'].get('patterns', [])
        
        return JsonResponse({
            'success': True,
            'data': patterns,
            'total': len(patterns)
        })
    except Exception as e:
        logger.error(f"Error getting analysis patterns {analysis_id}: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
