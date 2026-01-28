"""Request execution API endpoint."""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import asyncio
from datetime import datetime

from apps.core.decorators.auth import require_super_admin
from ..services.durgasman_storage_service import (
    EnvironmentStorageService,
    RequestHistoryStorageService
)


@csrf_exempt
@require_http_methods(["POST"])
@require_super_admin
def execute_request(request):
    """Execute an API request."""
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    environment_storage = EnvironmentStorageService()
    history_storage = RequestHistoryStorageService()
    
    try:
        data = json.loads(request.body)

        # Get user's active environment
        environment_vars = {}
        try:
            # For now, get the first environment. In a real app, you'd have active environment selection
            environments_result = environment_storage.list(
                filters={'user': user_uuid},
                limit=1,
                offset=0
            )
            envs = environments_result.get('items', [])
            if envs:
                env = envs[0]
                variables = env.get('variables', [])
                environment_vars = {
                    var.get('key'): var.get('value')
                    for var in variables
                    if var.get('enabled', True)
                }
        except:
            pass  # No environment variables

        # Execute request
        from ..services.executor import execute_request_sync
        result = execute_request_sync(data, environment_vars)

        # Save to history
        history_storage.create_history(
            user=user_uuid,
            method=data['method'],
            url=data['url'],
            request_headers=data.get('headers', {}),
            request_body=data.get('body', ''),
            response_status=result['status'],
            response_headers=result.get('headers', {}),
            response_body=json.dumps(result.get('data', '')),
            response_time_ms=int(result['time']),
            response_size_bytes=result['size']
        )

        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({
            'status': 0,
            'statusText': 'Error',
            'error': str(e),
            'time': 0,
            'size': 0
        }, status=500)