"""
S3 Batch Operations for optimized bulk operations.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from apps.documentation.repositories.s3_json_storage import S3JSONStorage

logger = logging.getLogger(__name__)


class S3BatchOperations:
    """
    Batch operations for S3 to improve performance.
    
    Provides:
    - Parallel batch reads
    - Parallel batch writes
    - Connection reuse through shared S3Service
    """
    
    def __init__(self, storage: Optional[S3JSONStorage] = None, max_workers: int = 10):
        """
        Initialize batch operations.
        
        Args:
            storage: S3JSONStorage instance
            max_workers: Maximum number of parallel workers
        """
        if storage is None:
            from apps.documentation.services import get_shared_s3_storage
            self.storage = get_shared_s3_storage()
        else:
            self.storage = storage
        self.max_workers = max_workers
    
    def batch_read_json(
        self,
        s3_keys: List[str],
        fail_on_error: bool = False
    ) -> Dict[str, Any]:
        """
        Read multiple JSON files from S3 in parallel.
        
        Args:
            s3_keys: List of S3 keys to read
            fail_on_error: If True, raise exception on first error; if False, continue and log errors
            
        Returns:
            Dictionary mapping S3 keys to their JSON data (or None if not found/error)
        """
        results = {}
        
        def read_single(key: str) -> Tuple[str, Optional[Dict[str, Any]]]:
            """Read a single JSON file."""
            try:
                data = self.storage.read_json(key)
                return (key, data)
            except Exception as e:
                logger.warning(f"Failed to read {key}: {e}")
                if fail_on_error:
                    raise
                return (key, None)
        
        # Execute reads in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_key = {
                executor.submit(read_single, key): key
                for key in s3_keys
            }
            
            for future in as_completed(future_to_key):
                try:
                    key, data = future.result()
                    results[key] = data
                except Exception as e:
                    key = future_to_key[future]
                    logger.error(f"Error reading {key}: {e}")
                    if fail_on_error:
                        raise
                    results[key] = None
        
        return results
    
    def batch_write_json(
        self,
        items: List[Tuple[str, Dict[str, Any]]],
        fail_on_error: bool = False
    ) -> Dict[str, bool]:
        """
        Write multiple JSON files to S3 in parallel.
        
        Args:
            items: List of tuples (s3_key, data_dict)
            fail_on_error: If True, raise exception on first error; if False, continue and log errors
            
        Returns:
            Dictionary mapping S3 keys to success status (True/False)
        """
        results = {}
        
        def write_single(key: str, data: Dict[str, Any]) -> Tuple[str, bool]:
            """Write a single JSON file."""
            try:
                self.storage.write_json(key, data)
                return (key, True)
            except Exception as e:
                logger.warning(f"Failed to write {key}: {e}")
                if fail_on_error:
                    raise
                return (key, False)
        
        # Execute writes in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_key = {
                executor.submit(write_single, key, data): key
                for key, data in items
            }
            
            for future in as_completed(future_to_key):
                try:
                    key, success = future.result()
                    results[key] = success
                except Exception as e:
                    key = future_to_key[future]
                    logger.error(f"Error writing {key}: {e}")
                    if fail_on_error:
                        raise
                    results[key] = False
        
        return results
    
    def batch_delete(
        self,
        s3_keys: List[str],
        fail_on_error: bool = False
    ) -> Dict[str, bool]:
        """
        Delete multiple files from S3 in parallel.
        
        Args:
            s3_keys: List of S3 keys to delete
            fail_on_error: If True, raise exception on first error; if False, continue and log errors
            
        Returns:
            Dictionary mapping S3 keys to success status (True/False)
        """
        results = {}
        
        def delete_single(key: str) -> Tuple[str, bool]:
            """Delete a single file."""
            try:
                self.storage.delete_json(key)
                return (key, True)
            except Exception as e:
                logger.warning(f"Failed to delete {key}: {e}")
                if fail_on_error:
                    raise
                return (key, False)
        
        # Execute deletes in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_key = {
                executor.submit(delete_single, key): key
                for key in s3_keys
            }
            
            for future in as_completed(future_to_key):
                try:
                    key, success = future.result()
                    results[key] = success
                except Exception as e:
                    key = future_to_key[future]
                    logger.error(f"Error deleting {key}: {e}")
                    if fail_on_error:
                        raise
                    results[key] = False
        
        return results
