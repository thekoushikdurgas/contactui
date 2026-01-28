"""
Standardized API Response Utilities

Provides consistent response formatting across all API endpoints.
"""
import logging
from typing import Any, Dict, Optional
from django.http import JsonResponse

logger = logging.getLogger(__name__)


class APIResponse:
    """
    Standardized API response format.

    Format:
    {
        "success": bool,
        "data": Any,           # Response payload
        "message": str,        # Human-readable message
        "errors": List[str],   # Error details (when success=False)
        "meta": Dict,          # Metadata (pagination, etc.)
        "timestamp": int,      # Response timestamp
        "request_id": str      # Request identifier for debugging
    }
    """

    def __init__(self, success: bool = True, data: Any = None, message: str = "",
                 errors: Optional[list] = None, meta: Optional[Dict] = None,
                 status_code: int = 200):
        self.success = success
        self.data = data
        self.message = message
        self.errors = errors or []
        self.meta = meta or {}
        self.status_code = status_code
        self.timestamp = self._get_timestamp()
        self.request_id = self._generate_request_id()

    def _get_timestamp(self) -> int:
        """Get current timestamp in milliseconds."""
        import time
        return int(time.time() * 1000)

    def _generate_request_id(self) -> str:
        """Generate unique request identifier."""
        import uuid
        return str(uuid.uuid4())[:8]

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        response = {
            "success": self.success,
            "timestamp": self.timestamp,
            "request_id": self.request_id
        }

        if self.data is not None:
            response["data"] = self.data

        if self.message:
            response["message"] = self.message

        if self.errors:
            response["errors"] = self.errors

        if self.meta:
            response["meta"] = self.meta

        return response

    def to_json_response(self) -> JsonResponse:
        """Convert to Django JsonResponse."""
        return JsonResponse(
            self.to_dict(),
            status=self.status_code,
            safe=False
        )


# Convenience functions
def success_response(data: Any = None, message: str = "", meta: Optional[Dict] = None) -> APIResponse:
    """Create successful response."""
    return APIResponse(success=True, data=data, message=message, meta=meta)


def error_response(message: str = "An error occurred", errors: Optional[list] = None,
                  status_code: int = 400) -> APIResponse:
    """Create error response."""
    return APIResponse(success=False, message=message, errors=errors, status_code=status_code)


def paginated_response(data: Any, total: int, page: int = 1, page_size: int = 50,
                      message: str = "") -> APIResponse:
    """Create paginated response."""
    meta = {
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    }
    return APIResponse(success=True, data=data, message=message, meta=meta)


def validation_error_response(errors: list) -> APIResponse:
    """Create validation error response."""
    return APIResponse(
        success=False,
        message="Validation failed",
        errors=errors,
        status_code=422
    )


def not_found_response(resource: str = "Resource") -> APIResponse:
    """Create not found response."""
    return APIResponse(
        success=False,
        message=f"{resource} not found",
        status_code=404
    )


def unauthorized_response(message: str = "Unauthorized access") -> APIResponse:
    """Create unauthorized response."""
    return APIResponse(
        success=False,
        message=message,
        status_code=401
    )


def forbidden_response(message: str = "Access forbidden") -> APIResponse:
    """Create forbidden response."""
    return APIResponse(
        success=False,
        message=message,
        status_code=403
    )


def server_error_response(message: str = "Internal server error") -> APIResponse:
    """Create server error response."""
    logger.error(f"Server error: {message}")
    return APIResponse(
        success=False,
        message=message,
        status_code=500
    )


# Rate limiting response
def rate_limited_response(message: str = "Rate limit exceeded", retry_after: int = 60) -> APIResponse:
    """Create rate limited response."""
    return APIResponse(
        success=False,
        message=message,
        meta={"retry_after": retry_after},
        status_code=429
    )