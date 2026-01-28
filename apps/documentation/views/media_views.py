"""Media Manager APIs and per-file operation views."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import unquote

from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from apps.documentation.services.file_operations import FileOperationsService
from apps.documentation.services.media_manager_service import MediaManagerService
from apps.documentation.services.media_sync_service import MediaSyncService
from apps.documentation.services import pages_service, endpoints_service, relationships_service, postman_service
from apps.documentation.utils.relationship_id import generate_relationship_id
import markdown
from apps.documentation.utils.api_responses import (
    APIResponse,
    error_response,
    not_found_response,
    server_error_response,
    success_response,
    validation_error_response,
)
from apps.documentation.utils.paths import get_media_root
from apps.documentation.utils.security import AuditLogger, SecurityValidator, require_secure_path
from apps.documentation.utils.view_helpers import parse_json_body, validate_detail_tab

logger = logging.getLogger(__name__)


def _ensure_under_media(full_path: Path, media_root: Path) -> bool:
    """Return True if full_path is under media_root."""
    try:
        full_path.resolve().relative_to(media_root.resolve())
        return True
    except ValueError:
        return False


# Use shared helper function (Task 2.3.1)
from apps.documentation.utils.view_helpers import parse_json_body

def _parse_json_body(request: HttpRequest) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Parse JSON body (uses shared helper)."""
    return parse_json_body(request)


def _validate_file_path(file_path: str) -> Tuple[Optional[str], Optional[Path]]:
    """Validate and resolve file path. Returns (relative_path, full_path) or (None, None)."""
    media_root = get_media_root()
    fp = unquote(file_path).replace("\\", "/").lstrip("/")
    
    # Security validation
    if ".." in fp or not SecurityValidator.validate_path_safety(fp):
        return None, None
    
    full = (media_root / fp).resolve()
    if not _ensure_under_media(full, media_root) or not full.exists() or not full.is_file():
        return None, None
    
    return fp, full


# -----------------------------------------------------------------------------
# Media Manager APIs
# -----------------------------------------------------------------------------


@login_required
@require_http_methods(["GET"])
def list_files_api(request):
    """GET /docs/api/media/files/?resource_type=pages&search=..."""
    start_time = time.time()
    try:
        svc = MediaManagerService()
        resource_type = request.GET.get("resource_type", "pages")
        filters = {
            "sync_status": request.GET.get("sync_status"),
            "search": request.GET.get("search", ""),
            "sort_by": request.GET.get("sort_by", "name"),
            "sort_order": request.GET.get("sort_order", "asc"),
            "subdirectory": request.GET.get("subdirectory"),  # For relationships and postman
        }
        files = svc.list_files(resource_type, filters)
        response = success_response(
            data=files,
            message=f"Retrieved {len(files)} files",
            meta={
                "total": len(files),
                "resource_type": resource_type,
                "filters_applied": any(filters.values())
            }
        )

        # Audit logging
        response_time = int((time.time() - start_time) * 1000)
        AuditLogger.log_api_access(
            request, "/docs/api/media/files/", "GET",
            success=True, response_time=response_time
        )
        AuditLogger.log_file_access(
            request, "list", f"resource:{resource_type}",
            resource_type=resource_type, success=True,
            details=f"filters: {filters}, count: {len(files)}"
        )

        return response.to_json_response()
    except Exception as e:
        logger.exception("list_files_api")
        response_time = int((time.time() - start_time) * 1000)
        AuditLogger.log_api_access(
            request, "/docs/api/media/files/", "GET",
            success=False, response_time=response_time
        )
        return server_error_response(f"Failed to list files: {str(e)}").to_json_response()


@login_required
@require_http_methods(["GET"])
@require_secure_path
def get_file_api(request: HttpRequest, file_path: str) -> JsonResponse:
    """GET /docs/api/media/files/<path:file_path>/"""
    start_time = time.time()
    fp, full = _validate_file_path(file_path)
    
    if not fp or not full:
        AuditLogger.log_file_access(request, "read", file_path, success=False, details="File not found")
        return not_found_response("File").to_json_response()

    # Validate file extension
    if not SecurityValidator.validate_file_extension(full.name):
        AuditLogger.log_security_event(
            request, "extension_validation_failed", f"Disallowed extension: {full.name}"
        )
        return error_response("File type not allowed", status_code=400).to_json_response()

    try:
        svc = MediaManagerService()
        detail = svc.get_file_detail(str(full))
        if not detail:
            AuditLogger.log_file_access(request, "read", fp, success=False, details="File not found")
            return not_found_response("File").to_json_response()

        response = success_response(data=detail, message="File details retrieved successfully")

        # Audit logging
        response_time = int((time.time() - start_time) * 1000)
        AuditLogger.log_api_access(
            request, f"/docs/api/media/files/{file_path}/", "GET", success=True, response_time=response_time
        )
        AuditLogger.log_file_access(
            request,
            "read",
            fp,
            resource_type=detail.get("resource_type", ""),
            success=True,
            details=f"size: {detail.get('metadata', {}).get('size', 0)}",
        )

        return response.to_json_response()
    except Exception as e:
        logger.exception("get_file_api")
        return server_error_response(f"Failed to get file details: {str(e)}").to_json_response()


@login_required
@require_http_methods(["POST"])
def create_file_api(request: HttpRequest) -> JsonResponse:
    """POST /docs/api/media/files/create/ body: {resource_type, data, auto_sync}"""
    data, error_msg = _parse_json_body(request)
    if error_msg:
        logger.warning("Invalid request body in create_file_api: %s", error_msg)
        return error_response(message=error_msg, status_code=400).to_json_response()
    
    resource_type = data.get("resource_type")
    file_data = data.get("data", {})
    auto_sync = data.get("auto_sync", False)
    
    if not resource_type:
        return error_response(message="resource_type is required", status_code=400).to_json_response()
    
    try:
        svc = MediaManagerService()
        out = svc.create_file(resource_type, file_data, auto_sync=auto_sync)
        if out.get("success"):
            logger.info("File created successfully: %s", resource_type)
            return success_response(data=out, message="File created successfully", status_code=201).to_json_response()
        return error_response(message=out.get("error", "Create failed"), status_code=400).to_json_response()
    except Exception as e:
        logger.exception("create_file_api")
        return server_error_response(f"Error creating file: {str(e)}").to_json_response()


@login_required
@require_http_methods(["PUT", "POST"])
def update_file_api(request: HttpRequest, file_path: str) -> JsonResponse:
    """PUT/POST /docs/api/media/files/<path:file_path>/update/ body: {data, auto_sync}"""
    fp, full = _validate_file_path(file_path)
    if not fp or not full:
        return not_found_response("File").to_json_response()

    data, error_msg = _parse_json_body(request)
    if error_msg:
        logger.warning("Invalid request body in update_file_api: %s", error_msg)
        return error_response(message=error_msg, status_code=400).to_json_response()

    try:
        file_data = data.get("data", {})
        auto_sync = data.get("auto_sync", False)
        svc = MediaManagerService()
        out = svc.update_file(str(full), file_data, auto_sync=auto_sync)
        if out.get("success"):
            logger.info("File updated successfully: %s", fp)
            return success_response(data=out, message="File updated successfully").to_json_response()
        return error_response(message=out.get("error", "Update failed"), status_code=400).to_json_response()
    except Exception as e:
        logger.exception("update_file_api")
        return server_error_response(f"Error updating file: {str(e)}").to_json_response()


@login_required
@require_http_methods(["DELETE"])
def delete_file_api(request: HttpRequest, file_path: str) -> JsonResponse:
    """DELETE /docs/api/media/files/<path:file_path>/?delete_remote=true"""
    fp, full = _validate_file_path(file_path)
    if not fp or not full:
        return not_found_response("File").to_json_response()
    
    delete_remote = request.GET.get("delete_remote", "false").lower() == "true"
    try:
        svc = MediaManagerService()
        out = svc.delete_file(str(full), delete_remote=delete_remote)
        if out.get("success"):
            logger.info("File deleted successfully: %s", fp)
            return success_response(message="File deleted successfully").to_json_response()
        return error_response(message=out.get("error", "Delete failed"), status_code=400).to_json_response()
    except Exception as e:
        logger.exception("delete_file_api")
        return server_error_response(f"Error deleting file: {str(e)}").to_json_response()


