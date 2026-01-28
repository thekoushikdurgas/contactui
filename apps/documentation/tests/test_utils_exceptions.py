"""Tests for custom exception classes."""

from django.test import TestCase

from apps.documentation.utils.exceptions import (
    DocumentationError,
    S3Error,
    RepositoryError,
    LambdaAPIError,
)
from apps.core.exceptions import ServiceError


class DocumentationErrorTestCase(TestCase):
    """Test DocumentationError exception."""

    def test_documentation_error_creation(self):
        """Test creating DocumentationError with message."""
        error = DocumentationError("Test error message")
        self.assertEqual(str(error), "Test error message")
        self.assertIsInstance(error, ServiceError)
        self.assertEqual(error.service_name, "DocumentationService")
        self.assertEqual(error.error_code, "documentation_error")

    def test_documentation_error_with_resource_id(self):
        """Test creating DocumentationError with resource_id."""
        error = DocumentationError(
            "Resource not found",
            resource_id="page_123"
        )
        self.assertEqual(error.resource_id, "page_123")
        self.assertEqual(str(error), "Resource not found")

    def test_documentation_error_with_operation(self):
        """Test creating DocumentationError with operation."""
        error = DocumentationError(
            "Operation failed",
            operation="create_page"
        )
        self.assertEqual(error.operation, "create_page")

    def test_documentation_error_with_custom_error_code(self):
        """Test creating DocumentationError with custom error code."""
        error = DocumentationError(
            "Custom error",
            error_code="custom_error_code"
        )
        self.assertEqual(error.error_code, "custom_error_code")

    def test_documentation_error_inheritance(self):
        """Test that DocumentationError inherits from ServiceError."""
        error = DocumentationError("Test")
        self.assertIsInstance(error, ServiceError)
        self.assertIsInstance(error, Exception)

    def test_documentation_error_all_fields(self):
        """Test creating DocumentationError with all fields."""
        error = DocumentationError(
            message="Complete error",
            resource_id="resource_123",
            operation="update",
            service_name="CustomService",
            error_code="custom_code"
        )
        self.assertEqual(error.resource_id, "resource_123")
        self.assertEqual(error.operation, "update")
        self.assertEqual(error.service_name, "CustomService")
        self.assertEqual(error.error_code, "custom_code")


class ExceptionImportsTestCase(TestCase):
    """Test that exceptions are properly imported and re-exported."""

    def test_s3_error_imported(self):
        """Test that S3Error can be imported."""
        from apps.documentation.utils.exceptions import S3Error
        self.assertTrue(issubclass(S3Error, Exception))

    def test_repository_error_imported(self):
        """Test that RepositoryError can be imported."""
        from apps.documentation.utils.exceptions import RepositoryError
        self.assertTrue(issubclass(RepositoryError, Exception))

    def test_lambda_api_error_imported(self):
        """Test that LambdaAPIError can be imported."""
        from apps.documentation.utils.exceptions import LambdaAPIError
        self.assertTrue(issubclass(LambdaAPIError, Exception))

    def test_exception_usage(self):
        """Test that exceptions can be raised and caught."""
        try:
            raise DocumentationError("Test error")
        except DocumentationError as e:
            self.assertEqual(str(e), "Test error")
        except Exception:
            self.fail("DocumentationError should be caught by its own type")
