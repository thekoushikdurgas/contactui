"""
Unit tests for core APIClient (apps.core.services.api_client).

Tests cover:
- HTTP request methods (GET, POST, PUT, PATCH, DELETE)
- Retry logic with different strategies
- Request validation
- Error handling
- Metrics tracking
- Context manager support
"""

from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
import httpx
import time

from apps.core.services.api_client import APIClient, RetryStrategy
from apps.core.exceptions import LambdaAPIError


class APIClientTestCase(TestCase):
    """Test cases for core APIClient class."""

    def setUp(self):
        """Set up test fixtures."""
        self.base_url = "https://api.example.com"
        self.api_key = "test-api-key"
        self.client = APIClient(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=30,
            max_retries=3,
            retry_delay=1.0
        )

    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self.client, 'close'):
            self.client.close()

    def test_init(self):
        """Test client initialization."""
        self.assertEqual(self.client.base_url, self.base_url)
        self.assertEqual(self.client.api_key, self.api_key)
        self.assertEqual(self.client.timeout, 30)
        self.assertEqual(self.client.max_retries, 3)
        self.assertEqual(self.client.retry_delay, 1.0)
        self.assertIsNotNone(self.client.client)

    def test_init_strips_trailing_slash(self):
        """Test that base_url trailing slash is stripped."""
        client = APIClient(base_url="https://api.example.com/")
        self.assertEqual(client.base_url, "https://api.example.com")

    def test_validate_endpoint_adds_slash(self):
        """Test endpoint validation adds leading slash."""
        endpoint = self.client._validate_endpoint("test")
        self.assertTrue(endpoint.startswith("/"))
        self.assertEqual(endpoint, "/test")

    def test_validate_endpoint_prevents_path_traversal(self):
        """Test endpoint validation prevents path traversal."""
        with self.assertRaises(ValueError):
            self.client._validate_endpoint("../etc/passwd")
        with self.assertRaises(ValueError):
            self.client._validate_endpoint("//test")

    def test_validate_endpoint_empty_raises(self):
        """Test empty endpoint raises ValueError."""
        with self.assertRaises(ValueError):
            self.client._validate_endpoint("")

    def test_validate_request_data_post_requires_dict(self):
        """Test POST request requires dict data."""
        with self.assertRaises(ValueError):
            self.client._validate_request_data("not a dict", "POST")

    def test_validate_request_data_get_allows_none(self):
        """Test GET request allows None data."""
        result = self.client._validate_request_data(None, "GET")
        self.assertIsNone(result)

    def test_get_headers_includes_api_key(self):
        """Test headers include API key."""
        headers = self.client._get_headers()
        self.assertIn("X-API-Key", headers)
        self.assertEqual(headers["X-API-Key"], self.api_key)

    def test_get_headers_additional_headers(self):
        """Test additional headers are merged."""
        headers = self.client._get_headers({"Custom-Header": "value"})
        self.assertEqual(headers["Custom-Header"], "value")
        self.assertIn("X-API-Key", headers)

    def test_calculate_backoff_exponential(self):
        """Test exponential backoff calculation."""
        self.client.retry_strategy = RetryStrategy.EXPONENTIAL
        self.client.retry_delay = 1.0
        self.assertEqual(self.client._calculate_backoff(0), 1.0)
        self.assertEqual(self.client._calculate_backoff(1), 2.0)
        self.assertEqual(self.client._calculate_backoff(2), 4.0)

    def test_calculate_backoff_linear(self):
        """Test linear backoff calculation."""
        self.client.retry_strategy = RetryStrategy.LINEAR
        self.client.retry_delay = 1.0
        self.assertEqual(self.client._calculate_backoff(0), 1.0)
        self.assertEqual(self.client._calculate_backoff(1), 2.0)
        self.assertEqual(self.client._calculate_backoff(2), 3.0)

    def test_calculate_backoff_fixed(self):
        """Test fixed backoff calculation."""
        self.client.retry_strategy = RetryStrategy.FIXED
        self.client.retry_delay = 1.0
        self.assertEqual(self.client._calculate_backoff(0), 1.0)
        self.assertEqual(self.client._calculate_backoff(1), 1.0)
        self.assertEqual(self.client._calculate_backoff(2), 1.0)

    @patch.object(APIClient, '_retry_request')
    def test_get_request(self, mock_retry):
        """Test GET request."""
        mock_retry.return_value = {"data": "test"}
        result = self.client.get("/test", params={"key": "value"})
        self.assertEqual(result, {"data": "test"})
        mock_retry.assert_called_once_with("get", "/test", params={"key": "value"})

    @patch.object(APIClient, '_retry_request')
    def test_post_request(self, mock_retry):
        """Test POST request."""
        mock_retry.return_value = {"id": "123"}
        result = self.client.post("/test", json_data={"name": "test"})
        self.assertEqual(result, {"id": "123"})
        mock_retry.assert_called_once()

    @patch.object(APIClient, '_retry_request')
    def test_put_request(self, mock_retry):
        """Test PUT request."""
        mock_retry.return_value = {"updated": True}
        result = self.client.put("/test/123", json_data={"name": "updated"})
        self.assertEqual(result, {"updated": True})

    @patch.object(APIClient, '_retry_request')
    def test_patch_request(self, mock_retry):
        """Test PATCH request."""
        mock_retry.return_value = {"patched": True}
        result = self.client.patch("/test/123", json_data={"field": "value"})
        self.assertEqual(result, {"patched": True})

    @patch.object(APIClient, '_retry_request')
    def test_delete_request_success(self, mock_retry):
        """Test DELETE request success."""
        mock_retry.return_value = {}
        result = self.client.delete("/test/123")
        self.assertTrue(result)

    @patch.object(APIClient, '_retry_request')
    def test_delete_request_failure(self, mock_retry):
        """Test DELETE request failure."""
        mock_retry.side_effect = LambdaAPIError("Delete failed", endpoint="/test/123")
        result = self.client.delete("/test/123")
        self.assertFalse(result)

    def test_retry_request_success_first_attempt(self):
        """Test retry request succeeds on first attempt."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_response.content = b'{"data": "test"}'
        mock_response.raise_for_status = Mock()

        self.client.client = Mock()
        self.client.client.get.return_value = mock_response

        result = self.client._retry_request("get", "/test")
        self.assertEqual(result, {"data": "test"})
        self.assertEqual(self.client.client.get.call_count, 1)

    def test_retry_request_retries_on_500(self):
        """Test retry request retries on 500 error."""
        mock_response_500 = Mock()
        mock_response_500.status_code = 500
        mock_response_500.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error",
            request=Mock(),
            response=mock_response_500
        )

        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"data": "success"}
        mock_response_200.content = b'{"data": "success"}'
        mock_response_200.raise_for_status = Mock()

        self.client.client = Mock()
        self.client.client.get.side_effect = [mock_response_500, mock_response_200]

        with patch('time.sleep'):  # Skip actual sleep
            result = self.client._retry_request("get", "/test")
            self.assertEqual(result, {"data": "success"})
            self.assertEqual(self.client.client.get.call_count, 2)

    def test_retry_request_no_retry_on_400(self):
        """Test retry request doesn't retry on 400 error."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad Request",
            request=Mock(),
            response=mock_response
        )

        self.client.client = Mock()
        self.client.client.get.return_value = mock_response

        with self.assertRaises(LambdaAPIError):
            self.client._retry_request("get", "/test")
        self.assertEqual(self.client.client.get.call_count, 1)

    def test_retry_request_retries_on_429(self):
        """Test retry request retries on 429 (rate limit)."""
        mock_response_429 = Mock()
        mock_response_429.status_code = 429
        mock_response_429.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Rate Limited",
            request=Mock(),
            response=mock_response_429
        )

        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"data": "ok"}
        mock_response_200.content = b'{"data": "ok"}'
        mock_response_200.raise_for_status = Mock()

        self.client.client = Mock()
        self.client.client.get.side_effect = [mock_response_429, mock_response_200]

        with patch('time.sleep'):
            result = self.client._retry_request("get", "/test")
            self.assertEqual(result, {"data": "ok"})
            self.assertEqual(self.client.client.get.call_count, 2)

    def test_retry_request_retries_on_request_error(self):
        """Test retry request retries on RequestError."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "ok"}
        mock_response.content = b'{"data": "ok"}'
        mock_response.raise_for_status = Mock()

        self.client.client = Mock()
        self.client.client.get.side_effect = [
            httpx.RequestError("Connection error", request=Mock()),
            mock_response
        ]

        with patch('time.sleep'):
            result = self.client._retry_request("get", "/test")
            self.assertEqual(result, {"data": "ok"})
            self.assertEqual(self.client.client.get.call_count, 2)

    def test_get_metrics(self):
        """Test metrics tracking."""
        self.client.request_count = 10
        self.client.error_count = 2
        self.client.retry_count = 3
        self.client.total_response_time = 5.0

        metrics = self.client.get_metrics()
        self.assertEqual(metrics["request_count"], 10)
        self.assertEqual(metrics["error_count"], 2)
        self.assertEqual(metrics["retry_count"], 3)
        self.assertEqual(metrics["success_rate"], 80.0)
        self.assertIn("average_response_time_ms", metrics)

    def test_context_manager(self):
        """Test context manager support."""
        with APIClient(base_url=self.base_url) as client:
            self.assertIsNotNone(client)
        # Client should be closed after context exit
        # (actual close behavior depends on httpx.Client implementation)

    def test_close(self):
        """Test client close method."""
        mock_client = Mock()
        self.client.client = mock_client
        self.client.close()
        mock_client.close.assert_called_once()
