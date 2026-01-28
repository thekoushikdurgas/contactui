"""Synchronous S3 JSON storage client for Django."""

import json
import logging
from typing import Any, Callable, Dict, List, Optional

from apps.core.services.s3_service import S3Service
from apps.core.exceptions import S3Error
from apps.documentation.utils.exceptions import RepositoryError
from django.conf import settings

logger = logging.getLogger(__name__)


class S3JSONStorage:
    """Synchronous client for S3 JSON file operations."""

    def __init__(self, s3_service: Optional[S3Service] = None):
        """Initialize S3 JSON storage client.
        
        Args:
            s3_service: Optional S3Service instance. If not provided, creates new one.
        """
        self.s3_service = s3_service or S3Service()
        self.bucket_name = settings.S3_BUCKET_NAME
        self.max_retries = 3
        self.retry_delay = 0.1  # Initial delay in seconds

    def read_json(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """
        Read and parse JSON file from S3.

        Args:
            s3_key: The S3 key (path) of the JSON file

        Returns:
            Parsed JSON data as dictionary, or None if file doesn't exist
            
        Raises:
            S3Error: If S3 operation fails (other than file not found)
        """
        try:
            file_content = self.s3_service.download_file(s3_key)
            if not isinstance(file_content, (bytes, bytearray, str)):
                logger.warning(f"Unexpected file_content type for {s3_key}: {type(file_content)}")
                return None
            if isinstance(file_content, bytes):
                content_str = file_content.decode('utf-8')
            else:
                content_str = file_content
            return json.loads(content_str)
        except S3Error as e:
            if 'NoSuchKey' in str(e) or '404' in str(e) or 'not found' in str(e).lower() or 'FILE_NOT_FOUND' in str(e):
                logger.debug(f"JSON file not found: {s3_key}")
                return None
            raise
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"Failed to parse JSON from {s3_key}: {e}")
            raise RepositoryError(
                f"Failed to parse JSON from S3: {str(e)}",
                entity_id=s3_key,
                operation='read_json',
                error_code='JSON_PARSE_ERROR'
            )

    def write_json(
        self,
        s3_key: str,
        data: Dict[str, Any],
        etag: Optional[str] = None,
    ) -> str:
        """
        Write JSON data to S3.

        Args:
            s3_key: The S3 key (path) where to write the JSON
            data: The data dictionary to write as JSON
            etag: Optional ETag for conditional write (not fully implemented in sync version)

        Returns:
            The S3 key where the file was written
            
        Raises:
            S3Error: If S3 upload fails
            RepositoryError: If JSON serialization fails
        """
        try:
            json_content = json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8')
            self.s3_service.upload_file(
                file_content=json_content,
                s3_key=s3_key,
                content_type='application/json'
            )
            logger.info(f"Wrote JSON to S3: {s3_key}")
            return s3_key
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize JSON for {s3_key}: {e}")
            raise RepositoryError(
                f"Failed to serialize JSON: {str(e)}",
                entity_id=s3_key,
                operation='write_json',
                error_code='JSON_SERIALIZE_ERROR'
            )
        except S3Error:
            raise

    def delete_json(self, s3_key: str) -> bool:
        """
        Delete JSON file from S3.

        Args:
            s3_key: The S3 key (path) of the JSON file to delete

        Returns:
            True if deleted successfully
            
        Raises:
            S3Error: If S3 delete fails
        """
        try:
            return self.s3_service.delete_file(s3_key)
        except S3Error as e:
            if 'NoSuchKey' in str(e) or '404' in str(e) or 'not found' in str(e).lower() or 'FILE_NOT_FOUND' in str(e):
                logger.debug(f"JSON file not found (already deleted): {s3_key}")
                return True
            raise
        except Exception as e:
            logger.error(f"Failed to delete JSON from {s3_key}: {e}")
            return False

    def list_json_files(
        self,
        prefix: str,
        max_keys: Optional[int] = None,
    ) -> List[str]:
        """
        List JSON files in S3 with given prefix.

        Args:
            prefix: The prefix to filter files by
            max_keys: Maximum number of keys to return

        Returns:
            List of S3 keys (paths) for JSON files
        """
        try:
            files = self.s3_service.list_files(prefix=prefix, max_keys=max_keys or 1000)
            keys = [f['key'] for f in files if f['key'].endswith('.json')]
            return keys[:max_keys] if max_keys else keys
        except Exception as e:
            logger.error(f"Failed to list JSON files with prefix {prefix}: {e}")
            return []

    def file_exists(self, s3_key: str) -> bool:
        """
        Check if JSON file exists in S3.

        Args:
            s3_key: The S3 key (path) to check

        Returns:
            True if file exists, False otherwise
        """
        try:
            files = self.s3_service.list_files(prefix=s3_key, max_keys=1)
            return len(files) > 0 and files[0]['key'] == s3_key
        except Exception:
            return False
