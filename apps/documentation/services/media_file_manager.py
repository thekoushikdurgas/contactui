"""Media File Manager – scan, metadata, S3 keys, CRUD for media/ JSON."""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from django.conf import settings

from apps.documentation.utils.paths import (
    get_endpoints_dir,
    get_media_root,
    get_n8n_dir,
    get_pages_dir,
    get_postman_dir,
    get_relationships_dir,
    list_directory_files,
)

logger = logging.getLogger(__name__)

INDEX_EXCLUDE: Set[str] = {
    "index.json",
    "pages_index.json",
    "endpoints_index.json",
    "postman_index.json",
    "relationships_index.json",
}


class MediaFileManagerService:
    """Scan media dirs, metadata, S3 keys, and CRUD for documentation JSON."""

    def __init__(self) -> None:
        self.media_root = get_media_root()
        self.data_prefix = (getattr(settings, "S3_DATA_PREFIX", "data/") or "data/").rstrip("/")

    def _resource_dirs(self, resource_type: str) -> List[Path]:
        """Return directories to scan for a resource type. media/result/ is not included (operation results, not documentation content)."""
        if resource_type == "pages":
            return [get_pages_dir()]
        if resource_type == "endpoints":
            return [get_endpoints_dir()]
        if resource_type == "relationships":
            rel = get_relationships_dir()
            return [rel / "by-page", rel / "by-endpoint"]
        if resource_type == "postman":
            pm = get_postman_dir()
            return [pm / "collection", pm / "environment", pm / "configurations"]
        if resource_type == "n8n":
            n8n = get_n8n_dir()
            return [n8n / "workflows", n8n / "Database Cleaning", n8n / "Email Pattern",
                   n8n / "P2PMigration", n8n / "Sales Navigator Workflows"]
        return []

    def scan_media_directory(self, resource_type: str) -> List[Dict[str, Any]]:
        """
        List JSON files in the given resource type (pages, endpoints, relationships, postman).
        Excludes index files. Returns list of {file_path, relative_path, name, size, modified, resource_type, s3_key}.
        """
        result: List[Dict[str, Any]] = []
        dirs = self._resource_dirs(resource_type)

        for d in dirs:
            if not d.exists():
                continue
            files = list_directory_files(d, extensions=[".json"], exclude_files=INDEX_EXCLUDE)
            for fi in files:
                fp = Path(fi["path"])
                s3_key = self.calculate_s3_key(fp, resource_type)
                rel = (fi.get("relative_path") or "").replace("\\", "/")
                
                # Extract subdirectory for relationships and postman
                subdirectory = None
                if resource_type in ["relationships", "postman"]:
                    # Extract subdirectory from relative_path (e.g., "relationships/by-page/file.json" -> "by-page")
                    parts = rel.split("/")
                    if len(parts) >= 2:
                        # Find the resource_type part and get the next part as subdirectory
                        try:
                            resource_idx = next(i for i, part in enumerate(parts) if part == resource_type)
                            if resource_idx + 1 < len(parts):
                                subdirectory = parts[resource_idx + 1]
                        except StopIteration:
                            # Fallback: try to find subdirectory from directory name
                            subdirectory = d.name if d.name != resource_type else None
                
                file_data = {
                    "file_path": fi["path"],
                    "relative_path": rel,
                    "name": fi["name"],
                    "size": fi["size"],
                    "modified": fi["modified"],
                    "resource_type": resource_type,
                    "s3_key": s3_key,
                }
                
                if subdirectory:
                    file_data["subdirectory"] = subdirectory
                
                result.append(file_data)

        result.sort(key=lambda x: (x["name"].lower(), x["relative_path"]))
        return result

    def get_file_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Return {file_path, size, modified, hash, exists} for a file."""
        p = Path(file_path)
        if not p.exists() or not p.is_file():
            return {"file_path": str(p), "size": 0, "modified": None, "hash": None, "exists": False}
        try:
            st = p.stat()
            h = hashlib.md5()
            with open(p, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            return {
                "file_path": str(p),
                "size": st.st_size,
                "modified": datetime.fromtimestamp(st.st_mtime),
                "hash": h.hexdigest(),
                "exists": True,
            }
        except Exception as e:
            logger.warning("get_file_metadata error path=%s: %s", file_path, e)
            return None

    def calculate_s3_key(self, file_path: Path, resource_type: str) -> str:
        """Compute S3 key for a file. Uses data/ prefix and relationships directory."""
        name = file_path.name
        try:
            rel = file_path.resolve().relative_to(self.media_root.resolve())
            parts = rel.parts
        except ValueError:
            parts = (resource_type, name)

        if resource_type == "relationships" and len(parts) >= 2:
            # Handle both 'relationships' and legacy 'relationship' directory names
            # relationships/by-page/foo.json -> data/relationships/by-page/foo.json
            sub = "/".join(parts[1:])
            return f"{self.data_prefix}/relationships/{sub}"
        if resource_type == "postman" and len(parts) >= 2:
            sub = "/".join(parts[1:])
            return f"{self.data_prefix}/postman/{sub}"
        return f"{self.data_prefix}/{resource_type}/{name}"

    def _infer_resource_type(self, file_path: Path) -> str:
        try:
            rel = file_path.resolve().relative_to(self.media_root.resolve())
        except ValueError:
            return "project"
        parts = rel.parts
        if not parts:
            return "project"
        if parts[0] == "pages":
            return "pages"
        if parts[0] == "endpoints":
            return "endpoints"
        if parts[0] in ("relationship", "relationships"):  # Support both legacy and new names
            return "relationships"
        if parts[0] == "postman":
            return "postman"
        if parts[0] == "project":
            return "project"
        return "project"

    def get_file_content(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Read and parse JSON from path. Returns None on error."""
        p = Path(file_path)
        if not p.exists() or not p.is_file():
            return None
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("get_file_content error path=%s: %s", file_path, e)
            return None

    def get_file_detail(self, full_path: str) -> Optional[Dict[str, Any]]:
        """
        Return file detail: content, metadata, relative_path, resource_type, s3_key.
        Optional sync_status if we add remote comparison later.
        """
        p = Path(full_path)
        if not p.exists() or not p.is_file():
            return None
        try:
            rel = p.resolve().relative_to(self.media_root.resolve())
            relative_path = str(rel).replace("\\", "/")
        except ValueError:
            relative_path = p.name

        meta = self.get_file_metadata(full_path)
        content = self.get_file_content(full_path)
        resource_type = self._infer_resource_type(p)
        s3_key = self.calculate_s3_key(p, resource_type)

        sync_status = self.get_file_sync_status(full_path)
        detail: Dict[str, Any] = {
            "content": content,
            "metadata": meta or {},
            "relative_path": relative_path,
            "resource_type": resource_type,
            "s3_key": s3_key,
            "sync_status": sync_status,
        }
        return detail

    def create_file(self, resource_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new JSON file. resource_type in pages, endpoints, relationships, postman.
        Returns {success, file_path, relative_path, error}.
        """
        if resource_type == "pages":
            fid = data.get("page_id") or "unknown"
            directory = get_pages_dir()
        elif resource_type == "endpoints":
            fid = data.get("endpoint_id") or "unknown"
            directory = get_endpoints_dir()
        elif resource_type == "relationships":
            fid = data.get("relationship_id") or "unknown"
            directory = get_relationships_dir()  # default to root; could use by-page/by-endpoint
        elif resource_type == "postman":
            fid = data.get("config_id") or (data.get("info") or {}).get("name", "unknown")
            directory = get_postman_dir()
        else:
            return {"success": False, "file_path": None, "relative_path": None, "error": f"Unknown resource_type: {resource_type}"}

        directory.mkdir(parents=True, exist_ok=True)
        name = f"{fid}.json" if not str(fid).endswith(".json") else fid
        file_path = directory / name

        if file_path.exists():
            return {"success": False, "file_path": str(file_path), "relative_path": None, "error": "File already exists"}

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            try:
                rel = file_path.resolve().relative_to(self.media_root.resolve())
                relative_path = str(rel).replace("\\", "/")
            except ValueError:
                relative_path = name
            return {"success": True, "file_path": str(file_path), "relative_path": relative_path, "error": None}
        except Exception as e:
            logger.exception("create_file error")
            return {"success": False, "file_path": None, "relative_path": None, "error": str(e)}

    def update_file(self, full_path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Overwrite JSON file at full_path. Returns {success, file_path, relative_path, error}."""
        p = Path(full_path)
        if not p.exists() or not p.is_file():
            return {"success": False, "file_path": full_path, "relative_path": None, "error": "File not found"}
        try:
            with open(p, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            try:
                rel = p.resolve().relative_to(self.media_root.resolve())
                relative_path = str(rel).replace("\\", "/")
            except ValueError:
                relative_path = p.name
            return {"success": True, "file_path": full_path, "relative_path": relative_path, "error": None}
        except Exception as e:
            logger.exception("update_file error")
            return {"success": False, "file_path": full_path, "relative_path": None, "error": str(e)}

    def get_file_sync_status(self, file_path: str) -> Dict[str, Any]:
        """Return sync status for a file. Placeholder: local exists, remote unknown."""
        meta = self.get_file_metadata(file_path)
        return {
            "status": "unknown",
            "local_exists": bool(meta and meta.get("exists")),
            "remote_exists": None,
            "hash_match": None,
            "sync_needed": None,
        }

    def delete_file(self, full_path: str, delete_remote: bool = False) -> Dict[str, Any]:
        """
        Delete local file. If delete_remote, also delete from S3 using calculated key.
        Returns {success, error}.
        """
        p = Path(full_path)
        if not p.exists() or not p.is_file():
            return {"success": False, "error": "File not found"}

        try:
            resource_type = self._infer_resource_type(p)
            s3_key = self.calculate_s3_key(p, resource_type)
        except Exception:
            s3_key = None

        try:
            p.unlink()
        except OSError as e:
            return {"success": False, "error": str(e)}

        if delete_remote and s3_key:
            try:
                from apps.core.services.s3_service import S3Service
                svc = S3Service()
                svc.delete_file(s3_key)
            except Exception as e:
                logger.warning("S3 delete_file failed key=%s: %s", s3_key, e)
                return {"success": True, "error": f"Local deleted; S3 delete failed: {e}"}

        return {"success": True, "error": None}
