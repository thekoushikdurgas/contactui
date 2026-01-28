"""
Integration tests for pages views.

Tests the pages view layer including:
- Page list view
- Page detail view
- Page form view
- Page create API
- Page update API
- Page delete API
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


class PagesListViewTestCase(BaseAPITestCase):
    """Test cases for page list view."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.list_url = reverse('documentation:pages_list')
    
    @patch('apps.documentation.views.pages_views.pages_service')
    def test_page_list_view_success(self, mock_pages_service):
        """Test successful page list view."""
        mock_pages_service.list_pages.return_value = {
            "pages": [
                {"page_id": "page1", "page_type": "markdown", "metadata": {"title": "Page 1"}},
                {"page_id": "page2", "page_type": "html", "metadata": {"title": "Page 2"}}
            ],
            "total": 2,
            "source": "local"
        }
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Page 1', status_code=200)
    
    @patch('apps.documentation.views.pages_views.pages_service')
    def test_page_list_view_with_filters(self, mock_pages_service):
        """Test page list view with filters."""
        mock_pages_service.list_pages.return_value = {
            "pages": [],
            "total": 0,
            "source": "local"
        }
        
        # Test with page_type filter
        response = self.client.get(self.list_url + '?page_type=markdown')
        self.assertEqual(response.status_code, 200)
        
        # Test with status filter
        response = self.client.get(self.list_url + '?status=published')
        self.assertEqual(response.status_code, 200)
    
    @patch('apps.documentation.views.pages_views.pages_service')
    def test_page_list_view_pagination(self, mock_pages_service):
        """Test page list view pagination."""
        mock_pages_service.list_pages.return_value = {
            "pages": [],
            "total": 0,
            "source": "local"
        }
        
        response = self.client.get(self.list_url + '?limit=10&offset=0')
        self.assertEqual(response.status_code, 200)
    
    def test_page_list_view_requires_login(self):
        """Test that page list view requires authentication."""
        client = Client()
        response = client.get(self.list_url)
        self.assertIn(response.status_code, [302, 401])


class PageDetailViewTestCase(BaseAPITestCase):
    """Test cases for page detail view."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.page_id = "test_page"
        self.detail_url = reverse('documentation:page_detail', args=[self.page_id])
    
    @patch('apps.documentation.views.pages_views.pages_service')
    @patch('apps.documentation.views.pages_views.endpoints_service')
    @patch('apps.documentation.views.pages_views.relationships_service')
    def test_page_detail_view_success(
        self,
        mock_relationships_service,
        mock_endpoints_service,
        mock_pages_service
    ):
        """Test successful page detail view."""
        mock_pages_service.get_page.return_value = {
            "page_id": self.page_id,
            "page_type": "markdown",
            "content": "# Test Page",
            "metadata": {"title": "Test Page"}
        }
        mock_endpoints_service.list_endpoints.return_value = {"endpoints": []}
        mock_relationships_service.list_relationships.return_value = {"relationships": []}
        
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Page', status_code=200)
    
    @patch('apps.documentation.views.pages_views.pages_service')
    def test_page_detail_view_not_found(self, mock_pages_service):
        """Test page detail view with non-existent page."""
        from apps.documentation.utils.exceptions import NotFoundError
        mock_pages_service.get_page.side_effect = NotFoundError("Page not found")
        
        response = self.client.get(self.detail_url)
        # Should handle error gracefully
        self.assertIn(response.status_code, [200, 404])
    
    @patch('apps.documentation.views.pages_views.pages_service')
    def test_page_detail_view_with_tab(self, mock_pages_service):
        """Test page detail view with tab parameter."""
        mock_pages_service.get_page.return_value = {
            "page_id": self.page_id,
            "page_type": "markdown",
            "content": "# Test",
            "metadata": {}
        }
        
        response = self.client.get(self.detail_url + '?tab=content')
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(self.detail_url + '?tab=relationships')
        self.assertEqual(response.status_code, 200)


class PageFormViewTestCase(BaseAPITestCase):
    """Test cases for page form view."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.create_url = reverse('documentation:page_create')
        self.edit_url = reverse('documentation:page_edit', args=['test_page'])
    
    def test_page_form_view_create_get(self):
        """Test page create form GET request."""
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
    
    @patch('apps.documentation.views.pages_views.pages_service')
    def test_page_form_view_edit_get(self, mock_pages_service):
        """Test page edit form GET request."""
        mock_pages_service.get_page.return_value = {
            "page_id": "test_page",
            "page_type": "markdown",
            "content": "# Test",
            "metadata": {}
        }
        
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 200)
    
    @patch('apps.documentation.views.pages_views.pages_service')
    def test_page_form_view_post_success(self, mock_pages_service):
        """Test page form POST (create/update)."""
        mock_pages_service.create_page.return_value = {
            "page_id": "new_page",
            "page_type": "markdown"
        }
        
        response = self.client.post(self.create_url, {
            'page_id': 'new_page',
            'page_type': 'markdown',
            'content': '# New Page'
        })
        
        # Should redirect or return success
        self.assertIn(response.status_code, [200, 302])


