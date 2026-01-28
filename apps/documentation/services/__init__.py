"""Documentation services package."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.documentation.repositories.unified_storage import UnifiedStorage
    from apps.documentation.repositories.local_json_storage import LocalJSONStorage
    from apps.documentation.repositories.s3_json_storage import S3JSONStorage

# Shared storage instances for all services to use
# This reduces redundant instantiation and allows services to share the same storage
_shared_unified_storage = None
_shared_local_storage = None
_shared_s3_storage = None
_shared_s3_index_manager = None


def get_shared_local_storage():
    """Get or create shared LocalJSONStorage instance."""
    global _shared_local_storage
    if _shared_local_storage is None:
        from apps.documentation.repositories.local_json_storage import LocalJSONStorage
        _shared_local_storage = LocalJSONStorage()
    return _shared_local_storage


def get_shared_s3_storage():
    """Get or create shared S3JSONStorage instance."""
    global _shared_s3_storage
    if _shared_s3_storage is None:
        from apps.documentation.repositories.s3_json_storage import S3JSONStorage
        _shared_s3_storage = S3JSONStorage()
    return _shared_s3_storage


def get_shared_s3_index_manager():
    """Get or create shared S3IndexManager instance."""
    global _shared_s3_index_manager
    if _shared_s3_index_manager is None:
        from apps.documentation.utils.s3_index_manager import S3IndexManager
        _shared_s3_index_manager = S3IndexManager(storage=get_shared_s3_storage())
    return _shared_s3_index_manager


def get_shared_unified_storage():
    """Get or create shared UnifiedStorage instance."""
    global _shared_unified_storage
    if _shared_unified_storage is None:
        from apps.documentation.repositories.unified_storage import UnifiedStorage
        _shared_unified_storage = UnifiedStorage(
            local_storage=get_shared_local_storage(),
            s3_storage=get_shared_s3_storage()
        )
    return _shared_unified_storage


# Module-level service instances for reuse across views
# These are stateless and thread-safe, so they can be safely shared
_pages_service = None
_endpoints_service = None
_relationships_service = None
_postman_service = None


def get_pages_service():
    """Get or create shared PagesService instance."""
    global _pages_service
    if _pages_service is None:
        from apps.documentation.services.pages_service import PagesService
        _pages_service = PagesService(unified_storage=get_shared_unified_storage())
    return _pages_service


def get_endpoints_service():
    """Get or create shared EndpointsService instance."""
    global _endpoints_service
    if _endpoints_service is None:
        from apps.documentation.services.endpoints_service import EndpointsService
        _endpoints_service = EndpointsService(unified_storage=get_shared_unified_storage())
    return _endpoints_service


def get_relationships_service():
    """Get or create shared RelationshipsService instance."""
    global _relationships_service
    if _relationships_service is None:
        from apps.documentation.services.relationships_service import RelationshipsService
        _relationships_service = RelationshipsService(unified_storage=get_shared_unified_storage())
    return _relationships_service


def get_postman_service():
    """Get or create shared PostmanService instance."""
    global _postman_service
    if _postman_service is None:
        from apps.documentation.services.postman_service import PostmanService
        _postman_service = PostmanService(unified_storage=get_shared_unified_storage())
    return _postman_service


# Convenience module-level instances for direct import
# These use lazy initialization via the getter functions above
class _LazyService:
    """Lazy service wrapper that initializes on first access."""
    def __init__(self, getter):
        self._getter = getter
        self._instance = None
    
    def __getattr__(self, name):
        if self._instance is None:
            self._instance = self._getter()
        return getattr(self._instance, name)


# Export lazy service instances
pages_service = _LazyService(get_pages_service)
endpoints_service = _LazyService(get_endpoints_service)
relationships_service = _LazyService(get_relationships_service)
postman_service = _LazyService(get_postman_service)


# Media Manager Dashboard Service
_media_manager_dashboard_service = None


def get_media_manager_dashboard_service():
    """Get or create shared MediaManagerDashboardService instance."""
    global _media_manager_dashboard_service
    if _media_manager_dashboard_service is None:
        from apps.documentation.services.media_manager_dashboard_service import MediaManagerDashboardService
        _media_manager_dashboard_service = MediaManagerDashboardService()
    return _media_manager_dashboard_service
