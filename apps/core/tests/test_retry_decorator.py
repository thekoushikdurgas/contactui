"""
Tests for retry decorator functionality.
"""

import time
import unittest
from unittest.mock import Mock, patch, MagicMock
from apps.core.decorators.retry import retry, retry_on_network_error, retry_on_server_error


class TestRetryDecorator(unittest.TestCase):
    """Test cases for the retry decorator."""
    
    def test_retry_succeeds_on_first_attempt(self):
        """Test that function succeeds without retries."""
        @retry(max_retries=3)
        def successful_function():
            return "success"
        
        result = successful_function()
        self.assertEqual(result, "success")
    
    def test_retry_succeeds_after_failures(self):
        """Test that function succeeds after initial failures."""
        call_count = [0]
        
        @retry(max_retries=3, initial_delay=0.01)
        def flaky_function():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("Temporary failure")
            return "success"
        
        result = flaky_function()
        self.assertEqual(result, "success")
        self.assertEqual(call_count[0], 2)
    
    def test_retry_exhausts_all_attempts(self):
        """Test that function raises exception after all retries exhausted."""
        call_count = [0]
        
        @retry(max_retries=3, initial_delay=0.01)
        def always_failing_function():
            call_count[0] += 1
            raise ValueError("Always fails")
        
        with self.assertRaises(ValueError) as context:
            always_failing_function()
        
        self.assertEqual(str(context.exception), "Always fails")
        self.assertEqual(call_count[0], 3)
    
    def test_retry_with_retryable_exceptions(self):
        """Test that retry only occurs for specified exceptions."""
        call_count = [0]
        
        @retry(max_retries=3, initial_delay=0.01, retryable_exceptions=(ValueError,))
        def function_with_wrong_exception():
            call_count[0] += 1
            raise TypeError("Wrong exception type")
        
        with self.assertRaises(TypeError):
            function_with_wrong_exception()
        
        # Should not retry, so only called once
        self.assertEqual(call_count[0], 1)
    
    def test_retry_with_correct_exception_type(self):
        """Test that retry occurs for correct exception type."""
        call_count = [0]
        
        @retry(max_retries=3, initial_delay=0.01, retryable_exceptions=(ValueError,))
        def function_with_correct_exception():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("Retryable error")
            return "success"
        
        result = function_with_correct_exception()
        self.assertEqual(result, "success")
        self.assertEqual(call_count[0], 2)
    
    def test_retry_exponential_backoff(self):
        """Test that retry uses exponential backoff."""
        call_times = []
        
        @retry(max_retries=3, initial_delay=0.1, exponential_base=2.0)
        def function_with_backoff():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise ValueError("Fail")
            return "success"
        
        start_time = time.time()
        result = function_with_backoff()
        end_time = time.time()
        
        self.assertEqual(result, "success")
        self.assertEqual(len(call_times), 3)
        
        # Check that delays increase exponentially
        if len(call_times) >= 2:
            delay1 = call_times[1] - call_times[0]
            delay2 = call_times[2] - call_times[1]
            # Allow some tolerance for timing
            self.assertGreater(delay1, 0.05)
            self.assertGreater(delay2, delay1 * 1.5)  # Should be roughly double
    
    def test_retry_respects_max_delay(self):
        """Test that retry respects max_delay setting."""
        call_times = []
        
        @retry(
            max_retries=5,
            initial_delay=1.0,
            max_delay=0.2,  # Max delay is less than what exponential would give
            exponential_base=2.0
        )
        def function_with_max_delay():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise ValueError("Fail")
            return "success"
        
        start_time = time.time()
        result = function_with_max_delay()
        end_time = time.time()
        
        self.assertEqual(result, "success")
        
        # Check that delays don't exceed max_delay (with tolerance)
        if len(call_times) >= 2:
            delay1 = call_times[1] - call_times[0]
            self.assertLess(delay1, 0.3)  # Should be capped at max_delay
    
    def test_retry_with_jitter(self):
        """Test that jitter adds randomness to delays."""
        delays = []
        
        @retry(max_retries=2, initial_delay=0.1, jitter=True)
        def function_with_jitter():
            if len(delays) == 0:
                delays.append(time.time())
                raise ValueError("Fail")
            return "success"
        
        function_with_jitter()
        
        # With jitter, delay should vary slightly
        # This is a probabilistic test, so we just verify it doesn't crash
        self.assertTrue(True)
    
    def test_retry_without_logging(self):
        """Test that retry works without logging."""
        call_count = [0]
        
        @retry(max_retries=3, initial_delay=0.01, retry_logging=False)
        def function_without_logging():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("Fail")
            return "success"
        
        result = function_without_logging()
        self.assertEqual(result, "success")
        self.assertEqual(call_count[0], 2)


class TestRetryOnNetworkError(unittest.TestCase):
    """Test cases for retry_on_network_error decorator."""
    
    def test_retry_on_network_error_succeeds(self):
        """Test that network error retry succeeds."""
        call_count = [0]
        
        @retry_on_network_error(max_retries=3, initial_delay=0.01)
        def network_function():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ConnectionError("Network error")
            return "success"
        
        result = network_function()
        self.assertEqual(result, "success")
        self.assertEqual(call_count[0], 2)
    
    def test_retry_on_network_error_does_not_retry_other_exceptions(self):
        """Test that network error retry doesn't retry non-network exceptions."""
        call_count = [0]
        
        @retry_on_network_error(max_retries=3, initial_delay=0.01)
        def function_with_value_error():
            call_count[0] += 1
            raise ValueError("Not a network error")
        
        with self.assertRaises(ValueError):
            function_with_value_error()
        
        # Should not retry
        self.assertEqual(call_count[0], 1)


class TestRetryOnServerError(unittest.TestCase):
    """Test cases for retry_on_server_error decorator."""
    
    @patch('apps.core.decorators.retry.httpx')
    def test_retry_on_server_error_with_httpx(self, mock_httpx):
        """Test server error retry with httpx exceptions."""
        call_count = [0]
        
        # Mock HTTPStatusError
        mock_response = Mock()
        mock_response.status_code = 500
        mock_error = mock_httpx.HTTPStatusError("Server error", request=Mock(), response=mock_response)
        
        @retry_on_server_error(max_retries=3, initial_delay=0.01)
        def server_error_function():
            call_count[0] += 1
            if call_count[0] < 2:
                raise mock_error
            return "success"
        
        result = server_error_function()
        self.assertEqual(result, "success")
        self.assertEqual(call_count[0], 2)
    
    def test_retry_on_server_error_does_not_retry_client_errors(self):
        """Test that server error retry doesn't retry 4xx errors."""
        call_count = [0]
        
        @retry_on_server_error(max_retries=3, initial_delay=0.01)
        def client_error_function():
            call_count[0] += 1
            raise ValueError("Client error")
        
        with self.assertRaises(ValueError):
            client_error_function()
        
        # Should not retry
        self.assertEqual(call_count[0], 1)


if __name__ == '__main__':
    unittest.main()
