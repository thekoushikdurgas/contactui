"""
API Versioning utilities for managing API versions.
"""

import logging
from typing import Optional, Dict, Any, Callable
from django.http import JsonResponse, HttpRequest
from django.urls import path, include
from functools import wraps

logger = logging.getLogger(__name__)


class APIVersion:
    """
    Represents an API version with its configuration.
    """
    
    def __init__(
        self,
        version: str,
        is_default: bool = False,
        is_deprecated: bool = False,
        deprecation_date: Optional[str] = None,
        sunset_date: Optional[str] = None
    ):
        """
        Initialize API version.
        
        Args:
            version: Version string (e.g., 'v1', 'v2')
            is_default: Whether this is the default version
            is_deprecated: Whether this version is deprecated
            deprecation_date: Date when version was deprecated (ISO format)
            sunset_date: Date when version will be removed (ISO format)
        """
        self.version = version
        self.is_default = is_default
        self.is_deprecated = is_deprecated
        self.deprecation_date = deprecation_date
        self.sunset_date = sunset_date
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert version to dictionary."""
        return {
            'version': self.version,
            'is_default': self.is_default,
            'is_deprecated': self.is_deprecated,
            'deprecation_date': self.deprecation_date,
            'sunset_date': self.sunset_date
        }


class APIVersionManager:
    """
    Manager for API versions.
    """
    
    def __init__(self):
        """Initialize version manager."""
        self.versions: Dict[str, APIVersion] = {}
        self.default_version: Optional[str] = None
    
    def register_version(
        self,
        version: str,
        is_default: bool = False,
        is_deprecated: bool = False,
        deprecation_date: Optional[str] = None,
        sunset_date: Optional[str] = None
    ) -> None:
        """
        Register an API version.
        
        Args:
            version: Version string
            is_default: Whether this is the default version
            is_deprecated: Whether this version is deprecated
            deprecation_date: Date when version was deprecated
            sunset_date: Date when version will be removed
        """
        api_version = APIVersion(
            version=version,
            is_default=is_default,
            is_deprecated=is_deprecated,
            deprecation_date=deprecation_date,
            sunset_date=sunset_date
        )
        
        self.versions[version] = api_version
        
        if is_default:
            self.default_version = version
    
    def get_version(self, version: str) -> Optional[APIVersion]:
        """Get version by string."""
        return self.versions.get(version)
    
    def get_default_version(self) -> Optional[APIVersion]:
        """Get default version."""
        if self.default_version:
            return self.versions.get(self.default_version)
        return None
    
    def list_versions(self) -> Dict[str, Dict[str, Any]]:
        """List all registered versions."""
        return {
            version: api_version.to_dict()
            for version, api_version in self.versions.items()
        }


# Global version manager instance
version_manager = APIVersionManager()

# Register default versions
version_manager.register_version('v1', is_default=True)
version_manager.register_version('v2', is_default=False)


def get_api_version(request: HttpRequest) -> Optional[str]:
    """
    Extract API version from request.
    
    Checks:
    1. URL path (e.g., /api/v1/...)
    2. Accept header (e.g., application/vnd.api+json;version=v1)
    3. Query parameter (e.g., ?version=v1)
    
    Args:
        request: Django request object
        
    Returns:
        Version string or None
    """
    # Check URL path
    path_parts = request.path.split('/')
    for i, part in enumerate(path_parts):
        if part.startswith('v') and part[1:].isdigit():
            return part
    
    # Check Accept header
    accept_header = request.META.get('HTTP_ACCEPT', '')
    if 'version=' in accept_header:
        try:
            version_part = accept_header.split('version=')[1].split(';')[0].strip()
            if version_part.startswith('v'):
                return version_part
        except (IndexError, AttributeError):
            pass
    
    # Check query parameter
    version_param = request.GET.get('version')
    if version_param:
        return version_param
    
    return None


def require_api_version(
    min_version: Optional[str] = None,
    max_version: Optional[str] = None
):
    """
    Decorator to require specific API version.
    
    Args:
        min_version: Minimum required version
        max_version: Maximum allowed version
        
    Usage:
        @require_api_version(min_version='v1', max_version='v2')
        def my_api_view(request):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            version = get_api_version(request)
            
            if not version:
                # Use default version
                default = version_manager.get_default_version()
                if default:
                    version = default.version
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'API version not specified'
                    }, status=400)
            
            api_version = version_manager.get_version(version)
            
            if not api_version:
                return JsonResponse({
                    'success': False,
                    'error': f'Invalid API version: {version}'
                }, status=400)
            
            # Check if deprecated
            if api_version.is_deprecated:
                logger.warning(f"Deprecated API version used: {version}")
                # Add deprecation warning header
                response = func(request, *args, **kwargs)
                if isinstance(response, JsonResponse):
                    response['X-API-Deprecated'] = 'true'
                    if api_version.sunset_date:
                        response['X-API-Sunset'] = api_version.sunset_date
                return response
            
            # Check version constraints
            if min_version or max_version:
                version_num = int(version[1:]) if version[1:].isdigit() else 0
                
                if min_version:
                    min_num = int(min_version[1:]) if min_version[1:].isdigit() else 0
                    if version_num < min_num:
                        return JsonResponse({
                            'success': False,
                            'error': f'API version {version} is too old. Minimum: {min_version}'
                        }, status=400)
                
                if max_version:
                    max_num = int(max_version[1:]) if max_version[1:].isdigit() else 0
                    if version_num > max_num:
                        return JsonResponse({
                            'success': False,
                            'error': f'API version {version} is too new. Maximum: {max_version}'
                        }, status=400)
            
            return func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def api_version_info(request: HttpRequest) -> JsonResponse:
    """
    API endpoint to get version information.
    
    Returns:
        JsonResponse with version information
    """
    versions = version_manager.list_versions()
    default = version_manager.get_default_version()
    
    return JsonResponse({
        'success': True,
        'versions': versions,
        'default_version': default.version if default else None,
        'current_version': get_api_version(request)
    })
