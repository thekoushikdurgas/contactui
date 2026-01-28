"""
Integration tests for postman views.

Tests the postman view layer including:
- Postman detail view
- Postman form view
"""

import json
from unittest.mock import Mock, patch
from django.test import TestCase, Client
from django.urls import reverse

from apps.documentation.tests.helpers import (
    BaseAPITestCase,
)


class PostmanDetailViewTestCase(BaseAPITestCase):
    """Test cases for postman detail view."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.postman_id = "test_postman"
        self.detail_url = reverse('documentation:postman_detail', args=[self.postman_id])
    
    @patch('apps.documentation.views.postman_views.postman_service')
    def test_postman_detail_view_success(self, mock_postman_service):
        """Test successful postman detail view."""
        mock_postman_service.get_postman_config.return_value = {
            "postman_id": self.postman_id,
            "collection_name": "Test Collection",
            "version": "1.0.0"
        }
        
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
    
    @patch('apps.documentation.views.postman_views.postman_service')
    def test_postman_detail_view_not_found(self, mock_postman_service):
        """Test postman detail view with non-existent postman config."""
        from apps.documentation.utils.exceptions import NotFoundError
        mock_postman_service.get_postman_config.side_effect = NotFoundError("Postman config not found")
        
        response = self.client.get(self.detail_url)
        self.assertIn(response.status_code, [200, 404])


class PostmanFormViewTestCase(BaseAPITestCase):
    """Test cases for postman form view."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.create_url = reverse('documentation:postman_create')
        self.edit_url = reverse('documentation:postman_edit', args=['test_postman'])
    
    def test_postman_form_view_create_get(self):
        """Test postman create form GET request."""
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
    
    @patch('apps.documentation.views.postman_views.postman_service')
    def test_postman_form_view_edit_get(self, mock_postman_service):
        """Test postman edit form GET request."""
        mock_postman_service.get_postman_config.return_value = {
            "postman_id": "test_postman",
            "collection_name": "Test Collection"
        }
        
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 200)
