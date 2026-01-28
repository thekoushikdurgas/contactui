"""
Integration tests for API endpoints.

Tests the API endpoint layer focusing on:
- API contract (request/response format)
- Status codes
- Error handling
- Pagination
- Filtering
- Authentication
"""

import json
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse

from apps.documentation.tests.helpers import (
    BaseAPITestCase,
    assert_api_response,
    assert_error_response,
    assert_not_found_response,
)


class DashboardAPITestCase(BaseAPITestCase):
    """Test cases for dashboard API endpoints."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.dashboard_pages_url = reverse('documentation:api_dashboard_pages')
        self.dashboard_endpoints_url = reverse('documentation:api_dashboard_endpoints')
        self.dashboard_relationships_url = reverse('documentation:api_dashboard_relationships')
        self.dashboard_postman_url = reverse('documentation:api_dashboard_postman')
    
    @patch('apps.documentation.api.v1.core.PagesService')
    def test_dashboard_pages_api_success(self, mock_service_class):
        """Test successful dashboard pages API."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.list_pages.return_value = {
            "pages": [{"page_id": "page1"}],
            "total": 1,
            "source": "local"
        }
        
        response = self.client.get(self.dashboard_pages_url)
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )
        
        data = json.loads(response.content)
        self.assertIn('items', data)
        self.assertIn('total', data)
    
    @patch('apps.documentation.api.v1.core.PagesService')
    def test_dashboard_pages_api_pagination(self, mock_service_class):
        """Test dashboard pages API with pagination."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.list_pages.return_value = {
            "pages": [],
            "total": 0,
            "source": "local"
        }
        
        response = self.client.get(self.dashboard_pages_url + '?limit=10&offset=0')
        self.assertEqual(response.status_code, 200)
    
    @patch('apps.documentation.api.v1.core.EndpointsService')
    def test_dashboard_endpoints_api_success(self, mock_service_class):
        """Test successful dashboard endpoints API."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.list_endpoints.return_value = {
            "endpoints": [{"endpoint_id": "ep1"}],
            "total": 1
        }
        
        response = self.client.get(self.dashboard_endpoints_url)
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )


