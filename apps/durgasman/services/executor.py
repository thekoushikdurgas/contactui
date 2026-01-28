"""HTTP Request Executor for Durgasman."""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any
from django.conf import settings


class RequestExecutor:
    """Asynchronous HTTP request executor with variable resolution."""

    def __init__(self, timeout: int = 30):
        self.timeout = aiohttp.ClientTimeout(total=timeout)

    async def execute_request(self, request_data: Dict[str, Any], environment_vars: Dict[str, str] = None) -> Dict[str, Any]:
        """Execute an API request asynchronously."""

        # Resolve variables in URL and other fields
        url = self._resolve_variables(request_data['url'], environment_vars or {})
        headers = self._resolve_headers(request_data.get('headers', []), environment_vars or {})
        body = self._resolve_variables(request_data.get('body', ''), environment_vars or {})

        start_time = time.time()

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # Prepare request
                method = request_data['method'].upper()
                request_kwargs = {'headers': headers}

                # Handle request body
                if body and method in ['POST', 'PUT', 'PATCH']:
                    # Try to parse as JSON, fallback to raw text
                    try:
                        json_body = json.loads(body)
                        request_kwargs['json'] = json_body
                    except (json.JSONDecodeError, TypeError):
                        request_kwargs['data'] = body

                # Make the request
                async with session.request(method, url, **request_kwargs) as response:
                    # Read response
                    response_text = await response.text()
                    response_time = (time.time() - start_time) * 1000

                    # Try to parse JSON response
                    try:
                        response_data = json.loads(response_text) if response_text else None
                    except (json.JSONDecodeError, TypeError):
                        response_data = response_text

                    return {
                        'status': response.status,
                        'statusText': response.reason,
                        'headers': dict(response.headers),
                        'data': response_data,
                        'time': round(response_time, 2),
                        'size': len(response_text.encode('utf-8'))
                    }

        except aiohttp.ClientError as e:
            response_time = (time.time() - start_time) * 1000
            return {
                'status': 0,
                'statusText': 'Connection Error',
                'error': f'Failed to connect: {str(e)}',
                'time': round(response_time, 2),
                'size': 0
            }
        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            return {
                'status': 0,
                'statusText': 'Timeout',
                'error': f'Request timed out after {self.timeout.total} seconds',
                'time': round(response_time, 2),
                'size': 0
            }
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                'status': 0,
                'statusText': 'Error',
                'error': str(e),
                'time': round(response_time, 2),
                'size': 0
            }

    def _resolve_variables(self, text: str, variables: Dict[str, str]) -> str:
        """Replace {{variable}} placeholders with values."""
        if not text or not variables:
            return text

        for key, value in variables.items():
            placeholder = f'{{{{key}}}}'
            text = text.replace(placeholder, str(value))

        return text

    def _resolve_headers(self, headers: list, variables: Dict[str, str]) -> Dict[str, str]:
        """Convert header list to dict and resolve variables."""
        result = {}

        for header in headers:
            if not header.get('enabled', True):
                continue

            key = self._resolve_variables(header.get('key', ''), variables)
            value = self._resolve_variables(header.get('value', ''), variables)

            if key:
                result[key] = value

        return result

    def validate_request_data(self, request_data: Dict[str, Any]) -> tuple[bool, str]:
        """Validate request data before execution."""
        if not request_data.get('url'):
            return False, "URL is required"

        if not request_data.get('method'):
            return False, "HTTP method is required"

        # Validate URL format
        url = request_data['url']
        if not (url.startswith('http://') or url.startswith('https://') or url.startswith('{{')):
            return False, "URL must start with http://, https://, or contain variables"

        return True, "Valid"


# Synchronous wrapper for Django views
def execute_request_sync(request_data: Dict[str, Any], environment_vars: Dict[str, str] = None) -> Dict[str, Any]:
    """Synchronous wrapper for the async executor."""
    executor = RequestExecutor()
    return asyncio.run(executor.execute_request(request_data, environment_vars))