@login_required
@require_http_methods(["GET"])
def sync_status_api(request: HttpRequest) -> JsonResponse:
    """GET /docs/api/media/sync-status/"""
    try:
        svc = MediaManagerService()
        summary = svc.get_sync_summary()
        return success_response(data=summary, message="Sync status retrieved successfully").to_json_response()
    except Exception as e:
        logger.exception("sync_status_api")
        return server_error_response(f"Error retrieving sync status: {str(e)}").to_json_response()


@login_required
@require_http_methods(["POST"])
def sync_file_api(request: HttpRequest, file_path: str) -> JsonResponse:
    """POST /docs/api/media/sync/<path:file_path>/ body: {direction}"""
    fp, full = _validate_file_path(file_path)
    if not fp or not full:
        return not_found_response("File").to_json_response()
    
    data, error_msg = _parse_json_body(request)
    if error_msg and request.body:  # Only error if body is provided but invalid
        logger.warning("Invalid request body in sync_file_api: %s", error_msg)
        return error_response(message=error_msg, status_code=400).to_json_response()
    
    direction = (data or {}).get("direction", "to_lambda")
    try:
        svc = MediaManagerService()
        result = svc.sync_file(str(full), direction=direction)
        if result.get("success"):
            logger.info("File synced successfully: %s (direction: %s)", fp, direction)
            return success_response(data={"sync_result": result}, message="File synced successfully").to_json_response()
        return error_response(message=result.get("error", "Sync failed"), status_code=400).to_json_response()
    except Exception as e:
        logger.exception("sync_file_api")
        return server_error_response(f"Error syncing file: {str(e)}").to_json_response()


@login_required
@require_http_methods(["POST"])
def bulk_sync_api(request: HttpRequest) -> JsonResponse:
    """POST /docs/api/media/bulk-sync/ body: {resource_type, direction, file_paths?}"""
    data, error_msg = _parse_json_body(request)
    if error_msg and request.body:
        logger.warning("Invalid request body in bulk_sync_api: %s", error_msg)
        return error_response(message=error_msg, status_code=400).to_json_response()

    try:
        data = data or {}
        resource_type = data.get("resource_type", "all")
        direction = data.get("direction", "to_lambda")
        file_paths = data.get("file_paths", [])
        sync_svc = MediaSyncService()
        results: Dict[str, Any] = {}
        types = (
            ["pages", "endpoints", "relationships", "postman"]
            if resource_type == "all"
            else [resource_type]
        )
        for rt in types:
            if direction == "to_lambda" and file_paths:
                for fpath in file_paths:
                    results[fpath] = sync_svc.sync_file_to_s3(fpath)
            else:
                results[rt] = sync_svc._sync_resource_type(rt, dry_run=False)
        logger.info("Bulk sync completed: %s files/resources", len(results))
        return success_response(data={"results": results}, message="Bulk sync completed").to_json_response()
    except Exception as e:
        logger.exception("bulk_sync_api")
        return server_error_response(f"Error performing bulk sync: {str(e)}").to_json_response()


# -----------------------------------------------------------------------------
# Index regeneration APIs
# -----------------------------------------------------------------------------


def _regenerate_index(name: str):
    from apps.documentation.services.index_generator_service import IndexGeneratorService
    gen = IndexGeneratorService()
    fn = getattr(gen, f"generate_{name}_index", None)
    if not fn:
        return {"success": False, "error": f"Unknown index: {name}"}
    return fn()


def _regenerate_response(name: str) -> JsonResponse:
    """Generate response for index regeneration."""
    out = _regenerate_index(name)
    if out.get("success"):
        logger.info("Index regenerated successfully: %s", name)
        return success_response(data=out, message=f"{name.title()} index regenerated successfully").to_json_response()
    logger.error("Failed to regenerate index: %s", name)
    return server_error_response(out.get("error", "Index regeneration failed")).to_json_response()


@login_required
@require_http_methods(["POST"])
def regenerate_pages_index_api(request: HttpRequest) -> JsonResponse:
    """POST /docs/api/media/regenerate/pages/"""
    return _regenerate_response("pages")


@login_required
@require_http_methods(["POST"])
def regenerate_endpoints_index_api(request: HttpRequest) -> JsonResponse:
    """POST /docs/api/media/regenerate/endpoints/"""
    return _regenerate_response("endpoints")


@login_required
@require_http_methods(["POST"])
def regenerate_postman_index_api(request: HttpRequest) -> JsonResponse:
    """POST /docs/api/media/regenerate/postman/"""
    return _regenerate_response("postman")


@login_required
@require_http_methods(["POST"])
def regenerate_relationships_index_api(request: HttpRequest) -> JsonResponse:
    """POST /docs/api/media/regenerate/relationships/"""
    return _regenerate_response("relationships")


@login_required
@require_http_methods(["POST"])
def regenerate_all_indexes_api(request: HttpRequest) -> JsonResponse:
    """POST /docs/api/media/regenerate/all/"""
    from apps.documentation.services.index_generator_service import IndexGeneratorService

    gen = IndexGeneratorService()
    out = gen.generate_all_indexes()
    if out.get("success"):
        logger.info("All indexes regenerated successfully")
        return success_response(data=out, message="All indexes regenerated successfully").to_json_response()
    logger.error("Failed to regenerate all indexes")
    return server_error_response(out.get("error", "Index regeneration failed")).to_json_response()


# -----------------------------------------------------------------------------
# Per-file operations: preview, analyze, validate, generate, upload
# -----------------------------------------------------------------------------


