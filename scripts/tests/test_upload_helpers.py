import sys
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

# Ensure scripts package is importable
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.utils.upload_helpers import (
    sanitize_path,
    normalize_method,
    normalize_endpoint_path,
    generate_s3_key,
    load_and_validate_file,
)


class UploadHelpersTestCase(unittest.TestCase):
    """Tests for upload helper utilities."""

    def test_sanitize_path(self):
        self.assertEqual(sanitize_path("/foo/bar"), "foo_bar")
        self.assertEqual(sanitize_path(""), "root")

    def test_normalize_method(self):
        self.assertEqual(normalize_method("post"), "POST")
        self.assertEqual(normalize_method(""), "GET")

    def test_normalize_endpoint_path(self):
        self.assertEqual(normalize_endpoint_path("graphql", "Login"), "graphql/Login")
        self.assertEqual(normalize_endpoint_path("v1", "/health"), "/health")

    @patch("scripts.utils.upload_helpers.config.get_s3_data_prefix", return_value="data/")
    def test_generate_s3_key(self, mock_prefix):
        key = generate_s3_key("pages", "test")
        self.assertEqual(key, "data/pages/test.json")
        key = generate_s3_key("relationships", "page/endpoint", "by-page")
        self.assertEqual(key, "data/relationships/by-page/page_endpoint.json")

    def test_load_and_validate_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "sample.json"
            file_path.write_text('{"page_id": "test"}', encoding="utf-8")
            data, error, validation_errors = load_and_validate_file(
                file_path,
                resource_type="pages",
                required_fields=["page_id"],
            )
            self.assertIsNotNone(data)
            self.assertIsNone(error)
            self.assertEqual(validation_errors, [])


if __name__ == "__main__":
    unittest.main()
