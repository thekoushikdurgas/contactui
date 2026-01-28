"""Postman Collection Importer for Durgasman."""

import json
import uuid as uuid_lib
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..services.durgasman_storage_service import CollectionStorageService


def import_postman_collection(file_path: str, user_uuid: str) -> Dict[str, Any]:
    """Import Postman collection from media/postman/collection/"""
    # Convert user_uuid to string if needed
    if hasattr(user_uuid, 'uuid'):
        user_uuid = str(user_uuid.uuid)
    elif hasattr(user_uuid, 'id'):
        user_uuid = str(user_uuid.id)
    else:
        user_uuid = str(user_uuid)
    
    storage = CollectionStorageService()
    
    with open(file_path, 'r') as f:
        data = json.load(f)

    # Create collection
    collection = storage.create_collection(
        name=data['info']['name'],
        description=data['info'].get('description', ''),
        user=user_uuid
    )
    
    collection_id = collection.get('collection_id') or collection.get('id')
    requests = []

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

            requests.append({
                'request_id': str(uuid_lib.uuid4()),
                'name': f"{folder_path}{item['name']}".strip(),
                'method': request_data.get('method', 'GET'),
                'url': raw_url,
                'headers': headers,
                'params': params,
                'body': body,
                'auth_type': _extract_auth_type(request_data),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
            })
        elif 'item' in item:
            # This is a folder
            new_path = f"{folder_path}{item['name']}/"
            for sub_item in item['item']:
                process_item(sub_item, new_path)

    # Process all items in the collection
    for item in data.get('item', []):
        process_item(item)
    
    # Update collection with requests
    storage.update_collection(collection_id, requests=requests)
    
    # Return updated collection
    return storage.get_collection(collection_id)


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


def import_postman_environment(file_path: str, user_uuid: str) -> Dict[str, Any]:
    """Import environment variables from media/postman/environment/"""
    from ..services.durgasman_storage_service import EnvironmentStorageService
    
    # Convert user_uuid to string if needed
    if hasattr(user_uuid, 'uuid'):
        user_uuid = str(user_uuid.uuid)
    elif hasattr(user_uuid, 'id'):
        user_uuid = str(user_uuid.id)
    else:
        user_uuid = str(user_uuid)
    
    storage = EnvironmentStorageService()

    with open(file_path, 'r') as f:
        data = json.load(f)

    variables = []
    for var in data.get('values', []):
        if isinstance(var, dict):
            variables.append({
                'key': var.get('key', ''),
                'value': var.get('value', ''),
                'enabled': var.get('enabled', True)
            })

    environment = storage.create_environment(
        name=data['name'],
        user=user_uuid,
        variables=variables
    )

    return environment


def export_to_postman(collection: Dict[str, Any]) -> Dict[str, Any]:
    """Export Durgasman collection to Postman v2.1 format."""
    items = []

    requests = collection.get('requests', [])
    for request in requests:
        # Convert headers
        headers = []
        for h in request.get('headers', []):
            if h.get('enabled', True):
                headers.append({
                    'key': h.get('key', ''),
                    'value': h.get('value', ''),
                    'type': 'text'
                })

        # Convert query parameters
        query = []
        for p in request.get('params', []):
            if p.get('enabled', True):
                query.append({
                    'key': p.get('key', ''),
                    'value': p.get('value', ''),
                    'type': 'text'
                })

        # Build URL object
        url_obj = {
            'raw': request.get('url', ''),
            'protocol': 'https',
            'host': ['api', 'example', 'com'],  # This would need to be parsed from URL
        }

        if query:
            url_obj['query'] = query

        # Build request body
        body = {}
        if request.get('body'):
            body = {
                'mode': 'raw',
                'raw': request.get('body', ''),
                'options': {
                    'raw': {
                        'language': 'json'
                    }
                }
            }

        item = {
            'name': request.get('name', ''),
            'request': {
                'method': request.get('method', 'GET'),
                'header': headers,
                'body': body,
                'url': url_obj,
            },
            'response': []
        }

        items.append(item)

    return {
        'info': {
            'name': collection.get('name', ''),
            'description': collection.get('description', ''),
            'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json',
        },
        'item': items,
        'variable': []
    }