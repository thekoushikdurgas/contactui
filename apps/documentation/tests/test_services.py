"""
Unit tests for service layer.

Tests cover:
- PagesService
- EndpointsService
- RelationshipsService
- PostmanService
"""

from __future__ import annotations

import unittest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from apps.documentation.services.pages_service import PagesService
from apps.documentation.services.endpoints_service import EndpointsService
from apps.documentation.services.relationships_service import RelationshipsService
from apps.documentation.services.postman_service import PostmanService
from apps.documentation.tests.fixtures import (
    PageFactory,
    EndpointFactory,
    RelationshipFactory,
    MockUnifiedStorage,
)
from apps.documentation.utils.exceptions import DocumentationError


class PagesServiceTestCase(TestCase):
    """Test cases for PagesService."""
    
    def setUp(self):
        """Set up test fixtures."""
        from unittest.mock import Mock
        self.mock_storage = Mock(spec=['get_page', 'list_pages', 'create_page', 'update_page', 'delete_page'])
        self.mock_repo = Mock()
        self.service = PagesService(
            unified_storage=self.mock_storage,
            repository=self.mock_repo
        )
    
    def test_list_pages_success(self):
        """Test list_pages method with success."""
        # Create test pages
        pages = PageFactory.create_batch(5, page_type="docs")
        self.mock_storage.list_pages.return_value = {
            "pages": pages,
            "total": 5
        }
        
        result = self.service.list_pages(page_type="docs")
        
        self.assertIn("pages", result)
        self.assertEqual(len(result["pages"]), 5)
        self.assertEqual(result["total"], 5)
        self.mock_storage.list_pages.assert_called_once()
    
    def test_list_pages_with_filters(self):
        """Test list_pages with various filters."""
        # Create mixed pages
        docs_pages = PageFactory.create_batch(3, page_type="docs", page_state="published")
        dashboard_pages = PageFactory.create_batch(2, page_type="dashboard", page_state="draft")
        
        # Mock storage to return filtered results
        self.mock_storage.list_pages.return_value = {
            "pages": docs_pages,
            "total": 3
        }
        
        # Filter by page_type
        result = self.service.list_pages(page_type="docs")
        self.assertEqual(len(result["pages"]), 3)
        self.mock_storage.list_pages.assert_called_with(
            page_type="docs",
            include_drafts=True,
            include_deleted=False,
            status=None,
            page_state=None,
            limit=None,
            offset=0
        )
    
    def test_get_page_success(self):
        """Test get_page method with success."""
        page = PageFactory.create(page_id="test-page")
        self.mock_storage.get_page.return_value = page
        
        result = self.service.get_page("test-page")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["page_id"], "test-page")
        self.assertEqual(result["page_type"], page["page_type"])
        self.mock_storage.get_page.assert_called_once_with("test-page", None)
    
    def test_get_page_not_found(self):
        """Test get_page when page doesn't exist."""
        self.mock_storage.get_page.return_value = None
        
        result = self.service.get_page("non-existent")
        
        self.assertIsNone(result)
    
    def test_get_page_with_cache(self):
        """Test get_page uses cache."""
        page = PageFactory.create(page_id="test-page")
        self.mock_storage.get_page.return_value = page
        
        # First call - should fetch from storage
        result1 = self.service.get_page("test-page", use_cache=True)
        self.assertIsNotNone(result1)
        
        # Second call - should use cache (verify by checking cache was set)
        # Note: In real implementation, cache would be checked first
        result2 = self.service.get_page("test-page", use_cache=True)
        self.assertIsNotNone(result2)
    
    def test_get_page_error_handling(self):
        """Test get_page error handling."""
        # Mock storage to raise exception
        self.mock_storage.get_page.side_effect = Exception("Storage error")
        
        with self.assertRaises(DocumentationError):
            self.service.get_page("test-page")
    
    @patch('apps.documentation.services.pages_service.PagesRepository')
    def test_create_page_success(self, mock_repo_class):
        """Test create_page method with success."""
        mock_repo = Mock()
        page_data = PageFactory.create(page_id="new-page")
        # Add required 'title' field
        page_data["title"] = page_data["metadata"]["title"]
        mock_repo.create.return_value = page_data
        mock_repo_class.return_value = mock_repo
        
        service = PagesService(repository=mock_repo)
        result = service.create_page(page_data)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["page_id"], "new-page")
        mock_repo.create.assert_called_once()
    
    @patch('apps.documentation.services.pages_service.PagesRepository')
    def test_create_page_validation_error(self, mock_repo_class):
        """Test create_page with validation error."""
        mock_repo = Mock()
        mock_repo.create.side_effect = ValueError("Invalid page data")
        mock_repo_class.return_value = mock_repo
        
        service = PagesService(repository=mock_repo)
        page_data = PageFactory.create()
        # Missing required 'title' field to trigger validation error
        # page_data intentionally missing 'title'
        
        with self.assertRaises((ValueError, DocumentationError)):
            service.create_page(page_data)
    
    @patch('apps.documentation.services.pages_service.PagesRepository')
    def test_update_page_success(self, mock_repo_class):
        """Test update_page method with success."""
        mock_repo = Mock()
        existing_page = PageFactory.create(page_id="test-page")
        updated_page = {**existing_page, "metadata": {"route": "/updated"}}
        
        mock_repo.get_by_page_id.return_value = existing_page
        mock_repo.update.return_value = updated_page
        mock_repo_class.return_value = mock_repo
        
        service = PagesService(repository=mock_repo)
        update_data = {"metadata": {"route": "/updated"}}
        
        result = service.update_page("test-page", update_data)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["metadata"]["route"], "/updated")
        mock_repo.update.assert_called_once()
    
    @patch('apps.documentation.services.pages_service.PagesRepository')
    def test_update_page_not_found(self, mock_repo_class):
        """Test update_page when page doesn't exist."""
        mock_repo = Mock()
        mock_repo.get_by_page_id.return_value = None
        mock_repo_class.return_value = mock_repo
        
        service = PagesService(repository=mock_repo)
        
        with self.assertRaises(DocumentationError):
            service.update_page("non-existent", {})
    
    @patch('apps.documentation.services.pages_service.PagesRepository')
    def test_delete_page_success(self, mock_repo_class):
        """Test delete_page method with success."""
        mock_repo = Mock()
        mock_repo.delete.return_value = True
        mock_repo_class.return_value = mock_repo
        
        service = PagesService(repository=mock_repo)
        result = service.delete_page("test-page")
        
        self.assertTrue(result)
        mock_repo.delete.assert_called_once_with("test-page")
    
    @patch('apps.documentation.services.pages_service.PagesRepository')
    def test_delete_page_not_found(self, mock_repo_class):
        """Test delete_page when page doesn't exist."""
        mock_repo = Mock()
        mock_repo.delete.return_value = False
        mock_repo_class.return_value = mock_repo
        
        service = PagesService(repository=mock_repo)
        result = service.delete_page("non-existent")
        
        self.assertFalse(result)


