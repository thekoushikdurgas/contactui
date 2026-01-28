#!/usr/bin/env python
"""
Route Migration Script - Migrate /docs/media-manager/* routes to /docs/*

This script generates a mapping of all route migrations and validates route ordering.
"""

ROUTE_MIGRATIONS = {
    # Health & Service Info (7 routes)
    'media-manager/service-info/': 'service-info/',
    'media-manager/docs/endpoint-stats/': 'docs/endpoint-stats/',
    'media-manager/health/': 'health/',
    'media-manager/health/database/': 'health/database/',
    'media-manager/health/cache/': 'health/cache/',
    'media-manager/health/storage/': 'health/storage/',
    'media-manager/health/external-api/': 'health/external-api/',
    
    # Pages API (20 routes)
    'media-manager/pages/format/': 'pages/format/',
    'media-manager/pages/statistics/': 'pages/statistics/',
    'media-manager/pages/types/': 'pages/types/',
    'media-manager/pages/by-type/docs/': 'pages/by-type/docs/',
    'media-manager/pages/by-type/marketing/': 'pages/by-type/marketing/',
    'media-manager/pages/by-type/dashboard/': 'pages/by-type/dashboard/',
    'media-manager/pages/by-type/<str:page_type>/published/': 'pages/by-type/<str:page_type>/published/',
    'media-manager/pages/by-type/<str:page_type>/draft/': 'pages/by-type/<str:page_type>/draft/',
    'media-manager/pages/by-type/<str:page_type>/stats/': 'pages/by-type/<str:page_type>/stats/',
    'media-manager/pages/by-type/<str:page_type>/count/': 'pages/by-type/<str:page_type>/count/',
    'media-manager/pages/by-state/<str:state>/count/': 'pages/by-state/<str:state>/count/',
    'media-manager/pages/by-state/<str:state>/': 'pages/by-state/<str:state>/',
    'media-manager/pages/by-user-type/<str:user_type>/': 'pages/by-user-type/<str:user_type>/',
    'media-manager/pages/<str:page_id>/sections/': 'pages/<str:page_id>/sections/',
    'media-manager/pages/<str:page_id>/components/': 'pages/<str:page_id>/components/',
    'media-manager/pages/<str:page_id>/endpoints/': 'pages/<str:page_id>/endpoints/',
    'media-manager/pages/<str:page_id>/versions/': 'pages/<str:page_id>/versions/',
    'media-manager/pages/<str:page_id>/access-control/': 'pages/<str:page_id>/access-control/',
    'media-manager/pages/<str:page_id>/': 'pages/<str:page_id>/',
    'media-manager/pages/': 'pages/',  # Tab route - merge with dashboard
    
    # Endpoints API (28 routes)
    'media-manager/endpoints/format/': 'endpoints/format/',
    'media-manager/endpoints/statistics/': 'endpoints/statistics/',
    'media-manager/endpoints/api-versions/': 'endpoints/api-versions/',
    'media-manager/endpoints/methods/': 'endpoints/methods/',
    'media-manager/endpoints/by-api-version/v1/': 'endpoints/by-api-version/v1/',
    'media-manager/endpoints/by-api-version/v4/': 'endpoints/by-api-version/v4/',
    'media-manager/endpoints/by-api-version/graphql/': 'endpoints/by-api-version/graphql/',
    'media-manager/endpoints/by-api-version/<str:api_version>/count/': 'endpoints/by-api-version/<str:api_version>/count/',
    'media-manager/endpoints/by-api-version/<str:api_version>/stats/': 'endpoints/by-api-version/<str:api_version>/stats/',
    'media-manager/endpoints/by-api-version/<str:api_version>/by-method/<str:method>/': 'endpoints/by-api-version/<str:api_version>/by-method/<str:method>/',
    'media-manager/endpoints/by-method/GET/': 'endpoints/by-method/GET/',
    'media-manager/endpoints/by-method/POST/': 'endpoints/by-method/POST/',
    'media-manager/endpoints/by-method/QUERY/': 'endpoints/by-method/QUERY/',
    'media-manager/endpoints/by-method/MUTATION/': 'endpoints/by-method/MUTATION/',
    'media-manager/endpoints/by-method/<str:method>/count/': 'endpoints/by-method/<str:method>/count/',
    'media-manager/endpoints/by-method/<str:method>/stats/': 'endpoints/by-method/<str:method>/stats/',
    'media-manager/endpoints/by-state/<str:state>/count/': 'endpoints/by-state/<str:state>/count/',
    'media-manager/endpoints/by-state/<str:state>/': 'endpoints/by-state/<str:state>/',
    'media-manager/endpoints/by-lambda/<str:service_name>/count/': 'endpoints/by-lambda/<str:service_name>/count/',
    'media-manager/endpoints/by-lambda/<str:service_name>/': 'endpoints/by-lambda/<str:service_name>/',
    'media-manager/endpoints/<str:endpoint_id>/pages/': 'endpoints/<str:endpoint_id>/pages/',
    'media-manager/endpoints/<str:endpoint_id>/access-control/': 'endpoints/<str:endpoint_id>/access-control/',
    'media-manager/endpoints/<str:endpoint_id>/lambda-services/': 'endpoints/<str:endpoint_id>/lambda-services/',
    'media-manager/endpoints/<str:endpoint_id>/files/': 'endpoints/<str:endpoint_id>/files/',
    'media-manager/endpoints/<str:endpoint_id>/methods/': 'endpoints/<str:endpoint_id>/methods/',
    'media-manager/endpoints/<str:endpoint_id>/used-by-pages/': 'endpoints/<str:endpoint_id>/used-by-pages/',
    'media-manager/endpoints/<str:endpoint_id>/dependencies/': 'endpoints/<str:endpoint_id>/dependencies/',
    'media-manager/endpoints/<str:endpoint_id>/': 'endpoints/<str:endpoint_id>/',
    'media-manager/endpoints/': 'endpoints/',  # Tab route - merge with dashboard
    
    # Relationships API (38 routes)
    'media-manager/relationships/format/': 'relationships/format/',
    'media-manager/relationships/statistics/': 'relationships/statistics/',
    'media-manager/relationships/graph/': 'relationships/graph/',
    'media-manager/relationships/usage-types/': 'relationships/usage-types/',
    'media-manager/relationships/usage-contexts/': 'relationships/usage-contexts/',
    'media-manager/relationships/by-page/<str:page_id>/primary/': 'relationships/by-page/<str:page_id>/primary/',
    'media-manager/relationships/by-page/<str:page_id>/secondary/': 'relationships/by-page/<str:page_id>/secondary/',
    'media-manager/relationships/by-page/<str:page_id>/count/': 'relationships/by-page/<str:page_id>/count/',
    'media-manager/relationships/by-page/<str:page_id>/by-usage-type/<str:usage_type>/': 'relationships/by-page/<str:page_id>/by-usage-type/<str:usage_type>/',
    'media-manager/relationships/by-page/<str:page_id>/': 'relationships/by-page/<str:page_id>/',
    'media-manager/relationships/by-endpoint/<str:endpoint_id>/pages/': 'relationships/by-endpoint/<str:endpoint_id>/pages/',
    'media-manager/relationships/by-endpoint/<str:endpoint_id>/count/': 'relationships/by-endpoint/<str:endpoint_id>/count/',
    'media-manager/relationships/by-endpoint/<str:endpoint_id>/by-usage-context/<str:usage_context>/': 'relationships/by-endpoint/<str:endpoint_id>/by-usage-context/<str:usage_context>/',
    'media-manager/relationships/by-endpoint/<str:endpoint_id>/': 'relationships/by-endpoint/<str:endpoint_id>/',
    'media-manager/relationships/by-usage-type/primary/': 'relationships/by-usage-type/primary/',
    'media-manager/relationships/by-usage-type/secondary/': 'relationships/by-usage-type/secondary/',
    'media-manager/relationships/by-usage-type/conditional/': 'relationships/by-usage-type/conditional/',
    'media-manager/relationships/by-usage-type/<str:usage_type>/count/': 'relationships/by-usage-type/<str:usage_type>/count/',
    'media-manager/relationships/by-usage-type/<str:usage_type>/by-usage-context/<str:usage_context>/': 'relationships/by-usage-type/<str:usage_type>/by-usage-context/<str:usage_context>/',
    'media-manager/relationships/by-usage-context/data_fetching/': 'relationships/by-usage-context/data_fetching/',
    'media-manager/relationships/by-usage-context/data_mutation/': 'relationships/by-usage-context/data_mutation/',
    'media-manager/relationships/by-usage-context/authentication/': 'relationships/by-usage-context/authentication/',
    'media-manager/relationships/by-usage-context/analytics/': 'relationships/by-usage-context/analytics/',
    'media-manager/relationships/by-usage-context/<str:usage_context>/count/': 'relationships/by-usage-context/<str:usage_context>/count/',
    'media-manager/relationships/by-state/<str:state>/count/': 'relationships/by-state/<str:state>/count/',
    'media-manager/relationships/by-state/<str:state>/': 'relationships/by-state/<str:state>/',
    'media-manager/relationships/by-lambda/<str:service_name>/': 'relationships/by-lambda/<str:service_name>/',
    'media-manager/relationships/by-invocation-pattern/<str:pattern>/': 'relationships/by-invocation-pattern/<str:pattern>/',
    'media-manager/relationships/by-postman-config/<str:config_id>/': 'relationships/by-postman-config/<str:config_id>/',
    'media-manager/relationships/performance/slow/': 'relationships/performance/slow/',
    'media-manager/relationships/performance/errors/': 'relationships/performance/errors/',
    'media-manager/relationships/<str:relationship_id>/access-control/': 'relationships/<str:relationship_id>/access-control/',
    'media-manager/relationships/<str:relationship_id>/data-flow/': 'relationships/<str:relationship_id>/data-flow/',
    'media-manager/relationships/<str:relationship_id>/performance/': 'relationships/<str:relationship_id>/performance/',
    'media-manager/relationships/<str:relationship_id>/dependencies/': 'relationships/<str:relationship_id>/dependencies/',
    'media-manager/relationships/<str:relationship_id>/postman/': 'relationships/<str:relationship_id>/postman/',
    'media-manager/relationships/<str:relationship_id>/': 'relationships/<str:relationship_id>/',
    'media-manager/relationships/': 'relationships/',  # Tab route - merge with dashboard
    
    # Postman API (14 routes)
    'media-manager/postman/format/': 'postman/format/',
    'media-manager/postman/statistics/': 'postman/statistics/',
    'media-manager/postman/by-state/<str:state>/count/': 'postman/by-state/<str:state>/count/',
    'media-manager/postman/by-state/<str:state>/': 'postman/by-state/<str:state>/',
    'media-manager/postman/<str:config_id>/collection/': 'postman/<str:config_id>/collection/',
    'media-manager/postman/<str:config_id>/environments/<str:env_name>/': 'postman/<str:config_id>/environments/<str:env_name>/',
    'media-manager/postman/<str:config_id>/environments/': 'postman/<str:config_id>/environments/',
    'media-manager/postman/<str:config_id>/mappings/<str:mapping_id>/': 'postman/<str:config_id>/mappings/<str:mapping_id>/',
    'media-manager/postman/<str:config_id>/mappings/': 'postman/<str:config_id>/mappings/',
    'media-manager/postman/<str:config_id>/test-suites/<str:suite_id>/': 'postman/<str:config_id>/test-suites/<str:suite_id>/',
    'media-manager/postman/<str:config_id>/test-suites/': 'postman/<str:config_id>/test-suites/',
    'media-manager/postman/<str:config_id>/access-control/': 'postman/<str:config_id>/access-control/',
    'media-manager/postman/<str:config_id>/': 'postman/<str:config_id>/',
    'media-manager/postman/': 'postman/',  # Tab route - merge with dashboard
    
    # Index API (8 routes)
    'media-manager/index/pages/validate/': 'index/pages/validate/',
    'media-manager/index/endpoints/validate/': 'index/endpoints/validate/',
    'media-manager/index/relationships/validate/': 'index/relationships/validate/',
    'media-manager/index/postman/validate/': 'index/postman/validate/',
    'media-manager/index/pages/': 'index/pages/',
    'media-manager/index/endpoints/': 'index/endpoints/',
    'media-manager/index/relationships/': 'index/relationships/',
    'media-manager/index/postman/': 'index/postman/',
    
    # Dashboard API (4 routes)
    'media-manager/dashboard/pages/': 'dashboard/pages/',
    'media-manager/dashboard/endpoints/': 'dashboard/endpoints/',
    'media-manager/dashboard/relationships/': 'dashboard/relationships/',
    'media-manager/dashboard/postman/': 'dashboard/postman/',
    
    # Statistics (1 route)
    'media-manager/statistics/': 'statistics/',
}

