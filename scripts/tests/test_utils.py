import os
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure scripts package is importable
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.utils.validators import (
    ValidationError,
    load_json_file,
    validate_json_structure,
    validate_date_consistency,
    validate_route,
)


class ValidatorsTestCase(unittest.TestCase):
    """Tests for validators utilities."""

    def test_validate_json_structure_missing_fields(self):
        data = {"name": "test"}
        is_valid, errors = validate_json_structure(data, ["name", "id"])
        self.assertFalse(is_valid)
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], ValidationError)
        self.assertEqual(errors[0].field, "id")

    def test_validate_date_consistency_invalid(self):
        is_valid, errors = validate_date_consistency(
            "2024-01-02T00:00:00Z",
            "2024-01-01T00:00:00Z",
        )
        self.assertFalse(is_valid)
        self.assertTrue(errors)
        self.assertEqual(errors[0].field, "updated_at")

    def test_validate_route(self):
        is_valid, errors = validate_route("/valid")
        self.assertTrue(is_valid)
        self.assertEqual(errors, [])

        is_valid, errors = validate_route("invalid")
        self.assertFalse(is_valid)
        self.assertTrue(errors)

    def test_load_json_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.json"
            path.write_text('{"key": "value"}', encoding="utf-8")
            data, error = load_json_file(path)
            self.assertEqual(data, {"key": "value"})
            self.assertIsNone(error)


if __name__ == "__main__":
    unittest.main()
