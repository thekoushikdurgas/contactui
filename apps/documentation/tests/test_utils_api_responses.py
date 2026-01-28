"""
Unit tests for api_responses module.

Tests cover:
- APIResponse class
- All response helper functions
- Response format validation
- Edge cases
"""

from __future__ import annotations

import json
from django.test import TestCase
from django.http import JsonResponse
from apps.documentation.utils.api_responses import (
    APIResponse,
    success_response,
    error_response,
    paginated_response,
    validation_error_response,
    not_found_response,
    forbidden_response,
    unauthorized_response,
    server_error_response,
    rate_limited_response,
)


class APIResponseTestCase(TestCase):
    """Test cases for APIResponse class."""
    
    def test_init_defaults(self):
        """Test APIResponse initialization with defaults."""
        response = APIResponse()
        
        self.assertTrue(response.success)
        self.assertIsNone(response.data)
        self.assertEqual(response.message, "")
        self.assertEqual(response.errors, [])
        self.assertEqual(response.meta, {})
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.timestamp)
        self.assertIsNotNone(response.request_id)
        self.assertEqual(len(response.request_id), 8)
    
    def test_init_with_data(self):
        """Test APIResponse initialization with data."""
        data = {"page_id": "test", "page_type": "docs"}
        response = APIResponse(success=True, data=data, message="Success")
        
        self.assertTrue(response.success)
        self.assertEqual(response.data, data)
        self.assertEqual(response.message, "Success")
    
    def test_init_error_response(self):
        """Test APIResponse initialization for error."""
        errors = ["Field required", "Invalid type"]
        response = APIResponse(
            success=False,
            message="Validation failed",
            errors=errors,
            status_code=400
        )
        
        self.assertFalse(response.success)
        self.assertEqual(response.message, "Validation failed")
        self.assertEqual(response.errors, errors)
        self.assertEqual(response.status_code, 400)
    
    def test_to_dict_success(self):
        """Test to_dict() for success response."""
        data = {"page_id": "test"}
        response = APIResponse(success=True, data=data, message="Success")
        result = response.to_dict()
        
        self.assertTrue(result["success"])
        self.assertEqual(result["data"], data)
        self.assertEqual(result["message"], "Success")
        self.assertIn("timestamp", result)
        self.assertIn("request_id", result)
        self.assertNotIn("errors", result)
        self.assertNotIn("meta", result)
    
    def test_to_dict_error(self):
        """Test to_dict() for error response."""
        errors = ["Error 1", "Error 2"]
        response = APIResponse(
            success=False,
            message="Failed",
            errors=errors,
            status_code=400
        )
        result = response.to_dict()
        
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Failed")
        self.assertEqual(result["errors"], errors)
        self.assertNotIn("data", result)
    
    def test_to_dict_with_meta(self):
        """Test to_dict() with metadata."""
        meta = {"pagination": {"page": 1, "total": 10}}
        response = APIResponse(success=True, meta=meta)
        result = response.to_dict()
        
        self.assertEqual(result["meta"], meta)
    
    def test_to_dict_omits_empty_fields(self):
        """Test to_dict() omits empty optional fields."""
        response = APIResponse()
        result = response.to_dict()
        
        self.assertNotIn("data", result)
        self.assertNotIn("message", result)
        self.assertNotIn("errors", result)
        self.assertNotIn("meta", result)
    
    def test_to_json_response(self):
        """Test to_json_response() conversion."""
        data = {"page_id": "test"}
        response = APIResponse(success=True, data=data)
        json_response = response.to_json_response()
        
        self.assertIsInstance(json_response, JsonResponse)
        self.assertEqual(json_response.status_code, 200)
        
        content = json.loads(json_response.content)
        self.assertTrue(content["success"])
        self.assertEqual(content["data"], data)
    
    def test_to_json_response_with_status_code(self):
        """Test to_json_response() with custom status code."""
        response = APIResponse(success=False, status_code=404)
        json_response = response.to_json_response()
        
        self.assertEqual(json_response.status_code, 404)
    
    def test_timestamp_generation(self):
        """Test timestamp is generated correctly."""
        import time
        
        response1 = APIResponse()
        time.sleep(0.01)  # Small delay
        response2 = APIResponse()
        
        self.assertGreater(response2.timestamp, response1.timestamp)
        self.assertIsInstance(response1.timestamp, int)
    
    def test_request_id_generation(self):
        """Test request ID is unique."""
        response1 = APIResponse()
        response2 = APIResponse()
        
        self.assertNotEqual(response1.request_id, response2.request_id)
        self.assertEqual(len(response1.request_id), 8)
        self.assertEqual(len(response2.request_id), 8)


