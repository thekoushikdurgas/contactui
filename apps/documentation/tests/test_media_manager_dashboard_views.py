"""
Integration tests for Media Manager Dashboard views.

Tests cover:
- media_manager_dashboard view
- media_manager_page_detail view
- media_manager_endpoint_detail view
- media_manager_relationship_detail view
- media_manager_postman_detail view
- media_manager_health view
- media_manager_statistics view
"""

from __future__ import annotations

import json
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.documentation.tests.helpers import (
    BaseAPITestCase,
    create_test_user,
    authenticate_client,
)

User = get_user_model()


class MediaManagerDashboardViewsTestCase(BaseAPITestCase):
    """Test cases for Media Manager Dashboard views."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.dashboard_url = reverse('documentation:media_manager_dashboard')
        self.pages_url = reverse('documentation:media_manager_pages')
        self.endpoints_url = reverse('documentation:media_manager_endpoints')
        self.relationships_url = reverse('documentation:media_manager_relationships')
        self.postman_url = reverse('documentation:media_manager_postman')
        self.health_url = reverse('documentation:media_manager_health')
        self.statistics_url = reverse('documentation:media_manager_statistics')
    
    def test_media_manager_dashboard_get(self):
        """Test Media Manager Dashboard page GET request."""
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Media Manager Dashboard', status_code=200)
    
    def test_media_manager_dashboard_requires_login(self):
        """Test that Media Manager Dashboard requires authentication."""
        client = Client()  # Unauthenticated client
        response = client.get(self.dashboard_url)
        # Should redirect to login
        self.assertIn(response.status_code, [302, 401])
    
    def test_media_manager_dashboard_with_tab(self):
        """Test Media Manager Dashboard with tab parameter."""
        response = self.client.get(self.dashboard_url + '?tab=pages')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context.get('active_tab'), 'pages')
        
        response = self.client.get(self.dashboard_url + '?tab=endpoints')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context.get('active_tab'), 'endpoints')
    
    def test_media_manager_dashboard_with_view_mode(self):
        """Test Media Manager Dashboard with view mode parameter."""
        for view_mode in ('list', 'grid'):
            response = self.client.get(
                self.dashboard_url,
                {'tab': 'pages', 'view': view_mode}
            )
            self.assertEqual(response.status_code, 200, f'view={view_mode}')
            self.assertEqual(response.context.get('view_mode'), view_mode)
    
    def test_media_manager_dashboard_all_tabs(self):
        """Test Media Manager Dashboard renders for all tab values."""
        for tab in ('pages', 'endpoints', 'relationships', 'postman'):
            response = self.client.get(self.dashboard_url, {'tab': tab})
            self.assertEqual(response.status_code, 200, f'tab={tab}')
            self.assertEqual(response.context.get('active_tab'), tab)
    
    def test_media_manager_dashboard_context_data(self):
        """Test Media Manager Dashboard context includes required data."""
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        
        context = response.context
        self.assertIn('active_tab', context)
        self.assertIn('view_mode', context)
        self.assertIn('overview_stats', context)
        self.assertIn('health_status', context)
        self.assertIn('initial_data', context)
    
    @patch('apps.documentation.views.media_manager_dashboard.get_media_manager_dashboard_service')
    def test_media_manager_dashboard_overview_stats(self, mock_get_service):
        """Test Media Manager Dashboard loads overview statistics."""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        mock_service.get_dashboard_overview.return_value = {
            'pages': {'total': 10},
            'endpoints': {'total': 20},
            'relationships': {'total': 15},
            'postman': {'total': 5}
        }
        
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('overview_stats', response.context)
    
    def test_media_manager_page_detail_get(self):
        """Test Media Manager Page Detail view GET request."""
        page_id = 'test-page'
        detail_url = reverse('documentation:media_manager_page_detail', args=[page_id])
        
        with patch('apps.documentation.views.media_manager_dashboard.get_pages_service') as mock_get_service:
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            mock_service.get_page.return_value = {
                'page_id': page_id,
                'page_type': 'docs',
                'metadata': {'status': 'published'}
            }
            mock_service.get_page_sections.return_value = []
            mock_service.get_page_components.return_value = []
            mock_service.get_page_endpoints.return_value = []
            mock_service.get_page_versions.return_value = []
            mock_service.get_page_access_control.return_value = None
            
            response = self.client.get(detail_url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, page_id, status_code=200)
    
    def test_media_manager_page_detail_not_found(self):
        """Test Media Manager Page Detail view with non-existent page."""
        page_id = 'non-existent'
        detail_url = reverse('documentation:media_manager_page_detail', args=[page_id])
        
        with patch('apps.documentation.views.media_manager_dashboard.get_pages_service') as mock_get_service:
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            mock_service.get_page.return_value = None
            
            response = self.client.get(detail_url)
            self.assertEqual(response.status_code, 404)
    
    def test_media_manager_endpoint_detail_get(self):
        """Test Media Manager Endpoint Detail view GET request."""
        endpoint_id = 'test-endpoint'
        detail_url = reverse('documentation:media_manager_endpoint_detail', args=[endpoint_id])
        
        with patch('apps.documentation.views.media_manager_dashboard.get_endpoints_service') as mock_get_service:
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            mock_service.get_endpoint.return_value = {
                'endpoint_id': endpoint_id,
                'method': 'GET',
                'endpoint_path': '/api/v1/test/'
            }
            mock_service.get_endpoint_pages.return_value = {'pages': []}
            mock_service.get_endpoint_access_control.return_value = None
            mock_service.get_endpoint_lambda_services.return_value = []
            mock_service.get_endpoint_files.return_value = []
            mock_service.get_endpoint_dependencies.return_value = []
            
            response = self.client.get(detail_url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, endpoint_id, status_code=200)
    
    def test_media_manager_health_get(self):
        """Test Media Manager Health view GET request."""
        with patch('apps.documentation.views.media_manager_dashboard.get_comprehensive_health_status') as mock_health:
            mock_health.return_value = {
                'status': 'healthy',
                'components': {
                    'application': {'status': 'healthy'},
                    'database': {'status': 'healthy'}
                }
            }
            
            response = self.client.get(self.health_url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Health Status', status_code=200)
    
    def test_media_manager_statistics_get(self):
        """Test Media Manager Statistics view GET request."""
        with patch('apps.documentation.views.media_manager_dashboard.get_media_manager_dashboard_service') as mock_get_service:
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            mock_service.pages_service.get_pages_statistics.return_value = {'total': 10}
            mock_service.endpoints_service.get_api_version_statistics.return_value = {'versions': []}
            mock_service.relationships_service.get_statistics.return_value = {'total_relationships': 15}
            mock_service.postman_service.get_statistics.return_value = {'total_configurations': 5}
            
            response = self.client.get(self.statistics_url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Statistics', status_code=200)
