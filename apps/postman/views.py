"""Postman views."""
import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from apps.documentation.services.endpoints_service import EndpointsService
from apps.ai_agent.services.postman_parser import PostmanCollectionParser
from apps.ai_agent.services.media_loader import MediaFileLoaderService

logger = logging.getLogger(__name__)


@login_required
def postman_dashboard(request):
    """Enhanced Postman API client dashboard - replaces React component."""
    endpoints_service = EndpointsService()
    media_loader = MediaFileLoaderService()
    postman_parser = PostmanCollectionParser(media_loader)

    try:
        # Get endpoints for API testing
        endpoints_result = endpoints_service.list_endpoints(limit=50)
        endpoints = endpoints_result.get('endpoints', [])
    except Exception as e:
        logger.error(f"Error loading endpoints: {e}")
        endpoints = []

    try:
        # Load Postman collections from local files
        collections = postman_parser.parse_collections()
    except Exception as e:
        logger.error(f"Error loading Postman collections: {e}")
        collections = []

    context = {
        'endpoints': endpoints,
        'collections': collections,
        'recent_requests': []
    }
    return render(request, 'postman/dashboard_enhanced.html', context)


@login_required
def postman_homepage(request):
    """Postman homepage."""
    return render(request, 'postman/homepage.html')
