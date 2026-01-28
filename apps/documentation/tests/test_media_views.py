"""
Integration tests for media views.

Tests the media view layer including:
- Media file list API
- Media file get API
- Media file create API
- Media file update API
- Media file delete API
- Media sync APIs
- Media index regeneration APIs
"""

import json
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from pathlib import Path

from apps.documentation.tests.helpers import (
    BaseAPITestCase,
    assert_api_response,
    assert_error_response,
)


class MediaFilesListAPITestCase(BaseAPITestCase):
    """Test cases for media files list API."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.list_api_url = reverse('documentation:api_media_files')
    
    @patch('apps.documentation.views.media_views.MediaManagerService')
    def test_list_files_api_success(self, mock_service_class):
        """Test successful media files list API."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.list_files.return_value = [
            {"file_path": "file1.json", "name": "file1.json", "size": 1024},
            {"file_path": "file2.json", "name": "file2.json", "size": 2048}
        ]
        
        response = self.client.get(self.list_api_url)
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )
    
    @patch('apps.documentation.views.media_views.MediaManagerService')
    def test_list_files_api_resource_type_param(self, mock_service_class):
        """Test list files API accepts resource_type query param."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.list_files.return_value = []
        
        for resource_type in ('pages', 'endpoints', 'relationships', 'postman'):
            response = self.client.get(
                self.list_api_url,
                {'resource_type': resource_type}
            )
            self.assertEqual(response.status_code, 200)
            mock_service.list_files.assert_called()
            call_kwargs = mock_service.list_files.call_args
            self.assertEqual(call_kwargs[0][0], resource_type)
    
    @patch('apps.documentation.views.media_views.MediaManagerService')
    def test_list_files_api_subdirectory_param(self, mock_service_class):
        """Test list files API accepts subdirectory filter for relationships/postman."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.list_files.return_value = []
        
        response = self.client.get(
            self.list_api_url,
            {'resource_type': 'relationships', 'subdirectory': 'by-page'}
        )
        self.assertEqual(response.status_code, 200)
        mock_service.list_files.assert_called_once()
        filters = mock_service.list_files.call_args[0][1]
        self.assertEqual(filters.get('subdirectory'), 'by-page')


class MediaFileGetAPITestCase(BaseAPITestCase):
    """Test cases for media file get API."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.file_path = "test/file.md"
        self.get_api_url = reverse('documentation:api_media_file', args=[self.file_path])
    
    @patch('apps.documentation.views.media_views.MediaManagerService')
    def test_get_file_api_success(self, mock_service_class):
        """Test successful media file get API."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.get_file.return_value = {
            "path": self.file_path,
            "content": "# Test File",
            "size": 1024
        }
        
        response = self.client.get(self.get_api_url)
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )


class MediaFileCreateAPITestCase(BaseAPITestCase):
    """Test cases for media file create API."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.create_api_url = reverse('documentation:api_media_file_create')
    
    @patch('apps.documentation.views.media_views.MediaManagerService')
    def test_create_file_api_success(self, mock_service_class):
        """Test successful media file creation via API."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.create_file.return_value = {
            "path": "new/file.md",
            "size": 512
        }
        
        response = self.client.post(
            self.create_api_url,
            data=json.dumps({
                "file_path": "new/file.md",
                "content": "# New File"
            }),
            content_type='application/json'
        )
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )


class MediaFileUpdateAPITestCase(BaseAPITestCase):
    """Test cases for media file update API."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.file_path = "test/file.md"
        self.update_api_url = reverse('documentation:api_media_file_update', args=[self.file_path])
    
    @patch('apps.documentation.views.media_views.MediaManagerService')
    def test_update_file_api_success(self, mock_service_class):
        """Test successful media file update via API."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.update_file.return_value = {
            "path": self.file_path,
            "size": 2048
        }
        
        response = self.client.post(
            self.update_api_url,
            data=json.dumps({
                "content": "# Updated File"
            }),
            content_type='application/json'
        )
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )


class MediaFileDeleteAPITestCase(BaseAPITestCase):
    """Test cases for media file delete API."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.file_path = "test/file.md"
        self.delete_api_url = reverse('documentation:api_media_file_delete', args=[self.file_path])
    
    @patch('apps.documentation.views.media_views.MediaManagerService')
    def test_delete_file_api_success(self, mock_service_class):
        """Test successful media file deletion via API."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.delete_file.return_value = True
        
        response = self.client.post(self.delete_api_url)
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )


class MediaSyncAPITestCase(BaseAPITestCase):
    """Test cases for media sync APIs."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.sync_status_url = reverse('documentation:api_media_sync_status')
        self.file_path = "test/file.md"
        self.sync_file_url = reverse('documentation:api_media_sync_file', args=[self.file_path])
        self.bulk_sync_url = reverse('documentation:api_media_bulk_sync')
    
    @patch('apps.documentation.views.media_views.MediaSyncService')
    def test_sync_status_api_success(self, mock_service_class):
        """Test successful sync status API."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.get_sync_status.return_value = {
            "synced": 10,
            "pending": 2,
            "failed": 0
        }
        
        response = self.client.get(self.sync_status_url)
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )
    
    @patch('apps.documentation.views.media_views.MediaSyncService')
    def test_sync_file_api_success(self, mock_service_class):
        """Test successful file sync API."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.sync_file.return_value = {
            "path": self.file_path,
            "synced": True
        }
        
        response = self.client.post(self.sync_file_url)
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )


class MediaIndexRegenerationAPITestCase(BaseAPITestCase):
    """Test cases for media index regeneration APIs."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.regenerate_pages_url = reverse('documentation:api_media_regenerate_pages_index')
        self.regenerate_endpoints_url = reverse('documentation:api_media_regenerate_endpoints_index')
        self.regenerate_all_url = reverse('documentation:api_media_regenerate_all_indexes')
    
    @patch('apps.documentation.views.media_views._regenerate_index')
    def test_regenerate_pages_index_api_success(self, mock_regenerate):
        """Test successful pages index regeneration."""
        mock_regenerate.return_value = None
        
        response = self.client.post(self.regenerate_pages_url)
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )
    
    @patch('apps.documentation.views.media_views._regenerate_index')
    def test_regenerate_all_indexes_api_success(self, mock_regenerate):
        """Test successful all indexes regeneration."""
        mock_regenerate.return_value = None
        
        response = self.client.post(self.regenerate_all_url)
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )
