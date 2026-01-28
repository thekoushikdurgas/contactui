"""Data transformation layer for converting between Django and Lambda API formats."""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from apps.documentation.schemas.lambda_models import (
    validate_page_data,
    validate_endpoint_data,
    validate_relationship_data
)

logger = logging.getLogger(__name__)


class DataTransformer:
    """Transform data between Django form format and Lambda API format."""
    
    @staticmethod
    def django_to_lambda_page(django_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Django form data to Lambda API PageDocumentation format.
        
        Args:
            django_data: Django form data (from request.POST or form.cleaned_data)
            
        Returns:
            Lambda API format page data
        """
        page_id = django_data.get('page_id')
        if not page_id:
            raise ValueError("page_id is required")
        
        # Build metadata
        metadata = django_data.get('metadata', {})
        if not isinstance(metadata, dict):
            metadata = {}
        
        # Map title to purpose if needed
        if 'title' in django_data and 'purpose' not in metadata:
            metadata['purpose'] = django_data.get('title', '')
        
        # Ensure required metadata fields
        if 'route' not in metadata:
            metadata['route'] = django_data.get('route', '/')
        if 'file_path' not in metadata:
            metadata['file_path'] = django_data.get('file_path', '')
        if 'purpose' not in metadata:
            metadata['purpose'] = django_data.get('purpose', '')
        if 's3_key' not in metadata:
            metadata['s3_key'] = f"data/pages/{page_id}.json"
        if 'last_updated' not in metadata:
            metadata['last_updated'] = datetime.now(timezone.utc).isoformat()
        
        # Set defaults for optional fields
        if 'status' not in metadata:
            metadata['status'] = django_data.get('status', 'published')
        if 'page_state' not in metadata:
            metadata['page_state'] = django_data.get('page_state', 'development')
        if 'authentication' not in metadata:
            metadata['authentication'] = django_data.get('authentication', 'Not required')
        
        # Handle uses_endpoints
        if 'uses_endpoints' not in metadata:
            metadata['uses_endpoints'] = django_data.get('uses_endpoints', [])
        
        # Handle ui_components
        if 'ui_components' not in metadata:
            metadata['ui_components'] = django_data.get('ui_components', [])
        
        # Build complete page data
        lambda_data = {
            '_id': django_data.get('_id') or f"{page_id}-001",
            'page_id': page_id,
            'page_type': django_data.get('page_type', 'docs'),
            'metadata': metadata,
            'content': django_data.get('content', ''),
            'created_at': django_data.get('created_at') or datetime.now(timezone.utc).isoformat(),
        }
        
        # Add optional enhanced fields
        if 'access_control' in django_data:
            lambda_data['access_control'] = django_data['access_control']
        if 'sections' in django_data:
            lambda_data['sections'] = django_data['sections']
        if 'fallback_data' in django_data:
            lambda_data['fallback_data'] = django_data['fallback_data']
        if 'mock_data' in django_data:
            lambda_data['mock_data'] = django_data['mock_data']
        if 'demo_data' in django_data:
            lambda_data['demo_data'] = django_data['demo_data']
        
        # Validate and normalize
        try:
            lambda_data = validate_page_data(lambda_data)
        except Exception as e:
            logger.error(f"Validation error in django_to_lambda_page: {e}")
            raise ValueError(f"Invalid page data: {e}")
        
        return lambda_data
    
    @staticmethod
    def lambda_to_django_page(lambda_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Lambda API page data to Django form format.
        
        Args:
            lambda_data: Lambda API page data
            
        Returns:
            Django form format data
        """
        django_data = lambda_data.copy()
        
        # Flatten metadata for form display
        metadata = django_data.get('metadata', {})
        if isinstance(metadata, dict):
            # Extract common fields to top level for easier form access
            django_data['route'] = metadata.get('route', '/')
            django_data['file_path'] = metadata.get('file_path', '')
            django_data['purpose'] = metadata.get('purpose', '')
            django_data['status'] = metadata.get('status', 'published')
            django_data['page_state'] = metadata.get('page_state', 'development')
            django_data['title'] = metadata.get('purpose', '')  # Map purpose to title for form
        
        # Handle _id vs id
        if '_id' in django_data and 'id' not in django_data:
            django_data['id'] = django_data['_id']
        
        return django_data
    
    @staticmethod
    def django_to_lambda_endpoint(django_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Django form data to Lambda API EndpointDocumentation format."""
        endpoint_id = django_data.get('endpoint_id')
        if not endpoint_id:
            raise ValueError("endpoint_id is required")
        
        # Build lambda data
        lambda_data = {
            '_id': django_data.get('_id') or f"{endpoint_id}-001",
            'endpoint_id': endpoint_id,
            'endpoint_path': django_data.get('endpoint_path', ''),
            'method': django_data.get('method', 'QUERY').upper(),
            'api_version': django_data.get('api_version', 'v1'),
            'description': django_data.get('description', ''),
            'created_at': django_data.get('created_at') or datetime.now(timezone.utc).isoformat(),
            'updated_at': django_data.get('updated_at') or datetime.now(timezone.utc).isoformat(),
            'endpoint_state': django_data.get('endpoint_state', 'development'),
        }
        
        # Handle file references (legacy or new format)
        if 'service_file' in django_data:
            lambda_data['service_file'] = django_data['service_file']
        if 'router_file' in django_data:
            lambda_data['router_file'] = django_data['router_file']
        
        # Handle files object
        if 'files' in django_data:
            lambda_data['files'] = django_data['files']
        
        # Handle methods
        if 'service_methods' in django_data:
            lambda_data['service_methods'] = django_data['service_methods']
        if 'repository_methods' in django_data:
            lambda_data['repository_methods'] = django_data['repository_methods']
        
        # Handle methods object
        if 'methods' in django_data:
            lambda_data['methods'] = django_data['methods']
        
        # Handle used_by_pages
        if 'used_by_pages' in django_data:
            lambda_data['used_by_pages'] = django_data['used_by_pages']
        
        # Handle optional fields
        if 'rate_limit' in django_data:
            lambda_data['rate_limit'] = django_data['rate_limit']
        if 'graphql_operation' in django_data:
            lambda_data['graphql_operation'] = django_data['graphql_operation']
        if 'sql_file' in django_data:
            lambda_data['sql_file'] = django_data['sql_file']
        
        # Handle enhanced fields
        if 'access_control' in django_data:
            lambda_data['access_control'] = django_data['access_control']
        if 'lambda_services' in django_data:
            lambda_data['lambda_services'] = django_data['lambda_services']
        
        # Validate and normalize
        try:
            lambda_data = validate_endpoint_data(lambda_data)
        except Exception as e:
            logger.error(f"Validation error in django_to_lambda_endpoint: {e}")
            raise ValueError(f"Invalid endpoint data: {e}")
        
        return lambda_data
    
    @staticmethod
    def lambda_to_django_endpoint(lambda_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Lambda API endpoint data to Django form format."""
        django_data = lambda_data.copy()
        
        # Handle _id vs id
        if '_id' in django_data and 'id' not in django_data:
            django_data['id'] = django_data['_id']
        
        return django_data
    
    @staticmethod
    def django_to_lambda_relationship(django_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Django form data to Lambda API EnhancedRelationship format."""
        # Build relationship_id if not present
        if 'relationship_id' not in django_data:
            page_path = django_data.get('page_path', '')
            endpoint_path = django_data.get('endpoint_path', '')
            method = django_data.get('method', 'QUERY')
            if page_path and endpoint_path:
                django_data['relationship_id'] = f"{page_path}|{endpoint_path}|{method}"
        
        # Ensure _id
        if '_id' not in django_data:
            relationship_id = django_data.get('relationship_id', 'unknown')
            django_data['_id'] = relationship_id
        
        # Ensure state
        if 'state' not in django_data:
            django_data['state'] = django_data.get('state', 'development')
        
        # Validate and normalize
        try:
            django_data = validate_relationship_data(django_data)
        except Exception as e:
            logger.error(f"Validation error in django_to_lambda_relationship: {e}")
            raise ValueError(f"Invalid relationship data: {e}")
        
        return django_data
    
    @staticmethod
    def lambda_to_django_relationship(lambda_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Lambda API relationship data to Django form format."""
        django_data = lambda_data.copy()
        
        # Handle _id vs id
        if '_id' in django_data and 'id' not in django_data:
            django_data['id'] = django_data['_id']
        
        # Flatten legacy fields if enhanced format
        if 'page_reference' in django_data and django_data['page_reference']:
            page_ref = django_data['page_reference']
            if 'page_path' not in django_data:
                django_data['page_path'] = page_ref.get('page_path', '')
        
        if 'endpoint_reference' in django_data and django_data['endpoint_reference']:
            endpoint_ref = django_data['endpoint_reference']
            if 'endpoint_path' not in django_data:
                django_data['endpoint_path'] = endpoint_ref.get('endpoint_path', '')
            if 'method' not in django_data:
                django_data['method'] = endpoint_ref.get('method', 'QUERY')
        
        if 'connection' in django_data and django_data['connection']:
            connection = django_data['connection']
            if 'via_service' not in django_data:
                django_data['via_service'] = connection.get('via_service', '')
            if 'via_hook' not in django_data:
                django_data['via_hook'] = connection.get('via_hook')
            if 'usage_type' not in django_data:
                django_data['usage_type'] = connection.get('usage_type', 'primary')
            if 'usage_context' not in django_data:
                django_data['usage_context'] = connection.get('usage_context', 'data_fetching')
        
        return django_data
    
    @staticmethod
    def calculate_computed_fields(data: Dict[str, Any], resource_type: str) -> Dict[str, Any]:
        """Auto-calculate computed fields for a resource.
        
        Args:
            data: Resource data dictionary
            resource_type: Type of resource ('page', 'endpoint', 'relationship')
            
        Returns:
            Data with computed fields calculated
        """
        if resource_type == 'page':
            metadata = data.get('metadata', {})
            if isinstance(metadata, dict):
                uses_endpoints = metadata.get('uses_endpoints', [])
                metadata['endpoint_count'] = len(uses_endpoints)
                
                # Derive api_versions
                api_versions_set = set()
                for endpoint in uses_endpoints:
                    if isinstance(endpoint, dict) and 'api_version' in endpoint:
                        api_versions_set.add(endpoint['api_version'])
                metadata['api_versions'] = sorted(list(api_versions_set))
                data['metadata'] = metadata
        
        elif resource_type == 'endpoint':
            used_by_pages = data.get('used_by_pages', [])
            data['page_count'] = len(used_by_pages)
        
        return data
    
    @staticmethod
    def handle_partial_update(
        existing: Dict[str, Any],
        updates: Dict[str, Any],
        resource_type: str
    ) -> Dict[str, Any]:
        """Handle partial update by merging with existing data.
        
        Args:
            existing: Existing resource data
            updates: Partial update data
            resource_type: Type of resource
            
        Returns:
            Merged data
        """
        def deep_merge(base: Dict, updates: Dict) -> Dict:
            """Deep merge two dictionaries."""
            result = base.copy()
            for key, value in updates.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                elif value is not None:  # Only update if value is not None
                    result[key] = value
            return result
        
        merged = deep_merge(existing, updates)
        
        # Recalculate computed fields
        merged = DataTransformer.calculate_computed_fields(merged, resource_type)
        
        # Update timestamp
        merged['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        return merged
