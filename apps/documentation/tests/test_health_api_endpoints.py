"""
Tests for health check API endpoints.

Tests the v1 API health endpoints:
- GET /api/v1/health/
- GET /api/v1/health/database/
- GET /api/v1/health/cache/
- GET /api/v1/health/storage/
- GET /api/v1/health/external-api/
"""

import json
from unittest.mock import patch, Mock
from django.test import TestCase, Client
from django.urls import reverse

from apps.documentation.tests.helpers import (
    BaseAPITestCase,
    assert_api_response,
)


class HealthAPITestCase(BaseAPITestCase):
    """Test cases for comprehensive health API endpoint."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.health_url = reverse('api_v1:health')
    
    @patch('apps.documentation.api.v1.health.get_comprehensive_health_status')
    def test_health_api_success(self, mock_health_check):
        """Test successful health API call."""
        mock_health_check.return_value = {
            "status": "healthy",
            "timestamp": 1234567890,
            "components": {
                "application": {"status": "healthy"},
                "database": {"status": "healthy"},
                "cache": {"status": "healthy"},
                "storage": {"status": "healthy"},
                "external_api": {"status": "healthy"},
            }
        }
        
        response = self.client.get(self.health_url)
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )
        
        data = json.loads(response.content)
        self.assertIn('data', data)
        health_data = data['data']
        self.assertIn('status', health_data)
        self.assertIn('components', health_data)


class HealthDatabaseAPITestCase(BaseAPITestCase):
    """Test cases for database health API endpoint."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.db_health_url = reverse('api_v1:health_database')
    
    @patch('apps.documentation.api.v1.health.check_database_health')
    def test_database_health_api_success(self, mock_db_check):
        """Test successful database health API call."""
        mock_db_check.return_value = {
            "status": "healthy",
            "response_time_ms": 5.2,
            "database": "test_db"
        }
        
        response = self.client.get(self.db_health_url)
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )


class HealthCacheAPITestCase(BaseAPITestCase):
    """Test cases for cache health API endpoint."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.cache_health_url = reverse('api_v1:health_cache')
    
    @patch('apps.documentation.api.v1.health.check_cache_health')
    def test_cache_health_api_success(self, mock_cache_check):
        """Test successful cache health API call."""
        mock_cache_check.return_value = {
            "status": "healthy",
            "response_time_ms": 2.1,
            "backend": "LocMemCache"
        }
        
        response = self.client.get(self.cache_health_url)
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )


class HealthStorageAPITestCase(BaseAPITestCase):
    """Test cases for storage health API endpoint."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.storage_health_url = reverse('api_v1:health_storage')
    
    @patch('apps.documentation.api.v1.health.check_storage_health')
    def test_storage_health_api_success(self, mock_storage_check):
        """Test successful storage health API call."""
        mock_storage_check.return_value = {
            "status": "healthy",
            "type": "local_json",
            "indexes": {
                "pages": 10,
                "endpoints": 5,
                "relationships": 3
            }
        }
        
        response = self.client.get(self.storage_health_url)
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )


class HealthExternalAPIAPITestCase(BaseAPITestCase):
    """Test cases for external API health endpoint."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.external_api_health_url = reverse('api_v1:health_external_api')
    
    @patch('apps.documentation.api.v1.health.check_external_api_health')
    def test_external_api_health_api_success(self, mock_api_check):
        """Test successful external API health API call."""
        mock_api_check.return_value = {
            "status": "healthy",
            "response_time_ms": 150.5,
            "api_status": "ok"
        }
        
        response = self.client.get(self.external_api_health_url)
        
        assert_api_response(
            self,
            response,
            expected_status=200,
            expected_success=True
        )
