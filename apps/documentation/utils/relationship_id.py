"""Relationship ID utilities for generating and parsing relationship IDs.

Ported from Lambda documentation.api.
"""

from typing import Dict


def sanitize_path(path: str) -> str:
    """
    Sanitize a path for use in relationship ID.

    Args:
        path: Path string (page_path or endpoint_path)

    Returns:
        Sanitized path string
    """
    sanitized = path.strip("/")
    sanitized = sanitized.replace("/", "_")
    sanitized = sanitized.replace(":", "_")
    sanitized = sanitized.replace(" ", "_")
    while "__" in sanitized:
        sanitized = sanitized.replace("__", "_")
    sanitized = sanitized.strip("_")
    if not sanitized:
        sanitized = "root"
    return sanitized


def generate_relationship_id(page_path: str, endpoint_path: str, method: str) -> str:
    """
    Generate a relationship ID from page path, endpoint path, and method.

    Format: {sanitized_page_path}_{sanitized_endpoint_path}_{method}

    Args:
        page_path: Page route (e.g., "/dashboard")
        endpoint_path: Endpoint path (e.g., "/api/v4/contacts")
        method: HTTP/GraphQL method (e.g., "GET", "QUERY")

    Returns:
        Relationship ID string
    """
    sanitized_page = sanitize_path(page_path)
    sanitized_endpoint = sanitize_path(endpoint_path)
    sanitized_method = method.upper()
    return f"{sanitized_page}_{sanitized_endpoint}_{sanitized_method}"


def parse_relationship_id(relationship_id: str) -> Dict[str, str]:
    """
    Parse a relationship ID to extract page_path, endpoint_path, and method.

    Note: This is a best-effort parse. The original paths may have been
    modified during sanitization (e.g., slashes replaced with underscores).
    For exact paths, use the relationship data stored in S3.

    Args:
        relationship_id: Relationship ID string

    Returns:
        Dictionary with page_path, endpoint_path, and method
    """
    parts = relationship_id.rsplit("_", 2)
    if len(parts) != 3:
        raise ValueError(f"Invalid relationship ID format: {relationship_id}")
    sanitized_page, sanitized_endpoint, method = parts
    page_path = f"/{sanitized_page.replace('_', '/')}"
    endpoint_path = f"/{sanitized_endpoint.replace('_', '/')}"
    return {
        "page_path": page_path,
        "endpoint_path": endpoint_path,
        "method": method,
    }
