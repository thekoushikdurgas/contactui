"""
Unit tests for response_validation module.
"""

import json
import unittest
from unittest.mock import Mock
from django.http import HttpRequest, JsonResponse
from pydantic import BaseModel, Field
from apps.documentation.utils.response_validation import (
    validate_response,
    validate_response_list,
    validate_response_type,
)
from apps.documentation.utils.api_responses import success_response, error_response


# Test schemas
class TestResponseSchema(BaseModel):
    """Test schema for response validation."""
    id: int
    name: str = Field(..., min_length=1)
    status: str = "active"


class TestNestedSchema(BaseModel):
    """Test schema with nested data."""
    page: TestResponseSchema
    metadata: dict


class TestListResponseSchema(BaseModel):
    """Test schema for list items."""
    id: int
    title: str


class TestResponseValidation(unittest.TestCase):
    """Test cases for @validate_response decorator."""
    
    def test_validate_response_success(self):
        """Test that valid response passes validation."""
        @validate_response(TestResponseSchema)
        def test_api(request: HttpRequest) -> JsonResponse:
            data = {"id": 1, "name": "Test Page", "status": "active"}
            return success_response(data).to_json_response()
        
        request = Mock(spec=HttpRequest)
        response = test_api(request)
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data']['id'], 1)
    
    def test_validate_response_missing_field(self):
        """Test that response with missing required field fails validation."""
        @validate_response(TestResponseSchema, strict=False)
        def test_api(request: HttpRequest) -> JsonResponse:
            data = {"id": 1}  # Missing 'name' field
            return success_response(data).to_json_response()
        
        request = Mock(spec=HttpRequest)
        response = test_api(request)
        
        # Should return error response due to validation failure
        self.assertEqual(response.status_code, 500)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
    
    def test_validate_response_invalid_type(self):
        """Test that response with invalid type fails validation."""
        @validate_response(TestResponseSchema, strict=False)
        def test_api(request: HttpRequest) -> JsonResponse:
            data = {"id": "not an int", "name": "Test"}  # Invalid type for id
            return success_response(data).to_json_response()
        
        request = Mock(spec=HttpRequest)
        response = test_api(request)
        
        # Should return error response
        self.assertEqual(response.status_code, 500)
    
    def test_validate_response_strict_mode(self):
        """Test that strict mode raises exception."""
        @validate_response(TestResponseSchema, strict=True)
        def test_api(request: HttpRequest) -> JsonResponse:
            data = {"id": 1}  # Missing 'name' field
            return success_response(data).to_json_response()
        
        request = Mock(spec=HttpRequest)
        
        with self.assertRaises(ValueError):
            test_api(request)
    
    def test_validate_response_entire_response(self):
        """Test validating entire response structure."""
        class FullResponseSchema(BaseModel):
            success: bool
            data: dict
        
        @validate_response(FullResponseSchema, validate_data_only=False)
        def test_api(request: HttpRequest) -> JsonResponse:
            return success_response({"id": 1}).to_json_response()
        
        request = Mock(spec=HttpRequest)
        response = test_api(request)
        
        self.assertEqual(response.status_code, 200)
    
    def test_validate_response_non_json_response(self):
        """Test that non-JsonResponse is not validated."""
        @validate_response(TestResponseSchema)
        def test_api(request: HttpRequest):
            return "not a JsonResponse"
        
        request = Mock(spec=HttpRequest)
        result = test_api(request)
        
        # Should return original response without validation
        self.assertEqual(result, "not a JsonResponse")
    
    def test_validate_response_no_data_field(self):
        """Test that response without 'data' field skips validation."""
        @validate_response(TestResponseSchema, validate_data_only=True)
        def test_api(request: HttpRequest) -> JsonResponse:
            # Return response without 'data' field
            response = JsonResponse({"success": True, "message": "OK"})
            return response
        
        request = Mock(spec=HttpRequest)
        response = test_api(request)
        
        # Should return original response
        self.assertEqual(response.status_code, 200)


class TestResponseListValidation(unittest.TestCase):
    """Test cases for @validate_response_list decorator."""
    
    def test_validate_response_list_success(self):
        """Test that valid list response passes validation."""
        @validate_response_list(TestListResponseSchema)
        def test_api(request: HttpRequest) -> JsonResponse:
            data = [
                {"id": 1, "title": "Page 1"},
                {"id": 2, "title": "Page 2"}
            ]
            return success_response(data).to_json_response()
        
        request = Mock(spec=HttpRequest)
        response = test_api(request)
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertEqual(len(response_data['data']), 2)
    
    def test_validate_response_list_invalid_item(self):
        """Test that list with invalid item fails validation."""
        @validate_response_list(TestListResponseSchema, strict=False)
        def test_api(request: HttpRequest) -> JsonResponse:
            data = [
                {"id": 1, "title": "Page 1"},
                {"id": 2}  # Missing 'title' field
            ]
            return success_response(data).to_json_response()
        
        request = Mock(spec=HttpRequest)
        response = test_api(request)
        
        # Should return error response
        self.assertEqual(response.status_code, 500)
    
    def test_validate_response_list_not_a_list(self):
        """Test that non-list response fails validation."""
        @validate_response_list(TestListResponseSchema, strict=False)
        def test_api(request: HttpRequest) -> JsonResponse:
            data = {"id": 1, "title": "Not a list"}
            return success_response(data).to_json_response()
        
        request = Mock(spec=HttpRequest)
        response = test_api(request)
        
        # Should return error response
        self.assertEqual(response.status_code, 500)
    
    def test_validate_response_list_strict_mode(self):
        """Test that strict mode raises exception."""
        @validate_response_list(TestListResponseSchema, strict=True)
        def test_api(request: HttpRequest) -> JsonResponse:
            data = [{"id": 1}]  # Missing 'title' field
            return success_response(data).to_json_response()
        
        request = Mock(spec=HttpRequest)
        
        with self.assertRaises(ValueError):
            test_api(request)


class TestResponseTypeValidation(unittest.TestCase):
    """Test cases for @validate_response_type decorator."""
    
    def test_validate_response_type_dict_success(self):
        """Test that dict type validation passes."""
        @validate_response_type(dict)
        def test_api(request: HttpRequest) -> JsonResponse:
            return success_response({"id": 1}).to_json_response()
        
        request = Mock(spec=HttpRequest)
        response = test_api(request)
        
        self.assertEqual(response.status_code, 200)
    
    def test_validate_response_type_list_success(self):
        """Test that list type validation passes."""
        @validate_response_type(list)
        def test_api(request: HttpRequest) -> JsonResponse:
            return success_response([1, 2, 3]).to_json_response()
        
        request = Mock(spec=HttpRequest)
        response = test_api(request)
        
        self.assertEqual(response.status_code, 200)
    
    def test_validate_response_type_mismatch(self):
        """Test that type mismatch fails validation."""
        @validate_response_type(dict, strict=False)
        def test_api(request: HttpRequest) -> JsonResponse:
            return success_response([1, 2, 3]).to_json_response()  # List instead of dict
        
        request = Mock(spec=HttpRequest)
        response = test_api(request)
        
        # Should return error response
        self.assertEqual(response.status_code, 500)
    
    def test_validate_response_type_strict_mode(self):
        """Test that strict mode raises exception."""
        @validate_response_type(dict, strict=True)
        def test_api(request: HttpRequest) -> JsonResponse:
            return success_response([1, 2, 3]).to_json_response()
        
        request = Mock(spec=HttpRequest)
        
        with self.assertRaises(TypeError):
            test_api(request)


if __name__ == '__main__':
    unittest.main()
