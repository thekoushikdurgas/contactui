"""
Unified Dashboard URL Helper Functions

Utility functions for generating Unified Dashboard URLs programmatically.
Updated to use new route names without media-manager prefix.
"""

from __future__ import annotations

from typing import Optional, Dict, Any
from django.urls import reverse
from django.core.exceptions import NoReverseMatch


def get_media_manager_dashboard_url(tab: Optional[str] = None, **query_params) -> str:
    """
    Generate URL for Unified Dashboard (formerly Media Manager Dashboard).
    
    Args:
        tab: Tab name (pages, endpoints, relationships, postman)
        **query_params: Additional query parameters
        
    Returns:
        URL string
    """
    # Use new unified dashboard routes
    if tab:
        try:
            # Try new tab-specific routes first
            url = reverse(f'documentation:dashboard_{tab}')
        except NoReverseMatch:
            # Fallback to main dashboard with tab query param
            url = reverse('documentation:dashboard')
            query_params = query_params or {}
            query_params['tab'] = tab
    else:
        url = reverse('documentation:dashboard')
    
    if query_params:
        from urllib.parse import urlencode
        query_string = urlencode(query_params)
        url = f"{url}?{query_string}"
    
    return url


def get_pages_url(page_id: Optional[str] = None, sub_resource: Optional[str] = None, **query_params) -> str:
    """
    Generate URL for Pages API views.
    
    Args:
        page_id: Page ID for detail/sub-resource views
        sub_resource: Sub-resource name (sections, components, endpoints, versions, access-control)
        **query_params: Additional query parameters
        
    Returns:
        URL string
    """
    if page_id and sub_resource:
        try:
            # Use new unified route names (without media_manager_ prefix)
            url = reverse(f'documentation:page_{sub_resource}', args=[page_id])
        except NoReverseMatch:
            # Fallback to enhanced detail view
            url = reverse('documentation:page_detail_enhanced', args=[page_id])
    elif page_id:
        # Use enhanced detail view
        url = reverse('documentation:page_detail_enhanced', args=[page_id])
    else:
        # Use dashboard pages route
        url = reverse('documentation:dashboard_pages')
    
    if query_params:
        from urllib.parse import urlencode
        query_string = urlencode(query_params)
        url = f"{url}?{query_string}"
    
    return url


def get_endpoints_url(endpoint_id: Optional[str] = None, sub_resource: Optional[str] = None, **query_params) -> str:
    """
    Generate URL for Endpoints API views.
    
    Args:
        endpoint_id: Endpoint ID for detail/sub-resource views
        sub_resource: Sub-resource name (pages, access-control, lambda-services, files, methods, used-by-pages, dependencies)
        **query_params: Additional query parameters
        
    Returns:
        URL string
    """
    if endpoint_id and sub_resource:
        # Normalize sub-resource name (convert hyphens to underscores)
        sub_resource_normalized = sub_resource.replace('-', '_')
        try:
            # Use new unified route names
            url = reverse(f'documentation:endpoint_{sub_resource_normalized}', args=[endpoint_id])
        except NoReverseMatch:
            # Fallback to enhanced detail view
            url = reverse('documentation:endpoint_detail_enhanced', args=[endpoint_id])
    elif endpoint_id:
        url = reverse('documentation:endpoint_detail_enhanced', args=[endpoint_id])
    else:
        url = reverse('documentation:dashboard_endpoints')
    
    if query_params:
        from urllib.parse import urlencode
        query_string = urlencode(query_params)
        url = f"{url}?{query_string}"
    
    return url


def get_relationships_url(relationship_id: Optional[str] = None, sub_resource: Optional[str] = None, **query_params) -> str:
    """
    Generate URL for Relationships API views.
    
    Args:
        relationship_id: Relationship ID for detail/sub-resource views
        sub_resource: Sub-resource name (access-control, data-flow, performance, dependencies, postman)
        **query_params: Additional query parameters
        
    Returns:
        URL string
    """
    if relationship_id and sub_resource:
        sub_resource_normalized = sub_resource.replace('-', '_')
        try:
            # Use new unified route names
            url = reverse(f'documentation:relationship_{sub_resource_normalized}', args=[relationship_id])
        except NoReverseMatch:
            # Fallback to enhanced detail view
            url = reverse('documentation:relationship_detail_enhanced', args=[relationship_id])
    elif relationship_id:
        url = reverse('documentation:relationship_detail_enhanced', args=[relationship_id])
    else:
        url = reverse('documentation:dashboard_relationships')
    
    if query_params:
        from urllib.parse import urlencode
        query_string = urlencode(query_params)
        url = f"{url}?{query_string}"
    
    return url


