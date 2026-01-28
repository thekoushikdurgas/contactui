"""
Integration tests for dashboard views.

Tests the dashboard view layer including:
- Dashboard rendering
- Dashboard statistics API
- Dashboard graph API
- Health status API
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
)

User = get_user_model()


class DashboardViewsTestCase(BaseAPITestCase):
    """Test cases for dashboard views."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.dashboard_url = reverse('documentation:dashboard')
    
    def test_documentation_dashboard_get(self):
        """Test dashboard page GET request."""
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'dashboard', status_code=200)
    
    def test_documentation_dashboard_requires_login(self):
        """Test that dashboard requires authentication."""
        client = Client()  # Unauthenticated client
        response = client.get(self.dashboard_url)
        # Should redirect to login
        self.assertIn(response.status_code, [302, 401])
    
    def test_documentation_dashboard_with_tab(self):
        """Test dashboard with tab parameter."""
        response = self.client.get(self.dashboard_url + '?tab=pages')
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(self.dashboard_url + '?tab=endpoints')
        self.assertEqual(response.status_code, 200)
    
    def test_documentation_dashboard_with_view_param(self):
        """Test dashboard with view mode parameter (list, files, sync)."""
        for view in ('list', 'files', 'sync'):
            response = self.client.get(
                self.dashboard_url,
                {'tab': 'pages', 'view': view}
            )
            self.assertEqual(response.status_code, 200, f'view={view}')
            self.assertEqual(response.context.get('view_mode'), view)
    
    def test_documentation_dashboard_with_page_params(self):
        """Test dashboard accepts page and page_size for deep linking."""
        response = self.client.get(
            self.dashboard_url,
            {'tab': 'pages', 'view': 'list', 'page': '2', 'page_size': '10'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context.get('active_tab'), 'pages')
        self.assertEqual(response.context.get('view_mode'), 'list')
    
    def test_documentation_dashboard_context_has_active_tab_and_view_mode(self):
        """Test dashboard context includes active_tab and view_mode."""
        response = self.client.get(
            self.dashboard_url,
            {'tab': 'relationships', 'view': 'files'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('active_tab', response.context)
        self.assertIn('view_mode', response.context)
        self.assertEqual(response.context['active_tab'], 'relationships')
        self.assertEqual(response.context['view_mode'], 'files')
    
    def test_documentation_dashboard_all_tabs(self):
        """Test dashboard renders for all tab values."""
        for tab in ('pages', 'endpoints', 'relationships', 'postman', 'graph'):
            response = self.client.get(self.dashboard_url, {'tab': tab})
            self.assertEqual(response.status_code, 200, f'tab={tab}')
            self.assertEqual(response.context.get('active_tab'), tab)
    
    @patch('apps.documentation.views.dashboard.pages_service')
    @patch('apps.documentation.views.dashboard.endpoints_service')
    @patch('apps.documentation.views.dashboard.relationships_service')
    @patch('apps.documentation.views.dashboard.postman_service')
    def test_dashboard_context_data(
        self,
        mock_postman_service,
        mock_relationships_service,
        mock_endpoints_service,
        mock_pages_service
    ):
        """Test that dashboard context contains expected data."""
        # Mock service responses
        mock_pages_service.list_pages.return_value = {"pages": [], "total": 0}
        mock_endpoints_service.list_endpoints.return_value = {"endpoints": [], "total": 0}
        mock_relationships_service.list_relationships.return_value = {"relationships": [], "total": 0}
        mock_postman_service.list_postman_configs.return_value = {"configs": [], "total": 0}
        
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that context contains expected keys
        context = response.context
        self.assertIsNotNone(context)


class DashboardStatsAPITestCase(BaseAPITestCase):
    """Test cases for dashboard statistics API."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.stats_url = reverse('documentation:dashboard_stats_api')
    
    @patch('apps.documentation.views.dashboard.pages_service')
    @patch('apps.documentation.views.dashboard.endpoints_service')
    @patch('apps.documentation.views.dashboard.relationships_service')
    @patch('apps.documentation.views.dashboard.postman_service')
    def test_dashboard_stats_api_success(
        self,
        mock_postman_service,
        mock_relationships_service,
        mock_endpoints_service,
        mock_pages_service
    ):
        """Test successful dashboard statistics API call."""
        # Mock service responses
        mock_pages_service.list_pages.return_value = {"pages": [], "total": 10}
        mock_endpoints_service.list_endpoints.return_value = {"endpoints": [], "total": 5}
        mock_relationships_service.list_relationships.return_value = {"relationships": [], "total": 3}
        mock_postman_service.list_postman_configs.return_value = {"configs": [], "total": 2}
        
        response = self.client.get(self.stats_url)
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )
        
        data = json.loads(response.content)
        self.assertIn('data', data)
        stats = data['data']
        self.assertIn('pages_count', stats)
        self.assertIn('endpoints_count', stats)
        self.assertIn('relationships_count', stats)
        self.assertIn('postman_count', stats)
    
    @patch('apps.documentation.views.dashboard.pages_service')
    def test_dashboard_stats_api_service_error(self, mock_pages_service):
        """Test dashboard stats API handles service errors."""
        mock_pages_service.list_pages.side_effect = Exception("Service error")
        
        response = self.client.get(self.stats_url)
        
        # Should return error response
        assert_error_response(self, response, expected_status=500)
    
    def test_dashboard_stats_api_requires_login(self):
        """Test that dashboard stats API requires authentication."""
        client = Client()
        response = client.get(self.stats_url)
        # Should return 401 or redirect
        self.assertIn(response.status_code, [302, 401, 403])


class DashboardGraphAPITestCase(BaseAPITestCase):
    """Test cases for dashboard graph API."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.graph_url = reverse('documentation:api_dashboard_graph')
    
    @patch('apps.documentation.views.dashboard.build_graph_data')
    def test_dashboard_graph_api_success(self, mock_build_graph):
        """Test successful dashboard graph API call."""
        mock_graph_data = {
            "nodes": [
                {"id": "page_1", "label": "Page 1", "type": "page"},
                {"id": "endpoint_1", "label": "Endpoint 1", "type": "endpoint"}
            ],
            "edges": [
                {"id": "rel_1", "source": "page_1", "target": "endpoint_1"}
            ],
            "statistics": {
                "total_nodes": 2,
                "total_edges": 1,
                "pages_count": 1,
                "endpoints_count": 1,
                "relationships_count": 1
            }
        }
        mock_build_graph.return_value = mock_graph_data
        
        response = self.client.get(self.graph_url)
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )
        
        data = json.loads(response.content)
        self.assertIn('data', data)
        graph_data = data['data']
        self.assertIn('nodes', graph_data)
        self.assertIn('edges', graph_data)
        self.assertIn('statistics', graph_data)
    
    @patch('apps.documentation.views.dashboard.build_graph_data')
    def test_dashboard_graph_api_error(self, mock_build_graph):
        """Test dashboard graph API handles errors."""
        mock_build_graph.side_effect = Exception("Graph build error")
        
        response = self.client.get(self.graph_url)
        
        # Should return error response
        assert_error_response(self, response, expected_status=500)
    
    def test_dashboard_graph_api_requires_login(self):
        """Test that dashboard graph API requires authentication."""
        client = Client()
        response = client.get(self.graph_url)
        self.assertIn(response.status_code, [302, 401, 403])


class HealthStatusAPITestCase(BaseAPITestCase):
    """Test cases for health status API."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.health_url = reverse('documentation:health_status_api')
    
    @patch('apps.documentation.views.dashboard.get_comprehensive_health_status')
    def test_health_status_api_success(self, mock_health_check):
        """Test successful health status API call."""
        mock_health_check.return_value = {
            "status": "healthy",
            "timestamp": 1234567890,
            "components": {
                "application": {"status": "healthy"},
                "database": {"status": "healthy"},
                "cache": {"status": "healthy"},
                "storage": {"status": "healthy"},
                "external_api": {"status": "healthy"},
            }
        }
        
        response = self.client.get(self.health_url)
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )
        
        data = json.loads(response.content)
        self.assertIn('data', data)
        health_data = data['data']
        self.assertIn('status', health_data)
        self.assertIn('components', health_data)
        self.assertEqual(health_data['status'], 'healthy')
    
    def test_health_status_api_unauthenticated(self):
        """Test health status API requires authentication."""
        client = Client()
        response = client.get(self.health_url)
        
        # Health endpoint requires authentication
        self.assertIn(response.status_code, [302, 401, 403])


class DashboardCacheTestCase(BaseAPITestCase):
    """Test cases for dashboard caching."""
    
    @patch('apps.documentation.views.dashboard.cache_manager')
    def test_dashboard_stats_caching(self, mock_cache_manager):
        """Test that dashboard stats are cached."""
        mock_cache_manager.get.return_value = None  # Cache miss
        mock_cache_manager.set.return_value = True
        
        stats_url = reverse('documentation:dashboard_stats_api')
        
        # First request - should cache
        response1 = self.client.get(stats_url)
        self.assertEqual(response1.status_code, 200)
        
        # Verify cache.set was called
        mock_cache_manager.set.assert_called()
    
    @patch('apps.documentation.views.dashboard.cache_manager')
    def test_dashboard_graph_caching(self, mock_cache_manager):
        """Test that dashboard graph data is cached."""
        mock_cache_manager.get.return_value = None  # Cache miss
        
        graph_url = reverse('documentation:api_dashboard_graph')
        
        response = self.client.get(graph_url)
        self.assertEqual(response.status_code, 200)
        
        # Verify cache operations were attempted
        mock_cache_manager.get.assert_called()
