"""
Unit tests for MediaManagerDashboardService.

Tests cover:
- get_dashboard_overview()
- get_resource_list()
- get_resource_detail()
- get_health_status()
- get_resource_counts()
"""

from __future__ import annotations

import unittest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase

from apps.documentation.services.media_manager_dashboard_service import MediaManagerDashboardService
from apps.documentation.tests.fixtures import (
    PageFactory,
    EndpointFactory,
    RelationshipFactory,
    MockUnifiedStorage,
)


class MediaManagerDashboardServiceTestCase(TestCase):
    """Test cases for MediaManagerDashboardService."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock individual services
        self.mock_pages_service = Mock()
        self.mock_endpoints_service = Mock()
        self.mock_relationships_service = Mock()
        self.mock_postman_service = Mock()
        
        # Create service instance with mocked dependencies
        with patch('apps.documentation.services.media_manager_dashboard_service.get_pages_service', return_value=self.mock_pages_service), \
             patch('apps.documentation.services.media_manager_dashboard_service.get_endpoints_service', return_value=self.mock_endpoints_service), \
             patch('apps.documentation.services.media_manager_dashboard_service.get_relationships_service', return_value=self.mock_relationships_service), \
             patch('apps.documentation.services.media_manager_dashboard_service.get_postman_service', return_value=self.mock_postman_service):
            self.service = MediaManagerDashboardService()
    
    def test_get_dashboard_overview_success(self):
        """Test get_dashboard_overview with success."""
        # Mock service responses
        self.mock_pages_service.get_pages_statistics.return_value = {
            'total': 10,
            'statistics': {
                'by_type': {'docs': 5, 'marketing': 3, 'dashboard': 2},
                'by_state': {'published': 7, 'draft': 3}
            },
            'last_updated': '2026-01-27T00:00:00Z'
        }
        
        self.mock_endpoints_service.get_api_version_statistics.return_value = {
            'versions': [
                {'api_version': 'v1', 'count': 50},
                {'api_version': 'v4', 'count': 30}
            ]
        }
        
        self.mock_endpoints_service.get_method_statistics.return_value = {
            'methods': [
                {'method': 'GET', 'count': 40},
                {'method': 'POST', 'count': 20}
            ]
        }
        
        self.mock_relationships_service.get_statistics.return_value = {
            'total_relationships': 25,
            'by_usage_type': {'primary': 15, 'secondary': 10},
            'by_usage_context': {'data_fetching': 20, 'data_mutation': 5}
        }
        
        self.mock_postman_service.get_statistics.return_value = {
            'total_configurations': 5,
            'by_state': {'published': 3, 'draft': 2},
            'updated_at': '2026-01-27T00:00:00Z'
        }
        
        result = self.service.get_dashboard_overview()
        
        self.assertIn('pages', result)
        self.assertIn('endpoints', result)
        self.assertIn('relationships', result)
        self.assertIn('postman', result)
        
        self.assertEqual(result['pages']['total'], 10)
        self.assertEqual(result['endpoints']['total'], 80)  # 50 + 30
        self.assertEqual(result['relationships']['total'], 25)
        self.assertEqual(result['postman']['total'], 5)
    
    def test_get_resource_list_pages(self):
        """Test get_resource_list for pages."""
        mock_pages = PageFactory.create_batch(3)
        self.mock_pages_service.list_pages.return_value = {
            'pages': mock_pages,
            'total': 3
        }
        
        filters = {'page_type': 'docs', 'limit': 10, 'offset': 0}
        result = self.service.get_resource_list('pages', filters)
        
        self.assertIn('pages', result)
        self.assertEqual(len(result['pages']), 3)
        self.assertEqual(result['total'], 3)
        self.mock_pages_service.list_pages.assert_called_once()
    
    def test_get_resource_list_endpoints(self):
        """Test get_resource_list for endpoints."""
        mock_endpoints = EndpointFactory.create_batch(5)
        self.mock_endpoints_service.list_endpoints.return_value = {
            'endpoints': mock_endpoints,
            'total': 5
        }
        
        filters = {'api_version': 'v1', 'limit': 10, 'offset': 0}
        result = self.service.get_resource_list('endpoints', filters)
        
        self.assertIn('endpoints', result)
        self.assertEqual(len(result['endpoints']), 5)
        self.assertEqual(result['total'], 5)
        self.mock_endpoints_service.list_endpoints.assert_called_once()
    
    def test_get_resource_list_relationships(self):
        """Test get_resource_list for relationships."""
        mock_relationships = RelationshipFactory.create_batch(4)
        self.mock_relationships_service.list_relationships.return_value = {
            'relationships': mock_relationships,
            'total': 4
        }
        
        filters = {'usage_type': 'primary', 'limit': 10, 'offset': 0}
        result = self.service.get_resource_list('relationships', filters)
        
        self.assertIn('relationships', result)
        self.assertEqual(len(result['relationships']), 4)
        self.assertEqual(result['total'], 4)
        self.mock_relationships_service.list_relationships.assert_called_once()
    
    def test_get_resource_list_postman(self):
        """Test get_resource_list for postman."""
        mock_configs = [
            {'config_id': 'config1', 'name': 'Config 1'},
            {'config_id': 'config2', 'name': 'Config 2'}
        ]
        self.mock_postman_service.list_configurations.return_value = {
            'configurations': mock_configs,
            'total': 2
        }
        
        filters = {'state': 'published', 'limit': 10, 'offset': 0}
        result = self.service.get_resource_list('postman', filters)
        
        self.assertIn('configurations', result)
        self.assertEqual(len(result['configurations']), 2)
        self.assertEqual(result['total'], 2)
        self.mock_postman_service.list_configurations.assert_called_once()
    
    def test_get_resource_list_invalid_type(self):
        """Test get_resource_list with invalid resource type."""
        with self.assertRaises(ValueError):
            self.service.get_resource_list('invalid_type', {})
    
    def test_get_resource_detail_pages(self):
        """Test get_resource_detail for pages."""
        mock_page = PageFactory.create(page_id='test-page')
        self.mock_pages_service.get_page.return_value = mock_page
        
        result = self.service.get_resource_detail('pages', 'test-page')
        
        self.assertIsNotNone(result)
        self.assertEqual(result['page_id'], 'test-page')
        self.mock_pages_service.get_page.assert_called_once_with('test-page')
    
    def test_get_resource_detail_endpoints(self):
        """Test get_resource_detail for endpoints."""
        mock_endpoint = EndpointFactory.create(endpoint_id='test-endpoint')
        self.mock_endpoints_service.get_endpoint.return_value = mock_endpoint
        
        result = self.service.get_resource_detail('endpoints', 'test-endpoint')
        
        self.assertIsNotNone(result)
        self.assertEqual(result['endpoint_id'], 'test-endpoint')
        self.mock_endpoints_service.get_endpoint.assert_called_once_with('test-endpoint')
    
    def test_get_resource_detail_not_found(self):
        """Test get_resource_detail when resource doesn't exist."""
        self.mock_pages_service.get_page.return_value = None
        
        result = self.service.get_resource_detail('pages', 'non-existent')
        
        self.assertIsNone(result)
    
    def test_get_health_status(self):
        """Test get_health_status."""
        mock_health = {
            'status': 'healthy',
            'components': {
                'application': {'status': 'healthy'},
                'database': {'status': 'healthy'},
                'cache': {'status': 'healthy'}
            }
        }
        
        with patch('apps.documentation.services.media_manager_dashboard_service.get_comprehensive_health_status', return_value=mock_health):
            result = self.service.get_health_status()
            
            self.assertIn('status', result)
            self.assertIn('components', result)
            self.assertEqual(result['status'], 'healthy')
    
    def test_get_resource_counts(self):
        """Test get_resource_counts."""
        self.mock_pages_service.list_pages.return_value = {'total': 10}
        self.mock_endpoints_service.list_endpoints.return_value = {'total': 20}
        self.mock_relationships_service.list_relationships.return_value = {'total': 15}
        self.mock_postman_service.list_configurations.return_value = {'total': 5}
        
        result = self.service.get_resource_counts()
        
        self.assertEqual(result['pages'], 10)
        self.assertEqual(result['endpoints'], 20)
        self.assertEqual(result['relationships'], 15)
        self.assertEqual(result['postman'], 5)
    
    def test_get_dashboard_overview_error_handling(self):
        """Test get_dashboard_overview handles errors gracefully."""
        self.mock_pages_service.get_pages_statistics.side_effect = Exception('Service error')
        
        result = self.service.get_dashboard_overview()
        
        # Should return empty structure on error
        self.assertIn('pages', result)
        self.assertEqual(result['pages']['total'], 0)
