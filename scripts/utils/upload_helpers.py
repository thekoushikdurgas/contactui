"""Common upload helper functions for scripts."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from scripts.utils.config import get_config
from scripts.utils.context import get_logger, is_django_context
from scripts.utils.validators import load_json_file, validate_json_structure

logger = get_logger(__name__)
config = get_config()


def sanitize_path(path: str) -> str:
    """
    Sanitize path for use in S3 key or filename.
    
    Args:
        path: Path string to sanitize
        
    Returns:
        Sanitized path string
    """
    sanitized = (path or "").strip("/")
    sanitized = sanitized.replace("/", "_")
    sanitized = sanitized.replace(":", "_")
    sanitized = sanitized.replace(" ", "_")
    while "__" in sanitized:
        sanitized = sanitized.replace("__", "_")
    sanitized = sanitized.strip("_")
    return sanitized or "root"


def normalize_method(method: Any) -> str:
    """
    Normalize HTTP method to uppercase.
    
    Args:
        method: Method value (any type)
        
    Returns:
        Uppercase method string (defaults to "GET")
    """
    m = (method or "").strip()
    if not m:
        return "GET"
    return m.upper()


def normalize_endpoint_path(api_version: str, endpoint_path: Any) -> str:
    """
    Normalize endpoint path for API version.
    
    Args:
        api_version: API version (e.g., "v1", "graphql")
        endpoint_path: Endpoint path value
        
    Returns:
        Normalized endpoint path
    """
    p = (endpoint_path or "").strip()
    if not p:
        return p
    if api_version == "graphql" and not p.startswith("graphql/"):
        # GraphQL operation names may appear as "Login" etc
        p = p.lstrip("/")
        p = f"graphql/{p}"
    return p


def generate_s3_key(resource_type: str, resource_id: str, subdirectory: Optional[str] = None) -> str:
    """
    Generate S3 key for a resource.
    
    Args:
        resource_type: Type of resource ('pages', 'endpoints', 'relationships', 'postman')
        resource_id: Resource identifier (e.g., page_id, endpoint_id)
        subdirectory: Optional subdirectory (e.g., 'by-page', 'by-endpoint')
        
    Returns:
        S3 key string
    """
    data_prefix = config.get_s3_data_prefix()
    
    if resource_type == "relationships" and subdirectory:
        return f"{data_prefix}relationships/{subdirectory}/{sanitize_path(resource_id)}.json"
    elif resource_type == "postman" and subdirectory:
        return f"{data_prefix}postman/{subdirectory}/{resource_id}.json"
    else:
        return f"{data_prefix}{resource_type}/{resource_id}.json"


def normalize_for_lambda(data: Dict[str, Any], resource_type: str) -> Optional[Dict[str, Any]]:
    """
    Normalize data for Lambda API import.
    
    This function ensures data is in the correct format for Lambda API.
    It's a wrapper that tries to use Django's MediaFileManagerService if available,
    otherwise does basic normalization.
    
    Args:
        data: Data dictionary to normalize
        resource_type: Type of resource ('pages', 'endpoints', 'relationships')
        
    Returns:
        Normalized data dictionary or None if normalization fails
    """
    is_django = is_django_context()
    
    # Try to use Django's MediaFileManagerService if available
    if is_django:
        try:
            from apps.documentation.services.media_file_manager import MediaFileManagerService
            file_manager = MediaFileManagerService()
            
            # MediaFileManagerService doesn't have normalize_for_lambda, so we do basic normalization
            # Just ensure required fields are present
            normalized = data.copy()
            
            if resource_type == "pages":
                if "page_id" not in normalized:
                    return None
                # Ensure metadata exists
                if "metadata" not in normalized:
                    normalized["metadata"] = {}
                # Ensure route exists
                if "route" not in normalized.get("metadata", {}):
                    normalized["metadata"]["route"] = normalized.get("route", "/")
            
            elif resource_type == "endpoints":
                if "endpoint_id" not in normalized:
                    return None
                # Normalize method
                if "method" in normalized:
                    normalized["method"] = normalize_method(normalized["method"])
                # Normalize endpoint_path
                if "endpoint_path" in normalized and "api_version" in normalized:
                    normalized["endpoint_path"] = normalize_endpoint_path(
                        normalized["api_version"], normalized["endpoint_path"]
                    )
            
            elif resource_type == "relationships":
                # Ensure required fields
                required = ["page_path", "endpoint_path", "method"]
                if not all(field in normalized for field in required):
                    return None
                # Normalize method
                normalized["method"] = normalize_method(normalized["method"])
                # Normalize endpoint_path if api_version provided
                if "api_version" in normalized:
                    normalized["endpoint_path"] = normalize_endpoint_path(
                        normalized["api_version"], normalized["endpoint_path"]
                    )
            
            return normalized
        except ImportError:
            pass
    
    # Fallback: basic normalization without Django
    normalized = data.copy()
    
    if resource_type == "pages":
        if "page_id" not in normalized:
            return None
    elif resource_type == "endpoints":
        if "endpoint_id" not in normalized:
            return None
        if "method" in normalized:
            normalized["method"] = normalize_method(normalized["method"])
    elif resource_type == "relationships":
        required = ["page_path", "endpoint_path", "method"]
        if not all(field in normalized for field in required):
            return None
        normalized["method"] = normalize_method(normalized["method"])
    
    return normalized


def load_and_validate_file(
    file_path: Path,
    resource_type: str,
    required_fields: List[str],
) -> Tuple[Optional[Dict[str, Any]], Optional[str], List[str]]:
    """
    Load JSON file and validate it.
    
    Args:
        file_path: Path to JSON file
        resource_type: Type of resource for normalization
        required_fields: List of required field names
        
    Returns:
        Tuple of (data, error_message, validation_errors)
    """
    # Load file
    data, parse_error = load_json_file(file_path)
    if parse_error:
        return None, parse_error, []
    
    if data is None:
        return None, "Failed to load JSON", []
    
    # Validate required fields
    is_valid, validation_errors = validate_json_structure(data, required_fields)
    if not is_valid:
        error_messages = [str(e) for e in validation_errors]
        return None, f"Validation failed: {', '.join(error_messages)}", validation_errors
    
    # Normalize for Lambda API
    normalized = normalize_for_lambda(data, resource_type)
    if normalized is None:
        return None, "Failed to normalize data", []
    
    return normalized, None, []


def collect_upload_errors(
    errors: List[Dict[str, Any]],
    max_display: int = 10,
) -> Dict[str, Any]:
    """
    Collect and format upload errors for display.
    
    Args:
        errors: List of error dictionaries
        max_display: Maximum number of errors to display
        
    Returns:
        Dictionary with error summary
    """
    total_errors = len(errors)
    display_errors = errors[:max_display]
    remaining = max(0, total_errors - max_display)
    
    return {
        "total": total_errors,
        "display": display_errors,
        "remaining": remaining,
    }


def format_upload_summary(stats: Dict[str, Any]) -> str:
    """
    Format upload statistics as a summary string.
    
    Args:
        stats: Statistics dictionary
        
    Returns:
        Formatted summary string
    """
    lines = [
        f"  ➕ Created:   {stats.get('created', 0)}",
        f"  🔄 Updated:   {stats.get('updated', 0)}",
        f"  ❌ Errors:    {stats.get('errors', 0)}",
        f"  ⏭️  Skipped:   {stats.get('skipped', 0)}",
        f"  📄 Total:     {stats.get('total', 0)}",
        f"  ✅ Processed: {stats.get('processed', 0)}",
    ]
    return "\n".join(lines)


def get_exclude_files() -> set:
    """
    Get set of files to exclude from processing.
    
    Returns:
        Set of filenames to exclude
    """
    return {
        "index.json",
        "pages_index.json",
        "endpoints_index.json",
        "relationships_index.json",
        "postman_index.json",
        "schema.md",
        "README.md",
        "pages_index_example.json",
        "endpoints_index_example.json",
        "relationships_index_example.json",
    }
