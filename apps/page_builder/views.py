"""Page Builder views."""
from django.shortcuts import render
from apps.core.decorators.auth import require_super_admin


@require_super_admin
def page_builder_view(request):
    """Visual page builder."""
    from apps.documentation.services.pages_service import PagesService
    
    page_id = request.GET.get('page_id')
    page_data = None
    
    if page_id:
        pages_service = PagesService()
        page_data = pages_service.get_page(page_id)
    
    context = {
        'page_id': page_id,
        'page_data': page_data,
        'components': [
            {'type': 'text', 'name': 'Text Block'},
            {'type': 'image', 'name': 'Image'},
            {'type': 'code', 'name': 'Code Block'},
            {'type': 'table', 'name': 'Table'}
        ]
    }
    return render(request, 'page_builder/editor.html', context)
