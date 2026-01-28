#!/usr/bin/env python
"""
Script to update template URL names from media_manager_* to new unified route names.
"""

import os
import re
from pathlib import Path

# URL name mappings: old_name -> new_name
URL_MAPPINGS = {
    # Dashboard routes
    'media_manager_dashboard': 'dashboard',
    'media_manager_pages': 'dashboard_pages',
    'media_manager_endpoints': 'dashboard_endpoints',
    'media_manager_relationships': 'dashboard_relationships',
    'media_manager_postman': 'dashboard',  # Use main dashboard with tab
    
    # Page routes
    'media_manager_page_detail': 'page_detail_enhanced',
    'media_manager_page_sections': 'page_sections',
    'media_manager_page_components': 'page_components',
    'media_manager_page_endpoints': 'page_endpoints',
    'media_manager_page_versions': 'page_versions',
    'media_manager_page_access_control': 'page_access_control',
    
    # Pages API routes
    'media_manager_pages_format': 'pages_format',
    'media_manager_pages_statistics': 'pages_statistics',
    'media_manager_pages_types': 'pages_types',
    'media_manager_pages_by_type_docs': 'pages_by_type_docs',
    'media_manager_pages_by_type_marketing': 'pages_by_type_marketing',
    'media_manager_pages_by_type_dashboard': 'pages_by_type_dashboard',
    'media_manager_pages_by_type_published': 'pages_by_type_published',
    'media_manager_pages_by_type_draft': 'pages_by_type_draft',
    'media_manager_pages_by_type_stats': 'pages_by_type_stats',
    'media_manager_pages_by_type_count': 'pages_by_type_count',
    'media_manager_pages_by_state_count': 'pages_by_state_count',
    'media_manager_pages_by_state': 'pages_by_state',
    'media_manager_pages_by_user_type': 'pages_by_user_type',
    
    # Endpoint routes
    'media_manager_endpoint_detail': 'endpoint_detail_enhanced',
    'media_manager_endpoint_pages': 'endpoint_pages',
    'media_manager_endpoint_access_control': 'endpoint_access_control',
    'media_manager_endpoint_lambda_services': 'endpoint_lambda_services',
    'media_manager_endpoint_files': 'endpoint_files',
    'media_manager_endpoint_methods': 'endpoint_methods',
    'media_manager_endpoint_used_by_pages': 'endpoint_used_by_pages',
    'media_manager_endpoint_dependencies': 'endpoint_dependencies',
    
    # Endpoints API routes
    'media_manager_endpoints_format': 'endpoints_format',
    'media_manager_endpoints_statistics': 'endpoints_statistics',
    'media_manager_endpoints_api_versions': 'endpoints_api_versions',
    'media_manager_endpoints_methods': 'endpoints_methods',
    'media_manager_endpoints_by_api_version_v1': 'endpoints_by_api_version_v1',
    'media_manager_endpoints_by_api_version_v4': 'endpoints_by_api_version_v4',
    'media_manager_endpoints_by_api_version_graphql': 'endpoints_by_api_version_graphql',
    'media_manager_endpoints_by_api_version_count': 'endpoints_by_api_version_count',
    'media_manager_endpoints_by_api_version_stats': 'endpoints_by_api_version_stats',
    'media_manager_endpoints_by_api_version_by_method': 'endpoints_by_api_version_by_method',
    'media_manager_endpoints_by_method_get': 'endpoints_by_method_get',
    'media_manager_endpoints_by_method_post': 'endpoints_by_method_post',
    'media_manager_endpoints_by_method_query': 'endpoints_by_method_query',
    'media_manager_endpoints_by_method_mutation': 'endpoints_by_method_mutation',
    'media_manager_endpoints_by_method_count': 'endpoints_by_method_count',
    'media_manager_endpoints_by_method_stats': 'endpoints_by_method_stats',
    'media_manager_endpoints_by_state_count': 'endpoints_by_state_count',
    'media_manager_endpoints_by_state': 'endpoints_by_state',
    'media_manager_endpoints_by_lambda_count': 'endpoints_by_lambda_count',
    'media_manager_endpoints_by_lambda': 'endpoints_by_lambda',
    
    # Relationship routes
    'media_manager_relationship_detail': 'relationship_detail_enhanced',
    'media_manager_relationship_access_control': 'relationship_access_control',
    'media_manager_relationship_data_flow': 'relationship_data_flow',
    'media_manager_relationship_performance': 'relationship_performance',
    'media_manager_relationship_dependencies': 'relationship_dependencies',
    'media_manager_relationship_postman': 'relationship_postman',
    
    # Relationships API routes
    'media_manager_relationships_format': 'relationships_format',
    'media_manager_relationships_statistics': 'relationships_statistics',
    'media_manager_relationships_graph': 'relationships_graph',
    'media_manager_relationships_usage_types': 'relationships_usage_types',
    'media_manager_relationships_usage_contexts': 'relationships_usage_contexts',
    'media_manager_relationships_by_page_primary': 'relationships_by_page_primary',
    'media_manager_relationships_by_page_secondary': 'relationships_by_page_secondary',
    'media_manager_relationships_by_page_count': 'relationships_by_page_count',
    'media_manager_relationships_by_page_by_usage_type': 'relationships_by_page_by_usage_type',
    'media_manager_relationships_by_page': 'relationships_by_page',
    'media_manager_relationships_by_endpoint_pages': 'relationships_by_endpoint_pages',
    'media_manager_relationships_by_endpoint_count': 'relationships_by_endpoint_count',
    'media_manager_relationships_by_endpoint_by_usage_context': 'relationships_by_endpoint_by_usage_context',
    'media_manager_relationships_by_endpoint': 'relationships_by_endpoint',
    'media_manager_relationships_by_usage_type_primary': 'relationships_by_usage_type_primary',
    'media_manager_relationships_by_usage_type_secondary': 'relationships_by_usage_type_secondary',
    'media_manager_relationships_by_usage_type_conditional': 'relationships_by_usage_type_conditional',
    'media_manager_relationships_by_usage_type_count': 'relationships_by_usage_type_count',
    'media_manager_relationships_by_usage_type_by_usage_context': 'relationships_by_usage_type_by_usage_context',
    'media_manager_relationships_by_usage_context_data_fetching': 'relationships_by_usage_context_data_fetching',
    'media_manager_relationships_by_usage_context_data_mutation': 'relationships_by_usage_context_data_mutation',
    'media_manager_relationships_by_usage_context_authentication': 'relationships_by_usage_context_authentication',
    'media_manager_relationships_by_usage_context_analytics': 'relationships_by_usage_context_analytics',
    'media_manager_relationships_by_usage_context_count': 'relationships_by_usage_context_count',
    'media_manager_relationships_by_state_count': 'relationships_by_state_count',
    'media_manager_relationships_by_state': 'relationships_by_state',
    'media_manager_relationships_by_lambda': 'relationships_by_lambda',
    'media_manager_relationships_by_invocation_pattern': 'relationships_by_invocation_pattern',
    'media_manager_relationships_by_postman_config': 'relationships_by_postman_config',
    'media_manager_relationships_performance_slow': 'relationships_performance_slow',
    'media_manager_relationships_performance_errors': 'relationships_performance_errors',
    
    # Postman routes
    'media_manager_postman_detail': 'postman_detail_enhanced',
    'media_manager_postman_collection': 'postman_collection',
    'media_manager_postman_environments': 'postman_environments',
    'media_manager_postman_environment': 'postman_environment',
    'media_manager_postman_mappings': 'postman_mappings',
    'media_manager_postman_mapping': 'postman_mapping',
    'media_manager_postman_test_suites': 'postman_test_suites',
    'media_manager_postman_test_suite': 'postman_test_suite',
    'media_manager_postman_access_control': 'postman_access_control',
    
    # Postman API routes
    'media_manager_postman_format': 'postman_format',
    'media_manager_postman_statistics': 'postman_statistics',
    'media_manager_postman_by_state_count': 'postman_by_state_count',
    'media_manager_postman_by_state': 'postman_by_state',
    
    # Health routes
    'media_manager_health': 'health',
    'media_manager_health_database': 'health_database',
    'media_manager_health_cache': 'health_cache',
    'media_manager_health_storage': 'health_storage',
    'media_manager_health_external_api': 'health_external_api',
    
    # Index routes
    'media_manager_index_pages': 'index_pages',
    'media_manager_index_pages_validate': 'index_pages_validate',
    'media_manager_index_endpoints': 'index_endpoints',
    'media_manager_index_endpoints_validate': 'index_endpoints_validate',
    'media_manager_index_relationships': 'index_relationships',
    'media_manager_index_relationships_validate': 'index_relationships_validate',
    'media_manager_index_postman': 'index_postman',
    'media_manager_index_postman_validate': 'index_postman_validate',
    
    # Service info routes
    'media_manager_service_info': 'service_info',
    'media_manager_docs_endpoint_stats': 'docs_endpoint_stats',
    'media_manager_statistics': 'statistics',
}