def get_postman_url(config_id: Optional[str] = None, sub_resource: Optional[str] = None, **query_params) -> str:
    """
    Generate URL for Postman API views.
    
    Args:
        config_id: Configuration ID for detail/sub-resource views
        sub_resource: Sub-resource name (collection, environments, environment, mappings, mapping, test-suites, test-suite, access-control)
        **query_params: Additional query parameters (e.g., env_name, mapping_id, suite_id)
        
    Returns:
        URL string
    """
    if config_id and sub_resource:
        sub_resource_normalized = sub_resource.replace('-', '_')
        # Handle special cases that need additional parameters
        if sub_resource == 'environment' and 'env_name' in query_params:
            env_name = query_params.pop('env_name')
            try:
                # Use new unified route names
                url = reverse('documentation:postman_environment', args=[config_id, env_name])
            except NoReverseMatch:
                url = reverse('documentation:postman_detail_enhanced', args=[config_id])
        elif sub_resource == 'mapping' and 'mapping_id' in query_params:
            mapping_id = query_params.pop('mapping_id')
            try:
                url = reverse('documentation:postman_mapping', args=[config_id, mapping_id])
            except NoReverseMatch:
                url = reverse('documentation:postman_detail_enhanced', args=[config_id])
        elif sub_resource == 'test-suite' and 'suite_id' in query_params:
            suite_id = query_params.pop('suite_id')
            try:
                url = reverse('documentation:postman_test_suite', args=[config_id, suite_id])
            except NoReverseMatch:
                url = reverse('documentation:postman_detail_enhanced', args=[config_id])
        else:
            try:
                # Use new unified route names
                url = reverse(f'documentation:postman_{sub_resource_normalized}', args=[config_id])
            except NoReverseMatch:
                url = reverse('documentation:postman_detail_enhanced', args=[config_id])
    elif config_id:
        url = reverse('documentation:postman_detail_enhanced', args=[config_id])
    else:
        url = reverse('documentation:dashboard')  # Use main dashboard, postman tab
    
    if query_params:
        from urllib.parse import urlencode
        query_string = urlencode(query_params)
        url = f"{url}?{query_string}"
    
    return url


def get_health_url(health_type: Optional[str] = None) -> str:
    """
    Generate URL for Health API views.
    
    Args:
        health_type: Health type (database, cache, storage, external-api) or None for comprehensive health
        
    Returns:
        URL string
    """
    if health_type:
        try:
            # Use new unified route names
            url = reverse(f'documentation:health_{health_type}')
        except NoReverseMatch:
            url = reverse('documentation:health')
    else:
        url = reverse('documentation:health')
    
    return url


def get_index_url(index_type: str, validate: bool = False) -> str:
    """
    Generate URL for Index API views.
    
    Args:
        index_type: Index type (pages, endpoints, relationships, postman)
        validate: Whether to get validation URL
        
    Returns:
        URL string
    """
    if validate:
        try:
            # Use new unified route names
            url = reverse(f'documentation:index_{index_type}_validate')
        except NoReverseMatch:
            url = reverse(f'documentation:index_{index_type}')
    else:
        url = reverse(f'documentation:index_{index_type}')
    
    return url


def build_filter_url(base_url: str, filters: Dict[str, Any]) -> str:
    """
    Build URL with filter query parameters.
    
    Args:
        base_url: Base URL string
        filters: Dictionary of filter parameters
        
    Returns:
        URL string with query parameters
    """
    if not filters:
        return base_url
    
    from urllib.parse import urlencode, urlparse, urlunparse, parse_qs
    
    # Parse existing URL
    parsed = urlparse(base_url)
    existing_params = parse_qs(parsed.query)
    
    # Merge filters with existing params
    for key, value in filters.items():
        if value is not None:
            existing_params[key] = [str(value)]
    
    # Rebuild URL
    new_query = urlencode(existing_params, doseq=True)
    new_parsed = parsed._replace(query=new_query)
    
    return urlunparse(new_parsed)
