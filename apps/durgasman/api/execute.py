"""Request execution API endpoint."""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
import asyncio

from ..models import RequestHistory, Environment, EnvVariable


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def execute_request(request):
    """Execute an API request."""
    try:
        data = json.loads(request.body)

        # Get user's active environment
        environment_vars = {}
        try:
            # For now, get the first environment. In a real app, you'd have active environment selection
            env = Environment.objects.filter(user=request.user).first()
            if env:
                environment_vars = {
                    var.key: var.value
                    for var in env.env_variables.filter(enabled=True)
                }
        except:
            pass  # No environment variables

        # Execute request
        from ..services.executor import execute_request_sync
        result = execute_request_sync(data, environment_vars)

        # Save to history
        RequestHistory.objects.create(
            user=request.user,
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