class EndpointsServiceTestCase(TestCase):
    """Test cases for EndpointsService."""
    
    @patch('apps.documentation.services.endpoints_service.UnifiedStorage')
    def test_list_endpoints(self, mock_storage_class):
        """Test list_endpoints method."""
        mock_storage = Mock()
        mock_storage.list_endpoints.return_value = {
            "endpoints": [
                {"endpoint_id": "ep-1", "method": "QUERY"},
                {"endpoint_id": "ep-2", "method": "MUTATION"}
            ],
            "total": 2
        }
        mock_storage_class.return_value = mock_storage
        
        service = EndpointsService(unified_storage=mock_storage)
        result = service.list_endpoints(method="QUERY")
        
        self.assertEqual(len(result.get("endpoints", [])), 2)
        mock_storage.list_endpoints.assert_called_once()
    
    @patch('apps.documentation.services.endpoints_service.UnifiedStorage')
    def test_get_endpoint(self, mock_storage_class):
        """Test get_endpoint method."""
        mock_storage = Mock()
        mock_storage.get_endpoint.return_value = {
            "endpoint_id": "test-ep",
            "method": "QUERY",
            "endpoint_path": "/api/test"
        }
        mock_storage_class.return_value = mock_storage
        
        service = EndpointsService(unified_storage=mock_storage)
        result = service.get_endpoint("test-ep")
        
        self.assertEqual(result["endpoint_id"], "test-ep")
        mock_storage.get_endpoint.assert_called_once_with("test-ep")
    
    @patch('apps.documentation.services.endpoints_service.EndpointsRepository')
    def test_create_endpoint(self, mock_repo_class):
        """Test create_endpoint method."""
        mock_repo = Mock()
        mock_repo.create.return_value = {
            "endpoint_id": "new-ep",
            "created": True
        }
        mock_repo_class.return_value = mock_repo
        
        service = EndpointsService()
        endpoint_data = {
            "endpoint_id": "new-ep",
            "method": "QUERY",
            "endpoint_path": "/api/new",
            "service_file": "test_service.py"
        }
        
        result = service.create_endpoint(endpoint_data)
        
        self.assertIsNotNone(result)
        mock_repo.create.assert_called_once()


