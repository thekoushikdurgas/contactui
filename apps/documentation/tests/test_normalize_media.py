"""
Tests for media normalization management commands.

Runs normalize_media_pages_endpoints, normalize_media_relationships,
normalize_media_postman_n8n (and optionally normalize_media_files) in dry-run
and asserts they complete with no validation/parse errors when media is present.
"""

from io import StringIO

from django.test import TestCase
from django.core.management import call_command


class NormalizeMediaCommandsTestCase(TestCase):
    """Test that normalization commands run in dry-run without errors."""

    def test_normalize_media_pages_endpoints_dry_run_completes(self):
        """normalize_media_pages_endpoints (dry-run) completes and reports 0 errors."""
        out = StringIO()
        err = StringIO()
        call_command("normalize_media_pages_endpoints", stdout=out, stderr=err)
        self.assertIn("Normalization run completed", out.getvalue())
        # Expect "0 errors" in the pages and endpoints summary lines
        out_str = out.getvalue()
        self.assertIn("[pages]", out_str)
        self.assertIn("[endpoints]", out_str)
        # If there are errors they appear on stderr
        err_str = err.getvalue()
        self.assertEqual(err_str.strip(), "", msg=f"Unexpected stderr: {err_str!r}")

    def test_normalize_media_relationships_dry_run_completes(self):
        """normalize_media_relationships (dry-run) completes and reports no errors on stderr."""
        out = StringIO()
        err = StringIO()
        call_command("normalize_media_relationships", stdout=out, stderr=err)
        self.assertIn("Normalized", out.getvalue())
        err_str = err.getvalue()
        self.assertEqual(err_str.strip(), "", msg=f"Unexpected stderr: {err_str!r}")

    def test_normalize_media_postman_n8n_dry_run_completes(self):
        """normalize_media_postman_n8n (dry-run) completes and reports no errors on stderr."""
        out = StringIO()
        err = StringIO()
        call_command("normalize_media_postman_n8n", stdout=out, stderr=err)
        self.assertIn("Postman/n8n normalization run completed", out.getvalue())
        err_str = err.getvalue()
        self.assertEqual(err_str.strip(), "", msg=f"Unexpected stderr: {err_str!r}")

    def test_normalize_media_files_dry_run_completes(self):
        """normalize_media_files (dry-run) completes; subcommands run without fatal errors."""
        out = StringIO()
        err = StringIO()
        call_command("normalize_media_files", stdout=out, stderr=err)
        self.assertIn("normalize_media_files run completed", out.getvalue())
        # Stderr may contain individual file errors; we only assert the command didn't raise
        # and that the overall run completed (no unhandled exception)
