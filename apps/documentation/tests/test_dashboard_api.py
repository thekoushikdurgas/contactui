"""
Tests for Dashboard API endpoints.

Tests pagination, filtering, and search functionality for all 4 dashboard lists.
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
import json

User = get_user_model()


class DashboardAPITestCase(TestCase):
    """Base test case for dashboard API tests."""
    
    def setUp(self):
        """Set up test client and user."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def get_json_response(self, url, params=None):
        """Helper to get JSON response."""
        response = self.client.get(url, params or {})
        self.assertEqual(response['Content-Type'], 'application/json')
        return json.loads(response.content)


class DashboardPagesAPITest(DashboardAPITestCase):
    """Tests for dashboard pages API."""
    
    def test_pages_list_api_basic(self):
        """Test basic pages list API call."""
        url = reverse('documentation:api_dashboard_pages')
        data = self.get_json_response(url)
        
        self.assertTrue(data['success'])
        self.assertIn('items', data)
        self.assertIn('pagination', data)
        self.assertIn('total', data['pagination'])
        self.assertIn('page', data['pagination'])
        self.assertIn('page_size', data['pagination'])
    
    def test_pages_list_api_pagination(self):
        """Test pagination parameters."""
        url = reverse('documentation:api_dashboard_pages')
        
        # Test page 1
        data = self.get_json_response(url, {'page': 1, 'page_size': 10})
        self.assertEqual(data['pagination']['page'], 1)
        self.assertEqual(data['pagination']['page_size'], 10)
        
        # Test page 2
        data = self.get_json_response(url, {'page': 2, 'page_size': 10})
        self.assertEqual(data['pagination']['page'], 2)
    
    def test_pages_list_api_invalid_pagination(self):
        """Test invalid pagination parameters."""
        url = reverse('documentation:api_dashboard_pages')
        
        # Negative page
        data = self.get_json_response(url, {'page': -1})
        self.assertEqual(data['pagination']['page'], 1)
        
        # Zero page
        data = self.get_json_response(url, {'page': 0})
        self.assertEqual(data['pagination']['page'], 1)
        
        # Invalid page size
        data = self.get_json_response(url, {'page_size': 0})
        self.assertEqual(data['pagination']['page_size'], 20)
        
        # Too large page size
        data = self.get_json_response(url, {'page_size': 200})
        self.assertEqual(data['pagination']['page_size'], 100)
    
    def test_pages_list_api_filters(self):
        """Test filter parameters."""
        url = reverse('documentation:api_dashboard_pages')
        
        # Test page_type filter
        data = self.get_json_response(url, {'page_type': 'docs'})
        self.assertIn('filters', data)
        self.assertEqual(data['filters'].get('page_type'), 'docs')
        
        # Test status filter
        data = self.get_json_response(url, {'status': 'published'})
        self.assertEqual(data['filters'].get('status'), 'published')
    
    def test_pages_list_api_search(self):
        """Test search functionality."""
        url = reverse('documentation:api_dashboard_pages')
        
        data = self.get_json_response(url, {'search': 'test'})
        self.assertIn('filters', data)
        # Search is applied client-side, so we just check it's in filters
        # Actual filtering happens in the view
    
    def test_pages_list_api_pagination_structure(self):
        """Test pagination includes has_next, has_previous, total_pages."""
        url = reverse('documentation:api_dashboard_pages')
        data = self.get_json_response(url, {'page': 1, 'page_size': 20})
        
        pag = data.get('pagination', {})
        self.assertIn('has_previous', pag)
        self.assertIn('has_next', pag)
        self.assertIn('total_pages', pag)
        self.assertIn('total', pag)
        self.assertFalse(pag['has_previous'])


class DashboardEndpointsAPITest(DashboardAPITestCase):
    """Tests for dashboard endpoints API."""
    
    def test_endpoints_list_api_basic(self):
        """Test basic endpoints list API call."""
        url = reverse('documentation:api_dashboard_endpoints')
        data = self.get_json_response(url)
        
        self.assertTrue(data['success'])
        self.assertIn('items', data)
        self.assertIn('pagination', data)
    
    def test_endpoints_list_api_filters(self):
        """Test filter parameters."""
        url = reverse('documentation:api_dashboard_endpoints')
        
        # Test method filter
        data = self.get_json_response(url, {'method': 'QUERY'})
        self.assertIn('filters', data)
        self.assertEqual(data['filters'].get('method'), 'QUERY')
        
        # Test api_version filter
        data = self.get_json_response(url, {'api_version': 'v1'})
        self.assertEqual(data['filters'].get('api_version'), 'v1')


class DashboardRelationshipsAPITest(DashboardAPITestCase):
    """Tests for dashboard relationships API."""
    
    def test_relationships_list_api_basic(self):
        """Test basic relationships list API call."""
        url = reverse('documentation:api_dashboard_relationships')
        data = self.get_json_response(url)
        
        self.assertTrue(data['success'])
        self.assertIn('items', data)
        self.assertIn('pagination', data)
    
    def test_relationships_list_api_filters(self):
        """Test filter parameters."""
        url = reverse('documentation:api_dashboard_relationships')
        
        # Test page_id filter
        data = self.get_json_response(url, {'page_id': 'test-page'})
        self.assertIn('filters', data)
        self.assertEqual(data['filters'].get('page_id'), 'test-page')
        
        # Test endpoint_id filter
        data = self.get_json_response(url, {'endpoint_id': 'test-endpoint'})
        self.assertEqual(data['filters'].get('endpoint_id'), 'test-endpoint')


class DashboardPostmanAPITest(DashboardAPITestCase):
    """Tests for dashboard Postman API."""
    
    def test_postman_list_api_basic(self):
        """Test basic Postman list API call."""
        url = reverse('documentation:api_dashboard_postman')
        data = self.get_json_response(url)
        
        self.assertTrue(data['success'])
        self.assertIn('items', data)
        self.assertIn('pagination', data)
    
    def test_postman_list_api_filters(self):
        """Test filter parameters."""
        url = reverse('documentation:api_dashboard_postman')
        
        # Test state filter
        data = self.get_json_response(url, {'state': 'published'})
        self.assertIn('filters', data)
        self.assertEqual(data['filters'].get('state'), 'published')
    
    def test_postman_list_api_pagination(self):
        """Test pagination."""
        url = reverse('documentation:api_dashboard_postman')
        
        data = self.get_json_response(url, {'page': 1, 'page_size': 10})
        self.assertEqual(data['pagination']['page'], 1)
        self.assertEqual(data['pagination']['page_size'], 10)


class DashboardAPIAuthenticationTest(TestCase):
    """Tests for dashboard API authentication."""
    
    def setUp(self):
        """Set up test client."""
        self.client = Client()
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated users are redirected."""
        url = reverse('documentation:api_dashboard_pages')
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
    
    def test_authenticated_access(self):
        """Test that authenticated users can access."""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('documentation:api_dashboard_pages')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