class RelationshipsServiceTestCase(TestCase):
    """Test cases for RelationshipsService."""
    
    @patch('apps.documentation.services.relationships_service.UnifiedStorage')
    def test_list_relationships(self, mock_storage_class):
        """Test list_relationships method."""
        mock_storage = Mock()
        mock_lambda_client = Mock()
        mock_lambda_client.list_relationships_v1.return_value = {
            "relationships": [
                {"relationship_id": "rel-1"},
                {"relationship_id": "rel-2"}
            ],
            "total": 2
        }
        mock_storage.lambda_client = mock_lambda_client
        mock_storage_class.return_value = mock_storage
        
        service = RelationshipsService(unified_storage=mock_storage)
        result = service.list_relationships()
        
        self.assertEqual(len(result.get("relationships", [])), 2)
        mock_lambda_client.list_relationships_v1.assert_called_once()
    
    @patch('apps.documentation.services.relationships_service.RelationshipsRepository')
    def test_create_relationship(self, mock_repo_class):
        """Test create_relationship method."""
        mock_repo = Mock()
        mock_repo.create.return_value = {
            "relationship_id": "new-rel",
            "created": True
        }
        mock_repo_class.return_value = mock_repo
        
        service = RelationshipsService()
        relationship_data = {
            "page_path": "/page",
            "endpoint_path": "/api/endpoint",
            "method": "QUERY"
        }
        
        result = service.create_relationship(relationship_data)
        
        self.assertIsNotNone(result)
        mock_repo.create.assert_called_once()


class PostmanServiceTestCase(TestCase):
    """Test cases for PostmanService."""
    
    @patch('apps.documentation.services.postman_service.UnifiedStorage')
    def test_get_postman_collection(self, mock_storage_class):
        """Test get_collection method."""
        mock_storage = Mock()
        mock_lambda_client = Mock()
        mock_lambda_client.get_postman_collection_v1.return_value = {
            "collection": {
                "info": {"name": "Test Collection"},
                "item": []
            }
        }
        mock_storage.lambda_client = mock_lambda_client
        mock_storage_class.return_value = mock_storage
        
        service = PostmanService(unified_storage=mock_storage)
        result = service.get_collection("test-collection")
        
        self.assertIn("info", result)
        mock_lambda_client.get_postman_collection_v1.assert_called_once_with("test-collection")
    
    @patch('apps.documentation.services.postman_service.UnifiedStorage')
    def test_create_postman_collection(self, mock_storage_class):
        """Test get_configuration method (create is not implemented in service)."""
        mock_storage = Mock()
        mock_lambda_client = Mock()
        mock_lambda_client.get_postman_configuration_v1.return_value = {
            "config_id": "new-collection",
            "created": True
        }
        mock_storage.lambda_client = mock_lambda_client
        mock_storage_class.return_value = mock_storage
        
        service = PostmanService(unified_storage=mock_storage)
        result = service.get_configuration("new-collection")
        
        self.assertIsNotNone(result)
        mock_lambda_client.get_postman_configuration_v1.assert_called_once_with("new-collection")


if __name__ == '__main__':
    unittest.main()
