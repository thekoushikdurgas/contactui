"""
Test helpers and utilities for documentation app tests.

Provides:
- Test helpers (create_test_user, authenticate_client, etc.)
- Assertion utilities
- Request helpers
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional
from django.test import Client, TestCase
from django.contrib.auth import get_user_model
from django.http import JsonResponse

User = get_user_model()


# ============================================================================
# Test Helpers
# ============================================================================

def create_test_user(
    username: str = "testuser",
    email: Optional[str] = None,
    password: str = "testpass123",
    is_staff: bool = False,
    is_superuser: bool = False,
    **kwargs
) -> User:
    """
    Create a test user.
    
    Args:
        username: Username for the user
        email: Email address (defaults to username@test.com)
        password: Password for the user
        is_staff: Whether user is staff
        is_superuser: Whether user is superuser
        **kwargs: Additional user fields
    
    Returns:
        Created User instance
    """
    email = email or f"{username}@test.com"
    return User.objects.create_user(
        username=username,
        email=email,
        password=password,
        is_staff=is_staff,
        is_superuser=is_superuser,
        **kwargs
    )


def authenticate_client(client: Client, user: Optional[User] = None) -> User:
    """
    Authenticate a test client with a user.
    
    Args:
        client: Django test client
        user: User to authenticate (creates one if not provided)
    
    Returns:
        Authenticated User instance
    """
    if user is None:
        user = create_test_user()
    client.force_login(user)
    return user


def make_request(
    client: Client,
    method: str,
    path: str,
    data: Optional[Dict[str, Any]] = None,
    content_type: str = "application/json",
    **kwargs
) -> Any:
    """
    Make a test request.
    
    Args:
        client: Django test client
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        path: Request path
        data: Request data (will be JSON-encoded if content_type is application/json)
        content_type: Content type header
        **kwargs: Additional arguments to pass to client method
    
    Returns:
        Response object
    """
    method = method.upper()
    
    if data and content_type == "application/json":
        data = json.dumps(data)
        kwargs.setdefault("content_type", content_type)
    
    if method == "GET":
        return client.get(path, data=data, **kwargs)
    elif method == "POST":
        return client.post(path, data=data, **kwargs)
    elif method == "PUT":
        return client.put(path, data=data, **kwargs)
    elif method == "PATCH":
        return client.patch(path, data=data, **kwargs)
    elif method == "DELETE":
        return client.delete(path, data=data, **kwargs)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")


# ============================================================================
# Assertion Utilities
# ============================================================================

def assert_api_response(
    test_case: TestCase,
    response: Any,
    expected_status: int = 200,
    expected_success: Optional[bool] = None,
    expected_data_keys: Optional[list] = None,
    expected_message: Optional[str] = None,
):
    """
    Assert that an API response matches expected format.
    
    Args:
        test_case: TestCase instance
        response: Response object
        expected_status: Expected HTTP status code
        expected_success: Expected success field value (None to skip check)
        expected_data_keys: Expected keys in data field (None to skip check)
        expected_message: Expected message field value (None to skip check)
    """
    test_case.assertEqual(response.status_code, expected_status)
    
    if hasattr(response, "json"):
        data = response.json()
    else:
        data = json.loads(response.content)
    
    if expected_success is not None:
        test_case.assertEqual(data.get("success"), expected_success)
    
    if expected_data_keys:
        test_case.assertIn("data", data)
        for key in expected_data_keys:
            test_case.assertIn(key, data["data"])
    
    if expected_message:
        test_case.assertEqual(data.get("message"), expected_message)


def assert_paginated_response(
    test_case: TestCase,
    response: Any,
    expected_count: Optional[int] = None,
    min_count: Optional[int] = None,
    expected_keys: Optional[list] = None,
):
    """
    Assert that a paginated API response matches expected format.
    
    Args:
        test_case: TestCase instance
        response: Response object
        expected_count: Expected total count (None to skip check)
        min_count: Minimum expected count (None to skip check)
        expected_keys: Expected keys in each item (None to skip check)
    """
    assert_api_response(test_case, response, expected_status=200, expected_success=True)
    
    if hasattr(response, "json"):
        data = response.json()
    else:
        data = json.loads(response.content)
    
    test_case.assertIn("data", data)
    test_case.assertIn("items", data["data"])
    test_case.assertIn("total", data["data"])
    test_case.assertIn("page", data["data"])
    test_case.assertIn("page_size", data["data"])
    
    items = data["data"]["items"]
    
    if expected_count is not None:
        test_case.assertEqual(len(items), expected_count)
        test_case.assertEqual(data["data"]["total"], expected_count)
    
    if min_count is not None:
        test_case.assertGreaterEqual(len(items), min_count)
    
    if expected_keys and items:
        for key in expected_keys:
            test_case.assertIn(key, items[0])


def assert_error_response(
    test_case: TestCase,
    response: Any,
    expected_status: int,
    expected_message: Optional[str] = None,
    expected_error_type: Optional[str] = None,
):
    """
    Assert that an error API response matches expected format.
    
    Args:
        test_case: TestCase instance
        response: Response object
        expected_status: Expected HTTP status code
        expected_message: Expected error message (None to skip check)
        expected_error_type: Expected error type (None to skip check)
    """
    test_case.assertEqual(response.status_code, expected_status)
    
    if hasattr(response, "json"):
        data = response.json()
    else:
        data = json.loads(response.content)
    
    test_case.assertEqual(data.get("success"), False)
    test_case.assertIn("message", data)
    
    if expected_message:
        test_case.assertEqual(data.get("message"), expected_message)
    
    if expected_error_type:
        test_case.assertIn("errors", data)
        # Check if error type is in errors array or message
        errors = data.get("errors", [])
        if isinstance(errors, list):
            error_str = " ".join(str(e) for e in errors)
        else:
            error_str = str(errors)
        test_case.assertIn(expected_error_type.lower(), error_str.lower())


def assert_validation_error(
    test_case: TestCase,
    response: Any,
    expected_fields: Optional[list] = None,
):
    """
    Assert that a validation error response matches expected format.
    
    Args:
        test_case: TestCase instance
        response: Response object
        expected_fields: Expected fields with validation errors (None to skip check)
    """
    assert_error_response(test_case, response, expected_status=400)
    
    if hasattr(response, "json"):
        data = response.json()
    else:
        data = json.loads(response.content)
    
    test_case.assertIn("errors", data)
    
    if expected_fields:
        errors = data.get("errors", [])
        error_str = " ".join(str(e) for e in errors) if isinstance(errors, list) else str(errors)
        for field in expected_fields:
            test_case.assertIn(field.lower(), error_str.lower())


def assert_not_found_response(
    test_case: TestCase,
    response: Any,
    resource_name: Optional[str] = None,
):
    """
    Assert that a not found error response matches expected format.
    
    Args:
        test_case: TestCase instance
        response: Response object
        resource_name: Expected resource name in error message (None to skip check)
    """
    assert_error_response(test_case, response, expected_status=404)
    
    if resource_name:
        if hasattr(response, "json"):
            data = response.json()
        else:
            data = json.loads(response.content)
        
        message = data.get("message", "").lower()
        test_case.assertIn(resource_name.lower(), message)


# ============================================================================
# Base Test Classes
# ============================================================================

class BaseAPITestCase(TestCase):
    """Base test case for API tests."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = create_test_user()
        authenticate_client(self.client, self.user)
    
    def tearDown(self):
        """Clean up after tests."""
        User.objects.all().delete()


class BaseServiceTestCase(TestCase):
    """Base test case for service layer tests."""
    
    def setUp(self):
        """Set up test fixtures."""
        pass
    
    def tearDown(self):
        """Clean up after tests."""
        pass