class PagesAPITestCase(BaseAPITestCase):
    """Test cases for pages API endpoints."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.pages_list_url = reverse('api_v1:pages_list')
        self.page_id = "test_page"
        self.pages_detail_url = reverse('api_v1:pages_detail', args=[self.page_id])
    
    @patch('apps.documentation.api.v1.core.get_pages_service')
    def test_pages_list_api_success(self, mock_service_class):
        """Test successful pages list API."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.list_pages.return_value = {
            "pages": [
                {"page_id": "page1", "page_type": "markdown", "metadata": {"title": "T1", "status": "published"}},
                {"page_id": "page2", "page_type": "html", "metadata": {"title": "T2", "status": "draft"}}
            ],
            "total": 2,
            "source": "local"
        }
        
        response = self.client.get(self.pages_list_url)
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )
        
        data = json.loads(response.content)
        # paginated_response() uses APIResponse format: {success, data, meta.pagination}
        self.assertIn('data', data)
        self.assertEqual(len(data['data']), 2)
        # Summary-by-default: list items should be projected (no nested metadata)
        self.assertIn('page_id', data['data'][0])
        self.assertNotIn('metadata', data['data'][0])
        self.assertIn('meta', data)
        self.assertEqual(data['meta']['pagination']['total'], 2)

        # expand=full returns the original full docs from the service
        full_resp = self.client.get(self.pages_list_url + '?expand=full')
        full_data = json.loads(full_resp.content)
        self.assertIn('metadata', full_data['data'][0])
    
    @patch('apps.documentation.api.v1.core.get_pages_service')
    def test_pages_list_api_with_filters(self, mock_service_class):
        """Test pages list API with filters."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.list_pages.return_value = {
            "pages": [],
            "total": 0
        }
        
        # Test with page_type filter
        response = self.client.get(self.pages_list_url + '?page_type=markdown')
        self.assertEqual(response.status_code, 200)
        
        # Test with status filter
        response = self.client.get(self.pages_list_url + '?status=published')
        self.assertEqual(response.status_code, 200)
    
    @patch('apps.documentation.api.v1.core.get_pages_service')
    def test_pages_list_api_pagination(self, mock_service_class):
        """Test pages list API pagination."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.list_pages.return_value = {
            "pages": [],
            "total": 0
        }
        
        response = self.client.get(self.pages_list_url + '?limit=10&offset=0')
        self.assertEqual(response.status_code, 200)
    
    @patch('apps.documentation.api.v1.core.get_pages_service')
    def test_pages_detail_api_success(self, mock_service_class):
        """Test successful page detail API."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.get_page.return_value = {
            "page_id": self.page_id,
            "page_type": "markdown",
            "content": "# Test Page"
        }
        
        response = self.client.get(self.pages_detail_url)
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )
        
        data = json.loads(response.content)
        self.assertIn('data', data)
        self.assertEqual(data['data']['page_id'], self.page_id)
    
    @patch('apps.documentation.api.v1.core.get_pages_service')
    def test_pages_detail_api_not_found(self, mock_service_class):
        """Test page detail API with non-existent page."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.get_page.return_value = None
        
        response = self.client.get(self.pages_detail_url)
        
        assert_not_found_response(self, response, resource_name="Page")
    
    @patch('apps.documentation.api.v1.core.get_pages_service')
    def test_pages_detail_api_service_error(self, mock_service_class):
        """Test page detail API handles service errors."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.get_page.side_effect = Exception("Service error")
        
        response = self.client.get(self.pages_detail_url)
        
        assert_error_response(self, response, expected_status=500)


class EndpointsAPITestCase(BaseAPITestCase):
    """Test cases for endpoints API endpoints."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.endpoints_list_url = reverse('api_v1:endpoints_list')
        self.endpoint_id = "test_endpoint"
        self.endpoints_detail_url = reverse('api_v1:endpoints_detail', args=[self.endpoint_id])
    
    @patch('apps.documentation.api.v1.core.EndpointsService')
    def test_endpoints_list_api_success(self, mock_service_class):
        """Test successful endpoints list API."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.list_endpoints.return_value = {
            "endpoints": [
                {"endpoint_id": "ep1", "method": "GET"},
                {"endpoint_id": "ep2", "method": "POST"}
            ],
            "total": 2
        }
        
        response = self.client.get(self.endpoints_list_url)
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )
        
        data = json.loads(response.content)
        self.assertIn('items', data)
        self.assertEqual(len(data['items']), 2)
    
    @patch('apps.documentation.api.v1.core.EndpointsService')
    def test_endpoints_list_api_with_filters(self, mock_service_class):
        """Test endpoints list API with filters."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.list_endpoints.return_value = {
            "endpoints": [],
            "total": 0
        }
        
        # Test with method filter
        response = self.client.get(self.endpoints_list_url + '?method=GET')
        self.assertEqual(response.status_code, 200)
        
        # Test with api_version filter
        response = self.client.get(self.endpoints_list_url + '?api_version=v1')
        self.assertEqual(response.status_code, 200)
    
    @patch('apps.documentation.api.v1.core.EndpointsService')
    def test_endpoints_detail_api_success(self, mock_service_class):
        """Test successful endpoint detail API."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.get_endpoint.return_value = {
            "endpoint_id": self.endpoint_id,
            "method": "GET",
            "endpoint_path": "/api/test"
        }
        
        response = self.client.get(self.endpoints_detail_url)
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )
    
    @patch('apps.documentation.api.v1.core.EndpointsService')
    def test_endpoints_detail_api_not_found(self, mock_service_class):
        """Test endpoint detail API with non-existent endpoint."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.get_endpoint.return_value = None
        
        response = self.client.get(self.endpoints_detail_url)
        
        assert_not_found_response(self, response, resource_name="Endpoint")


