"""Templates views."""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
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
