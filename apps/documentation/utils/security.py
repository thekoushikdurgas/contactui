"""
Security utilities for documentation app.

Provides enhanced security measures for file operations and API access.
"""
import logging
import re
from pathlib import Path
from typing import Optional, Set
from django.core.exceptions import SuspiciousOperation
from django.http import HttpRequest

logger = logging.getLogger(__name__)

# Dangerous path patterns
DANGEROUS_PATH_PATTERNS = [
    r'\.\.',  # Directory traversal
    r'^\s*/',  # Absolute paths
    r'[\x00-\x1f\x7f-\x9f]',  # Control characters
    r'[<>:"|?*]',  # Windows forbidden characters
    r'^\.+$',  # Current/parent directory only
]

# Allowed file extensions for media files
ALLOWED_EXTENSIONS: Set[str] = {
    '.json', '.md', '.txt', '.csv', '.yaml', '.yml'
}

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


class SecurityValidator:
    """Security validation utilities."""

    @staticmethod
    def validate_path_safety(path: str) -> bool:
        """
        Validate that a path is safe from directory traversal attacks.

        Args:
            path: Path string to validate

        Returns:
            bool: True if path is safe
        """
        if not path:
            return False

        # Check for dangerous patterns
        for pattern in DANGEROUS_PATH_PATTERNS:
            if re.search(pattern, path):
                logger.warning(f"Dangerous path pattern detected: {pattern} in {path}")
                return False

        # Normalize path and check for traversal
        try:
            normalized = Path(path).resolve()
            # Additional check: ensure no .. components remain after resolution
            if '..' in str(normalized) or str(normalized).startswith('/'):
                return False
        except (ValueError, OSError):
            return False

        return True

    @staticmethod
    def validate_file_extension(filename: str) -> bool:
        """
        Validate file extension against allowed types.

        Args:
            filename: Filename to validate

        Returns:
            bool: True if extension is allowed
        """
        if not filename:
            return False

        extension = Path(filename).suffix.lower()
        return extension in ALLOWED_EXTENSIONS

    @staticmethod
    def validate_file_size(size: int) -> bool:
        """
        Validate file size against maximum allowed.

        Args:
            size: File size in bytes

        Returns:
            bool: True if size is within limits
        """
        return 0 < size <= MAX_FILE_SIZE

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent security issues.

        Args:
            filename: Original filename

        Returns:
            str: Sanitized filename
        """
        if not filename:
            return ""

        # Remove path separators and dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f\x7f-\x9f]', '', filename)

        # Limit length
        if len(sanitized) > 255:
            name, ext = Path(sanitized).stem, Path(sanitized).suffix
            sanitized = name[:255-len(ext)] + ext

        return sanitized.strip()

    @staticmethod
    def validate_request_origin(request: HttpRequest, allowed_origins: Optional[Set[str]] = None) -> bool:
        """
        Validate request origin for CSRF protection.

        Args:
            request: Django HTTP request
            allowed_origins: Set of allowed origin domains

        Returns:
            bool: True if origin is allowed
        """
        if allowed_origins is None:
            # Default allowed origins (can be configured)
            allowed_origins = {'localhost', '127.0.0.1'}

        origin = request.META.get('HTTP_ORIGIN', '')
        referer = request.META.get('HTTP_REFERER', '')

        # Extract domain from origin/referer
        def extract_domain(url: str) -> str:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                return parsed.netloc.split(':')[0]  # Remove port
            except:
                return ""

        origin_domain = extract_domain(origin)
        referer_domain = extract_domain(referer)

        return origin_domain in allowed_origins or referer_domain in allowed_origins


class AuditLogger:
    """Audit logging for security events."""

    @staticmethod
    def log_file_access(request: HttpRequest, action: str, resource: str,
                       resource_type: str = "", success: bool = True, details: str = ""):
        """
        Log file access operations.

        Args:
            request: Django HTTP request
            action: Action performed (read, write, delete, etc.)
            resource: Resource identifier
            resource_type: Type of resource
            success: Whether operation succeeded
            details: Additional details
        """
        user = getattr(request, 'user', None)
        user_id = user.id if user and user.is_authenticated else 'anonymous'
        ip = AuditLogger._get_client_ip(request)

        logger.info(
            f"AUDIT - File Access: user={user_id}, ip={ip}, action={action}, "
            f"resource={resource}, type={resource_type}, success={success}, details={details}"
        )

    @staticmethod
    def log_api_access(request: HttpRequest, endpoint: str, method: str,
                      success: bool = True, response_time: Optional[float] = None):
        """
        Log API access operations.

        Args:
            request: Django HTTP request
            endpoint: API endpoint accessed
            method: HTTP method
            success: Whether request succeeded
            response_time: Response time in milliseconds
        """
        user = getattr(request, 'user', None)
        user_id = user.id if user and user.is_authenticated else 'anonymous'
        ip = AuditLogger._get_client_ip(request)

        response_info = f", response_time={response_time}ms" if response_time else ""

        logger.info(
            f"AUDIT - API Access: user={user_id}, ip={ip}, method={method}, "
            f"endpoint={endpoint}, success={success}{response_info}"
        )

    @staticmethod
    def log_security_event(request: HttpRequest, event_type: str, details: str):
        """
        Log security-related events.

        Args:
            request: Django HTTP request
            event_type: Type of security event
            details: Event details
        """
        user = getattr(request, 'user', None)
        user_id = user.id if user and user.is_authenticated else 'anonymous'
        ip = AuditLogger._get_client_ip(request)

        logger.warning(
            f"AUDIT - Security Event: user={user_id}, ip={ip}, type={event_type}, details={details}"
        )

    @staticmethod
    def _get_client_ip(request: HttpRequest) -> str:
        """
        Get client IP address from request.

        Args:
            request: Django HTTP request

        Returns:
            str: Client IP address
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip


def require_secure_path(view_func):
    """
    Decorator to ensure path parameters are secure.

    Usage:
    @require_secure_path
    def my_view(request, file_path):
        # file_path is guaranteed to be safe
        pass
    """
    def wrapper(request, *args, **kwargs):
        # Check all string kwargs for path safety
        for key, value in kwargs.items():
            if isinstance(value, str) and not SecurityValidator.validate_path_safety(value):
                AuditLogger.log_security_event(
                    request,
                    "path_traversal_attempt",
                    f"Unsafe path detected in {key}: {value}"
                )
                raise SuspiciousOperation(f"Unsafe path detected: {value}")

        return view_func(request, *args, **kwargs)
    return wrapper