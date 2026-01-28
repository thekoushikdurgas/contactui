"""
Unit tests for repository layer.

Tests cover:
- PagesRepository
- EndpointsRepository
- RelationshipsRepository
- PostmanRepository (basic)

Uses mocked S3JSONStorage and S3IndexManager.
"""

from __future__ import annotations

from unittest.mock import Mock, MagicMock, patch
from django.test import TestCase

from apps.documentation.repositories.pages_repository import PagesRepository
from apps.documentation.repositories.endpoints_repository import EndpointsRepository
from apps.documentation.repositories.relationships_repository import RelationshipsRepository
from apps.documentation.repositories.postman_repository import PostmanRepository
from apps.documentation.tests.fixtures import PageFactory, EndpointFactory, RelationshipFactory
from apps.core.exceptions import RepositoryError


class PagesRepositoryTestCase(TestCase):
    """Test cases for PagesRepository."""

    def setUp(self):
        self.mock_storage = Mock()
        self.mock_index = Mock()
        self.repo = PagesRepository(storage=self.mock_storage, index_manager=self.mock_index)

    def test_get_by_page_id_success(self):
        page = PageFactory.create(page_id="test-page")
        self.mock_storage.read_json.return_value = page

        result = self.repo.get_by_page_id("test-page")

        self.assertIsNotNone(result)
        self.assertEqual(result["page_id"], "test-page")
        self.mock_storage.read_json.assert_called_once()
        call_args = self.mock_storage.read_json.call_args[0][0]
        self.assertIn("pages/", call_args)
        self.assertIn("test-page", call_args)

    def test_get_by_page_id_not_found(self):
        self.mock_storage.read_json.return_value = None

        result = self.repo.get_by_page_id("missing")

        self.assertIsNone(result)

    def test_get_by_page_id_page_type_filter_no_match(self):
        page = PageFactory.create(page_id="p1", page_type="docs")
        self.mock_storage.read_json.return_value = page

        result = self.repo.get_by_page_id("p1", page_type="dashboard")

        self.assertIsNone(result)

    def test_get_by_page_id_page_type_filter_match(self):
        page = PageFactory.create(page_id="p1", page_type="docs")
        self.mock_storage.read_json.return_value = page

        result = self.repo.get_by_page_id("p1", page_type="docs")

        self.assertIsNotNone(result)
        self.assertEqual(result["page_type"], "docs")

    def test_get_by_page_id_empty_page_id_raises(self):
        with self.assertRaises(ValueError) as ctx:
            self.repo.get_by_page_id("")
        self.assertIn("page_id", str(ctx.exception))

    def test_get_by_page_id_storage_error_raises_repository_error(self):
        self.mock_storage.read_json.side_effect = IOError("read failed")

        with self.assertRaises(RepositoryError) as ctx:
            self.repo.get_by_page_id("x")
        self.assertIn("Failed to get page", getattr(ctx.exception, "message", str(ctx.exception)))

    def test_get_by_route_success(self):
        page = PageFactory.create(page_id="about")
        self.mock_index.read_index.return_value = {
            "indexes": {"by_route": {"/about": "about"}},
        }
        self.mock_storage.read_json.return_value = page

        result = self.repo.get_by_route("/about")

        self.assertIsNotNone(result)
        self.assertEqual(result["page_id"], "about")
        self.mock_index.read_index.assert_called_once_with("pages")
        self.mock_storage.read_json.assert_called()

    def test_get_by_route_not_found(self):
        self.mock_index.read_index.return_value = {"indexes": {"by_route": {}}}

        result = self.repo.get_by_route("/missing")

        self.assertIsNone(result)
        self.mock_storage.read_json.assert_not_called()

    def test_get_by_route_empty_raises(self):
        with self.assertRaises(ValueError) as ctx:
            self.repo.get_by_route("")
        self.assertIn("route", str(ctx.exception))

    def test_list_all_success(self):
        pages = PageFactory.create_batch(3)
        self.mock_index.get_indexed_pages.return_value = pages

        result = self.repo.list_all(limit=10, offset=0)

        self.assertEqual(len(result), 3)
        self.mock_index.get_indexed_pages.assert_called_once()
        filters = self.mock_index.get_indexed_pages.call_args[0][0]
        self.assertEqual(filters["include_drafts"], True)
        self.assertEqual(filters["include_deleted"], False)

    def test_list_all_with_filters(self):
        self.mock_index.get_indexed_pages.return_value = []

        self.repo.list_all(
            page_type="docs",
            status="active",
            page_state="published",
            include_drafts=False,
            limit=5,
            offset=2,
        )

        filters = self.mock_index.get_indexed_pages.call_args[0][0]
        self.assertEqual(filters["page_type"], "docs")
        self.assertEqual(filters["status"], "active")
        self.assertEqual(filters["page_state"], "published")
        self.assertEqual(filters["include_drafts"], False)

    def test_list_all_index_error_raises_repository_error(self):
        self.mock_index.get_indexed_pages.side_effect = RuntimeError("index broken")

        with self.assertRaises(RepositoryError) as ctx:
            self.repo.list_all()
        self.assertIn("Failed to list pages", str(ctx.exception.message))

    def test_create_missing_page_id_raises(self):
        with self.assertRaises(ValueError) as ctx:
            self.repo.create({"metadata": {}})
        self.assertIn("page_id", str(ctx.exception))

    def test__get_page_key(self):
        key = self.repo._get_page_key("my-page")
        self.assertIn("pages/", key)
        self.assertIn("my-page", key)
        self.assertTrue(key.endswith(".json"))

    def test__validate_and_fix_route_adds_slash(self):
        fixed = self.repo._validate_and_fix_route("about", "about_page")
        self.assertTrue(fixed.startswith("/"))

    def test__validate_and_fix_route_empty_uses_page_id(self):
        fixed = self.repo._validate_and_fix_route("", "foo_page")
        self.assertTrue(fixed.startswith("/"))
        self.assertIn("foo", fixed)