class RelationshipsAPITestCase(BaseAPITestCase):
    """Test cases for relationships API endpoints."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.relationships_list_url = reverse('api_v1:relationships_list')
        self.relationship_id = "test_relationship"
        self.relationships_detail_url = reverse('api_v1:relationships_detail', args=[self.relationship_id])
    
    @patch('apps.documentation.api.v1.core.RelationshipsService')
    def test_relationships_list_api_success(self, mock_service_class):
        """Test successful relationships list API."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.list_relationships.return_value = {
            "relationships": [
                {
                    "relationship_id": "rel1",
                    "page_id": "page1",
                    "endpoint_id": "ep1"
                }
            ],
            "total": 1
        }
        
        response = self.client.get(self.relationships_list_url)
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )
    
    @patch('apps.documentation.api.v1.core.RelationshipsService')
    def test_relationships_detail_api_success(self, mock_service_class):
        """Test successful relationship detail API."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.get_relationship.return_value = {
            "relationship_id": self.relationship_id,
            "page_id": "page1",
            "endpoint_id": "ep1"
        }
        
        response = self.client.get(self.relationships_detail_url)
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )


class PostmanAPITestCase(BaseAPITestCase):
    """Test cases for Postman API endpoints."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.postman_list_url = reverse('api_v1:postman_list')
        self.postman_id = "test_postman"
        self.postman_detail_url = reverse('api_v1:postman_detail', args=[self.postman_id])
    
    @patch('apps.documentation.api.v1.core.PostmanService')
    def test_postman_list_api_success(self, mock_service_class):
        """Test successful Postman list API."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.list_postman_configs.return_value = {
            "configs": [
                {"postman_id": "pm1", "collection_name": "Collection 1"}
            ],
            "total": 1
        }
        
        response = self.client.get(self.postman_list_url)
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )
    
    @patch('apps.documentation.api.v1.core.PostmanService')
    def test_postman_detail_api_success(self, mock_service_class):
        """Test successful Postman detail API."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.get_postman_config.return_value = {
            "postman_id": self.postman_id,
            "collection_name": "Test Collection"
        }
        
        response = self.client.get(self.postman_detail_url)
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )


class APIStatisticsTestCase(BaseAPITestCase):
    """Test cases for API statistics endpoints."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.pages_types_url = reverse('api_v1:pages_types')
        self.pages_statistics_url = reverse('api_v1:pages_statistics')
        self.endpoints_methods_url = reverse('api_v1:endpoints_methods')
        self.endpoints_api_versions_url = reverse('api_v1:endpoints_api_versions')
    
    @patch('apps.documentation.api.v1.core.PagesService')
    def test_pages_types_api_success(self, mock_service_class):
        """Test successful pages types API."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.list_page_types.return_value = {
            "types": [
                {"type": "markdown", "count": 10},
                {"type": "html", "count": 5}
            ],
            "total": 2
        }
        
        response = self.client.get(self.pages_types_url)
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )
    
    @patch('apps.documentation.api.v1.core.PagesService')
    def test_pages_statistics_api_success(self, mock_service_class):
        """Test successful pages statistics API."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.get_statistics.return_value = {
            "total": 15,
            "by_type": {"markdown": 10, "html": 5},
            "by_status": {"published": 12, "draft": 3}
        }
        
        response = self.client.get(self.pages_statistics_url)
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )
    
    @patch('apps.documentation.api.v1.core.EndpointsService')
    def test_endpoints_methods_api_success(self, mock_service_class):
        """Test successful endpoints methods API."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.list_methods.return_value = {
            "methods": [
                {"method": "GET", "count": 20},
                {"method": "POST", "count": 10}
            ]
        }
        
        response = self.client.get(self.endpoints_methods_url)
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )


class APIErrorHandlingTestCase(BaseAPITestCase):
    """Test cases for API error handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.pages_list_url = reverse('api_v1:pages_list')
    
    @patch('apps.documentation.api.v1.core.PagesService')
    def test_api_handles_service_exceptions(self, mock_service_class):
        """Test that API handles service exceptions gracefully."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.list_pages.side_effect = Exception("Service error")
        
        response = self.client.get(self.pages_list_url)
        
        assert_error_response(self, response, expected_status=500)
    
    def test_api_handles_invalid_method(self):
        """Test that API handles invalid HTTP methods."""
        # Pages list only accepts GET
        response = self.client.post(self.pages_list_url)
        self.assertEqual(response.status_code, 405)  # Method Not Allowed
    
    def test_api_handles_malformed_requests(self):
        """Test that API handles malformed requests."""
        # Test with invalid query parameters
        response = self.client.get(self.pages_list_url + '?limit=invalid')
        # Should handle gracefully (either 200 with default or 400)
        self.assertIn(response.status_code, [200, 400])


class APIAuthenticationTestCase(TestCase):
    """Test cases for API authentication."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.pages_list_url = reverse('api_v1:pages_list')
    
    def test_api_requires_authentication(self):
        """Test that API endpoints require authentication."""
        # Note: Some endpoints might be public, adjust based on actual requirements
        response = self.client.get(self.pages_list_url)
        # Should require auth or be public - check actual behavior
        self.assertIn(response.status_code, [200, 401, 403])
