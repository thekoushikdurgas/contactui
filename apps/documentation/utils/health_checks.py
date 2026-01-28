"""
Health check utilities for monitoring system components.

Provides health check functions for:
- Application health
- Database health
- Cache health
- External API health
- Storage health
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional
from django.db import connection
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


def check_database_health() -> Dict[str, Any]:
    """
    Check database connectivity and health.
    
    Returns:
        Dict with 'status', 'response_time_ms', and 'error' (if any)
    """
    start_time = time.time()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        name = settings.DATABASES.get("default", {}).get("NAME", "unknown")
        # Ensure JSON-serializable: Path (e.g. WindowsPath) is not serializable
        database_display = str(name) if isinstance(name, Path) else name
        
        return {
            "status": "healthy",
            "response_time_ms": round(response_time, 2),
            "database": database_display,
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e),
            "response_time_ms": round((time.time() - start_time) * 1000, 2),
        }


def check_cache_health() -> Dict[str, Any]:
    """
    Check cache connectivity and health.
    
    Returns:
        Dict with 'status', 'response_time_ms', and cache backend info
    """
    start_time = time.time()
    test_key = "__health_check__"
    test_value = "test"
    
    try:
        # Test cache write
        cache.set(test_key, test_value, timeout=10)
        
        # Test cache read
        retrieved = cache.get(test_key)
        
        # Clean up
        cache.delete(test_key)
        
        response_time = (time.time() - start_time) * 1000
        
        if retrieved == test_value:
            cache_backend = settings.CACHES.get("default", {}).get("BACKEND", "unknown")
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "backend": cache_backend.split(".")[-1],  # Extract backend name
                "read_write_test": "passed",
            }
        else:
            return {
                "status": "unhealthy",
                "error": "Cache read/write test failed",
                "response_time_ms": round(response_time, 2),
            }
    except Exception as e:
        logger.error(f"Cache health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e),
            "response_time_ms": round((time.time() - start_time) * 1000, 2),
        }


def check_storage_health() -> Dict[str, Any]:
    """
    Check local storage and S3 storage health.
    
    Returns:
        Dict with 'status' and storage information for both local and S3
    """
    storage_info = {
        "local": {"status": "unknown"},
        "s3": {"status": "unknown"},
    }
    
    # Check local storage
    try:
        from apps.documentation.services import get_shared_local_storage
        
        storage = get_shared_local_storage()
        
        # Try to read an index to verify storage is accessible
        try:
            pages_index = storage.get_index("pages")
            endpoints_index = storage.get_index("endpoints")
            relationships_index = storage.get_index("relationships")
            
            storage_info["local"] = {
                "status": "healthy",
                "type": "local_json",
                "indexes": {
                    "pages": pages_index.get("total", 0),
                    "endpoints": endpoints_index.get("total", 0),
                    "relationships": relationships_index.get("total", 0),
                },
            }
        except Exception as e:
            logger.warning(f"Storage index read failed: {e}")
            storage_info["local"] = {
                "status": "degraded",
                "type": "local_json",
                "error": "Index read failed",
            }
    except Exception as e:
        logger.error(f"Local storage health check failed: {e}", exc_info=True)
        storage_info["local"] = {
            "status": "unhealthy",
            "error": str(e),
        }
    
    # Check S3 storage
    try:
        from apps.core.services.s3_service import S3Service
        from django.conf import settings
        
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            s3_service = S3Service()
            # Try to list files (lightweight operation)
            start_time = time.time()
            s3_service.list_files(prefix='health_check/', max_keys=1)
            response_time = (time.time() - start_time) * 1000
            
            storage_info["s3"] = {
                "status": "healthy",
                "bucket": settings.S3_BUCKET_NAME,
                "region": settings.AWS_REGION,
                "response_time_ms": round(response_time, 2),
            }
        else:
            storage_info["s3"] = {
                "status": "not_configured",
                "message": "AWS credentials not configured",
            }
    except Exception as e:
        logger.warning(f"S3 storage health check failed: {e}")
        storage_info["s3"] = {
            "status": "unhealthy",
            "error": str(e),
        }
    
    # Determine overall storage status
    local_healthy = storage_info["local"].get("status") == "healthy"
    s3_healthy = storage_info["s3"].get("status") in ["healthy", "not_configured"]
    
    if local_healthy and s3_healthy:
        overall_status = "healthy"
    elif storage_info["local"].get("status") == "unhealthy" and storage_info["s3"].get("status") == "unhealthy":
        overall_status = "unhealthy"
    else:
        overall_status = "degraded"
    
    return {
        "status": overall_status,
        "storage": storage_info,
    }


def check_external_api_health() -> Dict[str, Any]:
    """
    Check external API health (Lambda API removed).
    
    Returns:
        Dict with 'status' indicating Lambda API is no longer used
    """
    # Lambda API removed - return not available status
    return {
        "status": "not_available",
        "message": "Lambda API has been removed - services use local/S3/GraphQL directly",
        "response_time_ms": 0,
    }


def check_application_health() -> Dict[str, Any]:
    """
    Check overall application health.
    
    Returns:
        Dict with application status and version info
    """
    try:
        from django.conf import settings
        
        return {
            "status": "healthy",
            "version": getattr(settings, "VERSION", "1.0.0"),
            "environment": getattr(settings, "ENVIRONMENT", "development"),
            "debug": getattr(settings, "DEBUG", False),
        }
    except Exception as e:
        logger.error(f"Application health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e),
        }


def check_disk_space() -> Dict[str, Any]:
    """
    Check disk space availability.
    
    Returns:
        Dict with 'status' and disk space information
    """
    try:
        import shutil
        
        total, used, free = shutil.disk_usage('/')
        free_percent = (free / total) * 100
        
        return {
            "status": "healthy" if free_percent > 10 else "warning",
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "free_percent": round(free_percent, 2),
        }
    except Exception as e:
        logger.error(f"Disk space check failed: {e}", exc_info=True)
        return {
            "status": "unknown",
            "error": str(e),
        }


def get_comprehensive_health_status() -> Dict[str, Any]:
    """
    Get comprehensive health status for all system components.
    
    Returns:
        Dict with health status for all components and overall status
    """
    health_checks = {}
    
    # Wrap each health check in try-except to prevent one failure from breaking all checks
    try:
        health_checks["application"] = check_application_health()
    except Exception as e:
        logger.error(f"Application health check failed: {e}", exc_info=True)
        health_checks["application"] = {"status": "unhealthy", "error": str(e)}
    
    try:
        health_checks["database"] = check_database_health()
    except Exception as e:
        logger.error(f"Database health check failed: {e}", exc_info=True)
        health_checks["database"] = {"status": "unhealthy", "error": str(e)}
    
    try:
        health_checks["cache"] = check_cache_health()
    except Exception as e:
        logger.error(f"Cache health check failed: {e}", exc_info=True)
        health_checks["cache"] = {"status": "unhealthy", "error": str(e)}
    
    try:
        health_checks["storage"] = check_storage_health()
    except Exception as e:
        logger.error(f"Storage health check failed: {e}", exc_info=True)
        health_checks["storage"] = {"status": "unhealthy", "error": str(e)}
    
    try:
        health_checks["disk"] = check_disk_space()
    except Exception as e:
        logger.error(f"Disk space check failed: {e}", exc_info=True)
        health_checks["disk"] = {"status": "unknown", "error": str(e)}
    
    try:
        health_checks["external_api"] = check_external_api_health()
    except Exception as e:
        logger.error(f"External API health check failed: {e}", exc_info=True)
        health_checks["external_api"] = {"status": "unhealthy", "error": str(e)}
    
    # Determine overall status
    # Critical components: application, database
    critical_components = ["application", "database"]
    critical_healthy = all(
        health_checks.get(component, {}).get("status") == "healthy"
        for component in critical_components
    )
    
    # Non-critical components can be degraded but not unhealthy
    any_critical_unhealthy = any(
        health_checks.get(component, {}).get("status") == "unhealthy"
        for component in critical_components
    )
    
    if critical_healthy and not any_critical_unhealthy:
        overall_status = "healthy"
    elif any_critical_unhealthy:
        overall_status = "unhealthy"
    else:
        overall_status = "degraded"
    
    return {
        "status": overall_status,
        "timestamp": int(time.time()),
        "components": health_checks,
    }