class EndpointsRepositoryTestCase(TestCase):
    """Test cases for EndpointsRepository."""

    def setUp(self):
        self.mock_storage = Mock()
        self.mock_index = Mock()
        self.repo = EndpointsRepository(storage=self.mock_storage, index_manager=self.mock_index)

    def test_get_by_endpoint_id_success(self):
        ep = EndpointFactory.create(endpoint_id="ep1")
        self.mock_storage.read_json.return_value = ep

        result = self.repo.get_by_endpoint_id("ep1")

        self.assertIsNotNone(result)
        self.assertEqual(result["endpoint_id"], "ep1")

    def test_get_by_endpoint_id_not_found(self):
        self.mock_storage.read_json.return_value = None

        result = self.repo.get_by_endpoint_id("missing")

        self.assertIsNone(result)

    def test_list_all_success(self):
        eps = EndpointFactory.create_batch(2)
        self.mock_index.read_index.return_value = {"endpoints": eps}

        result = self.repo.list_all(limit=10, offset=0)

        self.assertEqual(len(result), 2)
        self.mock_index.read_index.assert_called_once_with("endpoints")


class RelationshipsRepositoryTestCase(TestCase):
    """Test cases for RelationshipsRepository."""

    def setUp(self):
        self.mock_storage = Mock()
        self.mock_index = Mock()
        self.repo = RelationshipsRepository(storage=self.mock_storage, index_manager=self.mock_index)

    def test_get_by_relationship_id_success(self):
        rel = RelationshipFactory.create(relationship_id="rel-1")
        self.mock_storage.read_json.return_value = rel

        result = self.repo.get_by_relationship_id("rel-1")

        self.assertIsNotNone(result)
        self.assertEqual(result["relationship_id"], "rel-1")

    def test_get_by_relationship_id_not_found(self):
        self.mock_storage.read_json.return_value = None

        result = self.repo.get_by_relationship_id("missing")

        self.assertIsNone(result)

    def test_list_all_success(self):
        rels = RelationshipFactory.create_batch(2)
        self.mock_index.read_index.return_value = {"relationships": rels, "indexes": {}}
        # list_all fetches each via get_by_relationship_id -> storage.read_json
        self.mock_storage.read_json.side_effect = rels

        result = self.repo.list_all(limit=10, offset=0)

        self.assertEqual(len(result), 2)
        self.mock_index.read_index.assert_called_once_with("relationships")


class PostmanRepositoryTestCase(TestCase):
    """Basic test cases for PostmanRepository."""

    def setUp(self):
        self.mock_storage = Mock()
        self.mock_index = Mock()
        self.repo = PostmanRepository(storage=self.mock_storage, index_manager=self.mock_index)

    def test_init(self):
        self.assertIs(self.repo.storage, self.mock_storage)
        self.assertIs(self.repo.index_manager, self.mock_index)

    def test_get_collection_by_id_not_found(self):
        self.mock_storage.read_json.return_value = None

        result = self.repo.get_collection_by_id("missing")

        self.assertIsNone(result)
