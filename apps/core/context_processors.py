"""Context processors for core app."""
import logging
from django.urls import resolve, Resolver404

logger = logging.getLogger(__name__)


from .navigation import SIDEBAR_MENU

def navigation(request):
    """Add navigation context to all templates."""
    try:
        resolver_match = resolve(request.path_info)
        current_url = resolver_match.url_name if resolver_match else None
        current_app = resolver_match.app_name if resolver_match else None
    except Resolver404:
        # URL not found - this is normal for some paths
        current_url = None
        current_app = None
    except Exception as e:
        # Log unexpected errors but don't break the template
        logger.warning(f"Error resolving URL in context processor: {e}", exc_info=True)
        current_url = None
        current_app = None
    
    # Process menu to set active states
    processed_menu = []
    for group in SIDEBAR_MENU:
        group_copy = group.copy()
        group_copy['active'] = False
        
        items_copy = []
        for item in group['items']:
            item_copy = item.copy()
            # Check if this item is active
            # Items can have either app_name/url_name or url
            is_active = False
            if 'app_name' in item and 'url_name' in item:
                # URL-based navigation item
                if item.get('app_name') == current_app and item.get('url_name') == current_url:
                    is_active = True
            elif 'url' in item:
                # Direct URL navigation item - check if current path matches
                if current_url and request.path_info == item.get('url'):
                    is_active = True
            
            item_copy['active'] = is_active
            if is_active:
                group_copy['active'] = True
            items_copy.append(item_copy)
        
        group_copy['items'] = items_copy
        processed_menu.append(group_copy)

    return {
        'current_view': current_url,
        'sidebar_menu': processed_menu,
        'user': request.user if hasattr(request, 'user') else None,
    }


def theme(request):
    """Add theme context to all templates."""
    theme_value = request.session.get('theme', 'light')
    return {
        'theme': theme_value,
    }
