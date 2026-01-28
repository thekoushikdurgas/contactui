"""Context processors for core app."""
import logging
from django.urls import resolve, Resolver404, reverse
from django.urls.exceptions import NoReverseMatch

logger = logging.getLogger(__name__)


from .navigation import SIDEBAR_MENU


def _is_item_active(item, current_app, current_url, request_path):
    """Check if a navigation item is active based on current route."""
    is_active = False
    
    # Check URL-based navigation item
    if 'app_name' in item and 'url_name' in item:
        if item.get('app_name') == current_app and item.get('url_name') == current_url:
            is_active = True
        # Also check for parameterized routes (e.g., edit/delete forms)
        elif current_app == item.get('app_name'):
            # Check if current URL matches pattern (e.g., page_edit, endpoint_create)
            url_name = item.get('url_name', '')
            if url_name in current_url or current_url in url_name:
                # More specific check for forms
                if 'create' in url_name and 'create' in current_url:
                    is_active = True
                elif 'edit' in url_name and 'edit' in current_url:
                    is_active = True
                elif 'delete' in url_name and 'delete' in current_url:
                    is_active = True
    
    # Check direct URL navigation item
    elif 'url' in item:
        if request_path == item.get('url'):
            is_active = True
    
    return is_active


def _process_item_children(children, current_app, current_url, request_path, parent_active=False):
    """Recursively process nested children items."""
    if not children:
        return []
    
    processed_children = []
    has_active_child = False
    
    for child in children:
        child_copy = child.copy()
        child_active = _is_item_active(child, current_app, current_url, request_path)
        
        # Process nested children if they exist
        if 'children' in child:
            child_copy['children'] = _process_item_children(
                child.get('children', []),
                current_app,
                current_url,
                request_path,
                child_active
            )
            # Check if any nested child is active
            child_active = child_active or any(
                c.get('active', False) for c in child_copy['children']
            )
        
        child_copy['active'] = child_active
        if child_active:
            has_active_child = True
        
        # Add return URL for create forms
        if child_copy.get('page_type') == 'static' and child_copy.get('access_via') == 'via_list':
            if 'app_name' in child_copy and 'url_name' in child_copy:
                try:
                    # Generate return URL pointing to list page
                    parent_url = reverse(f"{current_app}:{current_url}") if current_app and current_url else None
                    if parent_url:
                        # Build the form URL
                        app_name = child_copy['app_name']
                        url_name = child_copy['url_name']
                        form_url = reverse(f"{app_name}:{url_name}")
                        child_copy['url_with_return'] = f"{form_url}?return_url={parent_url}"
                except (NoReverseMatch, Exception) as e:
                    logger.debug(f"Could not generate return URL for {child_copy.get('label')}: {e}")
                    child_copy['url_with_return'] = None
        
        processed_children.append(child_copy)
    
    return processed_children


def navigation(request):
    """Add navigation context to all templates with nested item support."""
    try:
        resolver_match = resolve(request.path_info)
        current_url = resolver_match.url_name if resolver_match else None
        current_app = resolver_match.app_name if resolver_match else None
        request_path = request.path_info
    except Resolver404:
        # URL not found - this is normal for some paths
        current_url = None
        current_app = None
        request_path = request.path_info
    except Exception as e:
        # Log unexpected errors but don't break the template
        logger.warning(f"Error resolving URL in context processor: {e}", exc_info=True)
        current_url = None
        current_app = None
        request_path = request.path_info
    
    # Process menu to set active states (with nested support)
    processed_menu = []
    for group in SIDEBAR_MENU:
        group_copy = group.copy()
        group_copy['active'] = False
        
        items_copy = []
        for item in group['items']:
            item_copy = item.copy()
            
            # Check if this item is active
            is_active = _is_item_active(item, current_app, current_url, request_path)
            
            # Process children if they exist
            if 'children' in item:
                item_copy['children'] = _process_item_children(
                    item.get('children', []),
                    current_app,
                    current_url,
                    request_path,
                    is_active
                )
                # If any child is active, parent is also active
                has_active_child = any(c.get('active', False) for c in item_copy['children'])
                if has_active_child:
                    is_active = True
                    # Auto-expand parent when child is active
                    item_copy['expanded'] = True
            
            item_copy['active'] = is_active
            if is_active:
                group_copy['active'] = True
                # Auto-expand group when item is active
                group_copy['expanded'] = True
            
            items_copy.append(item_copy)
        
        group_copy['items'] = items_copy
        processed_menu.append(group_copy)

    return {
        'current_view': current_url,
        'current_app': current_app,
        'sidebar_menu': processed_menu,
        'user': request.user if hasattr(request, 'user') else None,
    }


def theme(request):
    """Add theme context to all templates."""
    theme_value = request.session.get('theme', 'light')
    return {
        'theme': theme_value,
    }
