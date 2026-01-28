"""Media Manager – high-level CRUD, list, sync, and sync summary for media JSON."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from apps.core.services.base_service import BaseService
from apps.documentation.services.media_file_manager import MediaFileManagerService
from apps.documentation.services.media_sync_service import MediaSyncService
from apps.documentation.utils.paths import get_media_root, get_project_dir

logger = logging.getLogger(__name__)


def _norm(path: str) -> str:
    """Normalize path separators (backslash to forward slash).
    
    Args:
        path: Path string to normalize
        
    Returns:
        Normalized path string
    """
    return (path or "").replace("\\", "/")


class MediaManagerService(BaseService):
    """
    High-level service for managing media files with CRUD, list, sync, and sync summary operations.
    
    This service acts as a facade over MediaFileManagerService and MediaSyncService,
    providing a unified interface for media file operations.
    
    Extends BaseService for consistent logging and error handling (Phase 3.1.1).
    """

    def __init__(self) -> None:
        """Initialize MediaManagerService with file manager and sync service."""
        super().__init__("MediaManagerService")
        self.file_manager = MediaFileManagerService()
        self.sync_service = MediaSyncService()
        self.media_root = get_media_root()

    def list_files(
        self,
        resource_type: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        List files for a resource type with filtering and sorting.
        
        Supports filters:
        - search: Filter by filename (case-insensitive)
        - subdirectory: Filter by subdirectory (for relationships and postman)
        - sort_by: Sort field ('name', 'size', 'modified')
        - sort_order: Sort direction ('asc' or 'desc')
        
        Includes project dir for resource_type 'project'.
        
        Args:
            resource_type: Type of resource ('pages', 'endpoints', 'relationships', 'postman', 'n8n', 'project')
            filters: Optional dictionary of filter criteria
            
        Returns:
            List of file dictionaries with metadata (file_path, relative_path, name, size, modified, etc.)
            
        Raises:
            ValueError: If resource_type is invalid
        """
        if not resource_type:
            raise ValueError("resource_type is required")
        
        filters = filters or {}
        files: List[Dict[str, Any]] = []

        if resource_type == "project":
            d = get_project_dir()
            if d.exists():
                for p in d.iterdir():
                    if p.is_file():
                        try:
                            st = p.stat()
                            rel = str(p.relative_to(self.media_root)).replace("\\", "/")
                            files.append({
                                "file_path": str(p),
                                "relative_path": _norm(rel),
                                "name": p.name,
                                "size": st.st_size,
                                "modified": st.st_mtime,
                                "resource_type": "project",
                                "s3_key": None,
                                "sync_status": "unknown",
                            })
                        except (OSError, ValueError):
                            continue
            files.sort(key=lambda x: x["name"].lower())
        else:
            files = self.file_manager.scan_media_directory(resource_type)
            for f in files:
                f["sync_status"] = "unknown"

        # Filters
        search = (filters.get("search") or "").strip().lower()
        if search:
            files = [x for x in files if search in (x.get("name") or "").lower()]
        
        # Subdirectory filter (for relationships and postman)
        subdirectory = filters.get("subdirectory")
        if subdirectory:
            files = [x for x in files if x.get("subdirectory") == subdirectory]

        sort_by = filters.get("sort_by") or "name"
        sort_order = (filters.get("sort_order") or "asc").lower()
        rev = sort_order == "desc"

        def _modified_ts(x: Dict[str, Any]) -> float:
            m = x.get("modified")
            if m is None:
                return 0.0
            if isinstance(m, (int, float)):
                return float(m)
            return getattr(m, "timestamp", lambda: 0.0)()

        if sort_by == "name":
            files.sort(key=lambda x: (x.get("name") or "").lower(), reverse=rev)
        elif sort_by == "size":
            files.sort(key=lambda x: x.get("size") or 0, reverse=rev)
        elif sort_by == "modified":
            files.sort(key=_modified_ts, reverse=rev)

        return files

    def get_file_detail(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary containing:
            - content: File content (if readable)
            - metadata: File metadata
            - relative_path: Relative path from media root
            - resource_type: Type of resource
            - s3_key: S3 key if synced
            - sync_status: Sync status ('synced', 'out_of_sync', 'not_synced', 'unknown')
            None if file not found
        """
        if not file_path:
            raise ValueError("file_path is required")
        
        return self.file_manager.get_file_detail(file_path)

    def create_file(
        self,
        resource_type: str,
        data: Dict[str, Any],
        auto_sync: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a new file for the specified resource type.
        
        Args:
            resource_type: Type of resource ('pages', 'endpoints', 'relationships', 'postman', 'n8n')
            data: File data dictionary (must include required fields for resource type)
            auto_sync: If True, automatically sync file to S3 after creation
            
        Returns:
            Dictionary with:
            - success: Boolean indicating success
            - file_path: Path to created file (if successful)
            - sync_result: Sync result dictionary (if auto_sync=True)
            - error: Error message (if failed)
            
        Raises:
            ValueError: If resource_type or data is invalid
        """
        if not resource_type:
            raise ValueError("resource_type is required")
        if not data:
            raise ValueError("data is required")
        
        out = self.file_manager.create_file(resource_type, data)
        if out.get("success") and auto_sync and out.get("file_path"):
            sync = self.sync_service.sync_file_to_s3(out["file_path"])
            out["sync_result"] = sync
            self.logger.info(f"Created and synced file: {out['file_path']}")
        elif out.get("success"):
            self.logger.info(f"Created file: {out.get('file_path', 'unknown')}")
        
        return out

    def update_file(
        self,
        file_path: str,
        data: Dict[str, Any],
        auto_sync: bool = False,
    ) -> Dict[str, Any]:
        """
        Update an existing file.
        
        Args:
            file_path: Path to the file to update
            data: Updated file data dictionary
            auto_sync: If True, automatically sync file to S3 after update
            
        Returns:
            Dictionary with:
            - success: Boolean indicating success
            - file_path: Path to updated file (if successful)
            - sync_result: Sync result dictionary (if auto_sync=True)
            - error: Error message (if failed)
            
        Raises:
            ValueError: If file_path or data is invalid
        """
        if not file_path:
            raise ValueError("file_path is required")
        if not data:
            raise ValueError("data is required")
        
        out = self.file_manager.update_file(file_path, data)
        if out.get("success") and auto_sync:
            sync = self.sync_service.sync_file_to_s3(file_path)
            out["sync_result"] = sync
            self.logger.info(f"Updated and synced file: {file_path}")
        elif out.get("success"):
            self.logger.info(f"Updated file: {file_path}")
        
        return out

    def delete_file(self, file_path: str, delete_remote: bool = False) -> Dict[str, Any]:
        """Delete local file; optionally delete from S3."""
        return self.file_manager.delete_file(file_path, delete_remote=delete_remote)

    def sync_file(self, file_path: str, direction: str = "to_lambda") -> Dict[str, Any]:
        """
        Sync a single file to or from S3.
        
        Args:
            file_path: Path to the file to sync
            direction: Sync direction ('to_lambda' for upload to S3, 'from_lambda' for download)
                      Note: 'from_lambda' is not yet implemented
            
        Returns:
            Dictionary with:
            - success: Boolean indicating success
            - file_path: Path to synced file (if successful)
            - error: Error message (if failed)
            
        Raises:
            ValueError: If file_path is invalid or direction is unsupported
        """
        if not file_path:
            raise ValueError("file_path is required")
        
        if direction == "from_lambda":
            return {"success": False, "error": "Sync from Lambda/S3 not implemented yet"}
        
        if direction != "to_lambda":
            raise ValueError(f"Unsupported sync direction: {direction}")
        
        result = self.sync_service.sync_file_to_s3(file_path)
        if result.get("success"):
            self.logger.info(f"Synced file to S3: {file_path}")
        
        return result

    def get_sync_summary(self) -> Dict[str, Any]:
        """
        Get aggregated sync statistics for all resource types.
        
        Returns a summary of file counts and sync status across all resource types.
        Currently uses placeholder sync status (all files marked as 'not_synced').
        Future enhancement: Implement real sync status checking.
        
        Returns:
            Dictionary with:
            - by_type: Dictionary mapping resource type to sync statistics
            - overall: Overall statistics across all resource types
            
        Example:
            {
                "by_type": {
                    "pages": {"total": 10, "synced": 0, "out_of_sync": 0, "not_synced": 10},
                    ...
                },
                "overall": {
                    "total_files": 50,
                    "total_synced": 0,
                    "total_out_of_sync": 0,
                    "total_not_synced": 50
                }
            }
        """
        resource_types = ["pages", "endpoints", "relationships", "postman", "n8n", "project"]
        by_type: Dict[str, Dict[str, Any]] = {}
        total_files = 0
        total_synced = 0
        total_out_of_sync = 0
        total_not_synced = 0

        for rt in resource_types:
            try:
                files = self.list_files(rt)
                n = len(files)
                total_files += n
                # Placeholder: no real sync state (future enhancement)
                total_not_synced += n
                by_type[rt] = {
                    "total": n,
                    "synced": 0,
                    "out_of_sync": 0,
                    "not_synced": n,
                }
            except Exception as e:
                self.logger.warning(f"Error getting sync summary for {rt}: {e}")
                by_type[rt] = {
                    "total": 0,
                    "synced": 0,
                    "out_of_sync": 0,
                    "not_synced": 0,
                }

        return {
            "by_type": by_type,
            "overall": {
                "total_files": total_files,
                "total_synced": total_synced,
                "total_out_of_sync": total_out_of_sync,
                "total_not_synced": total_not_synced,
            },
        }
