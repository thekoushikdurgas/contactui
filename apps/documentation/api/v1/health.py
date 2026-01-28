"""Health and service info API v1 views."""

from __future__ import annotations

from typing import Any

from django.views.decorators.http import require_http_methods
from django.http import HttpRequest, JsonResponse

from .base import api_response
from apps.documentation.utils.health_checks import (
    check_application_health,
    check_database_health,
    check_cache_health,
    check_storage_health,
    check_external_api_health,
    get_comprehensive_health_status,
)


@require_http_methods(["GET"])
def health(request: HttpRequest) -> JsonResponse:
    """
    GET /api/v1/health/
    
    Get comprehensive service health status including:
    - Application health
    - Database health
    - Cache health
    - Storage health
    - External API health
    """
    try:
        health_status = get_comprehensive_health_status()
        return JsonResponse({
            'success': True,
            'data': health_status
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def health_database(request: HttpRequest) -> JsonResponse:
    """
    GET /api/v1/health/database/
    
    Get database health status.
    """
    try:
        db_health = check_database_health()
        return JsonResponse({
            'success': True,
            'data': db_health
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def health_cache(request: HttpRequest) -> JsonResponse:
    """
    GET /api/v1/health/cache/
    
    Get cache health status.
    """
    try:
        cache_health = check_cache_health()
        return JsonResponse({
            'success': True,
            'data': cache_health
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def health_storage(request: HttpRequest) -> JsonResponse:
    """
    GET /api/v1/health/storage/
    
    Get storage health status.
    """
    try:
        storage_health = check_storage_health()
        return JsonResponse({
            'success': True,
            'data': storage_health
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def service_info(request: HttpRequest) -> JsonResponse:
    """
    GET /api/v1/
    
    Get service information.
    """
    return JsonResponse({
        'success': True,
        'data': {
            'service': 'Documentation API Service',
            'version': '1.0.0',
            'status': 'running'
        }
    })