@login_required
def media_file_preview(request: HttpRequest, file_path: str) -> HttpResponse:
    """GET /docs/media/preview/<path:file_path>?download=1"""
    fp, full = _validate_file_path(file_path)
    if not fp or not full:
        raise Http404("File not found")

    if request.GET.get("download") == "1":
        return FileResponse(open(full, "rb"), as_attachment=True, filename=full.name)

    ext = full.suffix.lower()
    try:
        with open(full, "r", encoding="utf-8") as f:
            raw = f.read()
    except UnicodeDecodeError:
        return FileResponse(open(full, "rb"), as_attachment=True, filename=full.name)

    if ext == ".json":
        try:
            content = json.loads(raw)
            raw = json.dumps(content, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            pass

    context: Dict[str, Any] = {
        "file_path": fp,
        "file_name": full.name,
        "content": raw,
        "file_type": "json" if ext == ".json" else "text",
        "size": full.stat().st_size,
    }
    return render(request, "documentation/media_file_preview.html", context)


@login_required
def media_file_viewer(request: HttpRequest, file_path: str) -> HttpResponse:
    """GET /docs/media/viewer/<path:file_path> – Enhanced page detail view for JSON files."""
    fp, full = _validate_file_path(file_path)
    if not fp or not full:
        raise Http404("File not found")

    svc = MediaManagerService()
    detail = svc.get_file_detail(str(full))
    if not detail:
        raise Http404("File not found")

    content = detail.get("content")
    resource_type = detail.get("resource_type", "")
    
    # Validate tab parameter - support page, endpoint, relationship, and postman tabs
    VALID_DETAIL_TABS = frozenset({"overview", "content", "relationships", "endpoints", "components", "access", "raw"})
    VALID_POSTMAN_DETAIL_TABS = frozenset({"overview", "requests", "variables", "environments", "endpoints", "raw"})
    
    def _validate_detail_tab(tab: Optional[str], is_postman: bool = False) -> str:
        """Validate detail tab (uses shared helper)."""
        resource_type = "postman" if is_postman else "pages"
        return validate_detail_tab(tab, resource_type)

    # Generate content_json for editor/raw view
    content_json = ""
    if isinstance(content, dict):
        content_json = json.dumps(content, indent=2, ensure_ascii=False)
    elif content is not None:
        content_json = str(content)

    metadata = detail.get("metadata") or {}
    sync_status = detail.get("sync_status") or {}
    
    # Check if this is a page JSON file - if so, show page detail view
    is_page_file = resource_type == "pages" and isinstance(content, dict) and content.get("page_id")
    
    # Check if this is an endpoint JSON file - if so, show endpoint detail view
    is_endpoint_file = resource_type == "endpoints" and isinstance(content, dict) and content.get("endpoint_id")
    
    # Check if this is a relationship JSON file - if so, show relationship detail view
    # Relationship files can be in two formats:
    # 1. By-page format: {"page_path": "...", "endpoints": [...]}
    # 2. By-endpoint format: {"endpoint_path": "...", "method": "...", "pages": [...]}
    # 3. Individual relationship: {"relationship_id": "...", "page_id": "...", "endpoint_id": "..."}
    is_relationship_file = (
        resource_type == "relationships" and isinstance(content, dict) and (
            content.get("relationship_id") or 
            (content.get("page_path") and content.get("endpoints")) or
            (content.get("endpoint_path") and content.get("pages"))
        )
    )
    
    # Check if this is a Postman collection JSON file - if so, show Postman detail view
    # Postman collections have info.name and info.schema matching Postman schema URL
    is_postman_file = (
        (resource_type == "postman" or "postman" in file_path.lower()) and 
        isinstance(content, dict) and 
        content.get("info") and 
        isinstance(content.get("info"), dict) and
        content.get("info", {}).get("name") and
        (
            content.get("info", {}).get("schema", "").startswith("https://schema.getpostman.com/json/collection/") or
            content.get("item") is not None  # item array is required for Postman collections
        )
    )
    
    # Determine active tab based on file type
    active_tab = _validate_detail_tab(request.GET.get("tab"), is_postman_file)
    
    # Base context for all file types
    context: Dict[str, Any] = {
        "file_path": fp,
        "file_name": full.name,
        "detail": detail,
        "content_json": content_json,
        "metadata": metadata,
        "sync_status": sync_status,
        "resource_type": resource_type,
        "s3_key": detail.get("s3_key"),
        "relative_path": detail.get("relative_path", fp),
        "is_page_file": is_page_file,
        "is_endpoint_file": is_endpoint_file,
        "is_relationship_file": is_relationship_file,
        "is_postman_file": is_postman_file,
    }
    
    # If it's an endpoint file, enhance context with endpoint detail data
    if is_endpoint_file:
        try:
            # Parse endpoint structure from content
            endpoint = content  # content is already the parsed endpoint dict
            
            # Generate endpoint JSON string
            endpoint_json = json.dumps(endpoint, indent=2, default=str)
            
            # Extract endpoint ID and path for relationship fetching
            endpoint_id = endpoint.get("endpoint_id")
            endpoint_path = endpoint.get("endpoint_path") or endpoint_id
            
            # Fetch relationships for this endpoint
            endpoint_relationships: List[Dict[str, Any]] = []
            try:
                if endpoint_path:
                    rel_result = relationships_service.list_relationships(endpoint_id=endpoint_path, limit=100)
                    endpoint_relationships = list(rel_result.get("relationships", []))
            except Exception as e:
                logger.warning("Failed to load relationships for endpoint %s: %s", endpoint_id, e)
            
            # Fetch pages using this endpoint
            pages_using_endpoint: List[Dict[str, Any]] = []
            if endpoint.get("used_by_pages"):
                pages_using_endpoint = endpoint["used_by_pages"]
            else:
                # Try to find pages that use this endpoint
                try:
                    all_pages = pages_service.list_pages(limit=1000)
                    for page in all_pages.get("pages", []):
                        uses_endpoints = page.get("metadata", {}).get("uses_endpoints", [])
                        for ep_ref in uses_endpoints:
                            ep_id = ep_ref.get("endpoint_id") or ep_ref.get("endpoint_path")
                            if ep_id == endpoint_id or ep_id == endpoint_path:
                                pages_using_endpoint.append({
                                    "page_id": page.get("page_id"),
                                    "page_path": page.get("metadata", {}).get("route") or page.get("route"),
                                    "page_title": page.get("metadata", {}).get("content_sections", {}).get("title"),
                                    "usage_context": ep_ref.get("usage_context"),
                                    "via_service": ep_ref.get("via_service"),
                                    "via_hook": ep_ref.get("via_hook"),
                                    "usage_type": ep_ref.get("usage_type"),
                                })
                except Exception as e:
                    logger.debug("Could not load pages using endpoint %s: %s", endpoint_id, e)
            
            # Format usage_context for display
            for page_usage in pages_using_endpoint:
                if page_usage.get("usage_context"):
                    page_usage["usage_context_display"] = page_usage["usage_context"].replace("_", " ").title()
            
            # Update tab validation for endpoint tabs
            VALID_ENDPOINT_TABS = frozenset({"overview", "request", "response", "graphql", "relationships", "lambda-services", "files", "methods", "access", "raw"})
            def _validate_endpoint_tab(tab: Optional[str]) -> str:
                """Validate and normalize tab query parameter for endpoint detail view."""
                if not tab or tab not in VALID_ENDPOINT_TABS:
                    return "overview"
                return tab
            
            endpoint_active_tab = _validate_endpoint_tab(request.GET.get("tab"))
            
            # Add endpoint-specific context
            context.update({
                "endpoint": endpoint,
                "endpoint_json": endpoint_json,
                "active_tab": endpoint_active_tab,
                "endpoint_relationships": endpoint_relationships,
                "relationships_count": len(endpoint_relationships),
                "pages_using_endpoint": pages_using_endpoint,
                "pages_count": len(pages_using_endpoint),
            })
        except Exception as e:
            logger.error("Error processing endpoint data for file %s: %s", file_path, e, exc_info=True)
            # Continue with basic context if endpoint processing fails
    
    # If it's a relationship file, enhance context with relationship detail data
    elif is_relationship_file:
        try:
            # Parse relationship structure from content
            # Handle different relationship file formats
            relationship = None
            relationship_json = ""
            
            # Check if it's an individual relationship (has relationship_id)
            if content.get("relationship_id"):
                relationship = content
            # Check if it's a by-page format (has page_path and endpoints array)
            elif content.get("page_path") and content.get("endpoints"):
                # Convert by-page format to individual relationship format
                # Use the first endpoint in the array as the primary relationship
                endpoints = content.get("endpoints", [])
                if endpoints:
                    first_endpoint = endpoints[0]
                    page_path = content.get("page_path", "")
                    endpoint_path = first_endpoint.get("endpoint_path", "")
                    method = first_endpoint.get("method", "QUERY")
                    relationship = {
                        "relationship_id": generate_relationship_id(page_path, endpoint_path, method),
                        "page_path": page_path,
                        "page_id": page_path,
                        "endpoint_path": endpoint_path,
                        "endpoint_id": endpoint_path,
                        "method": method,
                        "api_version": first_endpoint.get("api_version", "v1"),
                        "usage_type": first_endpoint.get("usage_type", "primary"),
                        "usage_context": first_endpoint.get("usage_context", ""),
                        "via_service": first_endpoint.get("via_service", ""),
                        "via_hook": first_endpoint.get("via_hook"),
                        "description": first_endpoint.get("description"),
                        "created_at": content.get("created_at"),
                        "updated_at": first_endpoint.get("updated_at") or content.get("updated_at"),
                    }
            # Check if it's a by-endpoint format (has endpoint_path and pages array)
            elif content.get("endpoint_path") and content.get("pages"):
                # Convert by-endpoint format to individual relationship format
                # Use the first page in the array as the primary relationship
                pages = content.get("pages", [])
                if pages:
                    first_page = pages[0]
                    page_path = first_page.get("page_path", "")
                    endpoint_path = content.get("endpoint_path", "")
                    method = content.get("method", "QUERY")
                    relationship = {
                        "relationship_id": generate_relationship_id(page_path, endpoint_path, method),
                        "page_path": page_path,
                        "page_id": page_path,
                        "endpoint_path": endpoint_path,
                        "endpoint_id": endpoint_path,
                        "method": method,
                        "api_version": content.get("api_version", "v1"),
                        "usage_type": first_page.get("usage_type", "primary"),
                        "usage_context": first_page.get("usage_context", ""),
                        "via_service": first_page.get("via_service", ""),
                        "via_hook": first_page.get("via_hook"),
                        "description": first_page.get("description"),
                        "created_at": content.get("created_at"),
                        "updated_at": first_page.get("updated_at") or content.get("updated_at"),
                    }
            
            if relationship:
                # Generate relationship JSON string
                relationship_json = json.dumps(relationship, indent=2, default=str)
                
                # Extract IDs for fetching linked entities
                page_id = relationship.get("page_id") or relationship.get("page_path")
                endpoint_id = relationship.get("endpoint_id") or relationship.get("endpoint_path")
                
                # Fetch linked page details
                linked_page = None
                if page_id:
                    try:
                        linked_page = pages_service.get_page(page_id)
                    except Exception as e:
                        logger.debug("Could not load page %s for relationship: %s", page_id, e)
                
                # Fetch linked endpoint details
                linked_endpoint = None
                if endpoint_id:
                    try:
                        linked_endpoint = endpoints_service.get_endpoint(endpoint_id)
                    except Exception as e:
                        logger.debug("Could not load endpoint %s for relationship: %s", endpoint_id, e)
                
                # Fetch related relationships (same page or endpoint)
                related_relationships: List[Dict[str, Any]] = []
                try:
                    # Get relationships for the same page
                    if page_id:
                        page_rels_result = relationships_service.list_relationships(page_id=page_id, limit=100)
                        for rel in page_rels_result.get("relationships", []):
                            rel_id = rel.get("relationship_id")
                            if rel_id and rel_id != relationship.get("relationship_id"):
                                related_relationships.append(rel)
                    
                    # Get relationships for the same endpoint
                    if endpoint_id:
                        endpoint_rels_result = relationships_service.list_relationships(endpoint_id=endpoint_id, limit=100)
                        for rel in endpoint_rels_result.get("relationships", []):
                            rel_id = rel.get("relationship_id")
                            if rel_id and rel_id != relationship.get("relationship_id"):
                                # Avoid duplicates
                                if not any(r.get("relationship_id") == rel_id for r in related_relationships):
                                    related_relationships.append(rel)
                except Exception as e:
                    logger.warning("Failed to load related relationships: %s", e)
                
                # Format usage_context for display
                if relationship.get("usage_context"):
                    relationship["usage_context_display"] = relationship["usage_context"].replace("_", " ").title()
                
                # Update tab validation for relationship tabs
                VALID_RELATIONSHIP_TABS = frozenset({"overview", "page", "endpoint", "usage", "related", "raw"})
                def _validate_relationship_tab(tab: Optional[str]) -> str:
                    """Validate and normalize tab query parameter for relationship detail view."""
                    if not tab or tab not in VALID_RELATIONSHIP_TABS:
                        return "overview"
                    return tab
                
                relationship_active_tab = _validate_relationship_tab(request.GET.get("tab"))
                
                # Add relationship-specific context
                context.update({
                    "relationship": relationship,
                    "relationship_json": relationship_json,
                    "active_tab": relationship_active_tab,
                    "linked_page": linked_page,
                    "linked_endpoint": linked_endpoint,
                    "related_relationships": related_relationships,
                    "related_count": len(related_relationships),
                })
        except Exception as e:
            logger.error("Error processing relationship data for file %s: %s", file_path, e, exc_info=True)
            # Continue with basic context if relationship processing fails
    
    # If it's a Postman collection file, enhance context with Postman detail data
    elif is_postman_file:
        try:
            # Parse Postman collection structure from content
            collection = content  # content is already the parsed collection dict
            
            # Extract collection info
            collection_info = collection.get("info", {})
            postman_id = collection_info.get("_postman_id") or collection_info.get("name") or file_path.split("/")[-1].replace(".postman_collection.json", "").replace(".json", "")
            
            # Extract variables
            variables = list(collection.get("variable", []))
            
            # Extract requests by flattening items recursively
            requests = []
            items = collection.get("item", [])
            
            def extract_requests(items_list, folder_path=''):
                """Recursively extract requests from items array."""
                for item in items_list:
                    if 'request' in item:
                        # This is a request
                        request_data = item.get('request', {})
                        url_data = request_data.get('url', {})
                        if isinstance(url_data, dict):
                            url = url_data.get('raw', '')
                        else:
                            url = url_data
                        
                        requests.append({
                            'name': item.get('name', 'Unnamed Request'),
                            'method': request_data.get('method', 'GET'),
                            'url': url,
                            'description': item.get('description', ''),
                            'folder': folder_path,
                            'headers': request_data.get('header', []),
                            'body': request_data.get('body', {}),
                        })
                    elif 'item' in item:
                        # This is a folder
                        folder_name = item.get('name', '')
                        new_folder_path = f"{folder_path}/{folder_name}" if folder_path else folder_name
                        extract_requests(item.get('item', []), new_folder_path)
            
            extract_requests(items)
            
            # Try to fetch environments and endpoint mappings (may not be available for media files)
            environments = []
            endpoint_mappings = []
            related_endpoints = []
            
            try:
                environments = postman_service.get_environments(postman_id)
            except Exception as e:
                logger.debug("Could not load environments for Postman collection %s: %s", postman_id, e)
            
            try:
                endpoint_mappings = postman_service.get_endpoint_mappings(postman_id)
                # Get related endpoints if mappings exist
                if endpoint_mappings:
                    for mapping in endpoint_mappings:
                        endpoint_id = mapping.get('endpoint_id')
                        if endpoint_id:
                            try:
                                endpoint = endpoints_service.get_endpoint(endpoint_id)
                                if endpoint:
                                    related_endpoints.append(endpoint)
                            except Exception as e:
                                logger.debug("Could not load endpoint %s: %s", endpoint_id, e)
            except Exception as e:
                logger.debug("Could not load endpoint mappings for Postman collection %s: %s", postman_id, e)
            
            # Generate Postman JSON string
            postman_json = json.dumps(collection, indent=2, default=str)
            
            # Update tab validation for Postman tabs
            VALID_POSTMAN_DETAIL_TABS = frozenset({"overview", "requests", "variables", "environments", "endpoints", "raw"})
            def _validate_postman_tab(tab: Optional[str]) -> str:
                """Validate and normalize tab query parameter for Postman detail view."""
                if not tab or tab not in VALID_POSTMAN_DETAIL_TABS:
                    return "overview"
                return tab
            
            postman_active_tab = _validate_postman_tab(request.GET.get("tab"))
            
            # Add Postman-specific context
            context.update({
                "collection": collection,
                "collection_info": collection_info,
                "postman_id": postman_id,
                "postman_json": postman_json,
                "active_tab": postman_active_tab,
                "variables": variables,
                "variables_count": len(variables),
                "requests": requests,
                "requests_count": len(requests),
                "environments": environments,
                "environments_count": len(environments),
                "endpoint_mappings": endpoint_mappings,
                "mappings_count": len(endpoint_mappings),
                "related_endpoints": related_endpoints,
                "endpoints_count": len(related_endpoints),
            })
        except Exception as e:
            logger.error("Error processing Postman collection data for file %s: %s", file_path, e, exc_info=True)
            # Continue with basic context if Postman processing fails
    
    # If it's a page file, enhance context with page detail data
    elif is_page_file:
        try:
            # Parse page structure from content
            page = content  # content is already the parsed page dict
            
            # Extract page content and convert to HTML if markdown
            page_content = page.get("content", "")
            page_html = ""
            if page_content:
                try:
                    page_html = markdown.markdown(page_content, extensions=["fenced_code", "tables"])
                except Exception:
                    page_html = ""
            
            # Generate page JSON string
            page_json = json.dumps(page, indent=2, default=str)
            
            # Extract page route for relationship fetching
            page_route = page.get("metadata", {}).get("route") or page.get("route")
            page_id = page.get("page_id")
            page_path = page_route or page_id
            
            # Fetch relationships
            page_relationships: List[Dict[str, Any]] = []
            try:
                if page_id:
                    rel_result = relationships_service.list_relationships(page_id=page_id, limit=100)
                    page_relationships = list(rel_result.get("relationships", []))
                    if page_path and page_path != page_id:
                        by_path = relationships_service.list_relationships(page_id=page_path, limit=100)
                        existing_ids = {r.get("relationship_id") for r in page_relationships}
                        for r in by_path.get("relationships", []):
                            if r.get("relationship_id") not in existing_ids:
                                page_relationships.append(r)
            except Exception as e:
                logger.warning("Failed to load relationships for page %s: %s", page_id, e)
            
            # Fetch endpoints
            endpoints_used: List[Dict[str, Any]] = []
            uses = page.get("metadata", {}).get("uses_endpoints")
            if uses:
                ids = [
                    r.get("endpoint_id") or r.get("endpoint_path")
                    for r in uses
                    if r.get("endpoint_id") or r.get("endpoint_path")
                ]
                bulk = endpoints_service.get_endpoints_bulk(ids) if ids else {}
                for ref in uses:
                    eid = ref.get("endpoint_id") or ref.get("endpoint_path")
                    if not eid:
                        continue
                    ep = bulk.get(eid)
                    if ep:
                        ep = dict(ep)
                        ep["usage_context"] = ref.get("usage_context")
                        ep["via_service"] = ref.get("via_service")
                        ep["via_hook"] = ref.get("via_hook")
                        ep["usage_type"] = ref.get("usage_type")
                        endpoints_used.append(ep)
                    else:
                        endpoints_used.append(ref)
            
            # Group relationships by type
            relationships_by_type: Dict[str, List[Dict[str, Any]]] = {
                "primary": [],
                "secondary": [],
                "conditional": [],
                "other": [],
            }
            for rel in page_relationships:
                ut = (rel.get("usage_type") or "other").lower()
                if ut in relationships_by_type:
                    relationships_by_type[ut].append(rel)
                else:
                    relationships_by_type["other"].append(rel)
            
            # Add page-specific context
            context.update({
                "page": page,
                "page_html": page_html,
                "page_json": page_json,
                "active_tab": active_tab,
                "page_relationships": page_relationships,
                "relationships_by_type": relationships_by_type,
                "relationships_count": len(page_relationships),
                "endpoints_used": endpoints_used,
                "endpoints_count": len(endpoints_used),
            })
        except Exception as e:
            logger.error("Error processing page data for file %s: %s", file_path, e, exc_info=True)
            # Continue with basic context if page processing fails

    return render(request, "documentation/media_file_viewer.html", context)


def _resolve_relative_path(file_path: str) -> Tuple[Optional[str], Optional[Path]]:
    """Validate and resolve relative file_path under media. Returns (fp, full) or (None, None)."""
    return _validate_file_path(file_path)


@login_required
@require_http_methods(["GET", "POST"])
def media_file_form(request, file_path: str = None):
    """GET/POST /docs/media/form/create/ or /docs/media/form/edit/<path:file_path>/"""
    svc = MediaManagerService()
    is_edit = file_path is not None
    
    # Validate tab parameter - support page, endpoint, relationship, and postman tabs
    VALID_PAGE_FORM_TABS = frozenset({"basic", "metadata", "content", "endpoints", "components", "access-control", "sections", "advanced"})
    VALID_ENDPOINT_FORM_TABS = frozenset({"basic", "request", "response", "graphql", "lambda-services", "files", "methods", "access-control", "advanced", "raw"})
    VALID_RELATIONSHIP_FORM_TABS = frozenset({"basic", "connection", "usage", "advanced"})
    VALID_POSTMAN_FORM_TABS = frozenset({"basic", "settings", "variables", "advanced"})
    
    def _validate_form_tab(tab: Optional[str], is_endpoint: bool = False, is_relationship: bool = False, is_postman: bool = False) -> str:
        """Validate and normalize tab query parameter for form view."""
        if is_postman:
            valid_tabs = VALID_POSTMAN_FORM_TABS
        elif is_relationship:
            valid_tabs = VALID_RELATIONSHIP_FORM_TABS
        elif is_endpoint:
            valid_tabs = VALID_ENDPOINT_FORM_TABS
        else:
            valid_tabs = VALID_PAGE_FORM_TABS
        if not tab or tab not in valid_tabs:
            return "basic"
        return tab

    if request.method == "GET":
        file_data = None
        fp = relative_path = None
        page = None
        endpoint = None
        relationship = None
        collection = None
        collection_info = {}
        is_page_file = False
        is_endpoint_file = False
        is_relationship_file = False
        is_postman_file = False
        available_endpoints: List[Dict[str, Any]] = []
        
        if is_edit:
            fp, full = _resolve_relative_path(file_path)
            if not fp:
                raise Http404("File not found")
            detail = svc.get_file_detail(str(full))
            if not detail:
                raise Http404("File not found")
            content = detail.get("content") or {}
            resource_type = detail.get("resource_type", "")
            
            # Check if this is a page JSON file
            is_page_file = resource_type == "pages" and isinstance(content, dict) and content.get("page_id")
            
            # Check if this is an endpoint JSON file
            is_endpoint_file = resource_type == "endpoints" and isinstance(content, dict) and content.get("endpoint_id")
            
            # Check if this is a relationship JSON file
            is_relationship_file = (
                resource_type == "relationships" and isinstance(content, dict) and (
                    content.get("relationship_id") or 
                    (content.get("page_path") and content.get("endpoints")) or
                    (content.get("endpoint_path") and content.get("pages"))
                )
            )
            
            # Check if this is a Postman collection JSON file
            is_postman_file = (
                (resource_type == "postman" or "postman" in file_path.lower()) and 
                isinstance(content, dict) and 
                content.get("info") and 
                isinstance(content.get("info"), dict) and
                content.get("info", {}).get("name") and
                (
                    content.get("info", {}).get("schema", "").startswith("https://schema.getpostman.com/json/collection/") or
                    content.get("item") is not None
                )
            )
            
            if is_page_file:
                # Parse page structure
                page = content
                # Fetch available endpoints for endpoints tab
                try:
                    ep_result = endpoints_service.list_endpoints(limit=100)
                    available_endpoints = ep_result.get("endpoints", [])
                except Exception as e:
                    logger.warning("Failed to load endpoints for form: %s", e)
            elif is_endpoint_file:
                # Parse endpoint structure
                endpoint = content
            elif is_postman_file:
                # Parse Postman collection structure
                collection = content
                collection_info = dict(collection.get("info", {}))
                # Add postman_id key for template access (maps from _postman_id)
                if "_postman_id" in collection_info:
                    collection_info["postman_id"] = collection_info["_postman_id"]
                # Extract variables for template
                variables = list(collection.get("variable", []))
            elif is_relationship_file:
                # Normalize relationship structure for the form view
                # Relationship files can be in three formats:
                # 1. Individual relationship: {"relationship_id": "...", "page_id": "...", "endpoint_id": "...", ...}
                # 2. By-page format: {"page_path": "...", "endpoints": [...]}
                # 3. By-endpoint format: {"endpoint_path": "...", "method": "...", "pages": [...]}
                relationship = None
                
                # Case 1: already an individual relationship
                if content.get("relationship_id"):
                    relationship = content
                # Case 2: by-page format – convert first endpoint entry to individual relationship
                elif content.get("page_path") and content.get("endpoints"):
                    endpoints = content.get("endpoints", [])
                    if endpoints:
                        first_endpoint = endpoints[0]
                        page_path = content.get("page_path", "")
                        endpoint_path = first_endpoint.get("endpoint_path", "")
                        method = first_endpoint.get("method", "QUERY")
                        relationship = {
                            "relationship_id": generate_relationship_id(page_path, endpoint_path, method),
                            "page_path": page_path,
                            "page_id": page_path,
                            "endpoint_path": endpoint_path,
                            "endpoint_id": endpoint_path,
                            "method": method,
                            "api_version": first_endpoint.get("api_version", "v1"),
                            "usage_type": first_endpoint.get("usage_type", "primary"),
                            "usage_context": first_endpoint.get("usage_context", ""),
                            "via_service": first_endpoint.get("via_service", ""),
                            "via_hook": first_endpoint.get("via_hook"),
                            "description": first_endpoint.get("description"),
                            "created_at": content.get("created_at"),
                            "updated_at": first_endpoint.get("updated_at") or content.get("updated_at"),
                        }
                # Case 3: by-endpoint format – convert first page entry to individual relationship
                elif content.get("endpoint_path") and content.get("pages"):
                    pages = content.get("pages", [])
                    if pages:
                        first_page = pages[0]
                        page_path = first_page.get("page_path", "")
                        endpoint_path = content.get("endpoint_path", "")
                        method = content.get("method", "QUERY")
                        relationship = {
                            "relationship_id": generate_relationship_id(page_path, endpoint_path, method),
                            "page_path": page_path,
                            "page_id": page_path,
                            "endpoint_path": endpoint_path,
                            "endpoint_id": endpoint_path,
                            "method": method,
                            "api_version": content.get("api_version", "v1"),
                            "usage_type": first_page.get("usage_type", "primary"),
                            "usage_context": first_page.get("usage_context", ""),
                            "via_service": first_page.get("via_service", ""),
                            "via_hook": first_page.get("via_hook"),
                            "description": first_page.get("description"),
                            "created_at": content.get("created_at"),
                            "updated_at": first_page.get("updated_at") or content.get("updated_at"),
                        }
                # Fallback: if normalization failed, keep original content so raw JSON editor still works
                if not relationship:
                    relationship = content
            
            file_data = {
                "resource_type": resource_type,
                "content": json.dumps(content, indent=2, ensure_ascii=False),
                "content_dict": content,
            }
            relative_path = detail.get("relative_path", fp)
        else:
            file_data = {"resource_type": "pages", "content": '{\n  "": ""\n}', "content_dict": {}}
            # For new page files, fetch endpoints
            try:
                ep_result = endpoints_service.list_endpoints(limit=100)
                available_endpoints = ep_result.get("endpoints", [])
            except Exception as e:
                logger.warning("Failed to load endpoints for form: %s", e)

        # Determine active tab based on file type
        active_tab = _validate_form_tab(request.GET.get("tab"), is_endpoint_file, is_relationship_file, is_postman_file)
        
        page_json = json.dumps(page, indent=2, default=str) if page else "{}"
        endpoint_json = json.dumps(endpoint, indent=2, default=str) if endpoint else "{}"
        relationship_json = json.dumps(relationship, indent=2, default=str) if relationship else "{}"
        collection_json = json.dumps(collection, indent=2, default=str) if collection else "{}"
        
        # Extract variables for Postman collections
        variables: List[Dict[str, Any]] = []
        if collection and isinstance(collection, dict):
            variables = list(collection.get("variable", []))
        
        context = {
            "file_data": file_data,
            "file_path": file_path,
            "relative_path": relative_path,
            "is_edit": is_edit,
            "error_message": None,
            "is_page_file": is_page_file,
            "is_endpoint_file": is_endpoint_file,
            "is_relationship_file": is_relationship_file,
            "is_postman_file": is_postman_file,
            "page": page,
            "endpoint": endpoint,
            "relationship": relationship,
            "collection": collection,
            "collection_info": collection_info,
            "variables": variables,
            "variables_count": len(variables),
            "page_json": page_json,
            "endpoint_json": endpoint_json,
            "relationship_json": relationship_json,
            "collection_json": collection_json,
            "active_tab": active_tab,
            "available_endpoints": available_endpoints,
        }
        return render(request, "documentation/media/file_form.html", context)

    # POST
    resource_type = (request.POST.get("resource_type") or "").strip()
    file_id = (request.POST.get("file_id") or "").strip()
    content_str = (request.POST.get("content") or "").strip()
    auto_sync = request.POST.get("auto_sync") == "on"
    
    # Check if this is a page file form submission
    page_data_raw = request.POST.get("page_data")
    is_page_form_submission = resource_type == "pages" and (page_data_raw or request.POST.get("page_id"))
    
    # Check if this is an endpoint file form submission
    endpoint_data_raw = request.POST.get("endpoint_data")
    is_endpoint_form_submission = resource_type == "endpoints" and (endpoint_data_raw or request.POST.get("endpoint_id"))
    
    # Check if this is a relationship file form submission
    relationship_data_raw = request.POST.get("relationship_data")
    is_relationship_form_submission = resource_type == "relationships" and (relationship_data_raw or request.POST.get("relationship_id"))
    
    # Check if this is a Postman collection file form submission
    postman_data_raw = request.POST.get("postman_data") or request.POST.get("collection_data")
    is_postman_form_submission = (
        (resource_type == "postman" or "postman" in (file_path or "").lower()) and 
        (postman_data_raw or request.POST.get("collection_name") or request.POST.get("collection_id"))
    )
    
    if is_endpoint_form_submission and endpoint_data_raw:
        # Use JSON from endpoint_data hidden field (from enhanced form)
        try:
            data = json.loads(endpoint_data_raw)
        except json.JSONDecodeError as e:
            # Load existing endpoint if editing
            endpoint = None
            if is_edit and file_path:
                try:
                    fp, full = _resolve_relative_path(file_path)
                    if fp:
                        detail = svc.get_file_detail(str(full))
                        if detail:
                            content = detail.get("content") or {}
                            if isinstance(content, dict) and content.get("endpoint_id"):
                                endpoint = content
                except Exception:
                    pass
            
            context = {
                "file_data": {"resource_type": resource_type, "content": content_str, "content_dict": {}},
                "file_path": file_path,
                "relative_path": file_path if is_edit else None,
                "is_edit": is_edit,
                "error_message": f"Invalid form data format: {e}",
                "is_endpoint_file": True,
                "endpoint": endpoint,
                "endpoint_json": json.dumps(endpoint, indent=2, default=str) if endpoint else "{}",
                "active_tab": request.GET.get("tab", "basic"),
                "available_endpoints": [],
            }
            return render(request, "documentation/media/file_form.html", context)
    elif is_endpoint_form_submission:
        # Collect form data from individual fields (fallback)
        data = {
            "endpoint_id": request.POST.get("endpoint_id") or (file_path.split("/")[-1].replace(".json", "") if file_path else file_id),
            "endpoint_path": request.POST.get("endpoint_path", ""),
            "method": request.POST.get("method", "QUERY"),
            "api_version": request.POST.get("api_version", "v1"),
            "description": request.POST.get("description", ""),
            "endpoint_state": request.POST.get("endpoint_state", "development"),
        }
        # Collect additional fields
        if request.POST.get("request_body"):
            data["request_body"] = request.POST.get("request_body")
        if request.POST.get("response_schema"):
            data["response_schema"] = request.POST.get("response_schema")
        if request.POST.get("graphql_operation"):
            data["graphql_operation"] = request.POST.get("graphql_operation")
        if request.POST.get("authentication"):
            data["authentication"] = request.POST.get("authentication")
        if request.POST.get("authorization"):
            data["authorization"] = request.POST.get("authorization")
        if request.POST.get("rate_limit"):
            data["rate_limit"] = request.POST.get("rate_limit")
    elif is_page_form_submission and page_data_raw:
        # Use JSON from page_data hidden field (from enhanced form)
        try:
            data = json.loads(page_data_raw)
        except json.JSONDecodeError as e:
            context = {
                "file_data": {"resource_type": resource_type, "content": content_str, "content_dict": {}},
                "file_path": file_path,
                "relative_path": file_path if is_edit else None,
                "is_edit": is_edit,
                "error_message": f"Invalid form data format: {e}",
                "is_page_file": True,
                "page": None,
                "page_json": "{}",
                "active_tab": request.GET.get("tab", "basic"),
                "available_endpoints": [],
            }
            return render(request, "documentation/media/file_form.html", context)
    elif is_postman_form_submission and postman_data_raw:
        # Use JSON from postman_data/collection_data hidden field (from enhanced form)
        try:
            data = json.loads(postman_data_raw)
        except json.JSONDecodeError as e:
            # Load existing Postman collection if editing
            collection = None
            collection_info = {}
            if is_edit and file_path:
                try:
                    fp, full = _resolve_relative_path(file_path)
                    if fp:
                        detail = svc.get_file_detail(str(full))
                        if detail:
                            content = detail.get("content") or {}
                            if isinstance(content, dict) and content.get("info") and content.get("info", {}).get("name"):
                                collection = content
                                collection_info = dict(collection.get("info", {}))
                except Exception:
                    pass
            
            context = {
                "file_data": {"resource_type": resource_type, "content": content_str, "content_dict": {}},
                "file_path": file_path,
                "relative_path": file_path if is_edit else None,
                "is_edit": is_edit,
                "error_message": f"Invalid form data format: {e}",
                "is_postman_file": True,
                "collection": collection,
                "collection_info": collection_info,
                "collection_json": json.dumps(collection, indent=2, default=str) if collection else "{}",
                "variables": list(collection.get("variable", [])) if collection else [],
                "variables_count": len(collection.get("variable", [])) if collection else 0,
                "active_tab": request.GET.get("tab", "basic"),
                "available_endpoints": [],
            }
            return render(request, "documentation/media/file_form.html", context)
    elif is_postman_form_submission:
        # Collect form data from individual fields (fallback)
        # Build Postman collection structure
        info_data: Dict[str, Any] = {
            "name": request.POST.get("collection_name", ""),
            "description": request.POST.get("collection_description", ""),
            "schema": request.POST.get(
                "collection_schema",
                "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            ),
        }
        
        # Get collection ID
        collection_id = request.POST.get("collection_id") or (file_path.split("/")[-1].replace(".postman_collection.json", "").replace(".json", "") if file_path else file_id)
        if collection_id:
            info_data["_postman_id"] = collection_id
        
        # Build collection data structure
        data = {
            "info": info_data,
            "item": collection.get("item", []) if collection else [],  # Preserve existing items
            "variable": [],  # Will be populated from variables form if needed
        }
        
        # Add variables if provided
        variables_json = request.POST.get("variables_json")
        if variables_json:
            try:
                data["variable"] = json.loads(variables_json)
            except json.JSONDecodeError:
                pass
        
        # Preserve existing auth, event if editing
        if collection:
            if collection.get("auth"):
                data["auth"] = collection.get("auth")
            if collection.get("event"):
                data["event"] = collection.get("event")
    elif is_relationship_form_submission and relationship_data_raw:
        # Use JSON from relationship_data hidden field (from enhanced form)
        try:
            data = json.loads(relationship_data_raw)
        except json.JSONDecodeError as e:
            # Load existing relationship if editing
            relationship = None
            if is_edit and file_path:
                try:
                    fp, full = _resolve_relative_path(file_path)
                    if fp:
                        detail = svc.get_file_detail(str(full))
                        if detail:
                            content = detail.get("content") or {}
                            if isinstance(content, dict) and (
                                content.get("relationship_id") or 
                                (content.get("page_path") and content.get("endpoints")) or
                                (content.get("endpoint_path") and content.get("pages"))
                            ):
                                relationship = content
                except Exception:
                    pass
            
            context = {
                "file_data": {"resource_type": resource_type, "content": content_str, "content_dict": {}},
                "file_path": file_path,
                "relative_path": file_path if is_edit else None,
                "is_edit": is_edit,
                "error_message": f"Invalid form data format: {e}",
                "is_relationship_file": True,
                "relationship": relationship,
                "relationship_json": json.dumps(relationship, indent=2, default=str) if relationship else "{}",
                "active_tab": request.GET.get("tab", "basic"),
                "available_endpoints": [],
            }
            return render(request, "documentation/media/file_form.html", context)
    elif is_relationship_form_submission:
        # Collect form data from individual fields (fallback)
        page_id = request.POST.get("page_id") or request.POST.get("page_path", "")
        endpoint_id = request.POST.get("endpoint_id") or request.POST.get("endpoint_path", "")
        method = request.POST.get("method", "QUERY")
        
        # Generate relationship_id if not provided
        relationship_id = request.POST.get("relationship_id", "")
        if not relationship_id and page_id and endpoint_id:
            relationship_id = generate_relationship_id(page_id, endpoint_id, method)
        
        data = {
            "relationship_id": relationship_id,
            "page_id": page_id,
            "page_path": request.POST.get("page_path", page_id),
            "endpoint_id": endpoint_id,
            "endpoint_path": request.POST.get("endpoint_path", endpoint_id),
            "method": method,
            "api_version": request.POST.get("api_version", "v1"),
            "usage_type": request.POST.get("usage_type", "primary"),
            "usage_context": request.POST.get("usage_context", ""),
            "via_service": request.POST.get("via_service", ""),
            "via_hook": request.POST.get("via_hook", ""),
            "description": request.POST.get("description", ""),
            "state": request.POST.get("state", "draft"),
            "relationship_type": request.POST.get("relationship_type", ""),
        }
    elif is_postman_form_submission and postman_data_raw:
        # Use JSON from postman_data/collection_data hidden field (from enhanced form)
        try:
            data = json.loads(postman_data_raw)
        except json.JSONDecodeError as e:
            # Load existing Postman collection if editing
            collection = None
            collection_info = {}
            if is_edit and file_path:
                try:
                    fp, full = _resolve_relative_path(file_path)
                    if fp:
                        detail = svc.get_file_detail(str(full))
                        if detail:
                            content = detail.get("content") or {}
                            if isinstance(content, dict) and content.get("info") and content.get("info", {}).get("name"):
                                collection = content
                                collection_info = dict(collection.get("info", {}))
                except Exception:
                    pass
            
            context = {
                "file_data": {"resource_type": resource_type, "content": content_str, "content_dict": {}},
                "file_path": file_path,
                "relative_path": file_path if is_edit else None,
                "is_edit": is_edit,
                "error_message": f"Invalid form data format: {e}",
                "is_postman_file": True,
                "collection": collection,
                "collection_info": collection_info,
                "collection_json": json.dumps(collection, indent=2, default=str) if collection else "{}",
                "variables": list(collection.get("variable", [])) if collection else [],
                "variables_count": len(collection.get("variable", [])) if collection else 0,
                "active_tab": request.GET.get("tab", "basic"),
                "available_endpoints": [],
            }
            return render(request, "documentation/media/file_form.html", context)
    elif is_postman_form_submission:
        # Collect form data from individual fields (fallback)
        # Build Postman collection structure
        info_data: Dict[str, Any] = {
            "name": request.POST.get("collection_name", ""),
            "description": request.POST.get("collection_description", ""),
            "schema": request.POST.get(
                "collection_schema",
                "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            ),
        }
        
        # Get collection ID from file path or form field
        collection_id = request.POST.get("collection_id") or (file_path.split("/")[-1].replace(".postman_collection.json", "").replace(".json", "") if file_path else file_id)
        if collection_id:
            info_data["_postman_id"] = collection_id
        
        # Load existing collection to preserve items, auth, event
        existing_collection = None
        if is_edit and file_path:
            try:
                fp, full = _resolve_relative_path(file_path)
                if fp:
                    detail = svc.get_file_detail(str(full))
                    if detail:
                        existing_content = detail.get("content") or {}
                        if isinstance(existing_content, dict) and existing_content.get("info"):
                            existing_collection = existing_content
            except Exception:
                pass
        
        # Build collection data structure
        data = {
            "info": info_data,
            "item": existing_collection.get("item", []) if existing_collection else [],  # Preserve existing items
            "variable": existing_collection.get("variable", []) if existing_collection else [],  # Preserve existing variables
        }
        
        # Preserve existing auth, event if editing
        if existing_collection:
            if existing_collection.get("auth"):
                data["auth"] = existing_collection.get("auth")
            if existing_collection.get("event"):
                data["event"] = existing_collection.get("event")
    elif is_page_form_submission:
        # Collect form data from individual fields (fallback)
        data = {
            "page_id": request.POST.get("page_id") or (file_path.split("/")[-1].replace(".json", "") if file_path else file_id),
            "page_type": request.POST.get("page_type", "docs"),
            "content": request.POST.get("content", ""),
            "metadata": {},
        }
        meta = data["metadata"]
        if request.POST.get("metadata_route"):
            meta["route"] = request.POST.get("metadata_route")
        if request.POST.get("metadata_status"):
            meta["status"] = request.POST.get("metadata_status")
        if request.POST.get("metadata_description"):
            meta["description"] = request.POST.get("metadata_description")
        if request.POST.get("metadata_purpose"):
            meta["purpose"] = request.POST.get("metadata_purpose")
        if request.POST.get("metadata_version"):
            meta["version"] = request.POST.get("metadata_version")
        if request.POST.get("metadata_page_state"):
            meta["page_state"] = request.POST.get("metadata_page_state")
        if request.POST.get("metadata_authentication"):
            meta["authentication"] = request.POST.get("metadata_authentication")
        if request.POST.get("metadata_authorization"):
            meta["authorization"] = request.POST.get("metadata_authorization")
        ac: Dict[str, bool] = {}
        if request.POST.get("access_public"):
            ac["public"] = True
        if request.POST.get("access_free_user"):
            ac["freeUser"] = True
        if request.POST.get("access_pro_user"):
            ac["proUser"] = True
        if request.POST.get("access_admin"):
            ac["admin"] = True
        if request.POST.get("access_super_admin"):
            ac["superAdmin"] = True
        if ac:
            meta["access_control"] = ac
    else:
        # Original JSON editor submission
        try:
            data = json.loads(content_str) if content_str else {}
        except json.JSONDecodeError as e:
            context = {
                "file_data": {"resource_type": resource_type, "file_id": file_id, "content": content_str, "content_dict": {}},
                "file_path": file_path,
                "relative_path": file_path if is_edit else None,
                "is_edit": is_edit,
                "error_message": f"Invalid JSON: {e}",
                "is_page_file": False,
                "page": None,
                "page_json": "{}",
                "active_tab": "basic",
                "available_endpoints": [],
            }
            return render(request, "documentation/media/file_form.html", context)

    if is_edit:
        fp, full = _resolve_relative_path(file_path)
        if not fp:
            raise Http404("File not found")
        out = svc.update_file(str(full), data, auto_sync=auto_sync)
        if out.get("success"):
            return redirect("documentation:media_file_viewer", file_path=fp)
        context = {
            "file_data": {"resource_type": resource_type, "content": content_str, "content_dict": data},
            "file_path": file_path,
            "relative_path": fp,
            "is_edit": True,
            "error_message": out.get("error", "Update failed"),
        }
        return render(request, "documentation/media/file_form.html", context)

    if not resource_type or not file_id:
        context = {
            "file_data": {"resource_type": resource_type, "file_id": file_id, "content": content_str, "content_dict": data},
            "file_path": None,
            "relative_path": None,
            "is_edit": False,
            "error_message": "Resource type and File ID are required.",
        }
        return render(request, "documentation/media/file_form.html", context)

    key = {"pages": "page_id", "endpoints": "endpoint_id", "relationships": "relationship_id", "postman": "config_id"}.get(resource_type, "id")
    if key not in data:
        data[key] = file_id
    out = svc.create_file(resource_type, data, auto_sync=auto_sync)
    if out.get("success"):
        rp = out.get("relative_path") or f"{resource_type}/{file_id}.json"
        return redirect("documentation:media_file_viewer", file_path=rp)
    context = {
        "file_data": {"resource_type": resource_type, "file_id": file_id, "content": content_str, "content_dict": data},
        "file_path": None,
        "relative_path": None,
        "is_edit": False,
        "error_message": out.get("error", "Create failed"),
    }
    return render(request, "documentation/media/file_form.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def media_file_delete_confirm(request: HttpRequest, file_path: str) -> HttpResponse:
    """GET/POST /docs/media/delete/<path:file_path>/"""
    fp, full = _resolve_relative_path(file_path)
    if not fp:
        raise Http404("File not found")
    svc = MediaManagerService()
    detail = svc.get_file_detail(str(full))
    if not detail:
        raise Http404("File not found")
    file_name = full.name
    metadata = detail.get("metadata") or {}
    file_data = {"size": metadata.get("size"), "resource_type": detail.get("resource_type"), "modified": metadata.get("modified")}

    if request.method == "GET":
        context = {"file_path": fp, "file_name": file_name, "file_data": file_data, "error_message": None}
        return render(request, "documentation/media/delete_confirm.html", context)

    delete_remote = request.POST.get("delete_remote") == "on"
    out = svc.delete_file(str(full), delete_remote=delete_remote)
    if out.get("success"):
        return redirect("documentation:media_manager_dashboard")
    context = {"file_path": fp, "file_name": file_name, "file_data": file_data, "error_message": out.get("error", "Delete failed")}
    return render(request, "documentation/media/delete_confirm.html", context)


def _run_file_op(request: HttpRequest, file_path: str, op: str) -> JsonResponse:
    """Shared logic for analyze/validate/generate/upload; file_path is relative."""
    fp, full = _validate_file_path(file_path)
    if not fp or not full:
        return not_found_response("File").to_json_response()
    
    fo = FileOperationsService()
    try:
        if op == "analyze":
            result = fo.analyze_single_file(fp)
        elif op == "validate":
            result = fo.validate_single_file(fp)
        elif op == "generate":
            result = fo.generate_json_for_file(fp)
        else:
            result = fo.upload_single_file_to_s3(fp)
        fo.save_operation_result(fp, op, result)
        
        # FileOperationsService returns results in various formats
        # Wrap in standardized response if needed
        if isinstance(result, dict) and "status" in result:
            # Already has status, return as-is but wrap in success_response if successful
            if result.get("status") == "success" or result.get("status") == "ok":
                return success_response(data=result, message=f"Operation {op} completed successfully").to_json_response()
            else:
                # Error result
                errors = result.get("errors", [result.get("error", "Operation failed")])
                return error_response(message=errors[0] if errors else "Operation failed", status_code=400).to_json_response()
        
        # Default: wrap in success response
        return success_response(data=result, message=f"Operation {op} completed successfully").to_json_response()
    except Exception as e:
        logger.exception("Error in _run_file_op for operation %s: %s", op, e)
        return server_error_response(f"Error performing {op} operation: {str(e)}").to_json_response()


@login_required
@require_http_methods(["POST"])
def analyze_file_view(request: HttpRequest, file_path: str) -> JsonResponse:
    """POST /docs/media/analyze/<path:file_path>/"""
    return _run_file_op(request, file_path, "analyze")


@login_required
@require_http_methods(["POST"])
def validate_file_view(request: HttpRequest, file_path: str) -> JsonResponse:
    """POST /docs/media/validate/<path:file_path>/"""
    return _run_file_op(request, file_path, "validate")


@login_required
@require_http_methods(["POST"])
def generate_json_file_view(request: HttpRequest, file_path: str) -> JsonResponse:
    """POST /docs/media/generate/<path:file_path>/"""
    return _run_file_op(request, file_path, "generate")


@login_required
@require_http_methods(["POST"])
def upload_file_to_s3_view(request: HttpRequest, file_path: str) -> JsonResponse:
    """POST /docs/media/upload/<path:file_path>/"""
    return _run_file_op(request, file_path, "upload_s3")
