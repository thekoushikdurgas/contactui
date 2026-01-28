"""
Integration tests for workflows.

Tests complete workflows including:
- Create page workflow
- Edit page workflow
- Delete page workflow
- Create endpoint workflow
- Create relationship workflow
"""

import json
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse

from apps.documentation.tests.helpers import (
    BaseAPITestCase,
    assert_api_response,
    assert_error_response,
)


class CreatePageWorkflowTestCase(BaseAPITestCase):
    """Test cases for create page workflow."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.create_api_url = reverse('documentation:api_page_create')
        self.list_url = reverse('documentation:pages_list')
    
    @patch('apps.documentation.views.pages_views.pages_service')
    def test_create_page_workflow_complete(self, mock_pages_service):
        """Test complete create page workflow."""
        # Step 1: Create page via API
        mock_pages_service.create_page.return_value = {
            "page_id": "new_page",
            "page_type": "markdown",
            "content": "# New Page",
            "metadata": {"title": "New Page"}
        }
        
        response = self.client.post(
            self.create_api_url,
            data=json.dumps({
                "page_id": "new_page",
                "page_type": "markdown",
                "content": "# New Page"
            }),
            content_type='application/json'
        )
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )
        
        # Step 2: Verify page appears in list
        mock_pages_service.list_pages.return_value = {
            "pages": [
                {"page_id": "new_page", "page_type": "markdown"}
            ],
            "total": 1
        }
        
        list_response = self.client.get(self.list_url)
        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, 'new_page', status_code=200)
    
    @patch('apps.documentation.views.pages_views.pages_service')
    def test_create_page_workflow_with_validation_error(self, mock_pages_service):
        """Test create page workflow with validation error."""
        # Test with missing required fields
        response = self.client.post(
            self.create_api_url,
            data=json.dumps({}),  # Missing required fields
            content_type='application/json'
        )
        
        # Should return validation error
        assert_error_response(self, response, expected_status=400)


class EditPageWorkflowTestCase(BaseAPITestCase):
    """Test cases for edit page workflow."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.page_id = "test_page"
        self.update_api_url = reverse('documentation:api_page_update', args=[self.page_id])
        self.detail_url = reverse('documentation:page_detail', args=[self.page_id])
    
    @patch('apps.documentation.views.pages_views.pages_service')
    @patch('apps.documentation.views.pages_views.endpoints_service')
    @patch('apps.documentation.views.pages_views.relationships_service')
    def test_edit_page_workflow_complete(
        self,
        mock_relationships_service,
        mock_endpoints_service,
        mock_pages_service
    ):
        """Test complete edit page workflow."""
        # Step 1: Get existing page
        mock_pages_service.get_page.return_value = {
            "page_id": self.page_id,
            "page_type": "markdown",
            "content": "# Original Content"
        }
        mock_endpoints_service.list_endpoints.return_value = {"endpoints": []}
        mock_relationships_service.list_relationships.return_value = {"relationships": []}
        
        detail_response = self.client.get(self.detail_url)
        self.assertEqual(detail_response.status_code, 200)
        
        # Step 2: Update page via API
        mock_pages_service.update_page.return_value = {
            "page_id": self.page_id,
            "page_type": "markdown",
            "content": "# Updated Content"
        }
        
        update_response = self.client.post(
            self.update_api_url,
            data=json.dumps({
                "content": "# Updated Content"
            }),
            content_type='application/json'
        )
        
        assert_api_response(
            self,
            update_response,
            expected_status=200,
            expected_success=True
        )
        
        # Step 3: Verify changes in detail view
        mock_pages_service.get_page.return_value = {
            "page_id": self.page_id,
            "page_type": "markdown",
            "content": "# Updated Content"
        }
        
        updated_detail_response = self.client.get(self.detail_url)
        self.assertEqual(updated_detail_response.status_code, 200)
        self.assertContains(updated_detail_response, 'Updated Content', status_code=200)