class SuccessResponseTestCase(TestCase):
    """Test cases for success_response() helper."""
    
    def test_success_response_default(self):
        """Test success_response() with defaults."""
        response = success_response()
        
        self.assertTrue(response.success)
        self.assertIsNone(response.data)
        self.assertEqual(response.message, "")
        self.assertEqual(response.status_code, 200)
    
    def test_success_response_with_data(self):
        """Test success_response() with data."""
        data = {"page_id": "test"}
        response = success_response(data=data)
        
        self.assertTrue(response.success)
        self.assertEqual(response.data, data)
    
    def test_success_response_with_message(self):
        """Test success_response() with message."""
        response = success_response(message="Operation successful")
        
        self.assertTrue(response.success)
        self.assertEqual(response.message, "Operation successful")
    
    def test_success_response_with_meta(self):
        """Test success_response() with metadata."""
        meta = {"count": 10}
        response = success_response(meta=meta)
        
        self.assertEqual(response.meta, meta)


class ErrorResponseTestCase(TestCase):
    """Test cases for error_response() helper."""
    
    def test_error_response_default(self):
        """Test error_response() with defaults."""
        response = error_response()
        
        self.assertFalse(response.success)
        self.assertEqual(response.message, "An error occurred")
        self.assertEqual(response.status_code, 400)
    
    def test_error_response_with_message(self):
        """Test error_response() with custom message."""
        response = error_response(message="Custom error")
        
        self.assertFalse(response.success)
        self.assertEqual(response.message, "Custom error")
    
    def test_error_response_with_errors(self):
        """Test error_response() with error list."""
        errors = ["Error 1", "Error 2"]
        response = error_response(errors=errors)
        
        self.assertEqual(response.errors, errors)
    
    def test_error_response_with_status_code(self):
        """Test error_response() with custom status code."""
        response = error_response(status_code=500)
        
        self.assertEqual(response.status_code, 500)


class PaginatedResponseTestCase(TestCase):
    """Test cases for paginated_response() helper."""
    
    def test_paginated_response_default(self):
        """Test paginated_response() with defaults."""
        items = [{"id": 1}, {"id": 2}]
        response = paginated_response(items, total=2)
        
        self.assertTrue(response.success)
        self.assertEqual(response.data, items)
        self.assertIn("pagination", response.meta)
        self.assertEqual(response.meta["pagination"]["total"], 2)
        self.assertEqual(response.meta["pagination"]["page"], 1)
        self.assertEqual(response.meta["pagination"]["page_size"], 50)
    
    def test_paginated_response_with_pagination(self):
        """Test paginated_response() with pagination params."""
        items = [{"id": i} for i in range(1, 21)]
        response = paginated_response(items, total=100, page=2, page_size=20)
        
        pagination = response.meta["pagination"]
        self.assertEqual(pagination["total"], 100)
        self.assertEqual(pagination["page"], 2)
        self.assertEqual(pagination["page_size"], 20)
        self.assertEqual(pagination["total_pages"], 5)
    
    def test_paginated_response_total_pages_calculation(self):
        """Test total_pages calculation."""
        # 100 items, 20 per page = 5 pages
        response = paginated_response([], total=100, page=1, page_size=20)
        self.assertEqual(response.meta["pagination"]["total_pages"], 5)
        
        # 101 items, 20 per page = 6 pages (rounded up)
        response = paginated_response([], total=101, page=1, page_size=20)
        self.assertEqual(response.meta["pagination"]["total_pages"], 6)
        
        # 99 items, 20 per page = 5 pages
        response = paginated_response([], total=99, page=1, page_size=20)
        self.assertEqual(response.meta["pagination"]["total_pages"], 5)


