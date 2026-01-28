"""Documentation views - export all views."""

from .dashboard import (
    documentation_dashboard,
    health_status_api,
    dashboard_stats_api,
)
from .pages_views import (
    page_list_view,
    page_detail_view,
    page_form_view,
    page_create_api,
    page_update_api,
    page_delete_api,
)
from .endpoints_views import (
    endpoint_list_view,
    endpoint_detail_view,
    endpoint_form_view,
    endpoint_create_api,
    endpoint_update_api,
    endpoint_delete_api,
)
from .relationships_views import (
    relationship_list_view,
    relationship_detail_view,
    relationship_form_view,
    relationship_create_api,
    relationship_update_api,
    relationship_delete_api,
)
from .postman_views import (
    postman_detail_view,
    postman_form_view,
)

# Legacy views are imported directly in urls.py to avoid circular imports
# They are not exported from this package to prevent import conflicts

# Export all views for backward compatibility
__all__ = [
    # Dashboard
    'documentation_dashboard',
    'health_status_api',
    'dashboard_stats_api',
    # Pages
    'page_list_view',
    'page_detail_view',
    'page_form_view',
    'page_create_api',
    'page_update_api',
    'page_delete_api',
    # Endpoints
    'endpoint_list_view',
    'endpoint_detail_view',
    'endpoint_form_view',
    'endpoint_create_api',
    'endpoint_update_api',
    'endpoint_delete_api',
    # Relationships
    'relationship_list_view',
    'relationship_detail_view',
    'relationship_form_view',
    'relationship_create_api',
    'relationship_update_api',
    'relationship_delete_api',
    # Postman
    'postman_detail_view',
    'postman_form_view',
    # Legacy views (from parent views.py)
    'list_pages_view',
    'get_page_view',
    'create_page_view',
    'update_page_view',
    'delete_page_view',
]
