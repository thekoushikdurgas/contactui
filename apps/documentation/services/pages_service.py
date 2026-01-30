"""Pages Service with multi-strategy pattern (Local → S3 → GraphQL/Lambda)."""

import logging
from typing import Optional, Dict, Any, List
from django.conf import settings
from apps.documentation.services.base import DocumentationServiceBase
from apps.documentation.repositories.unified_storage import UnifiedStorage
from apps.documentation.repositories.pages_repository import PagesRepository
from apps.documentation.utils.retry import retry_on_network_error
from apps.documentation.utils.exceptions import DocumentationError

logger = logging.getLogger(__name__)


class PagesService(DocumentationServiceBase):
    """Service for pages operations with multi-strategy pattern using UnifiedStorage."""
    
    def __init__(
        self,
        unified_storage: Optional[UnifiedStorage] = None,
        repository: Optional[PagesRepository] = None
    ):
        """Initialize pages service.
        
        Args:
            unified_storage: Optional UnifiedStorage instance. If not provided, creates new one.
            repository: Optional PagesRepository instance. If not provided, creates new one.
        """
        # Initialize base class with common patterns (Task 2.3.2)
        super().__init__(
            service_name="PagesService",
            unified_storage=unified_storage,
            repository=repository or PagesRepository(),
            resource_name="pages"
        )
        # Get graphql_service from unified_storage if available
        self.graphql_service = getattr(self.unified_storage, 'graphql_service', None)
    
    def get_page(
        self,
        page_id: str,
        page_type: Optional[str] = None,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get a single page with multi-strategy:
        1. Try Local JSON files
        2. Fallback to S3
        3. Fallback to GraphQL
        
        Uses DocumentationServiceBase._get_resource() for common patterns (Task 2.3.2).
        
        Args:
            page_id: Page identifier
            page_type: Optional page type filter
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Page data dictionary or None if not found
            
        Raises:
            DocumentationError: If retrieval fails after retries
        """
        return self._get_resource(
            resource_id=page_id,
            operation_name='get_page',
            storage_method='get_page',
            use_cache=use_cache,
            page_type=page_type
        )
    
    def list_pages(
        self,
        page_type: Optional[str] = None,
        include_drafts: bool = True,
        include_deleted: bool = False,
        status: Optional[str] = None,
        page_state: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        List pages with multi-strategy:
        1. Try Local JSON files
        2. Fallback to S3
        3. Fallback to GraphQL
        
        Uses DocumentationServiceBase._list_resources() for common patterns (Task 2.3.2).
        
        Args:
            page_type: Optional page type filter
            include_drafts: Whether to include draft pages (default: True)
            include_deleted: Whether to include deleted pages (default: False)
            status: Optional status filter
            page_state: Optional page state filter
            limit: Maximum number of results
            offset: Number of results to skip
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Dictionary with 'pages' list and 'total' count
            
        Raises:
            DocumentationError: If retrieval fails after retries
        """
        return self._list_resources(
            operation_name='list_pages',
            storage_method='list_pages',
            use_cache=use_cache,
            page_type=page_type,
            include_drafts=include_drafts,
            include_deleted=include_deleted,
            status=status,
            page_state=page_state,
            limit=limit,
            offset=offset
        )

    def get_page_by_id(
        self,
        page_id: str,
        page_type: Optional[str] = None,
        use_cache: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Alias for get_page for Lambda API parity."""
        return self.get_page(page_id=page_id, page_type=page_type, use_cache=use_cache)

    def get_pages_by_type(
        self,
        page_type: str,
        status: Optional[str] = None,
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        """Get all pages for a specific page type, optionally filtered by status."""
        result = self.list_pages(
            page_type=page_type,
            status=status,
            limit=None,
            offset=0,
            use_cache=use_cache,
        )
        return result.get("pages", [])

    def count_pages_by_type(self, page_type: str) -> int:
        """Count pages by type."""
        try:
            return self.unified_storage.count_pages_by_type(page_type)
        except Exception as e:
            self.logger.warning(f"count_pages_by_type failed: {e}")
            result = self.list_pages(page_type=page_type, limit=None, offset=0)
            return result.get("total", 0)

    def get_type_statistics(self) -> Dict[str, Any]:
        """Get statistics for all page types (docs, marketing, dashboard)."""
        return self.unified_storage.get_type_statistics()

    def list_pages_by_user_type(
        self,
        user_type: str,
        page_type: Optional[str] = None,
        include_drafts: bool = True,
        include_deleted: bool = False,
        status: Optional[str] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """List pages accessible by user_type based on access_control.can_view."""
        return self.unified_storage.list_pages_by_user_type(
            user_type=user_type,
            page_type=page_type,
            include_drafts=include_drafts,
            include_deleted=include_deleted,
            status=status,
        )

    def get_page_access_control(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get access_control sub-resource for a page. Returns None if page not found."""
        page = self.get_page(page_id)
        if not page:
            return None
        return page.get("access_control")

    def get_page_sections(self, page_id: str) -> Optional[Any]:
        """Get sections/content_sections sub-resource for a page."""
        page = self.get_page(page_id)
        if not page:
            return None
        return page.get("sections") or (page.get("metadata") or {}).get("content_sections")

    def get_page_components(self, page_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get ui_components sub-resource for a page."""
        page = self.get_page(page_id)
        if not page:
            return None
        return (page.get("metadata") or {}).get("ui_components")

    def get_page_endpoints(self, page_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get uses_endpoints sub-resource for a page."""
        page = self.get_page(page_id)
        if not page:
            return None
        return (page.get("metadata") or {}).get("uses_endpoints")

    def get_page_versions(self, page_id: str) -> Optional[List[Any]]:
        """Get versions sub-resource for a page."""
        page = self.get_page(page_id)
        if not page:
            return None
        return (page.get("metadata") or {}).get("versions")
    
    def get_pages_by_state(
        self,
        state: str,
        page_type: Optional[str] = None,
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get all pages filtered by state (published, draft, etc.).
        
        Args:
            state: Page state filter (published, draft, coming_soon, development, test)
            page_type: Optional page type filter
            use_cache: Whether to use cache (default: True)
            
        Returns:
            List of page dictionaries matching the state
            
        Raises:
            DocumentationError: If retrieval fails after retries
        """
        result = self.list_pages(
            page_type=page_type,
            page_state=state,
            limit=None,
            offset=0,
            use_cache=use_cache,
        )
        return result.get("pages", [])
    
    def count_pages_by_state(self, state: str, page_type: Optional[str] = None) -> int:
        """
        Count pages by state.
        
        Args:
            state: Page state filter (published, draft, coming_soon, development, test)
            page_type: Optional page type filter
            
        Returns:
            Number of pages matching the state
        """
        try:
            result = self.list_pages(
                page_type=page_type,
                page_state=state,
                limit=None,
                offset=0,
                use_cache=True,
            )
            return result.get("total", 0)
        except Exception as e:
            self.logger.warning(f"count_pages_by_state failed: {e}")
            return 0
    
    def get_pages_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive pages statistics matching /api/v1/pages/statistics/.
        
        Returns:
            Dictionary with comprehensive statistics including:
            - total: Total number of pages
            - version: Index version
            - last_updated: Last update timestamp
            - statistics: Breakdown by type, state, etc.
            - indexes: Index structure
        """
        try:
            # Get type statistics
            type_stats = self.get_type_statistics()
            
            # Get all pages for state breakdown
            all_pages_result = self.list_pages(limit=None, offset=0, use_cache=True)
            all_pages = all_pages_result.get("pages", [])
            
            # Calculate state breakdown
            by_state = {}
            by_type = {}
            total_with_endpoints = 0
            
            for page in all_pages:
                # Count by state
                metadata = page.get("metadata", {})
                state = metadata.get("page_state") or metadata.get("status", "published")
                by_state[state] = by_state.get(state, 0) + 1
                
                # Count by type
                page_type = page.get("page_type", "docs")
                by_type[page_type] = by_type.get(page_type, 0) + 1
                
                # Count pages with endpoints
                uses_endpoints = metadata.get("uses_endpoints", [])
                if uses_endpoints and len(uses_endpoints) > 0:
                    total_with_endpoints += 1
            
            # Get index data for version and last_updated
            try:
                from apps.documentation.services import get_shared_s3_index_manager
                index_manager = get_shared_s3_index_manager()
                index_data = index_manager.read_index("pages")
                version = index_data.get("version", "1.0.0")
                last_updated = index_data.get("last_updated")
                indexes = index_data.get("indexes", {})
            except Exception as e:
                self.logger.warning(f"Failed to get index data: {e}")
                version = "1.0.0"
                last_updated = None
                indexes = {}
            
            return {
                "total": len(all_pages),
                "version": version,
                "last_updated": last_updated,
                "statistics": {
                    "by_type": by_type,
                    "by_state": by_state,
                    "total_with_endpoints": total_with_endpoints,
                },
                "indexes": indexes,
            }
        except Exception as e:
            error_response = self._handle_error(
                e,
                context="Failed to get pages statistics",
                record_monitoring=True
            )
            raise DocumentationError(
                f"Failed to get pages statistics: {error_response.get('error', str(e))}"
            ) from e
    
    def create_page(self, page_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create page with data transformation.
        Lambda API is read-only, so we use S3 direct for writes.
        
        Uses DocumentationServiceBase patterns with specialized data transformation (Task 2.3.4).
        
        Args:
            page_data: Page data dictionary in Django format
            
        Returns:
            Created page data dictionary or None if creation failed
            
        Raises:
            ValueError: If page data is invalid
            DocumentationError: If creation fails after retries
        """
        from apps.documentation.utils.data_transformers import DataTransformer
        
        # Validate required fields
        required_fields = ['page_id', 'title']
        is_valid, error_msg = self._validate_input(page_data, required_fields)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Transform Django format to Lambda API format (specialized logic)
        try:
            lambda_data = DataTransformer.django_to_lambda_page(page_data)
        except Exception as e:
            self.logger.error(f"Data transformation error in create_page: {e}", exc_info=True)
            raise ValueError(f"Invalid page data: {e}") from e
        
        # Use base class method with transformed data
        try:
            result = self._create_resource(
                resource_data=lambda_data,
                operation_name='create_page'
            )
            
            # Additional cache clearing if needed (base class already handles this)
            if result:
                page_id = result.get('page_id') or page_data.get('page_id')
                self.logger.debug(f"Page {page_id} created successfully")
            
            return result
            
        except DocumentationError:
            # Re-raise DocumentationError as-is
            raise
        except Exception as e:
            error_response = self._handle_error(
                e,
                context=f"Failed to create page {page_data.get('page_id', 'unknown')}",
                record_monitoring=True
            )
            raise DocumentationError(
                f"Failed to create page: {error_response.get('error', str(e))}"
            ) from e
    
    def update_page(self, page_id: str, page_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update page with data transformation.
        Lambda API is read-only, so we use S3 direct for writes.
        
        Uses DocumentationServiceBase patterns with specialized data transformation (Task 2.3.4).
        
        Args:
            page_id: Page identifier
            page_data: Page data dictionary in Django format (partial updates supported)
            
        Returns:
            Updated page data dictionary or None if update failed
            
        Raises:
            ValueError: If page not found or data is invalid
            DocumentationError: If update fails after retries
        """
        from apps.documentation.utils.data_transformers import DataTransformer
        
        # Get existing page
        existing = self.repository.get_by_page_id(page_id)
        if not existing:
            raise ValueError(f"Page not found: {page_id}")
        
        # Transform Django format to Lambda API format (specialized logic)
        try:
            lambda_updates = DataTransformer.django_to_lambda_page(page_data)
            # Handle partial update (specialized logic)
            updated_data = DataTransformer.handle_partial_update(existing, lambda_updates, 'page')
        except Exception as e:
            self.logger.error(f"Data transformation error in update_page: {e}", exc_info=True)
            raise ValueError(f"Invalid page data: {e}") from e
        
        # Use base class method with transformed data
        try:
            result = self._update_resource(
                resource_id=page_id,
                resource_data=updated_data,
                operation_name='update_page'
            )
            
            # Additional logging if needed (base class already handles cache clearing)
            if result:
                self.logger.debug(f"Page {page_id} updated successfully")
            
            return result
            
        except DocumentationError:
            # Re-raise DocumentationError as-is
            raise
        except Exception as e:
            error_response = self._handle_error(
                e,
                context=f"Failed to update page {page_id}",
                record_monitoring=True
            )
            raise DocumentationError(
                f"Failed to update page {page_id}: {error_response.get('error', str(e))}"
            ) from e

    def _delete_local_page_file(self, page_id: str) -> None:
        """Remove local page file and invalidate local index cache so list_pages reflects delete."""
        try:
            from apps.documentation.services import get_shared_local_storage
            from django.core.cache import cache
            local_storage = get_shared_local_storage()
            local_storage.delete_file(f"pages/{page_id}.json")
            cache.delete(f"local_json_storage:index:pages")
        except Exception as e:
            self.logger.warning(f"Failed to delete local page file or clear index cache for {page_id}: {e}")

    def delete_page(self, page_id: str) -> bool:
        """
        Delete page with multi-strategy (GraphQL fallback).
        
        Uses DocumentationServiceBase patterns with GraphQL fallback logic (Task 2.3.4).
        
        Args:
            page_id: Page identifier
            
        Returns:
            True if deletion was successful, False otherwise
            
        Raises:
            DocumentationError: If deletion fails after retries
        """
        try:
            # Try GraphQL first (specialized logic)
            if self.graphql_service:
                try:
                    @retry_on_network_error(max_retries=3, initial_delay=1.0)
                    def _delete_via_graphql():
                        return self.graphql_service.delete_page(page_id)
                    
                    success = _delete_via_graphql()
                    if success:
                        # Use base class cache clearing
                        self._clear_resource_cache(page_id)
                        self._clear_list_cache()
                        self._delete_local_page_file(page_id)
                        self.logger.debug(f"Page {page_id} deleted via GraphQL")
                        return True
                except Exception as e:
                    self.logger.warning(f"GraphQL failed for delete_page, falling back: {e}")
            
            # Fallback to base class delete method (S3 direct)
            result = self._delete_resource(
                resource_id=page_id,
                operation_name='delete_page'
            )
            if result:
                self._delete_local_page_file(page_id)
            return result
            
        except DocumentationError:
            # Re-raise DocumentationError as-is
            raise
        except Exception as e:
            error_response = self._handle_error(
                e,
                context=f"Failed to delete page {page_id}",
                record_monitoring=True
            )
            raise DocumentationError(
                f"Failed to delete page {page_id}: {error_response.get('error', str(e))}"
            ) from e
    
    def _clear_cache_for_page(self, page_id: str) -> None:
        """
        Clear cache entries for a specific page.
        
        Args:
            page_id: Page identifier
        """
        try:
            # Use UnifiedStorage's pattern-based cache clearing
            self.unified_storage.clear_cache('pages', page_id)
            self.unified_storage.clear_cache('pages')
        except Exception as e:
            self.logger.warning(f"Failed to clear cache for page {page_id}: {e}")
