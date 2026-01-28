"""JSON Store views."""
import logging
from django.shortcuts import render
from apps.core.decorators.auth import require_super_admin
from apps.json_store.services.json_store_storage_service import JSONStoreStorageService

logger = logging.getLogger(__name__)


@require_super_admin
def list_json_view(request):
    """List all JSON store entries."""
    storage = JSONStoreStorageService()
    
    try:
        # Get user UUID for filtering (optional)
        user_uuid = None
        if hasattr(request, 'appointment360_user'):
            user_uuid = request.appointment360_user.get('uuid')
        
        # List all stores
        result = storage.list_stores(limit=100, offset=0)
        stores = result.get('items', [])
        
        entries = []
        for store in stores:
            entries.append({
                'key': store.get('key', ''),
                'data': store.get('data', {}),
                'type': store.get('type', 'custom'),
                'description': store.get('description', ''),
                'size': len(str(store.get('data', {}))),
                'created_at': store.get('created_at', ''),
            })
    except Exception as e:
        entries = []
        logger.error(f"Error listing JSON stores: {e}", exc_info=True)
    
    context = {
        'entries': entries,
        'total': len(entries)
    }
    return render(request, 'json_store/list.html', context)
