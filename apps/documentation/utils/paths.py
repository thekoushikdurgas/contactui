"""Path resolution utilities for documentation media operations."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from django.conf import settings


def get_workspace_root() -> Path:
    """Get workspace root directory (parent of BASE_DIR)."""
    return Path(settings.BASE_DIR).resolve().parent


def get_media_root() -> Path:
    """Get media directory root. Uses MEDIA_ROOT if set, else BASE_DIR / 'media'."""
    media = getattr(settings, "MEDIA_ROOT", None)
    if media:
        return Path(media).resolve()
    return Path(settings.BASE_DIR) / "media"


def get_result_dir() -> Path:
    """Get directory for operation result files (analyze, validate, generate, upload_s3). All *_result.json live under media/result/."""
    return get_media_root() / "result"


def get_pages_dir() -> Path:
    """Get pages directory."""
    return get_media_root() / "pages"


def get_endpoints_dir() -> Path:
    """Get endpoints directory."""
    return get_media_root() / "endpoints"


def get_relationships_dir() -> Path:
    """Get relationships directory. Note: On disk this may be 'relationships', 'relationship' (legacy), or 'relationship'."""
    # TODO: Migrate directory from 'relationship' / 'relationship' to 'relationships' on disk
    # For now, check all known names for backward compatibility
    media_root = get_media_root()
    relationships_dir = media_root / "relationships"
    relationship_dir = media_root / "relationship"
    relationship_dir = media_root / "relationship"  # singular, used in some setups
    if relationships_dir.exists():
        return relationships_dir
    if relationship_dir.exists():
        return relationship_dir
    if relationship_dir.exists():
        return relationship_dir
    return relationships_dir  # Return new name even if doesn't exist yet


def get_postman_dir() -> Path:
    """Get Postman directory."""
    return get_media_root() / "postman"


def get_n8n_dir() -> Path:
    """Get N8N directory."""
    return get_media_root() / "n8n"


def get_project_dir() -> Path:
    """Get project directory."""
    return get_media_root() / "project"


def get_scripts_dir() -> Path:
    """Get scripts directory."""
    return Path(settings.BASE_DIR) / "scripts"


def get_lambda_docs_api_dir() -> Optional[Path]:
    """Get Lambda documentation API directory if present."""
    root = get_workspace_root()
    for sub in ["lambda/documentation.api", "docs/lambda/documentation.api"]:
        p = root / sub
        if p.exists():
            return p
    return None


def list_directory_files(
    directory: Path,
    extensions: Optional[List[str]] = None,
    exclude_files: Optional[Set[str]] = None,
) -> List[Dict[str, Any]]:
    """
    List all files in a directory with metadata.

    Args:
        directory: Directory path to list.
        extensions: File extensions to include (e.g. ['.json', '.md']). 
                   If None, all files are included.
        exclude_files: Set of filenames to exclude (e.g. {'index.json'}).

    Returns:
        List of dictionaries containing file metadata:
        - name: Filename
        - path: Full absolute path
        - relative_path: Path relative to media root
        - size: File size in bytes
        - size_human: Human-readable file size (e.g., "1.5 MB")
        - modified: Modification timestamp as datetime object
        - extension: File extension (lowercase, e.g., ".json")
        
    Note:
        Files are sorted alphabetically by name (case-insensitive).
        Non-existent directories return an empty list.
    """
    exclude_files = exclude_files or set()
    files: List[Dict[str, Any]] = []
    media_root = get_media_root()

    if not directory.exists() or not directory.is_dir():
        return files

    try:
        for fp in directory.iterdir():
            if not fp.is_file():
                continue
            if extensions and fp.suffix.lower() not in [e.lower() for e in extensions]:
                continue
            if fp.name in exclude_files:
                continue
            try:
                st = fp.stat()
                try:
                    rel = str(fp.relative_to(media_root))
                except ValueError:
                    rel = str(fp)
                files.append({
                    "name": fp.name,
                    "path": str(fp),
                    "relative_path": rel.replace("\\", "/"),
                    "size": st.st_size,
                    "size_human": _format_file_size(st.st_size),
                    "modified": datetime.fromtimestamp(st.st_mtime),
                    "extension": fp.suffix.lower(),
                })
            except (OSError, PermissionError):
                continue
    except (OSError, PermissionError):
        pass

    files.sort(key=lambda x: x["name"].lower())
    return files


def _format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable form.
    
    Args:
        size_bytes: File size in bytes.
        
    Returns:
        Human-readable file size string (e.g., "1.5 KB", "2.3 MB", "500.0 B").
        
    Examples:
        >>> _format_file_size(1024)
        '1.0 KB'
        >>> _format_file_size(1536)
        '1.5 KB'
        >>> _format_file_size(1048576)
        '1.0 MB'
    """
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