class PageCreateAPITestCase(BaseAPITestCase):
    """Test cases for page create API."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.create_api_url = reverse('documentation:api_page_create')
    
    @patch('apps.documentation.views.pages_views.pages_service')
    def test_page_create_api_success(self, mock_pages_service):
        """Test successful page creation via API."""
        mock_pages_service.create_page.return_value = {
            "page_id": "new_page",
            "page_type": "markdown",
            "content": "# New Page",
            "metadata": {}
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
    
    def test_page_create_api_invalid_json(self):
        """Test page create API with invalid JSON."""
        response = self.client.post(
            self.create_api_url,
            data="invalid json",
            content_type='application/json'
        )
        
        assert_error_response(self, response, expected_status=400)
    
    def test_page_create_api_empty_body(self):
        """Test page create API with empty body."""
        response = self.client.post(
            self.create_api_url,
            data='',
            content_type='application/json'
        )
        
        assert_error_response(self, response, expected_status=400)
    
    @patch('apps.documentation.views.pages_views.pages_service')
    def test_page_create_api_service_error(self, mock_pages_service):
        """Test page create API handles service errors."""
        mock_pages_service.create_page.side_effect = Exception("Service error")
        
        response = self.client.post(
            self.create_api_url,
            data=json.dumps({"page_id": "test"}),
            content_type='application/json'
        )
        
        assert_error_response(self, response, expected_status=500)


class PageUpdateAPITestCase(BaseAPITestCase):
    """Test cases for page update API."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.page_id = "test_page"
        self.update_api_url = reverse('documentation:api_page_update', args=[self.page_id])
    
    @patch('apps.documentation.views.pages_views.pages_service')
    def test_page_update_api_success(self, mock_pages_service):
        """Test successful page update via API."""
        mock_pages_service.update_page.return_value = {
            "page_id": self.page_id,
            "page_type": "markdown",
            "content": "# Updated Page"
        }
        
        response = self.client.post(
            self.update_api_url,
            data=json.dumps({
                "content": "# Updated Page"
            }),
            content_type='application/json'
        )
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )
    
    @patch('apps.documentation.views.pages_views.pages_service')
    def test_page_update_api_not_found(self, mock_pages_service):
        """Test page update API with non-existent page."""
        from apps.documentation.utils.exceptions import NotFoundError
        mock_pages_service.update_page.side_effect = NotFoundError("Page not found")
        
        response = self.client.post(
            self.update_api_url,
            data=json.dumps({"content": "# Updated"}),
            content_type='application/json'
        )
        
        assert_not_found_response(self, response, resource_name="Page")


class PageDeleteAPITestCase(BaseAPITestCase):
    """Test cases for page delete API."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.page_id = "test_page"
        self.delete_api_url = reverse('documentation:api_page_delete', args=[self.page_id])
    
    @patch('apps.documentation.views.pages_views.pages_service')
    def test_page_delete_api_success(self, mock_pages_service):
        """Test successful page deletion via API."""
        mock_pages_service.delete_page.return_value = True
        
        response = self.client.post(self.delete_api_url)
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )
    
    @patch('apps.documentation.views.pages_views.pages_service')
    def test_page_delete_api_not_found(self, mock_pages_service):
        """Test page delete API with non-existent page."""
        from apps.documentation.utils.exceptions import NotFoundError
        mock_pages_service.delete_page.side_effect = NotFoundError("Page not found")
        
        response = self.client.post(self.delete_api_url)
        
        assert_not_found_response(self, response, resource_name="Page")
    
    @patch('apps.documentation.views.pages_views.pages_service')
    def test_page_delete_api_service_error(self, mock_pages_service):
        """Test page delete API handles service errors."""
        mock_pages_service.delete_page.side_effect = Exception("Service error")
        
        response = self.client.post(self.delete_api_url)
        
        assert_error_response(self, response, expected_status=500)


class PageDraftAPITestCase(BaseAPITestCase):
    """Test cases for page draft API."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.draft_api_url = reverse('documentation:api_page_draft')
    
    @patch('apps.documentation.views.pages_views.pages_service')
    def test_page_draft_api_success(self, mock_pages_service):
        """Test successful page draft creation via API."""
        mock_pages_service.create_draft_page.return_value = {
            "page_id": "draft_page",
            "page_type": "markdown",
            "status": "draft"
        }
        
        response = self.client.post(
            self.draft_api_url,
            data=json.dumps({
                "page_id": "draft_page",
                "page_type": "markdown"
            }),
            content_type='application/json'
        )
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )
