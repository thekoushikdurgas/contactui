"""
Integration tests for Media Manager Dashboard AJAX API endpoints.

Tests cover:
- get_pages_list_api
- get_endpoints_list_api
- get_relationships_list_api
- get_postman_list_api
- get_statistics_api
- get_health_api
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
    assert_api_response,
)

User = get_user_model()


class MediaManagerDashboardAPITestCase(BaseAPITestCase):
    """Test cases for Media Manager Dashboard API endpoints."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.pages_api_url = reverse('documentation:api_media_manager_pages')
        self.endpoints_api_url = reverse('documentation:api_media_manager_endpoints')
        self.relationships_api_url = reverse('documentation:api_media_manager_relationships')
        self.postman_api_url = reverse('documentation:api_media_manager_postman')
        self.statistics_api_url = reverse('documentation:api_media_manager_statistics')
        self.health_api_url = reverse('documentation:api_media_manager_health')
    
    def test_get_pages_list_api_success(self):
        """Test get_pages_list_api with success."""
        mock_pages = [
            {'page_id': 'page1', 'page_type': 'docs'},
            {'page_id': 'page2', 'page_type': 'docs'}
        ]
        
        with patch('apps.documentation.api.media_manager_api.get_pages_service') as mock_get_service:
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            mock_service.list_pages.return_value = {
                'pages': mock_pages,
                'total': 2
            }
            
            response = self.client.get(self.pages_api_url)
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.content)
            self.assertTrue(data.get('success'))
            self.assertIn('data', data)
            self.assertEqual(len(data['data']['pages']), 2)
            self.assertEqual(data['data']['total'], 2)
    
    def test_get_pages_list_api_with_filters(self):
        """Test get_pages_list_api with filters."""
        with patch('apps.documentation.api.media_manager_api.get_pages_service') as mock_get_service:
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            mock_service.list_pages.return_value = {'pages': [], 'total': 0}
            
            response = self.client.get(self.pages_api_url, {
                'page_type': 'docs',
                'status': 'published',
                'limit': 10,
                'offset': 0
            })
            
            self.assertEqual(response.status_code, 200)
            mock_service.list_pages.assert_called_once()
    
    def test_get_pages_list_api_with_search(self):
        """Test get_pages_list_api with search query."""
        mock_pages = [
            {'page_id': 'test-page', 'page_type': 'docs'},
            {'page_id': 'other-page', 'page_type': 'docs'}
        ]
        
        with patch('apps.documentation.api.media_manager_api.get_pages_service') as mock_get_service:
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            mock_service.list_pages.return_value = {
                'pages': mock_pages,
                'total': 2
            }
            
            response = self.client.get(self.pages_api_url, {'search': 'test'})
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.content)
            # Search should filter results
            self.assertTrue(data.get('success'))
    
    def test_get_endpoints_list_api_success(self):
        """Test get_endpoints_list_api with success."""
        mock_endpoints = [
            {'endpoint_id': 'endpoint1', 'method': 'GET'},
            {'endpoint_id': 'endpoint2', 'method': 'POST'}
        ]
        
        with patch('apps.documentation.api.media_manager_api.get_endpoints_service') as mock_get_service:
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            mock_service.list_endpoints.return_value = {
                'endpoints': mock_endpoints,
                'total': 2
            }
            
            response = self.client.get(self.endpoints_api_url)
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.content)
            self.assertTrue(data.get('success'))
            self.assertIn('data', data)
            self.assertEqual(len(data['data']['endpoints']), 2)
    
    def test_get_relationships_list_api_success(self):
        """Test get_relationships_list_api with success."""
        mock_relationships = [
            {'relationship_id': 'rel1', 'page_path': 'page1', 'endpoint_path': '/api/v1/test/'},
            {'relationship_id': 'rel2', 'page_path': 'page2', 'endpoint_path': '/api/v1/test2/'}
        ]
        
        with patch('apps.documentation.api.media_manager_api.get_relationships_service') as mock_get_service:
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            mock_service.list_relationships.return_value = {
                'relationships': mock_relationships,
                'total': 2
            }
            
            response = self.client.get(self.relationships_api_url)
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.content)
            self.assertTrue(data.get('success'))
            self.assertIn('data', data)
            self.assertEqual(len(data['data']['relationships']), 2)
    
    def test_get_postman_list_api_success(self):
        """Test get_postman_list_api with success."""
        mock_configs = [
            {'config_id': 'config1', 'name': 'Config 1'},
            {'config_id': 'config2', 'name': 'Config 2'}
        ]
        
        with patch('apps.documentation.api.media_manager_api.get_postman_service') as mock_get_service:
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            mock_service.list_configurations.return_value = {
                'configurations': mock_configs,
                'total': 2
            }
            
            response = self.client.get(self.postman_api_url)
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.content)
            self.assertTrue(data.get('success'))
            self.assertIn('data', data)
            self.assertEqual(len(data['data']['configurations']), 2)
    
    def test_get_statistics_api_success(self):
        """Test get_statistics_api with success."""
        with patch('apps.documentation.api.media_manager_api.get_media_manager_dashboard_service') as mock_get_service:
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            mock_service.pages_service.get_pages_statistics.return_value = {'total': 10}
            mock_service.endpoints_service.get_api_version_statistics.return_value = {'versions': []}
            mock_service.relationships_service.get_statistics.return_value = {'total_relationships': 15}
            mock_service.postman_service.get_statistics.return_value = {'total_configurations': 5}
            
            response = self.client.get(self.statistics_api_url)
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.content)
            self.assertTrue(data.get('success'))
            self.assertIn('data', data)
            self.assertIn('pages', data['data'])
            self.assertIn('endpoints', data['data'])
    
    def test_get_health_api_success(self):
        """Test get_health_api with success."""
        mock_health = {
            'status': 'healthy',
            'components': {
                'application': {'status': 'healthy'},
                'database': {'status': 'healthy'}
            }
        }
        
        with patch('apps.documentation.api.media_manager_api.get_comprehensive_health_status', return_value=mock_health):
            response = self.client.get(self.health_api_url)
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.content)
            self.assertTrue(data.get('success'))
            self.assertIn('data', data)
            self.assertEqual(data['data']['status'], 'healthy')
    
    def test_api_endpoints_require_login(self):
        """Test that API endpoints require authentication."""
        client = Client()  # Unauthenticated client
        
        endpoints = [
            self.pages_api_url,
            self.endpoints_api_url,
            self.relationships_api_url,
            self.postman_api_url,
            self.statistics_api_url,
            self.health_api_url
        ]
        
        for url in endpoints:
            response = client.get(url)
            self.assertIn(response.status_code, [302, 401], f'Endpoint {url} should require auth')
    
    def test_api_endpoints_only_get(self):
        """Test that API endpoints only accept GET requests."""
        endpoints = [
            self.pages_api_url,
            self.endpoints_api_url,
            self.relationships_api_url,
            self.postman_api_url,
            self.statistics_api_url,
            self.health_api_url
        ]
        
        for url in endpoints:
            # Try POST
            response = self.client.post(url)
            self.assertEqual(response.status_code, 405, f'POST to {url} should return 405')
            
            # Try PUT
            response = self.client.put(url)
            self.assertEqual(response.status_code, 405, f'PUT to {url} should return 405')
            
            # Try DELETE
            response = self.client.delete(url)
            self.assertEqual(response.status_code, 405, f'DELETE to {url} should return 405')
