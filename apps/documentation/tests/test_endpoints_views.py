"""
Integration tests for endpoints views.

Tests the endpoints view layer including:
- Endpoint list view
- Endpoint detail view
- Endpoint form view
- Endpoint create API
- Endpoint update API
- Endpoint delete API
"""

import json
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.documentation.tests.helpers import (
    BaseAPITestCase,
    create_test_user,
    authenticate_client,
    assert_api_response,
    assert_error_response,
    assert_not_found_response,
)

User = get_user_model()


class EndpointsListViewTestCase(BaseAPITestCase):
    """Test cases for endpoint list view."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.list_url = reverse('documentation:endpoints_list')
    
    @patch('apps.documentation.views.endpoints_views.endpoints_service')
    def test_endpoint_list_view_success(self, mock_endpoints_service):
        """Test successful endpoint list view."""
        mock_endpoints_service.list_endpoints.return_value = {
            "endpoints": [
                {"endpoint_id": "ep1", "method": "GET", "endpoint_path": "/api/test"},
                {"endpoint_id": "ep2", "method": "POST", "endpoint_path": "/api/test2"}
            ],
            "total": 2
        }
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
    
    @patch('apps.documentation.views.endpoints_views.endpoints_service')
    def test_endpoint_list_view_with_filters(self, mock_endpoints_service):
        """Test endpoint list view with filters."""
        mock_endpoints_service.list_endpoints.return_value = {
            "endpoints": [],
            "total": 0
        }
        
        response = self.client.get(self.list_url + '?method=GET')
        self.assertEqual(response.status_code, 200)
    
    def test_endpoint_list_view_requires_login(self):
        """Test that endpoint list view requires authentication."""
        client = Client()
        response = client.get(self.list_url)
        self.assertIn(response.status_code, [302, 401])


class EndpointDetailViewTestCase(BaseAPITestCase):
    """Test cases for endpoint detail view."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.endpoint_id = "test_endpoint"
        self.detail_url = reverse('documentation:endpoint_detail', args=[self.endpoint_id])
    
    @patch('apps.documentation.views.endpoints_views.endpoints_service')
    @patch('apps.documentation.views.endpoints_views.relationships_service')
    def test_endpoint_detail_view_success(
        self,
        mock_relationships_service,
        mock_endpoints_service
    ):
        """Test successful endpoint detail view."""
        mock_endpoints_service.get_endpoint.return_value = {
            "endpoint_id": self.endpoint_id,
            "method": "GET",
            "endpoint_path": "/api/test",
            "api_version": "v1"
        }
        mock_relationships_service.list_relationships.return_value = {"relationships": []}
        
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
    
    @patch('apps.documentation.views.endpoints_views.endpoints_service')
    def test_endpoint_detail_view_not_found(self, mock_endpoints_service):
        """Test endpoint detail view with non-existent endpoint."""
        from apps.documentation.utils.exceptions import NotFoundError
        mock_endpoints_service.get_endpoint.side_effect = NotFoundError("Endpoint not found")
        
        response = self.client.get(self.detail_url)
        self.assertIn(response.status_code, [200, 404])


class EndpointFormViewTestCase(BaseAPITestCase):
    """Test cases for endpoint form view."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.create_url = reverse('documentation:endpoint_create')
        self.edit_url = reverse('documentation:endpoint_edit', args=['test_endpoint'])
    
    def test_endpoint_form_view_create_get(self):
        """Test endpoint create form GET request."""
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
    
    @patch('apps.documentation.views.endpoints_views.endpoints_service')
    def test_endpoint_form_view_edit_get(self, mock_endpoints_service):
        """Test endpoint edit form GET request."""
        mock_endpoints_service.get_endpoint.return_value = {
            "endpoint_id": "test_endpoint",
            "method": "GET",
            "endpoint_path": "/api/test"
        }
        
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 200)


class EndpointCreateAPITestCase(BaseAPITestCase):
    """Test cases for endpoint create API."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.create_api_url = reverse('documentation:api_endpoint_create')
    
    @patch('apps.documentation.views.endpoints_views.endpoints_service')
    def test_endpoint_create_api_success(self, mock_endpoints_service):
        """Test successful endpoint creation via API."""
        mock_endpoints_service.create_endpoint.return_value = {
            "endpoint_id": "new_endpoint",
            "method": "GET",
            "endpoint_path": "/api/new"
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
    
    def test_endpoint_create_api_invalid_json(self):
        """Test endpoint create API with invalid JSON."""
        response = self.client.post(
            self.create_api_url,
            data="invalid json",
            content_type='application/json'
        )
        
        assert_error_response(self, response, expected_status=400)


class EndpointUpdateAPITestCase(BaseAPITestCase):
    """Test cases for endpoint update API."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.endpoint_id = "test_endpoint"
        self.update_api_url = reverse('documentation:api_endpoint_update', args=[self.endpoint_id])
    
    @patch('apps.documentation.views.endpoints_views.endpoints_service')
    def test_endpoint_update_api_success(self, mock_endpoints_service):
        """Test successful endpoint update via API."""
        mock_endpoints_service.update_endpoint.return_value = {
            "endpoint_id": self.endpoint_id,
            "method": "POST",
            "endpoint_path": "/api/updated"
        }
        
        response = self.client.post(
            self.update_api_url,
            data=json.dumps({
                "method": "POST"
            }),
            content_type='application/json'
        )
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )
    
    @patch('apps.documentation.views.endpoints_views.endpoints_service')
    def test_endpoint_update_api_not_found(self, mock_endpoints_service):
        """Test endpoint update API with non-existent endpoint."""
        from apps.documentation.utils.exceptions import NotFoundError
        mock_endpoints_service.update_endpoint.side_effect = NotFoundError("Endpoint not found")
        
        response = self.client.post(
            self.update_api_url,
            data=json.dumps({"method": "POST"}),
            content_type='application/json'
        )
        
        assert_not_found_response(self, response, resource_name="Endpoint")


class EndpointDeleteAPITestCase(BaseAPITestCase):
    """Test cases for endpoint delete API."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.endpoint_id = "test_endpoint"
        self.delete_api_url = reverse('documentation:api_endpoint_delete', args=[self.endpoint_id])
    
    @patch('apps.documentation.views.endpoints_views.endpoints_service')
    def test_endpoint_delete_api_success(self, mock_endpoints_service):
        """Test successful endpoint deletion via API."""
        mock_endpoints_service.delete_endpoint.return_value = True
        
        response = self.client.post(self.delete_api_url)
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )
    
    @patch('apps.documentation.views.endpoints_views.endpoints_service')
    def test_endpoint_delete_api_not_found(self, mock_endpoints_service):
        """Test endpoint delete API with non-existent endpoint."""
        from apps.documentation.utils.exceptions import NotFoundError
        mock_endpoints_service.delete_endpoint.side_effect = NotFoundError("Endpoint not found")
        
        response = self.client.post(self.delete_api_url)
        
        assert_not_found_response(self, response, resource_name="Endpoint")
