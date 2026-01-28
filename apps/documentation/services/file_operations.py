"""File-specific operations: analyze, validate, generate, upload single media JSON."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from apps.documentation.utils.paths import (
    get_endpoints_dir,
    get_media_root,
    get_pages_dir,
    get_postman_dir,
    get_project_dir,
    get_relationships_dir,
)

logger = logging.getLogger(__name__)


class FileOperationsService:
    """Single-file analyze, validate, generate, upload to S3, save result."""

    def __init__(self) -> None:
        self.media_root = get_media_root()

    def _validate_file_path(self, file_path: str) -> Optional[Path]:
        """Resolve relative path under media root; reject traversal. Return Path or None."""
        if not file_path or ".." in file_path:
            logger.warning("Invalid file path: %s", file_path)
            return None
        fp = file_path.strip().lstrip("/").replace("\\", "/")
        if ".." in fp:
            return None
        try:
            full = (self.media_root / fp).resolve()
            full.relative_to(self.media_root.resolve())
        except (ValueError, OSError):
            logger.warning("File path outside media root: %s", file_path)
            return None
        if not full.exists() or not full.is_file():
            logger.warning("File does not exist: %s", file_path)
            return None
        return full

    def _determine_file_directory(self, file_path: Path) -> Optional[str]:
        """Return 'pages'|'endpoints'|'relationships'|'postman'|'project' or None."""
        try:
            rel = file_path.resolve().relative_to(self.media_root.resolve())
            parts = rel.parts
            if not parts:
                return None
            d = parts[0]
            if d in ("pages", "endpoints", "retations", "relationships", "postman", "project"):
                return "relationships" if d == "retations" else d
        except ValueError:
            pass
        return None

    def _load_file_content(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load JSON from path. Return None on error."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Load file %s: %s", file_path, e)
            return None

    def analyze_single_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze one file: required fields by type. Returns {status, valid, errors, warnings, file_info, content_keys}."""
        resolved = self._validate_file_path(file_path)
        if not resolved:
            return {"status": "error", "valid": False, "errors": ["Invalid file path"], "warnings": [], "file_info": None}
        content = self._load_file_content(resolved)
        if content is None:
            return {
                "status": "error",
                "valid": False,
                "errors": ["Failed to load or parse JSON"],
                "warnings": [],
                "file_info": {"path": str(resolved), "name": resolved.name},
            }
        errors: list = []
        warnings: list = []
        directory = self._determine_file_directory(resolved)
        if directory == "pages":
            for k in ("_id", "page_id", "page_type", "metadata", "created_at"):
                if k not in content:
                    errors.append(f"Missing required field: {k}")
        elif directory == "endpoints":
            for k in ("_id", "endpoint_id", "endpoint_path", "method", "api_version"):
                if k not in content:
                    errors.append(f"Missing required field: {k}")
        elif directory == "relationships":
            if "page_path" not in content and "endpoint_path" not in content:
                errors.append("Missing required field: page_path or endpoint_path")
        st = resolved.stat()
        file_info = {
            "path": str(resolved),
            "name": resolved.name,
            "directory": directory,
            "size": st.st_size,
            "modified": datetime.fromtimestamp(st.st_mtime).isoformat(),
        }
        return {
            "status": "success",
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "file_info": file_info,
            "content_keys": list(content.keys()) if isinstance(content, dict) else [],
        }

    def validate_single_file(self, file_path: str) -> Dict[str, Any]:
        """Validate one file. Uses analyze; optionally Lambda later. Returns {status, valid, errors, warnings, lambda_api_response}."""
        result = self.analyze_single_file(file_path)
        result.setdefault("lambda_api_response", None)
        return result

    def generate_json_for_file(self, file_path: str) -> Dict[str, Any]:
        """Ensure file is valid JSON; 'generate' is effectively validate. Returns {status, generated, output_path, errors}."""
        resolved = self._validate_file_path(file_path)
        if not resolved:
            return {"status": "error", "generated": False, "output_path": None, "errors": ["Invalid file path"]}
        if self._load_file_content(resolved) is None:
            return {"status": "error", "generated": False, "output_path": None, "errors": ["File is not valid JSON"]}
        return {"status": "success", "generated": True, "output_path": str(resolved), "errors": [], "message": "File is valid JSON"}

    def upload_single_file_to_s3(self, file_path: str) -> Dict[str, Any]:
        """Upload one file to S3. Returns {status, uploaded, s3_key, errors, lambda_api_response}."""
        resolved = self._validate_file_path(file_path)
        if not resolved:
            return {"status": "error", "uploaded": False, "s3_key": None, "errors": ["Invalid file path"], "lambda_api_response": None}
        directory = self._determine_file_directory(resolved)
        if not directory:
            return {"status": "error", "uploaded": False, "s3_key": None, "errors": ["Could not determine file directory"], "lambda_api_response": None}
        try:
            from django.conf import settings
            prefix = (getattr(settings, "S3_DATA_PREFIX", "data/") or "data/").rstrip("/")
            name = resolved.name
            if directory == "pages":
                s3_key = f"{prefix}/pages/{name}"
            elif directory == "endpoints":
                s3_key = f"{prefix}/endpoints/{name}"
            elif directory == "relationships":
                try:
                    rel = resolved.relative_to(get_relationships_dir())
                    sub = str(rel).replace("\\", "/")
                    s3_key = f"{prefix}/relationships/{sub}"
                except ValueError:
                    s3_key = f"{prefix}/relationships/{name}"
            elif directory == "postman":
                try:
                    rel = resolved.relative_to(get_postman_dir())
                    sub = str(rel).replace("\\", "/")
                    s3_key = f"{prefix}/postman/{sub}"
                except ValueError:
                    s3_key = f"{prefix}/postman/{name}"
            elif directory == "project":
                return {"status": "error", "uploaded": False, "s3_key": None, "errors": ["Project files are not synced to S3"], "lambda_api_response": None}
            else:
                s3_key = f"{prefix}/{name}"
            with open(resolved, "rb") as f:
                body = f.read()
            from apps.core.services.s3_service import S3Service
            svc = S3Service()
            svc.upload_file(body, s3_key, content_type="application/json")
            return {"status": "success", "uploaded": True, "s3_key": s3_key, "errors": [], "lambda_api_response": None}
        except Exception as e:
            logger.exception("upload_single_file_to_s3")
            return {"status": "error", "uploaded": False, "s3_key": None, "errors": [str(e)], "lambda_api_response": None}

    def save_operation_result(self, file_path: str, operation: str, result: Dict[str, Any]) -> bool:
        """Write operation result as {stem}_result.json in the same directory as the source file."""
        resolved = self._validate_file_path(file_path)
        if not resolved:
            return False
        out_path = resolved.parent / f"{resolved.stem}_result.json"
        payload = {
            "operation": operation,
            "file_path": file_path,
            "status": result.get("status", "unknown"),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "result": result,
            "errors": result.get("errors", []),
            "warnings": result.get("warnings", []),
        }
        if "lambda_api_response" in result:
            payload["lambda_api_response"] = result["lambda_api_response"]
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            return True
        except OSError as e:
            logger.warning("save_operation_result %s: %s", out_path, e)
            return False
