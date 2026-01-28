"""
Unit tests for request_validation module.

Tests cover:
- @validate_request decorator
- @validate_query_params decorator
- @validate_path_params decorator
- Validation error handling
- Edge cases
"""

from __future__ import annotations

import json
from unittest.mock import Mock, patch
from django.test import TestCase
from django.http import HttpRequest, JsonResponse
from pydantic import BaseModel, Field, ValidationError as PydanticValidationError

from apps.documentation.utils.request_validation import (
    validate_request,
    validate_query_params,
    validate_path_params,
)
from apps.documentation.utils.api_responses import validation_error_response


# Test schemas
class TestSchema(BaseModel):
    """Test Pydantic schema."""
    page_id: str = Field(..., min_length=1)
    page_type: str = Field(..., pattern="^(docs|marketing|dashboard)$")


class TestQuerySchema(BaseModel):
    """Test query parameter schema."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class TestPathSchema(BaseModel):
    """Test path parameter schema."""
    page_id: str = Field(..., min_length=1)


class ValidateRequestTestCase(TestCase):
    """Test cases for @validate_request decorator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.request = Mock(spec=HttpRequest)
        self.request.method = "POST"
        self.request.content_type = "application/json"
    
    def test_validate_request_success(self):
        """Test successful validation."""
        @validate_request(TestSchema)
        def test_view(request: HttpRequest) -> JsonResponse:
            self.assertIsNotNone(request.validated_data)
            self.assertEqual(request.validated_data.page_id, "test-page")
            self.assertEqual(request.validated_data.page_type, "docs")
            from apps.documentation.utils.api_responses import success_response
            return success_response(data={"validated": True}).to_json_response()
        
        self.request.body = json.dumps({
            "page_id": "test-page",
            "page_type": "docs"
        }).encode()
        
        response = test_view(self.request)
        self.assertEqual(response.status_code, 200)
    
    def test_validate_request_missing_field(self):
        """Test validation with missing required field."""
        @validate_request(TestSchema)
        def test_view(request: HttpRequest) -> JsonResponse:
            pass  # Should not reach here
        
        self.request.body = json.dumps({"page_type": "docs"}).encode()
        
        response = test_view(self.request)
        self.assertEqual(response.status_code, 422)
        
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("errors", data)
        self.assertTrue(any("page_id" in str(err).lower() for err in data["errors"]))
    
    def test_validate_request_invalid_type(self):
        """Test validation with invalid field type."""
        @validate_request(TestSchema)
        def test_view(request: HttpRequest) -> JsonResponse:
            pass  # Should not reach here
        
        self.request.body = json.dumps({
            "page_id": "test",
            "page_type": "invalid"
        }).encode()
        
        response = test_view(self.request)
        self.assertEqual(response.status_code, 422)
        
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("errors", data)
    
    def test_validate_request_invalid_json(self):
        """Test validation with invalid JSON."""
        @validate_request(TestSchema)
        def test_view(request: HttpRequest) -> JsonResponse:
            pass  # Should not reach here
        
        self.request.body = b"invalid json{"
        
        response = test_view(self.request)
        self.assertEqual(response.status_code, 422)
        
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("Invalid JSON", data["errors"][0])
    
    def test_validate_request_empty_body_not_allowed(self):
        """Test validation with empty body when not allowed."""
        @validate_request(TestSchema, allow_empty=False)
        def test_view(request: HttpRequest) -> JsonResponse:
            pass  # Should not reach here
        
        self.request.body = b""
        
        response = test_view(self.request)
        self.assertEqual(response.status_code, 422)
        
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("body is required", data["errors"][0].lower())
    
    def test_validate_request_empty_body_allowed(self):
        """Test validation with empty body when allowed."""
        class OptionalSchema(BaseModel):
            page_id: str = Field(default="default")
        
        @validate_request(OptionalSchema, allow_empty=True)
        def test_view(request: HttpRequest) -> JsonResponse:
            self.assertIsNotNone(request.validated_data)
            from apps.documentation.utils.api_responses import success_response
            return success_response().to_json_response()
        
        self.request.body = b""
        
        response = test_view(self.request)
        self.assertEqual(response.status_code, 200)
    
    def test_validate_request_no_json_parsing(self):
        """Test validation without JSON parsing (uses POST data)."""
        @validate_request(TestSchema, parse_json=False)
        def test_view(request: HttpRequest) -> JsonResponse:
            self.assertIsNotNone(request.validated_data)
            from apps.documentation.utils.api_responses import success_response
            return success_response().to_json_response()
        
        self.request.POST = {
            "page_id": "test-page",
            "page_type": "docs"
        }
        self.request.body = b""
        
        response = test_view(self.request)
        self.assertEqual(response.status_code, 200)
    
    def test_validate_request_preserves_function_metadata(self):
        """Test that decorator preserves function metadata."""
        @validate_request(TestSchema)
        def test_view(request: HttpRequest) -> JsonResponse:
            """Test view function."""
            pass
        
        self.assertEqual(test_view.__name__, "test_view")
        self.assertEqual(test_view.__doc__, "Test view function.")


