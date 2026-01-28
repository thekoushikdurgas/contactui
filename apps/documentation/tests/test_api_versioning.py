"""
Tests for API versioning (versions endpoint, version router).
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
import json

from apps.documentation.api_router import (
    get_version_from_path,
    negotiate_version,
    SUPPORTED_VERSIONS,
    DEFAULT_VERSION,
    VERSION_INFO,
)

User = get_user_model()


class ApiVersionRouterTestCase(TestCase):
    """Test cases for version router utilities."""

    def test_get_version_from_path_v1(self):
        self.assertEqual(get_version_from_path("/docs/api/v1/pages/"), "v1")
        self.assertEqual(get_version_from_path("/docs/api/v1/health/"), "v1")

    def test_get_version_from_path_v2(self):
        self.assertEqual(get_version_from_path("/docs/api/v2/stats/"), "v2")

    def test_get_version_from_path_no_version(self):
        self.assertIsNone(get_version_from_path("/docs/api/health/"))
        self.assertIsNone(get_version_from_path("/docs/api/pages/"))

    def test_get_version_from_path_invalid(self):
        self.assertIsNone(get_version_from_path("/docs/api/v9/"))
        self.assertIsNone(get_version_from_path("/other/path/"))

    def test_supported_versions(self):
        self.assertIn("v1", SUPPORTED_VERSIONS)
        self.assertIn("v2", SUPPORTED_VERSIONS)
        self.assertEqual(DEFAULT_VERSION, "v1")

    def test_version_info_structure(self):
        for v in SUPPORTED_VERSIONS:
            self.assertIn(v, VERSION_INFO)
            info = VERSION_INFO[v]
            self.assertIn("deprecated", info)
            self.assertIn("description", info)


class ApiVersionsEndpointTestCase(TestCase):
    """Test cases for GET /docs/api/versions/."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.client.login(username="testuser", password="testpass123")

    def test_versions_endpoint_success(self):
        url = reverse("documentation:api_versions")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertIn("data", data)
        self.assertIn("versions", data["data"])
        self.assertIn("default_version", data["data"])
        self.assertEqual(data["data"]["default_version"], "v1")
        self.assertIn("v1", [x["version"] for x in data["data"]["versions"]])
        self.assertIn("v2", [x["version"] for x in data["data"]["versions"]])

    def test_versions_endpoint_v1_path(self):
        url = "/docs/api/v1/versions/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertIn("meta", data)
        self.assertEqual(data["meta"]["request_version"], "v1")

    def test_versions_endpoint_v2_path(self):
        url = "/docs/api/v2/versions/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(data["meta"]["request_version"], "v2")

    def test_versions_requires_login(self):
        self.client.logout()
        url = reverse("documentation:api_versions")
        response = self.client.get(url)
        self.assertIn(response.status_code, (302, 401, 403))
