"""Graph views."""
import logging
import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages

logger = logging.getLogger(__name__)


@login_required
def graph_view(request):
    """Project graph visualization."""
    from apps.documentation.services.pages_service import PagesService
    from apps.documentation.services.endpoints_service import EndpointsService
    from apps.documentation.services.relationships_service import RelationshipsService
    
    try:
        pages_service = PagesService()
        endpoints_service = EndpointsService()
        relationships_service = RelationshipsService()
        
        # Get pages and endpoints for graph nodes
        pages_result = pages_service.list_pages(limit=200)
        pages = pages_result.get('pages', [])
        
        endpoints_result = endpoints_service.list_endpoints(limit=200)
        endpoints = endpoints_result.get('endpoints', [])
        
        # Build graph nodes
        nodes = []
        for page in pages:
            nodes.append({
                'id': page.get('page_id', ''),
                'label': page.get('title', page.get('page_id', '')),
                'type': 'page',
                'page_type': page.get('page_type', 'docs'),
                'group': 1
            })
        
        for endpoint in endpoints:
            nodes.append({
                'id': endpoint.get('endpoint_id', ''),
                'label': endpoint.get('endpoint_path', endpoint.get('endpoint_id', '')),
                'type': 'endpoint',
                'method': endpoint.get('method', 'QUERY'),
                'group': 2
            })
        
        # Get relationships for edges
        relationships = relationships_service.list_relationships(limit=500)
        edges = []
        for rel in relationships.get('relationships', []):
            edges.append({
                'source': rel.get('page_id', ''),
                'target': rel.get('endpoint_id', ''),
                'type': rel.get('relationship_type', 'references'),
                'value': 1
            })
        
        graph_data = {
            'nodes': nodes,
            'edges': edges,
            'stats': {
                'total_nodes': len(nodes),
                'total_edges': len(edges),
                'pages_count': len([n for n in nodes if n.get('type') == 'page']),
                'endpoints_count': len([n for n in nodes if n.get('type') == 'endpoint'])
            }
        }
        
    except Exception as e:
        logger.error(f"Error loading graph data: {e}", exc_info=True)
        messages.warning(request, 'Some graph data could not be loaded.')
        graph_data = {
            'nodes': [],
            'edges': [],
            'stats': {
                'total_nodes': 0,
                'total_edges': 0,
                'pages_count': 0,
                'endpoints_count': 0
            }
        }
    
    context = {
        'graph_data': json.dumps(graph_data),
        'stats': graph_data.get('stats', {})
    }
    return render(request, 'graph/visualization.html', context)
