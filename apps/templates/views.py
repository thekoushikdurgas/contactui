"""Templates views."""
from django.shortcuts import render
from apps.core.decorators.auth import require_super_admin


@require_super_admin
def list_templates_view(request):
    """List all documentation templates."""
    context = {
        'templates': [
            {
                'id': 'api-doc',
                'name': 'API Documentation',
                'description': 'Template for API endpoint documentation',
                'category': 'api'
            },
            {
                'id': 'guide',
                'name': 'User Guide',
                'description': 'Template for user guides and tutorials',
                'category': 'guide'
            },
            {
                'id': 'reference',
                'name': 'Reference Documentation',
                'description': 'Template for reference documentation',
                'category': 'reference'
            }
        ]
    }
    return render(request, 'templates/list.html', context)
