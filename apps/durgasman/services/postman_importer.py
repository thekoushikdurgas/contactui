"""Postman Collection Importer for Durgasman."""

import json
import uuid
from typing import Dict, List, Any, Optional

from ..models import Collection, ApiRequest


def import_postman_collection(file_path: str, user) -> Collection:
    """Import Postman collection from media/postman/collection/"""
    with open(file_path, 'r') as f:
        data = json.load(f)

    collection = Collection.objects.create(
        name=data['info']['name'],
        description=data['info'].get('description', ''),
        user=user
    )

    def process_item(item: Dict[str, Any], folder_path: str = '') -> None:
        """Recursively process Postman items (requests and folders)."""
        if 'request' in item:
            # This is a request
            request_data = item['request']
            url = request_data.get('url', {})

            # Handle Postman URL format (string or object)
            if isinstance(url, dict):
                raw_url = url.get('raw', '')
                # Handle query parameters
                query_params = url.get('query', [])
            else:
                raw_url = url
                query_params = []

            # Convert headers to our format
            headers = []
            for h in request_data.get('header', []):
                if isinstance(h, dict):
                    headers.append({
                        'key': h.get('key', ''),
                        'value': h.get('value', ''),
                        'enabled': h.get('disabled', False) != True  # Postman uses 'disabled', we use 'enabled'
                    })

            # Convert query params to our format
            params = []
            for p in query_params:
                if isinstance(p, dict):
                    params.append({
                        'key': p.get('key', ''),
                        'value': p.get('value', ''),
                        'enabled': p.get('disabled', False) != True
                    })

            # Get request body
            body = ''
            body_data = request_data.get('body', {})
            if body_data and body_data.get('mode') == 'raw':
                body = body_data.get('raw', '')

            ApiRequest.objects.create(
                collection=collection,
                name=f"{folder_path}{item['name']}".strip(),
                method=request_data.get('method', 'GET'),
                url=raw_url,
                headers=headers,
                params=params,
                body=body,
                auth_type=_extract_auth_type(request_data),
            )
        elif 'item' in item:
            # This is a folder
            new_path = f"{folder_path}{item['name']}/"
            for sub_item in item['item']:
                process_item(sub_item, new_path)

    # Process all items in the collection
    for item in data.get('item', []):
        process_item(item)

    return collection


def _extract_auth_type(request_data: Dict[str, Any]) -> str:
    """Extract authentication type from Postman request."""
    auth = request_data.get('auth', {})
    if not auth:
        return 'None'

    auth_type = auth.get('type', '').lower()
    if auth_type == 'bearer':
        return 'Bearer Token'
    elif auth_type == 'basic':
        return 'Basic Auth'
    elif auth_type == 'apikey':
        return 'API Key'
    else:
        return 'None'


def import_postman_environment(file_path: str, user):
    """Import environment variables from media/postman/environment/"""
    from ..models import Environment, EnvVariable

    with open(file_path, 'r') as f:
        data = json.load(f)

    environment = Environment.objects.create(
        name=data['name'],
        user=user
    )

    for var in data.get('values', []):
        if isinstance(var, dict):
            EnvVariable.objects.create(
                environment=environment,
                key=var.get('key', ''),
                value=var.get('value', ''),
                enabled=var.get('enabled', True)
            )

    return environment


def export_to_postman(collection: Collection) -> Dict[str, Any]:
    """Export Durgasman collection to Postman v2.1 format."""
    items = []

    for request in collection.requests.all():
        # Convert headers
        headers = []
        for h in request.headers:
            if h.get('enabled', True):
                headers.append({
                    'key': h['key'],
                    'value': h['value'],
                    'type': 'text'
                })

        # Convert query parameters
        query = []
        for p in request.params:
            if p.get('enabled', True):
                query.append({
                    'key': p['key'],
                    'value': p['value'],
                    'type': 'text'
                })

        # Build URL object
        url_obj = {
            'raw': request.url,
            'protocol': 'https',
            'host': ['api', 'example', 'com'],  # This would need to be parsed from URL
        }

        if query:
            url_obj['query'] = query

        # Build request body
        body = {}
        if request.body:
            body = {
                'mode': 'raw',
                'raw': request.body,
                'options': {
                    'raw': {
                        'language': 'json'
                    }
                }
            }

        item = {
            'name': request.name,
            'request': {
                'method': request.method,
                'header': headers,
                'body': body,
                'url': url_obj,
            },
            'response': []
        }

        items.append(item)

    return {
        'info': {
            'name': collection.name,
            'description': collection.description or '',
            'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json',
        },
        'item': items,
        'variable': []
    }