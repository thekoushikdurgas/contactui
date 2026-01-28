"""Core S3 service for AWS S3 operations."""

import boto3
import logging
from typing import Optional, Dict, Any, List
from django.conf import settings
from botocore.exceptions import ClientError, BotoCoreError
from apps.core.exceptions import S3Error
from apps.core.decorators.retry import retry_on_network_error

logger = logging.getLogger(__name__)


class S3Service:
    """Service for interacting with AWS S3."""
    
    def __init__(self):
        """Initialize S3 client with connection pooling."""
        self.session = boto3.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.s3_client = self.session.client('s3')
        self.bucket_name = settings.S3_BUCKET_NAME
        self.data_prefix = settings.S3_DATA_PREFIX
        self.documentation_prefix = settings.S3_DOCUMENTATION_PREFIX
    
    @retry_on_network_error(max_retries=3, initial_delay=1.0, max_delay=10.0)
    def upload_file(self, file_content: bytes, s3_key: str, content_type: str = 'text/plain') -> bool:
        """
        Upload a file to S3 with retry logic for network errors.
        
        Args:
            file_content: File content as bytes
            s3_key: S3 object key (path)
            content_type: MIME type of the file
            
        Returns:
            True if successful
            
        Raises:
            S3Error: If upload fails
        """
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type
            )
            logger.info(f"File uploaded to S3: {s3_key}")
            return True
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Error uploading file to S3: {str(e)}")
            raise S3Error(
                f"Failed to upload file to S3: {str(e)}",
                s3_key=s3_key,
                operation='upload',
                error_code='S3_UPLOAD_FAILED'
            )
    
    def download_file(self, s3_key: str) -> bytes:
        """
        Download a file from S3.
        
        Args:
            s3_key: S3 object key (path)
            
        Returns:
            File content as bytes
            
        Raises:
            S3Error: If download fails
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return response['Body'].read()
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'NoSuchKey':
                raise S3Error(
                    f"File not found in S3: {s3_key}",
                    s3_key=s3_key,
                    operation='download',
                    error_code='FILE_NOT_FOUND'
                )
            logger.error(f"Error downloading file from S3: {str(e)}")
            raise S3Error(
                f"Failed to download file from S3: {str(e)}",
                s3_key=s3_key,
                operation='download',
                error_code='S3_DOWNLOAD_FAILED'
            )
    
    def list_files(self, prefix: str, max_keys: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        List files in S3 with given prefix.
        
        Args:
            prefix: The prefix to filter files by
            max_keys: Maximum number of keys to return
            
        Returns:
            List of file dictionaries with 'key' and 'size'
        """
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys or 1000
            )
            
            files = []
            for page in page_iterator:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        files.append({
                            'key': obj['Key'],
                            'size': obj['Size'],
                            'last_modified': obj['LastModified']
                        })
            
            return files
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Error listing files from S3: {str(e)}")
            return []
    
    @retry_on_network_error(max_retries=3, initial_delay=1.0, max_delay=10.0)
    def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3 with retry logic for network errors.
        
        Args:
            s3_key: S3 object key (path)
            
        Returns:
            True if successful
            
        Raises:
            S3Error: If delete fails
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"File deleted from S3: {s3_key}")
            return True
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Error deleting file from S3: {str(e)}")
            raise S3Error(
                f"Failed to delete file from S3: {str(e)}",
                s3_key=s3_key,
                operation='delete',
                error_code='S3_DELETE_FAILED'
            )
    
    def get_presigned_url(
        self,
        s3_key: str,
        expiration: int = 3600,
        http_method: str = 'GET'
    ) -> Optional[str]:
        """
        Generate a presigned URL for S3 object access.
        
        Args:
            s3_key: S3 object key (path)
            expiration: URL expiration time in seconds (default: 1 hour)
            http_method: HTTP method ('GET' or 'PUT')
            
        Returns:
            Presigned URL string, or None if generation fails
        """
        try:
            from botocore.client import Config
            s3_client = self.session.client('s3', config=Config(signature_version='s3v4'))
            
            url = s3_client.generate_presigned_url(
                'get_object' if http_method == 'GET' else 'put_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            logger.info(f"Generated presigned URL for {s3_key} (expires in {expiration}s)")
            return url
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Error generating presigned URL for {s3_key}: {str(e)}")
            return None
    
    @retry_on_network_error(max_retries=3, initial_delay=1.0, max_delay=10.0)
    def copy_file(
        self,
        source_key: str,
        destination_key: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Copy a file within S3 with retry logic for network errors.
        
        Args:
            source_key: Source S3 object key
            destination_key: Destination S3 object key
            metadata: Optional metadata to set on copied object
            
        Returns:
            True if successful
            
        Raises:
            S3Error: If copy fails
        """
        try:
            copy_source = {
                'Bucket': self.bucket_name,
                'Key': source_key
            }
            
            copy_params = {
                'Bucket': self.bucket_name,
                'Key': destination_key,
                'CopySource': copy_source
            }
            
            if metadata:
                copy_params['Metadata'] = metadata
                copy_params['MetadataDirective'] = 'REPLACE'
            
            self.s3_client.copy_object(**copy_params)
            logger.info(f"Copied file from {source_key} to {destination_key}")
            return True
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Error copying file from {source_key} to {destination_key}: {str(e)}")
            raise S3Error(
                f"Failed to copy file in S3: {str(e)}",
                s3_key=source_key,
                operation='copy',
                error_code='S3_COPY_FAILED'
            )
    
    def file_exists(self, s3_key: str) -> bool:
        """
        Check if a file exists in S3.
        
        Args:
            s3_key: S3 object key (path)
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == '404' or error_code == 'NoSuchKey':
                return False
            # Re-raise other errors
            logger.error(f"Error checking file existence for {s3_key}: {str(e)}")
            raise S3Error(
                f"Failed to check file existence: {str(e)}",
                s3_key=s3_key,
                operation='exists',
                error_code='S3_CHECK_FAILED'
            )
        except (BotoCoreError, Exception) as e:
            logger.error(f"Error checking file existence for {s3_key}: {str(e)}")
            return False
