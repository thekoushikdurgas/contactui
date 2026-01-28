"""Endpoint JSON Importer for Durgasman."""

import json
from typing import Dict, Any

from ..models import Collection, ApiRequest


def import_endpoint_json(file_path: str, user) -> Collection:
    """Convert endpoint JSON from media/endpoints/ to Durgasman collection."""

    with open(file_path, 'r') as f:
        endpoint_data = json.load(f)

    # Create collection for this endpoint
    collection_name = f"Endpoint: {endpoint_data.get('endpoint_id', 'Unknown')}"
    collection = Collection.objects.create(
        name=collection_name,
        description=endpoint_data.get('description', ''),
        user=user
    )

    # Handle different endpoint types
    if endpoint_data.get('api_version') == 'graphql':
        _import_graphql_endpoint(endpoint_data, collection)
    else:
        _import_rest_endpoint(endpoint_data, collection)

    return collection


def _import_graphql_endpoint(endpoint_data: Dict[str, Any], collection: Collection) -> None:
    """Import GraphQL endpoint from DocsAI format."""

    # Build GraphQL query/mutation
    operation = endpoint_data.get('graphql_operation', '')
    if not operation:
        # Try to build from available data
        operation_type = "query"
        if endpoint_data.get('method') == 'MUTATION':
            operation_type = "mutation"

        operation_name = endpoint_data.get('endpoint_id', '').replace('mutation_', '').replace('query_', '')
        operation = f"{operation_type} {operation_name} {{ }}"

    # Set up headers for GraphQL
    headers = [
        {
            'key': 'Content-Type',
            'value': 'application/json',
            'enabled': True
        },
        {
            'key': 'Authorization',
            'value': 'Bearer {{accessToken}}',
            'enabled': True
        }
    ]

    # Add any additional headers from the endpoint data
    if endpoint_data.get('authentication') and 'Bearer token' in endpoint_data['authentication']:
        pass  # Already added above

    # Build request body
    body = json.dumps({
        'query': operation,
        'variables': {}
    })

    # Create the API request
    ApiRequest.objects.create(
        collection=collection,
        name=endpoint_data.get('endpoint_id', 'GraphQL Request'),
        method='POST',
        url='/graphql',  # Your GraphQL endpoint
        headers=headers,
        body=body,
        response_schema=endpoint_data.get('response_schema', ''),
        auth_type='Bearer Token'
    )


def _import_rest_endpoint(endpoint_data: Dict[str, Any], collection: Collection) -> None:
    """Import REST endpoint from DocsAI format."""

    # Build URL from endpoint path
    base_url = "{{baseUrl}}"  # Would be replaced by environment variable
    endpoint_path = endpoint_data.get('endpoint_path', '')
    url = f"{base_url}{endpoint_path}"

    # Set up headers
    headers = [
        {
            'key': 'Content-Type',
            'value': 'application/json',
            'enabled': True
        }
    ]

    # Add authorization header if specified
    auth = endpoint_data.get('authentication', '')
    if 'Bearer token' in auth.lower():
        headers.append({
            'key': 'Authorization',
            'value': 'Bearer {{accessToken}}',
            'enabled': True
        })

    # Create the API request
    ApiRequest.objects.create(
        collection=collection,
        name=endpoint_data.get('endpoint_id', 'REST Request'),
        method=endpoint_data.get('method', 'GET'),
        url=url,
        headers=headers,
        response_schema=endpoint_data.get('response_schema', ''),
        auth_type='Bearer Token' if 'Bearer token' in auth.lower() else 'None'
    )


def import_multiple_endpoints(file_paths: list, user) -> Collection:
    """Import multiple endpoint JSON files into a single collection."""

    collection = Collection.objects.create(
        name="Imported Endpoints Collection",
        description=f"Imported from {len(file_paths)} endpoint files",
        user=user
    )

    for file_path in file_paths:
        try:
            with open(file_path, 'r') as f:
                endpoint_data = json.load(f)

            if endpoint_data.get('api_version') == 'graphql':
                _import_graphql_endpoint(endpoint_data, collection)
            else:
                _import_rest_endpoint(endpoint_data, collection)

        except Exception as e:
            # Log error but continue with other files
            print(f"Error importing {file_path}: {e}")
            continue

    return collection


def generate_request_from_endpoint_data(endpoint_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a request object from endpoint data without creating database records."""

    request_data = {
        'name': endpoint_data.get('endpoint_id', 'Generated Request'),
        'method': endpoint_data.get('method', 'GET'),
        'url': '/graphql' if endpoint_data.get('api_version') == 'graphql' else endpoint_data.get('endpoint_path', ''),
        'headers': [
            {
                'key': 'Content-Type',
                'value': 'application/json',
                'enabled': True
            }
        ],
        'params': [],
        'body': '',
        'auth_type': 'None',
        'response_schema': endpoint_data.get('response_schema', '')
    }

    # Add authentication
    auth = endpoint_data.get('authentication', '')
    if 'Bearer token' in auth.lower():
        request_data['headers'].append({
            'key': 'Authorization',
            'value': 'Bearer {{accessToken}}',
            'enabled': True
        })
        request_data['auth_type'] = 'Bearer Token'

    # Add GraphQL body if applicable
    if endpoint_data.get('api_version') == 'graphql':
        operation = endpoint_data.get('graphql_operation', '')
        request_data['body'] = json.dumps({
            'query': operation,
            'variables': {}
        })

    return request_data