def generate_route_mapping():
    """Generate route mapping documentation."""
    print("=" * 80)
    print("ROUTE MIGRATION MAPPING")
    print("=" * 80)
    print(f"\nTotal routes to migrate: {len(ROUTE_MIGRATIONS)}\n")
    
    categories = {
        'Health & Service Info': [],
        'Pages API': [],
        'Endpoints API': [],
        'Relationships API': [],
        'Postman API': [],
        'Index API': [],
        'Dashboard API': [],
        'Statistics': [],
    }
    
    for old, new in ROUTE_MIGRATIONS.items():
        if 'health' in old or 'service-info' in old or 'docs/endpoint-stats' in old:
            categories['Health & Service Info'].append((old, new))
        elif 'pages' in old and 'relationship' not in old:
            categories['Pages API'].append((old, new))
        elif 'endpoints' in old:
            categories['Endpoints API'].append((old, new))
        elif 'relationships' in old:
            categories['Relationships API'].append((old, new))
        elif 'postman' in old:
            categories['Postman API'].append((old, new))
        elif 'index' in old:
            categories['Index API'].append((old, new))
        elif 'dashboard' in old:
            categories['Dashboard API'].append((old, new))
        elif 'statistics' in old:
            categories['Statistics'].append((old, new))
    
    for category, routes in categories.items():
        if routes:
            print(f"\n{category} ({len(routes)} routes):")
            print("-" * 80)
            for old, new in routes:
                print(f"  {old:60} → {new}")

if __name__ == '__main__':
    generate_route_mapping()
