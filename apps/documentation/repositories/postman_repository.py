"""S3-based repository for Postman operations."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager

from django.conf import settings
from apps.documentation.repositories.s3_json_storage import S3JSONStorage
from apps.documentation.utils.s3_index_manager import S3IndexManager
from apps.core.exceptions import RepositoryError, S3Error

logger = logging.getLogger(__name__)


class PostmanRepository:
    """Repository for Postman operations using S3 JSON storage.
    
    Provides unified storage interface with error handling, batch operations,
    and transaction-like support for multiple operations.
    Handles both collections and environments.
    
    Note: This repository handles multiple resource types (collections, environments, configurations)
    and cannot fully extend BaseRepository. However, initialization follows similar patterns.
    """

    def __init__(
        self,
        storage: Optional[S3JSONStorage] = None,
        index_manager: Optional[S3IndexManager] = None,
    ):
        """Initialize Postman repository.
        
        Uses shared initialization pattern similar to BaseRepository (Task 2.3.5).
        
        Args:
            storage: Optional S3JSONStorage instance. If not provided, uses shared instance.
            index_manager: Optional S3IndexManager instance. If not provided, uses shared instance.
        """
        # Initialize storage (shared pattern from BaseRepository)
        if storage is None:
            from apps.documentation.services import get_shared_s3_storage
            self.storage = get_shared_s3_storage()
        else:
            self.storage = storage
        
        # Initialize index manager (shared pattern from BaseRepository)
        if index_manager is None:
            from apps.documentation.services import get_shared_s3_index_manager
            self.index_manager = get_shared_s3_index_manager()
        else:
            self.index_manager = index_manager
        
        # Set up prefixes (Postman-specific: multiple resource types)
        self.data_prefix = settings.S3_DATA_PREFIX
        self.collections_prefix = f"{self.data_prefix}postman/collections/"
        self.environments_prefix = f"{self.data_prefix}postman/environments/"
        self.configurations_prefix = f"{self.data_prefix}postman/configurations/"
        
        # Set up logger
        self.logger = logging.getLogger(f"{__name__}.PostmanRepository")

    def _get_collection_key(self, collection_id: str) -> str:
        """Get S3 key for collection JSON file."""
        return f"{self.collections_prefix}{collection_id}.json"

    def _get_environment_key(self, environment_id: str) -> str:
        """Get S3 key for environment JSON file."""
        return f"{self.environments_prefix}{environment_id}.json"

    def get_collection_by_id(self, collection_id: str) -> Optional[Dict[str, Any]]:
        """Get collection by ID (like PagesRepository.get_by_page_id)."""
        collection_key = self._get_collection_key(collection_id)
        collection_data = self.storage.read_json(collection_key)
        if not collection_data:
            return None

        if "_id" not in collection_data:
            collection_data["_id"] = collection_data.get("id", collection_id)

        return collection_data

    def get_environment_by_id(self, environment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get environment by ID.
        
        Args:
            environment_id: Environment identifier
            
        Returns:
            Environment data dictionary or None if not found
            
        Raises:
            RepositoryError: If retrieval fails
        """
        if not environment_id:
            raise ValueError("environment_id is required")
        
        try:
            environment_key = self._get_environment_key(environment_id)
            environment_data = self.storage.read_json(environment_key)
            if not environment_data:
                return None

            if "_id" not in environment_data:
                environment_data["_id"] = environment_data.get("id", environment_id)

            return environment_data
            
        except Exception as e:
            error_msg = f"Failed to get environment {environment_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise RepositoryError(
                message=error_msg,
                entity_id=environment_id,
                operation="get_environment_by_id",
                error_code="GET_FAILED"
            ) from e

    def list_collections(
        self,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List all collections with pagination.
        
        Uses index-based listing for performance, with fallback to file scanning.
        
        Args:
            limit: Optional limit for pagination
            offset: Offset for pagination
            
        Returns:
            List of collection dictionaries
        """
        try:
            # Try to use index for efficient listing
            index_data = self.index_manager.read_index('postman')
            collections_list = index_data.get('collections', [])
            
            # If index is empty, fallback to file scanning
            if not collections_list:
                self.logger.debug("Index empty or not available, falling back to file scanning")
                collections_list = self._scan_collections_files()
            
            # Apply pagination
            if limit is not None:
                paginated_collections = collections_list[offset:offset + limit]
            else:
                paginated_collections = collections_list[offset:]
            
            # Load full collection data for each item
            result_collections = []
            for coll_summary in paginated_collections:
                collection_id = coll_summary.get('collection_id') or coll_summary.get('id')
                if not collection_id:
                    continue
                
                # Load full collection data
                full_collection = self.get_collection_by_id(collection_id)
                if full_collection:
                    # Ensure _id is set
                    if "_id" not in full_collection:
                        full_collection["_id"] = collection_id
                    result_collections.append(full_collection)
            
            self.logger.debug(f"Listed {len(result_collections)} collections")
            return result_collections
            
        except Exception as e:
            error_msg = f"Failed to list collections: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            # Fallback to file scanning on error
            try:
                return self._scan_collections_files(limit, offset)
            except Exception as fallback_error:
                self.logger.error(f"Fallback file scanning also failed: {fallback_error}", exc_info=True)
                raise RepositoryError(
                    message=error_msg,
                    operation="list_collections",
                    error_code="LIST_FAILED"
                ) from e
    
    def list_environments(
        self,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List all environments with pagination.
        
        Uses index-based listing for performance, with fallback to file scanning.
        
        Args:
            limit: Optional limit for pagination
            offset: Offset for pagination
            
        Returns:
            List of environment dictionaries
        """
        try:
            # Try to use index for efficient listing
            index_data = self.index_manager.read_index('postman')
            environments_list = index_data.get('environments', [])
            
            # If index is empty, fallback to file scanning
            if not environments_list:
                self.logger.debug("Index empty or not available, falling back to file scanning")
                environments_list = self._scan_environments_files()
            
            # Apply pagination
            if limit is not None:
                paginated_environments = environments_list[offset:offset + limit]
            else:
                paginated_environments = environments_list[offset:]
            
            # Load full environment data for each item
            result_environments = []
            for env_summary in paginated_environments:
                environment_id = env_summary.get('environment_id') or env_summary.get('id')
                if not environment_id:
                    continue
                
                # Load full environment data
                full_environment = self.get_environment_by_id(environment_id)
                if full_environment:
                    # Ensure _id is set
                    if "_id" not in full_environment:
                        full_environment["_id"] = environment_id
                    result_environments.append(full_environment)
            
            self.logger.debug(f"Listed {len(result_environments)} environments")
            return result_environments
            
        except Exception as e:
            error_msg = f"Failed to list environments: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            # Fallback to file scanning on error
            try:
                return self._scan_environments_files(limit, offset)
            except Exception as fallback_error:
                self.logger.error(f"Fallback file scanning also failed: {fallback_error}", exc_info=True)
                raise RepositoryError(
                    message=error_msg,
                    operation="list_environments",
                    error_code="LIST_FAILED"
                ) from e
    
    def _scan_collections_files(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Fallback method to scan collection files directly.
        
        This is slower but works when index is not available.
        """
        try:
            # List all collection files
            file_keys = self.storage.list_json_files(self.collections_prefix, max_keys=10000)
            
            # Filter to exclude index.json
            json_files = [f for f in file_keys if not f.endswith('/index.json')]
            
            collections = []
            for file_key in json_files:
                try:
                    collection_data = self.storage.read_json(file_key)
                    if not collection_data:
                        continue
                    
                    # Extract collection ID from filename if not in data
                    collection_id = collection_data.get('id') or collection_data.get('collection_id')
                    if not collection_id:
                        collection_id = file_key.split('/')[-1].replace('.json', '')
                        collection_data['id'] = collection_id
                    
                    # Ensure _id is set
                    if "_id" not in collection_data:
                        collection_data["_id"] = collection_id
                    
                    collections.append(collection_data)
                except Exception as e:
                    self.logger.warning(f"Failed to read collection file {file_key}: {e}")
                    continue
            
            # Apply pagination
            if limit is not None:
                collections = collections[offset:offset + limit]
            else:
                collections = collections[offset:]
            
            self.logger.info(f"Scanned {len(collections)} collections from files")
            return collections
            
        except Exception as e:
            self.logger.error(f"Error scanning collection files: {e}", exc_info=True)
            return []
    
    def _scan_environments_files(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Fallback method to scan environment files directly.
        
        This is slower but works when index is not available.
        """
        try:
            # List all environment files
            file_keys = self.storage.list_json_files(self.environments_prefix, max_keys=10000)
            
            # Filter to exclude index.json
            json_files = [f for f in file_keys if not f.endswith('/index.json')]
            
            environments = []
            for file_key in json_files:
                try:
                    environment_data = self.storage.read_json(file_key)
                    if not environment_data:
                        continue
                    
                    # Extract environment ID from filename if not in data
                    environment_id = environment_data.get('id') or environment_data.get('environment_id')
                    if not environment_id:
                        environment_id = file_key.split('/')[-1].replace('.json', '')
                        environment_data['id'] = environment_id
                    
                    # Ensure _id is set
                    if "_id" not in environment_data:
                        environment_data["_id"] = environment_id
                    
                    environments.append(environment_data)
                except Exception as e:
                    self.logger.warning(f"Failed to read environment file {file_key}: {e}")
                    continue
            
            # Apply pagination
            if limit is not None:
                environments = environments[offset:offset + limit]
            else:
                environments = environments[offset:]
            
            self.logger.info(f"Scanned {len(environments)} environments from files")
            return environments
            
        except Exception as e:
            self.logger.error(f"Error scanning environment files: {e}", exc_info=True)
            return []

    def create_collection(self, collection_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new collection.
        
        Args:
            collection_data: Collection data dictionary
            
        Returns:
            Created collection data dictionary
            
        Raises:
            ValueError: If collection ID is missing
            RepositoryError: If creation fails
        """
        collection_id = collection_data.get("id") or collection_data.get("collection_id")
        if not collection_id:
            raise ValueError("Collection ID is required")

        try:
            collection_key = self._get_collection_key(collection_id)

            if "_id" not in collection_data:
                collection_data["_id"] = collection_id
            if "created_at" not in collection_data:
                collection_data["created_at"] = datetime.now(timezone.utc).isoformat()
            if "updated_at" not in collection_data:
                collection_data["updated_at"] = datetime.now(timezone.utc).isoformat()

            # Write to S3
            self.storage.write_json(collection_key, collection_data)

            self.logger.info(f"Created collection: {collection_id}")
            return collection_data
            
        except (S3Error, ValueError) as e:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            error_msg = f"Failed to create collection {collection_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise RepositoryError(
                message=error_msg,
                entity_id=collection_id,
                operation="create_collection",
                error_code="CREATE_FAILED"
            ) from e

    def create_environment(self, environment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new environment.
        
        Args:
            environment_data: Environment data dictionary
            
        Returns:
            Created environment data dictionary
            
        Raises:
            ValueError: If environment ID is missing
            RepositoryError: If creation fails
        """
        environment_id = environment_data.get("id") or environment_data.get("environment_id")
        if not environment_id:
            raise ValueError("Environment ID is required")

        try:
            environment_key = self._get_environment_key(environment_id)

            if "_id" not in environment_data:
                environment_data["_id"] = environment_id
            if "created_at" not in environment_data:
                environment_data["created_at"] = datetime.now(timezone.utc).isoformat()
            if "updated_at" not in environment_data:
                environment_data["updated_at"] = datetime.now(timezone.utc).isoformat()

            # Write to S3
            self.storage.write_json(environment_key, environment_data)

            self.logger.info(f"Created environment: {environment_id}")
            return environment_data
            
        except (S3Error, ValueError) as e:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            error_msg = f"Failed to create environment {environment_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise RepositoryError(
                message=error_msg,
                entity_id=environment_id,
                operation="create_environment",
                error_code="CREATE_FAILED"
            ) from e

    def update_collection(self, collection_id: str, collection_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing collection.
        
        Args:
            collection_id: Collection identifier
            collection_data: Collection data dictionary (partial updates supported)
            
        Returns:
            Updated collection data dictionary
            
        Raises:
            ValueError: If collection not found
            RepositoryError: If update fails
        """
        if not collection_id:
            raise ValueError("collection_id is required")
        
        collection_key = self._get_collection_key(collection_id)

        # Get existing collection
        existing = self.get_collection_by_id(collection_id)
        if not existing:
            raise ValueError(f"Collection not found: {collection_id}")

        try:
            # Merge updates
            existing.update(collection_data)
            existing["updated_at"] = datetime.now(timezone.utc).isoformat()

            # Write updated collection
            self.storage.write_json(collection_key, existing)

            self.logger.info(f"Updated collection: {collection_id}")
            return existing
            
        except (S3Error, ValueError) as e:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            error_msg = f"Failed to update collection {collection_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise RepositoryError(
                message=error_msg,
                entity_id=collection_id,
                operation="update_collection",
                error_code="UPDATE_FAILED"
            ) from e

    def update_environment(self, environment_id: str, environment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing environment.
        
        Args:
            environment_id: Environment identifier
            environment_data: Environment data dictionary (partial updates supported)
            
        Returns:
            Updated environment data dictionary
            
        Raises:
            ValueError: If environment not found
            RepositoryError: If update fails
        """
        if not environment_id:
            raise ValueError("environment_id is required")
        
        environment_key = self._get_environment_key(environment_id)

        # Get existing environment
        existing = self.get_environment_by_id(environment_id)
        if not existing:
            raise ValueError(f"Environment not found: {environment_id}")

        try:
            # Merge updates
            existing.update(environment_data)
            existing["updated_at"] = datetime.now(timezone.utc).isoformat()

            # Write updated environment
            self.storage.write_json(environment_key, existing)

            self.logger.info(f"Updated environment: {environment_id}")
            return existing
            
        except (S3Error, ValueError) as e:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            error_msg = f"Failed to update environment {environment_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise RepositoryError(
                message=error_msg,
                entity_id=environment_id,
                operation="update_environment",
                error_code="UPDATE_FAILED"
            ) from e

    def delete_collection(self, collection_id: str) -> bool:
        """
        Delete a collection.
        
        Args:
            collection_id: Collection identifier
            
        Returns:
            True if deletion was successful, False otherwise
            
        Raises:
            RepositoryError: If deletion fails
        """
        if not collection_id:
            raise ValueError("collection_id is required")
        
        collection_key = self._get_collection_key(collection_id)

        # Check if exists
        existing = self.get_collection_by_id(collection_id)
        if not existing:
            return False

        # Delete collection file
        try:
            self.storage.delete_json(collection_key)
            self.logger.info(f"Deleted collection: {collection_id}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to delete collection {collection_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise RepositoryError(
                message=error_msg,
                entity_id=collection_id,
                operation="delete_collection",
                error_code="DELETE_FAILED"
            ) from e

    def delete_environment(self, environment_id: str) -> bool:
        """
        Delete an environment.
        
        Args:
            environment_id: Environment identifier
            
        Returns:
            True if deletion was successful, False otherwise
            
        Raises:
            RepositoryError: If deletion fails
        """
        if not environment_id:
            raise ValueError("environment_id is required")
        
        environment_key = self._get_environment_key(environment_id)

        # Check if exists
        existing = self.get_environment_by_id(environment_id)
        if not existing:
            return False

        # Delete environment file
        try:
            self.storage.delete_json(environment_key)
            self.logger.info(f"Deleted environment: {environment_id}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to delete environment {environment_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise RepositoryError(
                message=error_msg,
                entity_id=environment_id,
                operation="delete_environment",
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
                txn.create_collection(collection1)
                txn.update_environment(env1)
                # If any operation fails, all operations are logged
        """
        operations: List[Dict[str, Any]] = []
        
        class TransactionContext:
            def __init__(self, repo: 'PostmanRepository', ops: List[Dict[str, Any]]):
                self.repo = repo
                self.ops = ops
            
            def create_collection(self, collection_data: Dict[str, Any]) -> Dict[str, Any]:
                result = self.repo.create_collection(collection_data)
                collection_id = collection_data.get("id") or collection_data.get("collection_id")
                self.ops.append({'type': 'create_collection', 'collection_id': collection_id, 'result': result})
                return result
            
            def update_collection(self, collection_id: str, collection_data: Dict[str, Any]) -> Dict[str, Any]:
                result = self.repo.update_collection(collection_id, collection_data)
                self.ops.append({'type': 'update_collection', 'collection_id': collection_id, 'result': result})
                return result
            
            def delete_collection(self, collection_id: str) -> bool:
                result = self.repo.delete_collection(collection_id)
                self.ops.append({'type': 'delete_collection', 'collection_id': collection_id, 'result': result})
                return result
            
            def create_environment(self, environment_data: Dict[str, Any]) -> Dict[str, Any]:
                result = self.repo.create_environment(environment_data)
                environment_id = environment_data.get("id") or environment_data.get("environment_id")
                self.ops.append({'type': 'create_environment', 'environment_id': environment_id, 'result': result})
                return result
            
            def update_environment(self, environment_id: str, environment_data: Dict[str, Any]) -> Dict[str, Any]:
                result = self.repo.update_environment(environment_id, environment_data)
                self.ops.append({'type': 'update_environment', 'environment_id': environment_id, 'result': result})
                return result
            
            def delete_environment(self, environment_id: str) -> bool:
                result = self.repo.delete_environment(environment_id)
                self.ops.append({'type': 'delete_environment', 'environment_id': environment_id, 'result': result})
                return result
        
        txn = TransactionContext(self, operations)
        try:
            yield txn
            self.logger.info(f"Transaction completed successfully with {len(operations)} operations")
        except Exception as e:
            self.logger.error(f"Transaction failed after {len(operations)} operations: {e}")
            # Log all operations for potential manual rollback
            for op in operations:
                self.logger.warning(f"Transaction operation: {op['type']} on {op.get('collection_id') or op.get('environment_id', 'unknown')}")
            raise
    
    def batch_create_collections(self, collections_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create multiple collections in batch.
        
        Args:
            collections_data: List of collection data dictionaries
            
        Returns:
            List of created collection data dictionaries
            
        Raises:
            RepositoryError: If batch creation fails
        """
        if not collections_data:
            return []
        
        results: List[Dict[str, Any]] = []
        errors: List[Tuple[str, Exception]] = []
        
        for collection_data in collections_data:
            try:
                result = self.create_collection(collection_data)
                results.append(result)
            except Exception as e:
                collection_id = collection_data.get("id") or collection_data.get("collection_id", "unknown")
                errors.append((collection_id, e))
                self.logger.error(f"Failed to create collection {collection_id} in batch: {e}")
        
        if errors:
            error_msg = f"Batch create failed for {len(errors)}/{len(collections_data)} collections"
            self.logger.error(error_msg)
            raise RepositoryError(
                message=error_msg,
                operation="batch_create_collections",
                error_code="BATCH_CREATE_PARTIAL_FAILURE"
            )
        
        self.logger.info(f"Batch created {len(results)} collections successfully")
        return results
    
    def batch_update_collections(self, updates: List[Tuple[str, Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Update multiple collections in batch.
        
        Args:
            updates: List of tuples (collection_id, collection_data)
            
        Returns:
            List of updated collection data dictionaries
            
        Raises:
            RepositoryError: If batch update fails
        """
        if not updates:
            return []
        
        results: List[Dict[str, Any]] = []
        errors: List[Tuple[str, Exception]] = []
        
        for collection_id, collection_data in updates:
            try:
                result = self.update_collection(collection_id, collection_data)
                results.append(result)
            except Exception as e:
                errors.append((collection_id, e))
                self.logger.error(f"Failed to update collection {collection_id} in batch: {e}")
        
        if errors:
            error_msg = f"Batch update failed for {len(errors)}/{len(updates)} collections"
            self.logger.error(error_msg)
            raise RepositoryError(
                message=error_msg,
                operation="batch_update_collections",
                error_code="BATCH_UPDATE_PARTIAL_FAILURE"
            )
        
        self.logger.info(f"Batch updated {len(results)} collections successfully")
        return results
    
    def batch_delete_collections(self, collection_ids: List[str]) -> List[str]:
        """
        Delete multiple collections in batch.
        
        Args:
            collection_ids: List of collection identifiers
            
        Returns:
            List of successfully deleted collection IDs
            
        Raises:
            RepositoryError: If batch deletion fails
        """
        if not collection_ids:
            return []
        
        results: List[str] = []
        errors: List[Tuple[str, Exception]] = []
        
        for collection_id in collection_ids:
            try:
                if self.delete_collection(collection_id):
                    results.append(collection_id)
            except Exception as e:
                errors.append((collection_id, e))
                self.logger.error(f"Failed to delete collection {collection_id} in batch: {e}")
        
        if errors:
            error_msg = f"Batch delete failed for {len(errors)}/{len(collection_ids)} collections"
            self.logger.error(error_msg)
            raise RepositoryError(
                message=error_msg,
                operation="batch_delete_collections",
                error_code="BATCH_DELETE_PARTIAL_FAILURE"
            )
        
        self.logger.info(f"Batch deleted {len(results)} collections successfully")
        return results
    
    def batch_create_environments(self, environments_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create multiple environments in batch.
        
        Args:
            environments_data: List of environment data dictionaries
            
        Returns:
            List of created environment data dictionaries
            
        Raises:
            RepositoryError: If batch creation fails
        """
        if not environments_data:
            return []
        
        results: List[Dict[str, Any]] = []
        errors: List[Tuple[str, Exception]] = []
        
        for environment_data in environments_data:
            try:
                result = self.create_environment(environment_data)
                results.append(result)
            except Exception as e:
                environment_id = environment_data.get("id") or environment_data.get("environment_id", "unknown")
                errors.append((environment_id, e))
                self.logger.error(f"Failed to create environment {environment_id} in batch: {e}")
        
        if errors:
            error_msg = f"Batch create failed for {len(errors)}/{len(environments_data)} environments"
            self.logger.error(error_msg)
            raise RepositoryError(
                message=error_msg,
                operation="batch_create_environments",
                error_code="BATCH_CREATE_PARTIAL_FAILURE"
            )
        
        self.logger.info(f"Batch created {len(results)} environments successfully")
        return results
    
    def batch_update_environments(self, updates: List[Tuple[str, Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Update multiple environments in batch.
        
        Args:
            updates: List of tuples (environment_id, environment_data)
            
        Returns:
            List of updated environment data dictionaries
            
        Raises:
            RepositoryError: If batch update fails
        """
        if not updates:
            return []
        
        results: List[Dict[str, Any]] = []
        errors: List[Tuple[str, Exception]] = []
        
        for environment_id, environment_data in updates:
            try:
                result = self.update_environment(environment_id, environment_data)
                results.append(result)
            except Exception as e:
                errors.append((environment_id, e))
                self.logger.error(f"Failed to update environment {environment_id} in batch: {e}")
        
        if errors:
            error_msg = f"Batch update failed for {len(errors)}/{len(updates)} environments"
            self.logger.error(error_msg)
            raise RepositoryError(
                message=error_msg,
                operation="batch_update_environments",
                error_code="BATCH_UPDATE_PARTIAL_FAILURE"
            )
        
        self.logger.info(f"Batch updated {len(results)} environments successfully")
        return results
    
    def batch_delete_environments(self, environment_ids: List[str]) -> List[str]:
        """
        Delete multiple environments in batch.
        
        Args:
            environment_ids: List of environment identifiers
            
        Returns:
            List of successfully deleted environment IDs
            
        Raises:
            RepositoryError: If batch deletion fails
        """
        if not environment_ids:
            return []
        
        results: List[str] = []
        errors: List[Tuple[str, Exception]] = []
        
        for environment_id in environment_ids:
            try:
                if self.delete_environment(environment_id):
                    results.append(environment_id)
            except Exception as e:
                errors.append((environment_id, e))
                self.logger.error(f"Failed to delete environment {environment_id} in batch: {e}")
        
        if errors:
            error_msg = f"Batch delete failed for {len(errors)}/{len(environment_ids)} environments"
            self.logger.error(error_msg)
            raise RepositoryError(
                message=error_msg,
                operation="batch_delete_environments",
                error_code="BATCH_DELETE_PARTIAL_FAILURE"
            )
        
        self.logger.info(f"Batch deleted {len(results)} environments successfully")
        return results