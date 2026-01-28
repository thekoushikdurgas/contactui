"""S3-based repository for endpoint operations."""

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


class EndpointsRepository(BaseRepository):
    """Repository for endpoint operations using S3 JSON storage.
    
    Provides unified storage interface with error handling, batch operations,
    and transaction-like support for multiple operations.
    
    Extends BaseRepository for common patterns (Task 2.3.3).
    """

    def __init__(
        self,
        storage: Optional[S3JSONStorage] = None,
        index_manager: Optional[S3IndexManager] = None,
    ):
        """Initialize endpoints repository.
        
        Args:
            storage: Optional S3JSONStorage instance. If not provided, uses shared instance.
            index_manager: Optional S3IndexManager instance. If not provided, uses shared instance.
        """
        # Initialize base class with common patterns (Task 2.3.3)
        super().__init__(
            resource_name="endpoints",
            storage=storage,
            index_manager=index_manager
        )
        # Keep endpoints_prefix for backward compatibility
        self.endpoints_prefix = self.resource_prefix

    def _get_endpoint_key(self, endpoint_id: str) -> str:
        """Get S3 key for endpoint JSON file."""
        return self._get_resource_key(endpoint_id)

    def get_by_endpoint_id(self, endpoint_id: str) -> Optional[Dict[str, Any]]:
        """
        Get endpoint by ID.
        
        Uses BaseRepository.get_by_id() for common patterns (Task 2.3.3).
        """
        return self.get_by_id(endpoint_id)

    def list_all(
        self,
        api_version: Optional[str] = None,
        method: Optional[str] = None,
        endpoint_state: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List all endpoints with optional filters.

        Uses BaseRepository.list_all() for common patterns (Task 2.3.3).

        Args:
            api_version: Optional API version filter
            method: Optional HTTP method filter
            endpoint_state: Optional endpoint state filter
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of endpoint data dictionaries (from index; full payload may require get_by_endpoint_id)
        """
        return super().list_all(
            limit=limit,
            offset=offset,
            api_version=api_version,
            method=method,
            endpoint_state=endpoint_state
        )

    def get_by_path_and_method(self, endpoint_path: str, method: str) -> Optional[Dict[str, Any]]:
        """Get endpoint by path and method using index then full read."""
        index_data = self.index_manager.read_index("endpoints")
        endpoints_list = index_data.get("endpoints", [])
        method_upper = (method or "GET").upper()
        for ep in endpoints_list:
            if ep.get("path") == endpoint_path or ep.get("endpoint_path") == endpoint_path:
                if ep.get("method", "").upper() == method_upper:
                    eid = ep.get("endpoint_id")
                    if eid:
                        return self.get_by_endpoint_id(eid)
                    break
        return None

    def get_endpoints_by_api_version(self, api_version: str) -> List[Dict[str, Any]]:
        """Get all endpoints for a specific API version (index-only)."""
        return self.list_all(api_version=api_version, limit=None, offset=0)

    def get_endpoints_by_method(self, method: str) -> List[Dict[str, Any]]:
        """Get all endpoints for a specific method (index-only)."""
        return self.list_all(method=method, limit=None, offset=0)

    def get_endpoints_by_version_and_method(
        self, api_version: str, method: str
    ) -> List[Dict[str, Any]]:
        """Get all endpoints for a specific API version and method."""
        return self.list_all(api_version=api_version, method=method, limit=None, offset=0)

    def count_endpoints_by_api_version(self, api_version: str) -> int:
        """Count endpoints by API version."""
        index_data = self.index_manager.read_index("endpoints")
        by_version = index_data.get("indexes", {}).get("by_api_version", {})
        return len(by_version.get(api_version, []))

    def count_endpoints_by_method(self, method: str) -> int:
        """Count endpoints by method."""
        index_data = self.index_manager.read_index("endpoints")
        by_method = index_data.get("indexes", {}).get("by_method", {})
        return len(by_method.get((method or "GET").upper(), []))

    def get_api_version_statistics(self) -> Dict[str, Any]:
        """Get statistics for all API versions."""
        index_data = self.index_manager.read_index("endpoints")
        by_version = index_data.get("indexes", {}).get("by_api_version", {})
        statistics = [{"api_version": v, "count": len(ids)} for v, ids in by_version.items()]
        total = sum(s["count"] for s in statistics)
        return {"versions": statistics, "total": total}

    def get_method_statistics(self) -> Dict[str, Any]:
        """Get statistics for all methods."""
        index_data = self.index_manager.read_index("endpoints")
        by_method = index_data.get("indexes", {}).get("by_method", {})
        statistics = [{"method": m, "count": len(ids)} for m, ids in by_method.items()]
        total = sum(s["count"] for s in statistics)
        return {"methods": statistics, "total": total}

    def create(self, endpoint_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new endpoint with full Lambda API model support.
        
        Args:
            endpoint_data: Endpoint data dictionary
            
        Returns:
            Created endpoint data dictionary
            
        Raises:
            ValueError: If endpoint_id is missing or data is invalid
            RepositoryError: If creation fails
        """
        from apps.documentation.schemas.lambda_models import validate_endpoint_data
        
        endpoint_id = endpoint_data.get("endpoint_id")
        if not endpoint_id:
            raise ValueError("endpoint_id is required")
        
        # Validate against Lambda API schema
        try:
            endpoint_data = validate_endpoint_data(endpoint_data)
        except Exception as e:
            self.logger.error(f"Validation error for endpoint {endpoint_id}: {e}", exc_info=True)
            raise ValueError(f"Invalid endpoint data: {e}") from e
        
        try:
            endpoint_key = self._get_endpoint_key(endpoint_id)
            
            if "_id" not in endpoint_data:
                endpoint_data["_id"] = f"{endpoint_id}-001"
            if "created_at" not in endpoint_data:
                endpoint_data["created_at"] = datetime.now(timezone.utc).isoformat()
            if "updated_at" not in endpoint_data:
                endpoint_data["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            # Auto-calculate page_count
            used_by_pages = endpoint_data.get("used_by_pages", [])
            endpoint_data["page_count"] = len(used_by_pages)
            
            # Ensure endpoint_state
            if "endpoint_state" not in endpoint_data:
                endpoint_data["endpoint_state"] = "development"
            
            # Ensure method is uppercase
            if "method" in endpoint_data:
                endpoint_data["method"] = endpoint_data["method"].upper()
            
            self.storage.write_json(endpoint_key, endpoint_data)
            
            # Incrementally update index
            try:
                self.index_manager.add_item_to_index('endpoints', endpoint_id, endpoint_data)
                self.logger.debug(f"Incrementally updated index for endpoint: {endpoint_id}")
            except Exception as e:
                self.logger.warning(f"Failed to update index for endpoint {endpoint_id}: {e}")
            
            self.logger.info(f"Created endpoint: {endpoint_id}")
            
            return endpoint_data
            
        except (S3Error, ValueError) as e:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            error_msg = f"Failed to create endpoint {endpoint_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise RepositoryError(
                message=error_msg,
                entity_id=endpoint_id,
                operation="create",
                error_code="CREATE_FAILED"
            ) from e

    def update(self, endpoint_id: str, endpoint_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing endpoint with full Lambda API model support.
        
        Args:
            endpoint_id: Endpoint identifier
            endpoint_data: Endpoint data dictionary (partial updates supported)
            
        Returns:
            Updated endpoint data dictionary
            
        Raises:
            ValueError: If endpoint not found or data is invalid
            RepositoryError: If update fails
        """
        from apps.documentation.schemas.lambda_models import validate_endpoint_data
        
        if not endpoint_id:
            raise ValueError("endpoint_id is required")
        
        endpoint_key = self._get_endpoint_key(endpoint_id)
        
        existing = self.get_by_endpoint_id(endpoint_id)
        if not existing:
            raise ValueError(f"Endpoint not found: {endpoint_id}")
        
        try:
            # Deep merge updates
            def deep_merge(base: Dict, updates: Dict) -> Dict:
                """Deep merge two dictionaries."""
                result = base.copy()
                for key, value in updates.items():
                    if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                        result[key] = deep_merge(result[key], value)
                    else:
                        result[key] = value
                return result
            
            existing = deep_merge(existing, endpoint_data)
            existing["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            # Validate against Lambda API schema
            try:
                existing = validate_endpoint_data(existing)
            except Exception as e:
                self.logger.error(f"Validation error for endpoint {endpoint_id}: {e}", exc_info=True)
                raise ValueError(f"Invalid endpoint data: {e}") from e
            
            # Auto-calculate page_count
            used_by_pages = existing.get("used_by_pages", [])
            existing["page_count"] = len(used_by_pages)
            
            # Ensure method is uppercase
            if "method" in existing:
                existing["method"] = existing["method"].upper()
            
            self.storage.write_json(endpoint_key, existing)
            
            # Incrementally update index
            try:
                self.index_manager.add_item_to_index('endpoints', endpoint_id, existing)
                self.logger.debug(f"Incrementally updated index for endpoint: {endpoint_id}")
            except Exception as e:
                self.logger.warning(f"Failed to update index for endpoint {endpoint_id}: {e}")
            
            self.logger.info(f"Updated endpoint: {endpoint_id}")
            
            return existing
            
        except (S3Error, ValueError) as e:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            error_msg = f"Failed to update endpoint {endpoint_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise RepositoryError(
                message=error_msg,
                entity_id=endpoint_id,
                operation="update",
                error_code="UPDATE_FAILED"
            ) from e

    def delete(self, endpoint_id: str) -> bool:
        """
        Delete an endpoint.
        
        Args:
            endpoint_id: Endpoint identifier
            
        Returns:
            True if deletion was successful, False otherwise
            
        Raises:
            RepositoryError: If deletion fails
        """
        if not endpoint_id:
            raise ValueError("endpoint_id is required")
        
        endpoint_key = self._get_endpoint_key(endpoint_id)
        
        try:
            self.storage.delete_json(endpoint_key)
            
            # Incrementally update index
            try:
                self.index_manager.remove_item_from_index('endpoints', endpoint_id)
                self.logger.debug(f"Incrementally removed endpoint from index: {endpoint_id}")
            except Exception as e:
                self.logger.warning(f"Failed to remove endpoint from index {endpoint_id}: {e}")
            
            self.logger.info(f"Deleted endpoint: {endpoint_id}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to delete endpoint {endpoint_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise RepositoryError(
                message=error_msg,
                entity_id=endpoint_id,
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
                txn.create(endpoint1)
                txn.update(endpoint2)
                # If any operation fails, all operations are logged
        """
        operations: List[Dict[str, Any]] = []
        
        class TransactionContext:
            def __init__(self, repo: 'EndpointsRepository', ops: List[Dict[str, Any]]):
                self.repo = repo
                self.ops = ops
            
            def create(self, endpoint_data: Dict[str, Any]) -> Dict[str, Any]:
                result = self.repo.create(endpoint_data)
                self.ops.append({'type': 'create', 'endpoint_id': endpoint_data.get('endpoint_id'), 'result': result})
                return result
            
            def update(self, endpoint_id: str, endpoint_data: Dict[str, Any]) -> Dict[str, Any]:
                result = self.repo.update(endpoint_id, endpoint_data)
                self.ops.append({'type': 'update', 'endpoint_id': endpoint_id, 'result': result})
                return result
            
            def delete(self, endpoint_id: str) -> bool:
                result = self.repo.delete(endpoint_id)
                self.ops.append({'type': 'delete', 'endpoint_id': endpoint_id, 'result': result})
                return result
        
        txn = TransactionContext(self, operations)
        try:
            yield txn
            self.logger.info(f"Transaction completed successfully with {len(operations)} operations")
        except Exception as e:
            self.logger.error(f"Transaction failed after {len(operations)} operations: {e}")
            # Log all operations for potential manual rollback
            for op in operations:
                self.logger.warning(f"Transaction operation: {op['type']} on {op.get('endpoint_id', 'unknown')}")
            raise
    
    def batch_create(self, endpoints_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create multiple endpoints in batch.
        
        Args:
            endpoints_data: List of endpoint data dictionaries
            
        Returns:
            List of created endpoint data dictionaries
            
        Raises:
            RepositoryError: If batch creation fails
        """
        if not endpoints_data:
            return []
        
        results: List[Dict[str, Any]] = []
        errors: List[Tuple[str, Exception]] = []
        
        for endpoint_data in endpoints_data:
            try:
                result = self.create(endpoint_data)
                results.append(result)
            except Exception as e:
                endpoint_id = endpoint_data.get("endpoint_id", "unknown")
                errors.append((endpoint_id, e))
                self.logger.error(f"Failed to create endpoint {endpoint_id} in batch: {e}")
        
        if errors:
            error_msg = f"Batch create failed for {len(errors)}/{len(endpoints_data)} endpoints"
            self.logger.error(error_msg)
            raise RepositoryError(
                message=error_msg,
                operation="batch_create",
                error_code="BATCH_CREATE_PARTIAL_FAILURE"
            )
        
        self.logger.info(f"Batch created {len(results)} endpoints successfully")
        return results
    
    def batch_update(self, updates: List[Tuple[str, Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Update multiple endpoints in batch.
        
        Args:
            updates: List of tuples (endpoint_id, endpoint_data)
            
        Returns:
            List of updated endpoint data dictionaries
            
        Raises:
            RepositoryError: If batch update fails
        """
        if not updates:
            return []
        
        results: List[Dict[str, Any]] = []
        errors: List[Tuple[str, Exception]] = []
        
        for endpoint_id, endpoint_data in updates:
            try:
                result = self.update(endpoint_id, endpoint_data)
                results.append(result)
            except Exception as e:
                errors.append((endpoint_id, e))
                self.logger.error(f"Failed to update endpoint {endpoint_id} in batch: {e}")
        
        if errors:
            error_msg = f"Batch update failed for {len(errors)}/{len(updates)} endpoints"
            self.logger.error(error_msg)
            raise RepositoryError(
                message=error_msg,
                operation="batch_update",
                error_code="BATCH_UPDATE_PARTIAL_FAILURE"
            )
        
        self.logger.info(f"Batch updated {len(results)} endpoints successfully")
        return results
    
    def batch_delete(self, endpoint_ids: List[str]) -> List[str]:
        """
        Delete multiple endpoints in batch.
        
        Args:
            endpoint_ids: List of endpoint identifiers
            
        Returns:
            List of successfully deleted endpoint IDs
            
        Raises:
            RepositoryError: If batch deletion fails
        """
        if not endpoint_ids:
            return []
        
        results: List[str] = []
        errors: List[Tuple[str, Exception]] = []
        
        for endpoint_id in endpoint_ids:
            try:
                if self.delete(endpoint_id):
                    results.append(endpoint_id)
            except Exception as e:
                errors.append((endpoint_id, e))
                self.logger.error(f"Failed to delete endpoint {endpoint_id} in batch: {e}")
        
        if errors:
            error_msg = f"Batch delete failed for {len(errors)}/{len(endpoint_ids)} endpoints"
            self.logger.error(error_msg)
            raise RepositoryError(
                message=error_msg,
                operation="batch_delete",
                error_code="BATCH_DELETE_PARTIAL_FAILURE"
            )
        
        self.logger.info(f"Batch deleted {len(results)} endpoints successfully")
        return results
