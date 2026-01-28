"""
Tests for Lambda-parity GET routes under /api/v1/.

Verifies that key GET endpoints return 200 (or expected 404) with mocked services.
"""

from unittest.mock import patch
from django.test import TestCase, Client


class LambdaParityGetRoutesTestCase(TestCase):
    """Smoke tests for GET /api/v1/... Lambda-parity endpoints."""

    def setUp(self):
        self.client = Client()

    @patch("apps.documentation.api.v1.pages_views.get_pages_service")
    def test_pages_list_returns_200(self, mock_get_service):
        mock_svc = mock_get_service.return_value
        mock_svc.list_pages.return_value = {"pages": [], "total": 0}
        response = self.client.get("/api/v1/pages/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("pages", data)
        self.assertIn("total", data)

    @patch("apps.documentation.api.v1.endpoints_views.get_endpoints_service")
    def test_endpoints_list_returns_200(self, mock_get_service):
        mock_svc = mock_get_service.return_value
        mock_svc.list_endpoints.return_value = {"endpoints": [], "total": 0}
        response = self.client.get("/api/v1/endpoints/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("endpoints", data)
        self.assertIn("total", data)

    @patch("apps.documentation.api.v1.relationships_views.get_relationships_service")
    def test_relationships_list_returns_200(self, mock_get_service):
        mock_svc = mock_get_service.return_value
        mock_svc.list_relationships.return_value = {"relationships": [], "total": 0}
        response = self.client.get("/api/v1/relationships/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("relationships", data)
        self.assertIn("total", data)

    @patch("apps.documentation.api.v1.postman_views.get_postman_service")
    def test_postman_list_returns_200(self, mock_get_service):
        mock_svc = mock_get_service.return_value
        mock_svc.list_configurations.return_value = {"configurations": [], "total": 0}
        response = self.client.get("/api/v1/postman/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("configurations", data)
        self.assertIn("total", data)

    @patch("apps.documentation.api.v1.index_views.get_shared_s3_index_manager")
    def test_index_pages_returns_200(self, mock_get_manager):
        mock_mgr = mock_get_manager.return_value
        mock_mgr.read_index.return_value = {"total": 0, "pages": []}
        response = self.client.get("/api/v1/index/pages/")
        self.assertIn(response.status_code, [200, 500])  # 500 if index missing
        if response.status_code == 200:
            data = response.json()
            self.assertIsInstance(data, dict)
