"""Tests for core services."""
from django.test import TestCase
from unittest.mock import Mock, patch, MagicMock
from apps.core.services.base_service import BaseService
from apps.core.services.graphql_client import GraphQLClient


class BaseServiceTest(TestCase):
    """Test BaseService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = BaseService('TestService')
    
    def test_service_initialization(self):
        """Test service initialization."""
        self.assertEqual(self.service.name, 'TestService')
        self.assertIsNotNone(self.service.logger)
        self.assertEqual(self.service.cache_timeout, 300)
    
    def test_cache_key_generation(self):
        """Test cache key generation."""
        key = self.service._get_cache_key('test', {'param': 'value'})
        self.assertIn('TestService', key)
        self.assertIn('test', key)
    
    def test_validate_input_success(self):
        """Test input validation with valid data."""
        data = {'name': 'Test', 'email': 'test@example.com'}
        is_valid, error = self.service._validate_input(data, ['name', 'email'])
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_input_missing_field(self):
        """Test input validation with missing field."""
        data = {'name': 'Test'}
        is_valid, error = self.service._validate_input(data, ['name', 'email'])
        self.assertFalse(is_valid)
        self.assertIn('email', error.lower())


class GraphQLClientTest(TestCase):
    """Test GraphQLClient."""
    
    @patch('apps.core.services.graphql_client.httpx.Client')
    def test_execute_query_success(self, mock_client_class):
        """Test successful query execution."""
        mock_response = Mock()
        mock_response.json.return_value = {'data': {'test': 'result'}}
        mock_response.raise_for_status = Mock()
        
        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        client = GraphQLClient('http://test.com', 'test-key')
        result = client.execute_query('query { test }')
        
        self.assertEqual(result, {'test': 'result'})
        mock_client.post.assert_called_once()
    
    @patch('apps.core.services.graphql_client.httpx.Client')
    def test_execute_query_with_errors(self, mock_client_class):
        """Test query execution with GraphQL errors."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': None,
            'errors': [{'message': 'Test error'}]
        }
        mock_response.raise_for_status = Mock()  # Doesn't raise, so code continues
        
        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        client = GraphQLClient('http://test.com', 'test-key')
        client.client = mock_client  # Set the mocked client
        
        # Import GraphQLError from the correct location (graphql_client module)
        from apps.core.services.graphql_client import GraphQLError
        # The code should check for errors in result and raise GraphQLError
        with self.assertRaises(GraphQLError):
            client.execute_query('query { test }', use_cache=False)
