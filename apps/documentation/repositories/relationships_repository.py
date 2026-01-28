"""S3-based repository for relationship operations."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager

from django.conf import settings
from apps.documentation.repositories.base import BaseRepository
from apps.documentation.repositories.s3_json_storage import S3JSONStorage
from apps.documentation.schemas.lambda_models import validate_relationship_data
from apps.documentation.utils.s3_index_manager import S3IndexManager
from apps.core.exceptions import RepositoryError, S3Error

logger = logging.getLogger(__name__)


class RelationshipsRepository(BaseRepository):
    """Repository for relationship operations using S3 JSON storage.
    
    Provides unified storage interface with error handling, batch operations,
    and transaction-like support for multiple operations.
    
    Extends BaseRepository for common patterns (Task 2.3.5).
    """

    def __init__(
        self,
        storage: Optional[S3JSONStorage] = None,
        index_manager: Optional[S3IndexManager] = None,
    ):
        """Initialize relationships repository.
        
        Args:
            storage: Optional S3JSONStorage instance. If not provided, uses shared instance.
            index_manager: Optional S3IndexManager instance. If not provided, uses shared instance.
        """
        # Initialize base class with common patterns (Task 2.3.5)
        super().__init__(
            resource_name="relationships",
            storage=storage,
            index_manager=index_manager
        )
        # Keep relationships_prefix for backward compatibility
        self.relationships_prefix = self.resource_prefix

    def _get_relationship_key(self, relationship_id: str) -> str:
        """Get S3 key for relationship JSON file."""
        return self._get_resource_key(relationship_id)

    def get_by_relationship_id(self, relationship_id: str) -> Optional[Dict[str, Any]]:
        """
        Get relationship by ID.
        
        Uses BaseRepository.get_by_id() for common patterns (Task 2.3.5).
        
        Args:
            relationship_id: Relationship identifier
            
        Returns:
            Relationship data dictionary or None if not found
            
        Raises:
            RepositoryError: If retrieval fails
        """
        return self.get_by_id(relationship_id)

    def list_all(
        self,
        page_id: Optional[str] = None,
        endpoint_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List all relationships with optional filters and pagination.
        
        Uses index-based filtering for performance, with fallback to file scanning.
        
        Args:
            page_id: Optional filter by page ID
            endpoint_id: Optional filter by endpoint ID
            limit: Optional limit for pagination
            offset: Offset for pagination
            
        Returns:
            List of relationship dictionaries
        """
        try:
            # Try to use index for efficient filtering
            index_data = self.index_manager.read_index('relationships')
            relationships_list = index_data.get('relationships', [])
            indexes = index_data.get('indexes', {})
            
            # If we have filters, use indexes to narrow down the list
            if page_id or endpoint_id:
                relationship_ids = set()
                
                # Filter by page_id using index
                if page_id:
                    by_page_index = indexes.get('by_page', {})
                    # Try exact match first
                    if page_id in by_page_index:
                        relationship_ids.update(by_page_index[page_id])
                    # Also try matching by page_path if available
                    for page_key, rel_ids in by_page_index.items():
                        if page_id in page_key or page_key in page_id:
                            relationship_ids.update(rel_ids)
                
                # Filter by endpoint_id using index
                if endpoint_id:
                    by_endpoint_index = indexes.get('by_endpoint', {})
                    # Try exact match first
                    for endpoint_key, rel_ids in by_endpoint_index.items():
                        if endpoint_id in endpoint_key or endpoint_key.endswith(f":{endpoint_id}"):
                            relationship_ids.update(rel_ids)
                
                # Filter relationships list to only include matching IDs
                if relationship_ids:
                    relationships_list = [
                        rel for rel in relationships_list
                        if rel.get('relationship_id') in relationship_ids
                    ]
                elif page_id or endpoint_id:
                    # If filters were provided but no matches found, return empty
                    return []
            
            # If no index data or relationships list is empty, fallback to file scanning
            if not relationships_list:
                self.logger.debug("Index empty or not available, falling back to file scanning")
                relationships_list = self._scan_relationships_files(page_id, endpoint_id)
            
            # Apply pagination
            if limit is not None:
                paginated_relationships = relationships_list[offset:offset + limit]
            else:
                paginated_relationships = relationships_list[offset:]
            
            # Load full relationship data for each item
            result_relationships = []
            for rel_summary in paginated_relationships:
                relationship_id = rel_summary.get('relationship_id')
                if not relationship_id:
                    continue
                
                # Load full relationship data
                full_relationship = self.get_by_relationship_id(relationship_id)
                if full_relationship:
                    # Ensure _id is set
                    if "_id" not in full_relationship:
                        full_relationship["_id"] = relationship_id
                    result_relationships.append(full_relationship)
            
            self.logger.debug(f"Listed {len(result_relationships)} relationships (filtered: page_id={page_id}, endpoint_id={endpoint_id})")
            return result_relationships
            
        except Exception as e:
            error_msg = f"Failed to list relationships: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            # Fallback to file scanning on error
            try:
                return self._scan_relationships_files(page_id, endpoint_id, limit, offset)
            except Exception as fallback_error:
                self.logger.error(f"Fallback file scanning also failed: {fallback_error}", exc_info=True)
                raise RepositoryError(
                    message=error_msg,
                    operation="list_all",
                    error_code="LIST_FAILED"
                ) from e
    
    def _scan_relationships_files(
        self,
        page_id: Optional[str] = None,
        endpoint_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Fallback method to scan relationship files directly.
        
        This is slower but works when index is not available.
        """
        try:
            # List all relationship files
            file_keys = self.storage.list_json_files(self.relationships_prefix, max_keys=10000)
            
            # Filter to exclude index.json
            json_files = [f for f in file_keys if not f.endswith('/index.json')]
            
            relationships = []
            for file_key in json_files:
                try:
                    relationship_data = self.storage.read_json(file_key)
                    if not relationship_data:
                        continue
                    
                    # Apply filters
                    if page_id:
                        rel_page_id = relationship_data.get('page_id') or relationship_data.get('page_path')
                        if not (page_id in str(rel_page_id) or str(rel_page_id) in page_id):
                            continue
                    
                    if endpoint_id:
                        rel_endpoint_id = relationship_data.get('endpoint_id') or relationship_data.get('endpoint_path')
                        if not (endpoint_id in str(rel_endpoint_id) or str(rel_endpoint_id) in endpoint_id):
                            continue
                    
                    # Ensure _id is set
                    relationship_id = relationship_data.get('relationship_id') or file_key.split('/')[-1].replace('.json', '')
                    if "_id" not in relationship_data:
                        relationship_data["_id"] = relationship_id
                    
                    relationships.append(relationship_data)
                except Exception as e:
                    self.logger.warning(f"Failed to read relationship file {file_key}: {e}")
                    continue
            
            # Apply pagination
            if limit is not None:
                relationships = relationships[offset:offset + limit]
            else:
                relationships = relationships[offset:]
            
            self.logger.info(f"Scanned {len(relationships)} relationships from files")
            return relationships
            
        except Exception as e:
            self.logger.error(f"Error scanning relationship files: {e}", exc_info=True)
            return []

    def create(self, relationship_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new relationship.
        
        Args:
            relationship_data: Relationship data dictionary
            
        Returns:
            Created relationship data dictionary
            
        Raises:
            ValueError: If relationship_id is missing
            RepositoryError: If creation fails
        """
        # Validate and normalize against canonical schema
        relationship_data = validate_relationship_data(relationship_data)

        relationship_id = relationship_data.get("relationship_id")
        if not relationship_id:
            raise ValueError("relationship_id is required")

        try:
            relationship_key = self._get_relationship_key(relationship_id)

            # Write to S3
            self.storage.write_json(relationship_key, relationship_data)
            
            # Incrementally update index
            try:
                self.index_manager.add_item_to_index('relationships', relationship_id, relationship_data)
                self.logger.debug(f"Incrementally updated index for relationship: {relationship_id}")
            except Exception as e:
                self.logger.warning(f"Failed to update index for relationship {relationship_id}: {e}")

            self.logger.info(f"Created relationship: {relationship_id}")
            return relationship_data
            
        except (S3Error, ValueError) as e:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            error_msg = f"Failed to create relationship {relationship_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise RepositoryError(
                message=error_msg,
                entity_id=relationship_id,
                operation="create",
                error_code="CREATE_FAILED"
            ) from e

    def update(self, relationship_id: str, relationship_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing relationship.
        
        Args:
            relationship_id: Relationship identifier
            relationship_data: Relationship data dictionary (partial updates supported)
            
        Returns:
            Updated relationship data dictionary
            
        Raises:
            ValueError: If relationship not found
            RepositoryError: If update fails
        """
        if not relationship_id:
            raise ValueError("relationship_id is required")
        
        relationship_key = self._get_relationship_key(relationship_id)

        try:
            # Load existing relationship, merge updates, and validate via canonical schema
            existing = self.get_by_relationship_id(relationship_id)
            if not existing:
                raise ValueError(f"Relationship not found: {relationship_id}")

            existing.update(relationship_data)
            existing["updated_at"] = datetime.now(timezone.utc).isoformat()
            validated = validate_relationship_data(existing)

            # Write updated relationship
            self.storage.write_json(relationship_key, validated)
            
            # Incrementally update index
            try:
                self.index_manager.add_item_to_index('relationships', relationship_id, validated)
                self.logger.debug(f"Incrementally updated index for relationship: {relationship_id}")
            except Exception as e:
                self.logger.warning(f"Failed to update index for relationship {relationship_id}: {e}")

            self.logger.info(f"Updated relationship: {relationship_id}")
            return validated
            
        except (S3Error, ValueError) as e:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            error_msg = f"Failed to update relationship {relationship_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise RepositoryError(
                message=error_msg,
                entity_id=relationship_id,
                operation="update",
                error_code="UPDATE_FAILED"
            ) from e

    def delete(self, relationship_id: str) -> bool:
        """
        Delete a relationship.
        
        Args:
            relationship_id: Relationship identifier
            
        Returns:
            True if deletion was successful, False otherwise
            
        Raises:
            RepositoryError: If deletion fails
        """
        if not relationship_id:
            raise ValueError("relationship_id is required")
        
        relationship_key = self._get_relationship_key(relationship_id)

        # Check if exists
        existing = self.get_by_relationship_id(relationship_id)
        if not existing:
            return False

        # Delete relationship file
        try:
            self.storage.delete_json(relationship_key)
            
            # Incrementally update index
            try:
                self.index_manager.remove_item_from_index('relationships', relationship_id)
                self.logger.debug(f"Incrementally removed relationship from index: {relationship_id}")
            except Exception as e:
                self.logger.warning(f"Failed to remove relationship from index {relationship_id}: {e}")
            
            self.logger.info(f"Deleted relationship: {relationship_id}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to delete relationship {relationship_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise RepositoryError(
                message=error_msg,
                entity_id=relationship_id,
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
                txn.create(relationship1)
                txn.update(relationship2)
                # If any operation fails, all operations are logged
        """
        operations: List[Dict[str, Any]] = []
        
        class TransactionContext:
            def __init__(self, repo: 'RelationshipsRepository', ops: List[Dict[str, Any]]):
                self.repo = repo
                self.ops = ops
            
            def create(self, relationship_data: Dict[str, Any]) -> Dict[str, Any]:
                result = self.repo.create(relationship_data)
                self.ops.append({'type': 'create', 'relationship_id': relationship_data.get('relationship_id'), 'result': result})
                return result
            
            def update(self, relationship_id: str, relationship_data: Dict[str, Any]) -> Dict[str, Any]:
                result = self.repo.update(relationship_id, relationship_data)
                self.ops.append({'type': 'update', 'relationship_id': relationship_id, 'result': result})
                return result
            
            def delete(self, relationship_id: str) -> bool:
                result = self.repo.delete(relationship_id)
                self.ops.append({'type': 'delete', 'relationship_id': relationship_id, 'result': result})
                return result
        
        txn = TransactionContext(self, operations)
        try:
            yield txn
            self.logger.info(f"Transaction completed successfully with {len(operations)} operations")
        except Exception as e:
            self.logger.error(f"Transaction failed after {len(operations)} operations: {e}")
            # Log all operations for potential manual rollback
            for op in operations:
                self.logger.warning(f"Transaction operation: {op['type']} on {op.get('relationship_id', 'unknown')}")
            raise
    
    def batch_create(self, relationships_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create multiple relationships in batch.
        
        Args:
            relationships_data: List of relationship data dictionaries
            
        Returns:
            List of created relationship data dictionaries
            
        Raises:
            RepositoryError: If batch creation fails
        """
        if not relationships_data:
            return []
        
        results: List[Dict[str, Any]] = []
        errors: List[Tuple[str, Exception]] = []
        
        for relationship_data in relationships_data:
            try:
                result = self.create(relationship_data)
                results.append(result)
            except Exception as e:
                relationship_id = relationship_data.get("relationship_id", "unknown")
                errors.append((relationship_id, e))
                self.logger.error(f"Failed to create relationship {relationship_id} in batch: {e}")
        
        if errors:
            error_msg = f"Batch create failed for {len(errors)}/{len(relationships_data)} relationships"
            self.logger.error(error_msg)
            raise RepositoryError(
                message=error_msg,
                operation="batch_create",
                error_code="BATCH_CREATE_PARTIAL_FAILURE"
            )
        
        self.logger.info(f"Batch created {len(results)} relationships successfully")
        return results
    
    def batch_update(self, updates: List[Tuple[str, Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Update multiple relationships in batch.
        
        Args:
            updates: List of tuples (relationship_id, relationship_data)
            
        Returns:
            List of updated relationship data dictionaries
            
        Raises:
            RepositoryError: If batch update fails
        """
        if not updates:
            return []
        
        results: List[Dict[str, Any]] = []
        errors: List[Tuple[str, Exception]] = []
        
        for relationship_id, relationship_data in updates:
            try:
                result = self.update(relationship_id, relationship_data)
                results.append(result)
            except Exception as e:
                errors.append((relationship_id, e))
                self.logger.error(f"Failed to update relationship {relationship_id} in batch: {e}")
        
        if errors:
            error_msg = f"Batch update failed for {len(errors)}/{len(updates)} relationships"
            self.logger.error(error_msg)
            raise RepositoryError(
                message=error_msg,
                operation="batch_update",
                error_code="BATCH_UPDATE_PARTIAL_FAILURE"
            )
        
        self.logger.info(f"Batch updated {len(results)} relationships successfully")
        return results
    
    def batch_delete(self, relationship_ids: List[str]) -> List[str]:
        """
        Delete multiple relationships in batch.
        
        Args:
            relationship_ids: List of relationship identifiers
            
        Returns:
            List of successfully deleted relationship IDs
            
        Raises:
            RepositoryError: If batch deletion fails
        """
        if not relationship_ids:
            return []
        
        results: List[str] = []
        errors: List[Tuple[str, Exception]] = []
        
        for relationship_id in relationship_ids:
            try:
                if self.delete(relationship_id):
                    results.append(relationship_id)
            except Exception as e:
                errors.append((relationship_id, e))
                self.logger.error(f"Failed to delete relationship {relationship_id} in batch: {e}")
        
        if errors:
            error_msg = f"Batch delete failed for {len(errors)}/{len(relationship_ids)} relationships"
            self.logger.error(error_msg)
            raise RepositoryError(
                message=error_msg,
                operation="batch_delete",
                error_code="BATCH_DELETE_PARTIAL_FAILURE"
            )
        
        self.logger.info(f"Batch deleted {len(results)} relationships successfully")
        return results