class ValidateQueryParamsTestCase(TestCase):
    """Test cases for @validate_query_params decorator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.request = Mock(spec=HttpRequest)
        self.request.method = "GET"
    
    def test_validate_query_params_success(self):
        """Test successful query parameter validation."""
        @validate_query_params(TestQuerySchema)
        def test_view(request: HttpRequest) -> JsonResponse:
            self.assertIsNotNone(request.validated_query_params)
            self.assertEqual(request.validated_query_params.page, 2)
            self.assertEqual(request.validated_query_params.page_size, 50)
            from apps.documentation.utils.api_responses import success_response
            return success_response().to_json_response()
        
        self.request.GET = {"page": "2", "page_size": "50"}
        
        response = test_view(self.request)
        self.assertEqual(response.status_code, 200)
    
    def test_validate_query_params_defaults(self):
        """Test query parameter validation with defaults."""
        @validate_query_params(TestQuerySchema)
        def test_view(request: HttpRequest) -> JsonResponse:
            self.assertIsNotNone(request.validated_query_params)
            self.assertEqual(request.validated_query_params.page, 1)  # Default
            self.assertEqual(request.validated_query_params.page_size, 20)  # Default
            from apps.documentation.utils.api_responses import success_response
            return success_response().to_json_response()
        
        self.request.GET = {}
        
        response = test_view(self.request)
        self.assertEqual(response.status_code, 200)
    
    def test_validate_query_params_invalid_type(self):
        """Test query parameter validation with invalid type."""
        @validate_query_params(TestQuerySchema)
        def test_view(request: HttpRequest) -> JsonResponse:
            pass  # Should not reach here
        
        self.request.GET = {"page": "invalid", "page_size": "50"}
        
        response = test_view(self.request)
        self.assertEqual(response.status_code, 422)
        
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("errors", data)
    
    def test_validate_query_params_out_of_range(self):
        """Test query parameter validation with out-of-range value."""
        @validate_query_params(TestQuerySchema)
        def test_view(request: HttpRequest) -> JsonResponse:
            pass  # Should not reach here
        
        self.request.GET = {"page": "0", "page_size": "50"}  # page < 1
        
        response = test_view(self.request)
        self.assertEqual(response.status_code, 422)
        
        data = json.loads(response.content)
        self.assertFalse(data["success"])


class ValidatePathParamsTestCase(TestCase):
    """Test cases for @validate_path_params decorator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.request = Mock(spec=HttpRequest)
    
    def test_validate_path_params_success(self):
        """Test successful path parameter validation."""
        @validate_path_params(TestPathSchema)
        def test_view(request: HttpRequest, page_id: str) -> JsonResponse:
            self.assertIsNotNone(request.validated_path_params)
            self.assertEqual(request.validated_path_params.page_id, "test-page")
            from apps.documentation.utils.api_responses import success_response
            return success_response().to_json_response()
        
        response = test_view(self.request, page_id="test-page")
        self.assertEqual(response.status_code, 200)
    
    def test_validate_path_params_missing(self):
        """Test path parameter validation with missing parameter."""
        @validate_path_params(TestPathSchema)
        def test_view(request: HttpRequest, page_id: str) -> JsonResponse:
            pass  # Should not reach here
        
        response = test_view(self.request, page_id="")  # Empty string
        
        self.assertEqual(response.status_code, 422)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("errors", data)
    
    def test_validate_path_params_invalid(self):
        """Test path parameter validation with invalid value."""
        @validate_path_params(TestPathSchema)
        def test_view(request: HttpRequest, page_id: str) -> JsonResponse:
            pass  # Should not reach here
        
        # page_id too short (min_length=1, but empty string fails)
        response = test_view(self.request, page_id="")
        
        self.assertEqual(response.status_code, 422)
        data = json.loads(response.content)
        self.assertFalse(data["success"])


class ValidationErrorFormattingTestCase(TestCase):
    """Test cases for validation error formatting."""
    
    def test_validation_error_formatting(self):
        """Test that validation errors are properly formatted."""
        @validate_request(TestSchema)
        def test_view(request: HttpRequest) -> JsonResponse:
            pass  # Should not reach here
        
        request = Mock(spec=HttpRequest)
        request.method = "POST"
        request.body = json.dumps({
            "page_id": "",  # Too short
            "page_type": "invalid"  # Invalid pattern
        }).encode()
        
        response = test_view(request)
        data = json.loads(response.content)
        
        self.assertFalse(data["success"])
        self.assertIn("errors", data)
        self.assertIsInstance(data["errors"], list)
        self.assertGreater(len(data["errors"]), 0)
        
        # Check error format: "field: message"
        for error in data["errors"]:
            self.assertIn(":", str(error))


class ValidationEdgeCasesTestCase(TestCase):
    """Test cases for edge cases in validation."""
    
    def test_validate_request_with_nested_data(self):
        """Test validation with nested data structures."""
        class NestedSchema(BaseModel):
            page_id: str
            metadata: dict
        
        @validate_request(NestedSchema)
        def test_view(request: HttpRequest) -> JsonResponse:
            self.assertIsNotNone(request.validated_data)
            self.assertIsInstance(request.validated_data.metadata, dict)
            from apps.documentation.utils.api_responses import success_response
            return success_response().to_json_response()
        
        request = Mock(spec=HttpRequest)
        request.method = "POST"
        request.body = json.dumps({
            "page_id": "test",
            "metadata": {"key": "value"}
        }).encode()
        
        response = test_view(request)
        self.assertEqual(response.status_code, 200)
    
    def test_validate_request_with_list_data(self):
        """Test validation with list data."""
        class ListSchema(BaseModel):
            items: list[str]
        
        @validate_request(ListSchema)
        def test_view(request: HttpRequest) -> JsonResponse:
            self.assertIsNotNone(request.validated_data)
            self.assertIsInstance(request.validated_data.items, list)
            from apps.documentation.utils.api_responses import success_response
            return success_response().to_json_response()
        
        request = Mock(spec=HttpRequest)
        request.method = "POST"
        request.body = json.dumps({
            "items": ["item1", "item2"]
        }).encode()
        
        response = test_view(request)
        self.assertEqual(response.status_code, 200)