class ValidationErrorResponseTestCase(TestCase):
    """Test cases for validation_error_response() helper."""
    
    def test_validation_error_response(self):
        """Test validation_error_response() with errors."""
        errors = ["Field 'page_id' is required", "Field 'page_type' is invalid"]
        response = validation_error_response(errors)
        
        self.assertFalse(response.success)
        self.assertEqual(response.errors, errors)
        self.assertEqual(response.status_code, 422)
        self.assertIn("validation", response.message.lower())


class NotFoundResponseTestCase(TestCase):
    """Test cases for not_found_response() helper."""
    
    def test_not_found_response_default(self):
        """Test not_found_response() with default."""
        response = not_found_response()
        
        self.assertFalse(response.success)
        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.message.lower())
    
    def test_not_found_response_with_resource(self):
        """Test not_found_response() with resource name."""
        response = not_found_response("Page")
        
        self.assertEqual(response.status_code, 404)
        self.assertIn("page", response.message.lower())


class ForbiddenResponseTestCase(TestCase):
    """Test cases for forbidden_response() helper."""
    
    def test_forbidden_response_default(self):
        """Test forbidden_response() with default."""
        response = forbidden_response()
        
        self.assertFalse(response.success)
        self.assertEqual(response.status_code, 403)
        self.assertIn("forbidden", response.message.lower())
    
    def test_forbidden_response_with_message(self):
        """Test forbidden_response() with custom message."""
        response = forbidden_response("Custom forbidden message")
        
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.message, "Custom forbidden message")


class UnauthorizedResponseTestCase(TestCase):
    """Test cases for unauthorized_response() helper."""
    
    def test_unauthorized_response_default(self):
        """Test unauthorized_response() with default."""
        response = unauthorized_response()
        
        self.assertFalse(response.success)
        self.assertEqual(response.status_code, 401)
        self.assertIn("unauthorized", response.message.lower())
    
    def test_unauthorized_response_with_message(self):
        """Test unauthorized_response() with custom message."""
        response = unauthorized_response("Custom auth message")
        
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.message, "Custom auth message")


class ServerErrorResponseTestCase(TestCase):
    """Test cases for server_error_response() helper."""
    
    def test_server_error_response_default(self):
        """Test server_error_response() with default."""
        response = server_error_response()
        
        self.assertFalse(response.success)
        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.message.lower())
    
    def test_server_error_response_with_message(self):
        """Test server_error_response() with custom message."""
        response = server_error_response("Database connection failed")
        
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.message, "Database connection failed")


class RateLimitedResponseTestCase(TestCase):
    """Test cases for rate_limited_response() helper."""
    
    def test_rate_limited_response_default(self):
        """Test rate_limited_response() with default."""
        response = rate_limited_response()
        
        self.assertFalse(response.success)
        self.assertEqual(response.status_code, 429)
        self.assertIn("rate limit", response.message.lower())
    
    def test_rate_limited_response_with_retry_after(self):
        """Test rate_limited_response() with retry_after."""
        response = rate_limited_response(retry_after=60)
        
        self.assertEqual(response.status_code, 429)
        self.assertIn("rate limit", response.message.lower())
        self.assertIn("retry_after", response.meta)
        self.assertEqual(response.meta["retry_after"], 60)
    
    def test_rate_limited_response_with_custom_message(self):
        """Test rate_limited_response() with custom message."""
        response = rate_limited_response(message="Too many requests", retry_after=30)
        
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.message, "Too many requests")
        self.assertIn("retry_after", response.meta)
        self.assertEqual(response.meta["retry_after"], 30)