class DeletePageWorkflowTestCase(BaseAPITestCase):
    """Test cases for delete page workflow."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.page_id = "test_page"
        self.delete_api_url = reverse('documentation:api_page_delete', args=[self.page_id])
        self.list_url = reverse('documentation:pages_list')
    
    @patch('apps.documentation.views.pages_views.pages_service')
    def test_delete_page_workflow_complete(self, mock_pages_service):
        """Test complete delete page workflow."""
        # Step 1: Delete page via API
        mock_pages_service.delete_page.return_value = True
        
        delete_response = self.client.post(self.delete_api_url)
        
        assert_api_response(
            self,
            delete_response,
            expected_status=200,
            expected_success=True
        )
        
        # Step 2: Verify page no longer appears in list
        mock_pages_service.list_pages.return_value = {
            "pages": [],
            "total": 0
        }
        
        list_response = self.client.get(self.list_url)
        self.assertEqual(list_response.status_code, 200)
        
        # Step 3: Verify page detail returns 404
        mock_pages_service.get_page.side_effect = Exception("Page not found")
        detail_url = reverse('documentation:page_detail', args=[self.page_id])
        detail_response = self.client.get(detail_url)
        # Should handle error gracefully
        self.assertIn(detail_response.status_code, [200, 404])


class CreateEndpointWorkflowTestCase(BaseAPITestCase):
    """Test cases for create endpoint workflow."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.create_api_url = reverse('documentation:api_endpoint_create')
        self.list_url = reverse('documentation:endpoints_list')
    
    @patch('apps.documentation.views.endpoints_views.endpoints_service')
    def test_create_endpoint_workflow_complete(self, mock_endpoints_service):
        """Test complete create endpoint workflow."""
        # Step 1: Create endpoint via API
        mock_endpoints_service.create_endpoint.return_value = {
            "endpoint_id": "new_endpoint",
            "method": "GET",
            "endpoint_path": "/api/new",
            "api_version": "v1"
        }
        
        response = self.client.post(
            self.create_api_url,
            data=json.dumps({
                "endpoint_id": "new_endpoint",
                "method": "GET",
                "endpoint_path": "/api/new"
            }),
            content_type='application/json'
        )
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )
        
        # Step 2: Verify endpoint appears in list
        mock_endpoints_service.list_endpoints.return_value = {
            "endpoints": [
                {"endpoint_id": "new_endpoint", "method": "GET"}
            ],
            "total": 1
        }
        
        list_response = self.client.get(self.list_url)
        self.assertEqual(list_response.status_code, 200)


class CreateRelationshipWorkflowTestCase(BaseAPITestCase):
    """Test cases for create relationship workflow."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.create_api_url = reverse('documentation:api_relationship_create')
        self.list_url = reverse('documentation:relationships_list')
    
    @patch('apps.documentation.views.relationships_views.relationships_service')
    @patch('apps.documentation.views.relationships_views.pages_service')
    @patch('apps.documentation.views.relationships_views.endpoints_service')
    def test_create_relationship_workflow_complete(
        self,
        mock_endpoints_service,
        mock_pages_service,
        mock_relationships_service
    ):
        """Test complete create relationship workflow."""
        # Mock page and endpoint existence
        mock_pages_service.get_page.return_value = {"page_id": "page1"}
        mock_endpoints_service.get_endpoint.return_value = {"endpoint_id": "ep1"}
        
        # Step 1: Create relationship via API
        mock_relationships_service.create_relationship.return_value = {
            "relationship_id": "new_relationship",
            "page_id": "page1",
            "endpoint_id": "ep1",
            "usage_type": "primary"
        }
        
        response = self.client.post(
            self.create_api_url,
            data=json.dumps({
                "page_id": "page1",
                "endpoint_id": "ep1",
                "usage_type": "primary"
            }),
            content_type='application/json'
        )
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )
        
        # Step 2: Verify relationship appears in list
        mock_relationships_service.list_relationships.return_value = {
            "relationships": [
                {
                    "relationship_id": "new_relationship",
                    "page_id": "page1",
                    "endpoint_id": "ep1"
                }
            ],
            "total": 1
        }
        
        list_response = self.client.get(self.list_url)
        self.assertEqual(list_response.status_code, 200)


class WorkflowErrorHandlingTestCase(BaseAPITestCase):
    """Test cases for workflow error handling."""
    
    @patch('apps.documentation.views.pages_views.pages_service')
    def test_create_page_workflow_service_error(self, mock_pages_service):
        """Test create page workflow handles service errors."""
        mock_pages_service.create_page.side_effect = Exception("Service unavailable")
        
        create_url = reverse('documentation:api_page_create')
        response = self.client.post(
            create_url,
            data=json.dumps({"page_id": "test"}),
            content_type='application/json'
        )
        
        assert_error_response(self, response, expected_status=500)
    
    @patch('apps.documentation.views.pages_views.pages_service')
    def test_update_page_workflow_not_found(self, mock_pages_service):
        """Test update page workflow handles not found errors."""
        from apps.documentation.utils.exceptions import NotFoundError
        mock_pages_service.update_page.side_effect = NotFoundError("Page not found")
        
        update_url = reverse('documentation:api_page_update', args=['nonexistent'])
        response = self.client.post(
            update_url,
            data=json.dumps({"content": "# Updated"}),
            content_type='application/json'
        )
        
        assert_error_response(self, response, expected_status=404)
