"""S3-based documentation repository for page operations."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager

from django.conf import settings
from apps.documentation.repositories.base import BaseRepository
from apps.documentation.repositories.s3_json_storage import S3JSONStorage
from apps.documentation.utils.s3_index_manager import S3IndexManager
from apps.core.exceptions import RepositoryError, S3Error

logger = logging.getLogger(__name__)


class PagesRepository(BaseRepository):
    """Repository for documentation page operations using S3 JSON storage.
    
    Provides unified storage interface with error handling, batch operations,
    and transaction-like support for multiple operations.
    
    Extends BaseRepository for common patterns (Task 2.3.3).
    """

    def __init__(
        self,
        storage: Optional[S3JSONStorage] = None,
        index_manager: Optional[S3IndexManager] = None,
    ):
        """Initialize S3 documentation repository.
        
        Args:
            storage: Optional S3JSONStorage instance. If not provided, uses shared instance.
            index_manager: Optional S3IndexManager instance. If not provided, uses shared instance.
        """
        # Initialize base class with common patterns (Task 2.3.3)
        super().__init__(
            resource_name="pages",
            storage=storage,
            index_manager=index_manager
        )
        # Keep pages_prefix for backward compatibility
        self.pages_prefix = self.resource_prefix

    def _get_page_key(self, page_id: str) -> str:
        """Get S3 key for page JSON file."""
        return f"{self.pages_prefix}{page_id}.json"
    
    def _validate_and_fix_route(self, route: Any, page_id: str) -> str:
        """Validate and fix route to ensure it starts with '/'."""
        if not isinstance(route, str) or not route:
            route = ""
        
        if not route.startswith("/"):
            if page_id and page_id != "unknown":
                route = "/" + page_id.replace("_page", "").replace("_", "-")
            else:
                route = "/"
        
        return route

    def get_by_page_id(
        self, page_id: str, page_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get documentation page by page_id.
        
        Uses BaseRepository.get_by_id() for common patterns (Task 2.3.3).
        
        Args:
            page_id: Page identifier
            page_type: Optional page type filter
            
        Returns:
            Page data dictionary or None if not found
            
        Raises:
            RepositoryError: If retrieval fails
        """
        return self.get_by_id(page_id, page_type=page_type)

    def get_by_route(self, route: str) -> Optional[Dict[str, Any]]:
        """
        Get documentation page by route.
        
        Args:
            route: Page route path
            
        Returns:
            Page data dictionary or None if not found
            
        Raises:
            RepositoryError: If retrieval fails
        """
        if not route:
            raise ValueError("route is required")
        
        try:
            index_data = self.index_manager.read_index("pages")
            route_index = index_data.get("indexes", {}).get("by_route", {})
            
            page_id = route_index.get(route)
            if not page_id:
                return None
            
            return self.get_by_page_id(page_id)
            
        except Exception as e:
            error_msg = f"Failed to get page by route {route}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise RepositoryError(
                message=error_msg,
                entity_id=route,
                operation="get_by_route",
                error_code="GET_BY_ROUTE_FAILED"
            ) from e

    def list_all(
        self,
        page_type: Optional[str] = None,
        include_drafts: bool = True,
        include_deleted: bool = False,
        status: Optional[str] = None,
        page_state: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List all documentation pages with optional filters and pagination.
        
        Args:
            page_type: Optional page type filter
            include_drafts: Whether to include draft pages (default: True)
            include_deleted: Whether to include deleted pages (default: False)
            status: Optional status filter
            page_state: Optional page state filter
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of page data dictionaries
            
        Raises:
            RepositoryError: If listing fails
        """
        try:
            filters = {}
            if page_type:
                filters["page_type"] = page_type
            if status:
                filters["status"] = status
            if page_state:
                filters["page_state"] = page_state
            filters["include_drafts"] = include_drafts
            filters["include_deleted"] = include_deleted
            
            indexed_pages = self.index_manager.get_indexed_pages(filters)
            
            if limit is not None:
                paginated_pages = indexed_pages[offset:offset + limit]
            else:
                paginated_pages = indexed_pages[offset:]
            
            result_pages = []
            for page in paginated_pages:
                page_copy = page.copy()
                page_id = page_copy.get("page_id") or "unknown"
                if "_id" not in page_copy:
                    page_copy["_id"] = f"{page_id}-001" if page_id != "unknown" else "unknown"
                
                if "created_at" not in page_copy or not page_copy.get("created_at"):
                    page_copy["created_at"] = datetime.now(timezone.utc).isoformat()
                
                metadata = page_copy.get("metadata") if isinstance(page_copy.get("metadata"), dict) else {}
                route = metadata.get("route") or page_copy.get("route") or "/"
                route = self._validate_and_fix_route(route, page_id)
                metadata["route"] = route
                page_copy["metadata"] = metadata
                page_copy["route"] = route
                
                result_pages.append(page_copy)
            
            return result_pages
            
        except Exception as e:
            error_msg = f"Failed to list pages: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise RepositoryError(
                message=error_msg,
                operation="list_all",
                error_code="LIST_FAILED"
            ) from e

    def get_pages_by_type(
        self,
        page_type: str,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get all pages for a specific page type, optionally filtered by status."""
        filters = {"page_type": page_type, "include_drafts": True, "include_deleted": False}
        if status:
            filters["status"] = status
        indexed = self.index_manager.get_indexed_pages(filters)
        result = []
        for item in indexed:
            page_id = item.get("page_id")
            if not page_id:
                continue
            try:
                page = self.get_by_page_id(page_id, page_type=page_type)
                if page:
                    if status:
                        page_status = page.get("metadata", {}).get("status", "published")
                        if page_status != status:
                            continue
                    result.append(page)
            except Exception as e:
                self.logger.warning(f"Failed to load page {page_id} for get_pages_by_type: {e}")
        return result

    def count_pages_by_type(self, page_type: str) -> int:
        """Count pages by type using index."""
        index_data = self.index_manager.read_index("pages")
        by_type = index_data.get("indexes", {}).get("by_type", {})
        page_ids = by_type.get(page_type, [])
        return len(page_ids)

    def get_type_statistics(self) -> Dict[str, Any]:
        """Get statistics for all page types (docs, marketing, dashboard)."""
        index_data = self.index_manager.read_index("pages")
        stats_data = index_data.get("statistics", {})
        by_type_stats = stats_data.get("by_type", {}) if isinstance(stats_data, dict) else {}
        if by_type_stats:
            statistics = []
            for page_type in ["docs", "marketing", "dashboard"]:
                type_stats = by_type_stats.get(page_type, {})
                statistics.append({
                    "type": page_type,
                    "count": type_stats.get("total", 0),
                    "published": type_stats.get("published", 0),
                    "draft": type_stats.get("draft", 0),
                    "deleted": type_stats.get("deleted", 0),
                })
            return {"statistics": statistics, "total": stats_data.get("total", 0)}
        by_type = index_data.get("indexes", {}).get("by_type", {})
        all_pages = self.list_all(limit=None, offset=0)
        count_by_type_status = {}
        for page_type in ["docs", "marketing", "dashboard"]:
            count_by_type_status[page_type] = {"published": 0, "draft": 0, "deleted": 0, "total": 0}
        for page in all_pages:
            pt = page.get("page_type", "docs")
            if pt not in count_by_type_status:
                count_by_type_status[pt] = {"published": 0, "draft": 0, "deleted": 0, "total": 0}
            status_val = page.get("metadata", {}).get("status", "published")
            count_by_type_status[pt]["total"] += 1
            if status_val == "published":
                count_by_type_status[pt]["published"] += 1
            elif status_val == "draft":
                count_by_type_status[pt]["draft"] += 1
            elif status_val == "deleted":
                count_by_type_status[pt]["deleted"] += 1
        statistics = []
        for page_type in ["docs", "marketing", "dashboard"]:
            s = count_by_type_status.get(page_type, {})
            statistics.append({
                "type": page_type,
                "count": s.get("total", 0),
                "published": s.get("published", 0),
                "draft": s.get("draft", 0),
                "deleted": s.get("deleted", 0),
            })
        total = sum(st["count"] for st in statistics)
        return {"statistics": statistics, "total": total}

    def create(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new documentation page with full Lambda API model support.
        
        Args:
            page_data: Page data dictionary
            
        Returns:
            Created page data dictionary
            
        Raises:
            ValueError: If page_id is missing or data is invalid
            RepositoryError: If creation fails
        """
        from apps.documentation.schemas.lambda_models import validate_page_data
        
        page_id = page_data.get("page_id")
        if not page_id:
            raise ValueError("page_id is required")
        
        # Validate against Lambda API schema
        try:
            page_data = validate_page_data(page_data)
        except Exception as e:
            self.logger.error(f"Validation error for page {page_id}: {e}", exc_info=True)
            raise ValueError(f"Invalid page data: {e}") from e
        
        try:
            page_key = self._get_page_key(page_id)
            
            # Ensure required fields
            if "_id" not in page_data:
                page_data["_id"] = f"{page_id}-001"
            if "created_at" not in page_data:
                page_data["created_at"] = datetime.now(timezone.utc).isoformat()
            
            # Validate and fix route
            metadata = page_data.get("metadata", {})
            if not isinstance(metadata, dict):
                metadata = {}
            route = metadata.get("route") or page_data.get("route") or "/"
            route = self._validate_and_fix_route(route, page_id)
            metadata["route"] = route
            page_data["metadata"] = metadata
            page_data["route"] = route
            
            # Auto-calculate computed fields
            uses_endpoints = metadata.get("uses_endpoints", [])
            metadata["endpoint_count"] = len(uses_endpoints)
            
            # Derive api_versions
            api_versions_set = set()
            for endpoint in uses_endpoints:
                if isinstance(endpoint, dict) and "api_version" in endpoint:
                    api_versions_set.add(endpoint["api_version"])
            metadata["api_versions"] = sorted(list(api_versions_set))
            page_data["metadata"] = metadata
            
            # Ensure s3_key in metadata
            if "s3_key" not in metadata:
                metadata["s3_key"] = f"data/pages/{page_id}.json"
            page_data["metadata"] = metadata
            
            # Write to S3
            self.storage.write_json(page_key, page_data)
            
            # Incrementally update index
            try:
                self.index_manager.add_item_to_index('pages', page_id, page_data)
                self.logger.debug(f"Incrementally updated index for page: {page_id}")
            except Exception as e:
                self.logger.warning(f"Failed to update index for page {page_id}: {e}")
            
            self.logger.info(f"Created page: {page_id}")
            
            return page_data
            
        except (S3Error, ValueError) as e:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            error_msg = f"Failed to create page {page_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise RepositoryError(
                message=error_msg,
                entity_id=page_id,
                operation="create",
                error_code="CREATE_FAILED"
            ) from e

    def update(self, page_id: str, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing documentation page with full Lambda API model support.
        
        Args:
            page_id: Page identifier
            page_data: Page data dictionary (partial updates supported)
            
        Returns:
            Updated page data dictionary
            
        Raises:
            ValueError: If page not found or data is invalid
            RepositoryError: If update fails
        """
        from apps.documentation.schemas.lambda_models import validate_page_data
        
        if not page_id:
            raise ValueError("page_id is required")
        
        page_key = self._get_page_key(page_id)
        
        # Get existing page
        existing = self.get_by_page_id(page_id)
        if not existing:
            raise ValueError(f"Page not found: {page_id}")
        
        try:
            # Merge updates (deep merge for nested structures)
            def deep_merge(base: Dict, updates: Dict) -> Dict:
                """Deep merge two dictionaries."""
                result = base.copy()
                for key, value in updates.items():
                    if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                        result[key] = deep_merge(result[key], value)
                    else:
                        result[key] = value
                return result
            
            existing = deep_merge(existing, page_data)
            existing["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            # Validate against Lambda API schema
            try:
                existing = validate_page_data(existing)
            except Exception as e:
                self.logger.error(f"Validation error for page {page_id}: {e}", exc_info=True)
                raise ValueError(f"Invalid page data: {e}") from e
            
            # Validate and fix route
            metadata = existing.get("metadata", {})
            if not isinstance(metadata, dict):
                metadata = {}
            route = metadata.get("route") or existing.get("route") or "/"
            route = self._validate_and_fix_route(route, page_id)
            metadata["route"] = route
            existing["metadata"] = metadata
            existing["route"] = route
            
            # Auto-calculate computed fields
            uses_endpoints = metadata.get("uses_endpoints", [])
            metadata["endpoint_count"] = len(uses_endpoints)
            
            # Derive api_versions
            api_versions_set = set()
            for endpoint in uses_endpoints:
                if isinstance(endpoint, dict) and "api_version" in endpoint:
                    api_versions_set.add(endpoint["api_version"])
            metadata["api_versions"] = sorted(list(api_versions_set))
            existing["metadata"] = metadata
            
            # Update last_updated in metadata
            metadata["last_updated"] = datetime.now(timezone.utc).isoformat()
            existing["metadata"] = metadata
        
            # Write to S3
            self.storage.write_json(page_key, existing)
            
            # Incrementally update index
            try:
                self.index_manager.add_item_to_index('pages', page_id, existing)
                self.logger.debug(f"Incrementally updated index for page: {page_id}")
            except Exception as e:
                self.logger.warning(f"Failed to update index for page {page_id}: {e}")
            
            self.logger.info(f"Updated page: {page_id}")
            
            return existing
            
        except (S3Error, ValueError) as e:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            error_msg = f"Failed to update page {page_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise RepositoryError(
                message=error_msg,
                entity_id=page_id,
                operation="update",
                error_code="UPDATE_FAILED"
            ) from e

    def delete(self, page_id: str) -> bool:
        """
        Delete a documentation page.
        
        Args:
            page_id: Page identifier
            
        Returns:
            True if deletion was successful, False otherwise
            
        Raises:
            RepositoryError: If deletion fails
        """
        if not page_id:
            raise ValueError("page_id is required")
        
        page_key = self._get_page_key(page_id)
        
        try:
            self.storage.delete_json(page_key)
            
            # Incrementally update index
            try:
                self.index_manager.remove_item_from_index('pages', page_id)
                self.logger.debug(f"Incrementally removed page from index: {page_id}")
            except Exception as e:
                self.logger.warning(f"Failed to remove page from index {page_id}: {e}")
            
            self.logger.info(f"Deleted page: {page_id}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to delete page {page_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise RepositoryError(
                message=error_msg,
                entity_id=page_id,
                operation="delete",
                error_code="DELETE_FAILED"
            ) from e
    
    @contextmanager
    def transaction(self):
        """
        Context manager for transaction-like operations.
        
        Note: S3 doesn't support true transactions, but this provides
        a consistent interface for batch operations with rollback capability.
        
        Usage:
            with repository.transaction() as txn:
                txn.create(page1)
                txn.update(page2)
                # If any operation fails, all operations are logged
        """
        operations: List[Dict[str, Any]] = []
        
        class TransactionContext:
            def __init__(self, repo: 'PagesRepository', ops: List[Dict[str, Any]]):
                self.repo = repo
                self.ops = ops
            
            def create(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
                result = self.repo.create(page_data)
                self.ops.append({'type': 'create', 'page_id': page_data.get('page_id'), 'result': result})
                return result
            
            def update(self, page_id: str, page_data: Dict[str, Any]) -> Dict[str, Any]:
                result = self.repo.update(page_id, page_data)
                self.ops.append({'type': 'update', 'page_id': page_id, 'result': result})
                return result
            
            def delete(self, page_id: str) -> bool:
                result = self.repo.delete(page_id)
                self.ops.append({'type': 'delete', 'page_id': page_id, 'result': result})
                return result
        
        txn = TransactionContext(self, operations)
        try:
            yield txn
            self.logger.info(f"Transaction completed successfully with {len(operations)} operations")
        except Exception as e:
            self.logger.error(f"Transaction failed after {len(operations)} operations: {e}")
            # Log all operations for potential manual rollback
            for op in operations:
                self.logger.warning(f"Transaction operation: {op['type']} on {op.get('page_id', 'unknown')}")
            raise
    
    def batch_create(self, pages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create multiple pages in batch.
        
        Args:
            pages_data: List of page data dictionaries
            
        Returns:
            List of created page data dictionaries
            
        Raises:
            RepositoryError: If batch creation fails
        """
        if not pages_data:
            return []
        
        results: List[Dict[str, Any]] = []
        errors: List[Tuple[str, Exception]] = []
        
        for page_data in pages_data:
            try:
                result = self.create(page_data)
                results.append(result)
            except Exception as e:
                page_id = page_data.get("page_id", "unknown")
                errors.append((page_id, e))
                self.logger.error(f"Failed to create page {page_id} in batch: {e}")
        
        if errors:
            error_msg = f"Batch create failed for {len(errors)}/{len(pages_data)} pages"
            self.logger.error(error_msg)
            raise RepositoryError(
                message=error_msg,
                operation="batch_create",
                error_code="BATCH_CREATE_PARTIAL_FAILURE"
            )
        
        self.logger.info(f"Batch created {len(results)} pages successfully")
        return results
    
    def batch_update(self, updates: List[Tuple[str, Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Update multiple pages in batch.
        
        Args:
            updates: List of tuples (page_id, page_data)
            
        Returns:
            List of updated page data dictionaries
            
        Raises:
            RepositoryError: If batch update fails
        """
        if not updates:
            return []
        
        results: List[Dict[str, Any]] = []
        errors: List[Tuple[str, Exception]] = []
        
        for page_id, page_data in updates:
            try:
                result = self.update(page_id, page_data)
                results.append(result)
            except Exception as e:
                errors.append((page_id, e))
                self.logger.error(f"Failed to update page {page_id} in batch: {e}")
        
        if errors:
            error_msg = f"Batch update failed for {len(errors)}/{len(updates)} pages"
            self.logger.error(error_msg)
            raise RepositoryError(
                message=error_msg,
                operation="batch_update",
                error_code="BATCH_UPDATE_PARTIAL_FAILURE"
            )
        
        self.logger.info(f"Batch updated {len(results)} pages successfully")
        return results
    
    def batch_delete(self, page_ids: List[str]) -> List[str]:
        """
        Delete multiple pages in batch.
        
        Args:
            page_ids: List of page identifiers
            
        Returns:
            List of successfully deleted page IDs
            
        Raises:
            RepositoryError: If batch deletion fails
        """
        if not page_ids:
            return []
        
        results: List[str] = []
        errors: List[Tuple[str, Exception]] = []
        
        for page_id in page_ids:
            try:
                if self.delete(page_id):
                    results.append(page_id)
            except Exception as e:
                errors.append((page_id, e))
                self.logger.error(f"Failed to delete page {page_id} in batch: {e}")
        
        if errors:
            error_msg = f"Batch delete failed for {len(errors)}/{len(page_ids)} pages"
            self.logger.error(error_msg)
            raise RepositoryError(
                message=error_msg,
                operation="batch_delete",
                error_code="BATCH_DELETE_PARTIAL_FAILURE"
            )
        
        self.logger.info(f"Batch deleted {len(results)} pages successfully")
        return results