def update_template_file(file_path: Path):
    """Update URL names in a single template file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        updated = False
        
        # Pattern to match {% url 'documentation:media_manager_*' %}
        pattern = r"{%\s*url\s+['\"]documentation:(\w+)['\"]"
        
        def replace_url(match):
            old_name = match.group(1)
            if old_name in URL_MAPPINGS:
                new_name = URL_MAPPINGS[old_name]
                return f"{{% url 'documentation:{new_name}'"
            return match.group(0)
        
        content = re.sub(pattern, replace_url, content)
        
        # Also handle patterns with arguments: {% url 'documentation:media_manager_*' arg1 arg2 %}
        pattern_with_args = r"{%\s*url\s+['\"]documentation:(\w+)['\"]\s+([^%}]+)"
        
        def replace_url_with_args(match):
            old_name = match.group(1)
            args = match.group(2)
            if old_name in URL_MAPPINGS:
                new_name = URL_MAPPINGS[old_name]
                return f"{{% url 'documentation:{new_name}' {args}"
            return match.group(0)
        
        content = re.sub(pattern_with_args, replace_url_with_args, content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to update all template files."""
    base_dir = Path(__file__).parent.parent
    templates_dir = base_dir / 'templates' / 'documentation'
    
    if not templates_dir.exists():
        print(f"Templates directory not found: {templates_dir}")
        return
    
    updated_files = []
    total_files = 0
    
    # Process all HTML files
    for html_file in templates_dir.rglob('*.html'):
        total_files += 1
        if update_template_file(html_file):
            updated_files.append(html_file.relative_to(base_dir))
    
    print(f"Processed {total_files} template files")
    print(f"Updated {len(updated_files)} files:")
    for file in updated_files:
        print(f"  - {file}")

if __name__ == '__main__':
    main()
