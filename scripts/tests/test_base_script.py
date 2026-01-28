import sys
import unittest
from pathlib import Path

# Ensure scripts package is importable
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.base.base_script import BaseScript


class DummyScript(BaseScript):
    """Simple script for testing BaseScript."""

    def run(self, args):
        return {"processed": 1}


class BaseScriptTestCase(unittest.TestCase):
    """Tests for BaseScript."""

    def test_initial_stats(self):
        script = DummyScript("dummy")
        script.setup()
        self.assertIn("total", script.stats)
        self.assertIn("errors", script.stats)
        self.assertEqual(script.stats["errors"], 0)

    def test_log_error_increments(self):
        script = DummyScript("dummy")
        script.setup()
        script.log_error(Exception("boom"), context="test")
        self.assertEqual(script.stats["errors"], 1)
        self.assertEqual(len(script.errors), 1)

    def test_parse_arguments_sets_dry_run(self):
        script = DummyScript("dummy")
        args = script.parse_arguments(["--dry-run"])
        self.assertTrue(args.dry_run)
        self.assertTrue(script.dry_run)


if __name__ == "__main__":
    unittest.main()
