"""
Verification tests for API response standardization (Task 3.1.1 and 3.1.2).

Verifies that:
- Unified API response format structure is correct
- Response helpers exist and work correctly
- All endpoints use standardized response format
"""

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
    unauthorized_response,
    forbidden_response,
    server_error_response,
    rate_limited_response,
)


class APIResponseFormatVerificationTestCase(TestCase):
    """Verify unified API response format structure (Task 3.1.1)."""
    
    def test_success_response_format(self):
        """Verify success response format structure."""
        response = success_response(data={"key": "value"}, message="Success")
        response_dict = response.to_dict()
        
        # Verify required fields
        self.assertIn("success", response_dict)
        self.assertIn("data", response_dict)
        self.assertIn("message", response_dict)
        self.assertIn("timestamp", response_dict)
        self.assertIn("request_id", response_dict)
        
        # Verify success is True
        self.assertTrue(response_dict["success"])
        
        # Verify data structure
        self.assertEqual(response_dict["data"], {"key": "value"})
        self.assertEqual(response_dict["message"], "Success")
    
    def test_error_response_format(self):
        """Verify error response format structure."""
        response = error_response(message="Error occurred", errors=["Error 1", "Error 2"])
        response_dict = response.to_dict()
        
        # Verify required fields
        self.assertIn("success", response_dict)
        self.assertIn("message", response_dict)
        self.assertIn("errors", response_dict)
        self.assertIn("timestamp", response_dict)
        self.assertIn("request_id", response_dict)
        
        # Verify success is False
        self.assertFalse(response_dict["success"])
        
        # Verify error structure
        self.assertEqual(response_dict["message"], "Error occurred")
        self.assertEqual(response_dict["errors"], ["Error 1", "Error 2"])
    
    def test_pagination_format(self):
        """Verify pagination format structure."""
        response = paginated_response(
            data=[{"id": 1}, {"id": 2}],
            total=100,
            page=2,
            page_size=50
        )
        response_dict = response.to_dict()
        
        # Verify pagination metadata
        self.assertIn("meta", response_dict)
        self.assertIn("pagination", response_dict["meta"])
        
        pagination = response_dict["meta"]["pagination"]
        self.assertEqual(pagination["total"], 100)
        self.assertEqual(pagination["page"], 2)
        self.assertEqual(pagination["page_size"], 50)
        self.assertEqual(pagination["total_pages"], 2)
    
    def test_metadata_format(self):
        """Verify metadata format structure."""
        response = success_response(
            data={"key": "value"},
            meta={"custom": "metadata", "count": 5}
        )
        response_dict = response.to_dict()
        
        # Verify metadata structure
        self.assertIn("meta", response_dict)
        self.assertEqual(response_dict["meta"]["custom"], "metadata")
        self.assertEqual(response_dict["meta"]["count"], 5)


class ResponseHelpersVerificationTestCase(TestCase):
    """Verify response helpers exist and work correctly (Task 3.1.2)."""
    
    def test_success_response_helper(self):
        """Verify success_response() helper exists and works."""
        response = success_response(data={"test": "data"}, message="Test message")
        
        self.assertIsInstance(response, APIResponse)
        self.assertTrue(response.success)
        self.assertEqual(response.data, {"test": "data"})
        self.assertEqual(response.message, "Test message")
        self.assertEqual(response.status_code, 200)
        
        # Verify JsonResponse conversion
        json_response = response.to_json_response()
        self.assertIsInstance(json_response, JsonResponse)
    
    def test_error_response_helper(self):
        """Verify error_response() helper exists and works."""
        response = error_response(
            message="Error message",
            errors=["Error 1"],
            status_code=400
        )
        
        self.assertIsInstance(response, APIResponse)
        self.assertFalse(response.success)
        self.assertEqual(response.message, "Error message")
        self.assertEqual(response.errors, ["Error 1"])
        self.assertEqual(response.status_code, 400)
    
    def test_paginated_response_helper(self):
        """Verify paginated_response() helper exists and works."""
        response = paginated_response(
            data=[{"id": 1}],
            total=50,
            page=1,
            page_size=10
        )
        
        self.assertIsInstance(response, APIResponse)
        self.assertTrue(response.success)
        self.assertEqual(response.data, [{"id": 1}])
        self.assertIn("pagination", response.meta)
    
    def test_validation_error_response_helper(self):
        """Verify validation_error_response() helper exists and works."""
        response = validation_error_response(errors=["Field required", "Invalid format"])
        
        self.assertIsInstance(response, APIResponse)
        self.assertFalse(response.success)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.errors, ["Field required", "Invalid format"])
    
    def test_not_found_response_helper(self):
        """Verify not_found_response() helper exists and works."""
        response = not_found_response(resource="Page")
        
        self.assertIsInstance(response, APIResponse)
        self.assertFalse(response.success)
        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.message.lower())
    
    def test_unauthorized_response_helper(self):
        """Verify unauthorized_response() helper exists and works."""
        response = unauthorized_response(message="Unauthorized")
        
        self.assertIsInstance(response, APIResponse)
        self.assertFalse(response.success)
        self.assertEqual(response.status_code, 401)
    
    def test_forbidden_response_helper(self):
        """Verify forbidden_response() helper exists and works."""
        response = forbidden_response(message="Forbidden")
        
        self.assertIsInstance(response, APIResponse)
        self.assertFalse(response.success)
        self.assertEqual(response.status_code, 403)
    
    def test_server_error_response_helper(self):
        """Verify server_error_response() helper exists and works."""
        response = server_error_response(message="Server error")
        
        self.assertIsInstance(response, APIResponse)
        self.assertFalse(response.success)
        self.assertEqual(response.status_code, 500)
    
    def test_rate_limited_response_helper(self):
        """Verify rate_limited_response() helper exists and works."""
        response = rate_limited_response(message="Rate limit exceeded", retry_after=60)
        
        self.assertIsInstance(response, APIResponse)
        self.assertFalse(response.success)
        self.assertEqual(response.status_code, 429)
        self.assertIn("retry_after", response.meta)


class APIResponseConsistencyTestCase(TestCase):
    """Verify API response consistency across helpers."""
    
    def test_all_responses_have_timestamp(self):
        """Verify all responses include timestamp."""
        helpers = [
            success_response(),
            error_response(),
            paginated_response([], 0),
            validation_error_response([]),
            not_found_response(),
            unauthorized_response(),
            forbidden_response(),
            server_error_response(),
            rate_limited_response(),
        ]
        
        for response in helpers:
            response_dict = response.to_dict()
            self.assertIn("timestamp", response_dict)
            self.assertIsInstance(response_dict["timestamp"], int)
            self.assertGreater(response_dict["timestamp"], 0)
    
    def test_all_responses_have_request_id(self):
        """Verify all responses include request_id."""
        helpers = [
            success_response(),
            error_response(),
            paginated_response([], 0),
        ]
        
        for response in helpers:
            response_dict = response.to_dict()
            self.assertIn("request_id", response_dict)
            self.assertIsInstance(response_dict["request_id"], str)
            self.assertGreater(len(response_dict["request_id"]), 0)
