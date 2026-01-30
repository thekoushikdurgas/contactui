"""Context-aware utilities for scripts that work in both Django and Lambda contexts."""

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, TYPE_CHECKING

# Type checking imports
if TYPE_CHECKING:
    from django.conf import settings as django_settings

# Context detection
_DJANGO_CONTEXT = None
_LAMBDA_CONTEXT = None


def _detect_context() -> tuple[bool, bool]:
    """Detect if we're running in Django or Lambda context."""
    global _DJANGO_CONTEXT, _LAMBDA_CONTEXT
    
    if _DJANGO_CONTEXT is not None:
        return _DJANGO_CONTEXT, _LAMBDA_CONTEXT
    
    # Check for Lambda context
    is_lambda = bool(os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))
    
    # Check for Django context
    is_django = False
    try:
        # Try to import Django settings
        if "DJANGO_SETTINGS_MODULE" in os.environ:
            import django
            apps_registry = getattr(django, "apps", None)
            ready = getattr(getattr(apps_registry, "apps", None), "ready", False) if apps_registry else False
            if not ready:
                django.setup()
            is_django = True
        else:
            # Try to import Django anyway (might be configured)
            try:
                from django.conf import settings
                if hasattr(settings, "BASE_DIR"):
                    is_django = True
            except (ImportError, RuntimeError):
                pass
    except (ImportError, RuntimeError):
        pass
    
    _DJANGO_CONTEXT = is_django
    _LAMBDA_CONTEXT = is_lambda
    
    return is_django, is_lambda


def is_django_context() -> bool:
    """Check if running in Django context."""
    is_django, _ = _detect_context()
    return is_django


def is_lambda_context() -> bool:
    """Check if running in Lambda context."""
    _, is_lambda = _detect_context()
    return is_lambda


def get_workspace_root() -> Path:
    """Get workspace root directory (parent of BASE_DIR or script parent)."""
    is_django, _ = _detect_context()
    
    if is_django:
        try:
            from django.conf import settings
            return Path(settings.BASE_DIR).resolve().parent
        except (ImportError, AttributeError):
            pass
    
    # Fallback: use script location
    # Scripts are in contact360/docsai/scripts/
    # Workspace root is contact360/
    script_dir = Path(__file__).resolve().parent.parent.parent
    return script_dir.parent


def get_media_root() -> Path:
    """Get media directory root. Uses Django MEDIA_ROOT if available, else workspace/media."""
    is_django, _ = _detect_context()
    
    if is_django:
        try:
            from django.conf import settings
            media = getattr(settings, "MEDIA_ROOT", None)
            if media:
                return Path(media).resolve()
            return Path(settings.BASE_DIR) / "media"
        except (ImportError, AttributeError):
            pass
    
    # Fallback: workspace/media
    workspace = get_workspace_root()
    return workspace / "docsai" / "media"


def get_pages_dir() -> Path:
    """Get pages directory."""
    return get_media_root() / "pages"


def get_endpoints_dir() -> Path:
    """Get endpoints directory."""
    return get_media_root() / "endpoints"


def get_relationships_dir() -> Path:
    """Get relationships directory. Uses 'relationship' on disk (legacy)."""
    return get_media_root() / "relationship"


def get_postman_dir() -> Path:
    """Get Postman directory."""
    return get_media_root() / "postman"


def get_logger(name: str) -> logging.Logger:
    """
    Get logger that works in both Django and Lambda contexts.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    is_django, _ = _detect_context()
    
    if is_django:
        try:
            import django
            from django.utils.log import getLogger
            return getLogger(name)
        except (ImportError, RuntimeError):
            pass
    
    # Fallback: standard Python logging
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def get_settings() -> Dict[str, Any]:
    """
    Get settings that work in both Django and Lambda contexts.
    
    Returns:
        Dictionary of settings (Django settings object or environment-based dict)
    """
    is_django, is_lambda = _detect_context()
    
    if is_django:
        try:
            from django.conf import settings as django_settings
            # Return a dict-like wrapper
            class SettingsDict:
                def __init__(self, settings_obj):
                    self._settings = settings_obj
                
                def __getattr__(self, name):
                    return getattr(self._settings, name)
                
                def get(self, name: str, default: Any = None) -> Any:
                    return getattr(self._settings, name, default)
                
                def __contains__(self, name: str) -> bool:
                    return hasattr(self._settings, name)
            
            return SettingsDict(django_settings)
        except (ImportError, RuntimeError):
            pass
    
    # Fallback: environment-based settings
    class EnvSettings:
        """Environment-based settings."""
        
        def __init__(self):
            self.S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "contact360docs")
            self.S3_DATA_PREFIX = os.getenv("S3_DATA_PREFIX", "data/")
            self.S3_DOCUMENTATION_PREFIX = os.getenv("S3_DOCUMENTATION_PREFIX", "documentation/")
            self.AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
            self.AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
            self.AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
            self.USE_LOCAL_JSON_FILES = os.getenv("USE_LOCAL_JSON_FILES", "False").lower() == "true"
            
            # Try to get BASE_DIR from script location
            try:
                script_dir = Path(__file__).resolve().parent.parent.parent
                self.BASE_DIR = str(script_dir)
            except Exception:
                self.BASE_DIR = os.getcwd()
        
        def get(self, name: str, default: Any = None) -> Any:
            return getattr(self, name, default)
        
        def __contains__(self, name: str) -> bool:
            return hasattr(self, name)
    
    return EnvSettings()


def find_docs_directory() -> Optional[Path]:
    """
    Find documentation directory in common locations.
    
    Returns:
        Path to docs directory or None if not found
    """
    workspace = get_workspace_root()
    
    # Common locations to search
    possible_paths = [
        workspace / "contact360" / "docs" / "pages",
        workspace / "frontent" / "docs" / "pages",
        workspace / "docs" / "pages",
        workspace / "docsai" / "media" / "pages",
        Path(__file__).parent.parent.parent / "media" / "pages",
    ]
    
    for path in possible_paths:
        if path.exists() and path.is_dir():
            return path
    
    return None
