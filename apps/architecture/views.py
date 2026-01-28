"""Architecture views."""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def architecture_view(request):
    """Architecture blueprint view."""
    from apps.documentation.services.pages_service import PagesService
    from apps.documentation.services.endpoints_service import EndpointsService
    import json
    
    pages_service = PagesService()
    endpoints_service = EndpointsService()
    
    try:
        # Get architecture data
        pages_result = pages_service.list_pages(page_type='architecture', limit=50)
        pages = pages_result.get('pages', [])
        
        endpoints_result = endpoints_service.list_endpoints(limit=50)
        endpoints = endpoints_result.get('endpoints', [])
        
        architecture_data = {
            'components': pages,
            'apis': endpoints,
            'layers': []
        }
    except Exception:
        architecture_data = {
            'components': [],
            'apis': [],
            'layers': []
        }
    
    context = {
        'architecture_data': json.dumps(architecture_data)
    }
    return render(request, 'architecture/blueprint.html', context)
