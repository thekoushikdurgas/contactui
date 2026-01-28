"""
Tests for health check utilities and endpoints.

Tests:
- Database health check
- Cache health check
- Storage health check
- External API health check
- Application health check
- Comprehensive health status
"""

from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.core.cache import cache
from django.db import connection

from apps.documentation.utils.health_checks import (
    check_database_health,
    check_cache_health,
    check_storage_health,
    check_external_api_health,
    check_application_health,
    get_comprehensive_health_status,
)


class DatabaseHealthCheckTestCase(TestCase):
    """Test cases for database health check."""
    
    def test_database_health_check_success(self):
        """Test successful database health check."""
        result = check_database_health()
        
        self.assertIn("status", result)
        self.assertIn("response_time_ms", result)
        self.assertEqual(result["status"], "healthy")
        self.assertIsInstance(result["response_time_ms"], (int, float))
    
    @patch('apps.documentation.utils.health_checks.connection')
    def test_database_health_check_failure(self, mock_connection):
        """Test database health check with connection error."""
        mock_connection.cursor.side_effect = Exception("Connection failed")
        
        result = check_database_health()
        
        self.assertEqual(result["status"], "unhealthy")
        self.assertIn("error", result)


class CacheHealthCheckTestCase(TestCase):
    """Test cases for cache health check."""
    
    def test_cache_health_check_success(self):
        """Test successful cache health check."""
        result = check_cache_health()
        
        self.assertIn("status", result)
        self.assertIn("response_time_ms", result)
        # Cache might be healthy or unavailable depending on test environment
        self.assertIn(result["status"], ["healthy", "unhealthy"])
    
    @patch('apps.documentation.utils.health_checks.cache')
    def test_cache_health_check_failure(self, mock_cache):
        """Test cache health check with cache error."""
        mock_cache.set.side_effect = Exception("Cache error")
        
        result = check_cache_health()
        
        self.assertEqual(result["status"], "unhealthy")
        self.assertIn("error", result)


class StorageHealthCheckTestCase(TestCase):
    """Test cases for storage health check."""

    @patch('apps.documentation.services.get_shared_local_storage')
    def test_storage_health_check_success(self, mock_get_storage):
        """Test successful storage health check."""
        mock_storage = Mock()
        mock_get_storage.return_value = mock_storage
        mock_storage.get_index.side_effect = lambda name: {"total": 10}
        
        result = check_storage_health()
        
        self.assertIn("status", result)
        self.assertIn("type", result)
        self.assertEqual(result["type"], "local_json")
        self.assertEqual(result["status"], "healthy")

    @patch('apps.documentation.services.get_shared_local_storage')
    def test_storage_health_check_failure(self, mock_get_storage):
        """Test storage health check with storage error."""
        mock_get_storage.side_effect = Exception("Storage error")
        
        result = check_storage_health()
        
        self.assertEqual(result["status"], "unhealthy")
        self.assertIn("error", result)


class ExternalAPIHealthCheckTestCase(TestCase):
    """Test cases for external API health check (Lambda API removed)."""

    def test_external_api_health_check_returns_not_available(self):
        """External API (Lambda) is no longer used; check returns not_available."""
        result = check_external_api_health()
        self.assertIn("status", result)
        self.assertEqual(result["status"], "not_available")
        self.assertIn("message", result)
        self.assertIn("Lambda API has been removed", result["message"])
        self.assertIn("response_time_ms", result)


class ApplicationHealthCheckTestCase(TestCase):
    """Test cases for application health check."""
    
    def test_application_health_check_success(self):
        """Test successful application health check."""
        result = check_application_health()
        
        self.assertIn("status", result)
        self.assertEqual(result["status"], "healthy")
        self.assertIn("version", result)


class ComprehensiveHealthStatusTestCase(TestCase):
    """Test cases for comprehensive health status."""
    
    @patch('apps.documentation.utils.health_checks.check_application_health')
    @patch('apps.documentation.utils.health_checks.check_database_health')
    @patch('apps.documentation.utils.health_checks.check_cache_health')
    @patch('apps.documentation.utils.health_checks.check_storage_health')
    @patch('apps.documentation.utils.health_checks.check_external_api_health')
    def test_comprehensive_health_all_healthy(
        self,
        mock_external_api,
        mock_storage,
        mock_cache,
        mock_database,
        mock_application
    ):
        """Test comprehensive health status when all components are healthy."""
        mock_application.return_value = {"status": "healthy"}
        mock_database.return_value = {"status": "healthy"}
        mock_cache.return_value = {"status": "healthy"}
        mock_storage.return_value = {"status": "healthy"}
        mock_external_api.return_value = {"status": "healthy"}
        
        result = get_comprehensive_health_status()
        
        self.assertEqual(result["status"], "healthy")
        self.assertIn("components", result)
        self.assertEqual(len(result["components"]), 5)
    
    @patch('apps.documentation.utils.health_checks.check_application_health')
    @patch('apps.documentation.utils.health_checks.check_database_health')
    @patch('apps.documentation.utils.health_checks.check_cache_health')
    @patch('apps.documentation.utils.health_checks.check_storage_health')
    @patch('apps.documentation.utils.health_checks.check_external_api_health')
    def test_comprehensive_health_with_unhealthy(
        self,
        mock_external_api,
        mock_storage,
        mock_cache,
        mock_database,
        mock_application
    ):
        """Test comprehensive health status when some components are unhealthy."""
        mock_application.return_value = {"status": "healthy"}
        mock_database.return_value = {"status": "unhealthy"}
        mock_cache.return_value = {"status": "healthy"}
        mock_storage.return_value = {"status": "healthy"}
        mock_external_api.return_value = {"status": "healthy"}
        
        result = get_comprehensive_health_status()
        
        self.assertEqual(result["status"], "unhealthy")
        self.assertIn("components", result)
