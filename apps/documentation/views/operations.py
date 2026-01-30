"""Documentation operations views."""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from apps.documentation.utils.paths import get_postman_dir

logger = logging.getLogger(__name__)

# #region agent log
def _agent_log(message: str, data: dict):
    try:
        payload = {"location": "operations.py", "message": message, "data": data, "timestamp": int(time.time() * 1000), "sessionId": "debug-session", "hypothesisId": "H2"}
        with open("d:\\code\\ayan\\contact\\.cursor\\debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except Exception:
        pass
# #endregion


@login_required
def operations_dashboard(request: HttpRequest) -> HttpResponse:
    """Operations dashboard view. GET /docs/operations/dashboard/"""
    try:
        return render(request, "documentation/operations/dashboard.html")
    except Exception as e:
        logger.error("Error rendering operations dashboard: %s", e, exc_info=True)
        raise


def _run_analyze_script(analysis_type: str) -> Dict[str, Any]:
    """Run scripts/analyze_docs_files.py and return report dict. Returns empty dict on error."""
    base_dir = Path(settings.BASE_DIR)
    script = base_dir / "scripts" / "analyze_docs_files.py"
    if not script.exists():
        logger.warning("Analyze script not found: %s", script)
        return {}
    args = ["python", str(script), "--output"]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        out_path = f.name
    args.append(out_path)
    if analysis_type == "pages":
        args.append("--pages-only")
    elif analysis_type == "endpoints":
        args.append("--endpoints-only")
    elif analysis_type == "relationships":
        args.append("--relationships-only")
    env = {**os.environ, "DJANGO_SETTINGS_MODULE": os.environ.get("DJANGO_SETTINGS_MODULE", "config.settings")}
    try:
        result = subprocess.run(
            args,
            cwd=str(base_dir),
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
        report_path = Path(out_path)
        if report_path.exists():
            try:
                data = json.loads(report_path.read_text(encoding="utf-8"))
                report_path.unlink(missing_ok=True)
                return data
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to read analyze report: %s", e)
        return {"analysis_error": result.stderr or str(result.returncode), "analysis_stdout": result.stdout or ""}
    except subprocess.TimeoutExpired:
        Path(out_path).unlink(missing_ok=True)
        return {"analysis_error": "Analysis timed out after 120 seconds."}
    except Exception as e:
        logger.exception("Error running analyze script: %s", e)
        Path(out_path).unlink(missing_ok=True)
        return {"analysis_error": str(e)}


@login_required
def analyze_docs_view(request: HttpRequest) -> HttpResponse:
    """Analyze documentation view. GET /docs/operations/analyze/ or POST to run analysis."""
    # #region agent log
    _agent_log("analyze_docs_view entry", {"method": request.method, "user": str(getattr(request.user, "pk", None)), "path": request.path})
    # #endregion
    context: Dict[str, Any] = {}
    if request.method == "POST":
        analysis_type = (request.POST.get("analysis_type") or "all").strip()
        if analysis_type not in ("all", "pages", "endpoints", "relationships"):
            analysis_type = "all"
        report = _run_analyze_script(analysis_type)
        context["report"] = report
        context["analysis_type"] = analysis_type
        # #region agent log
        _agent_log("analyze_docs_view POST completed", {"analysis_type": analysis_type, "has_report": bool(report), "has_error": "analysis_error" in report})
        # #endregion
    try:
        resp = render(request, "documentation/operations/analyze.html", context)
        # #region agent log
        _agent_log("analyze_docs_view rendered", {"method": request.method, "status": 200})
        # #endregion
        return resp
    except Exception as e:
        logger.error("Error rendering analyze docs view: %s", e, exc_info=True)
        # #region agent log
        _agent_log("analyze_docs_view exception", {"error": str(e)})
        # #endregion
        raise


@login_required
def validate_docs_view(request: HttpRequest) -> HttpResponse:
    """Validate documentation view. GET /docs/operations/validate/ or POST to run validation."""
    context: Dict[str, Any] = {}
    if request.method == "POST":
        report = _run_analyze_script("all")
        context["report"] = report
    try:
        return render(request, "documentation/operations/validate.html", context)
    except Exception as e:
        logger.error("Error rendering validate docs view: %s", e, exc_info=True)
        raise


def _run_generate_indexes(selected: list[str]) -> Dict[str, Any]:
    """Run index generation for selected types (pages, endpoints, relationships, postman). Returns {results: {name: {success, ...}}, success}."""
    from apps.documentation.services.index_generator_service import IndexGeneratorService
    gen = IndexGeneratorService()
    results: Dict[str, Any] = {}
    all_ok = True
    for name in selected:
        fn = getattr(gen, f"generate_{name}_index", None)
        if not fn:
            results[name] = {"success": False, "error": f"Unknown index: {name}"}
            all_ok = False
            continue
        try:
            out = fn()
            results[name] = out
            if not out.get("success"):
                all_ok = False
        except Exception as e:
            logger.exception("generate_%s_index", name)
            results[name] = {"success": False, "error": str(e)}
            all_ok = False
    return {"success": all_ok, "results": results}


@login_required
def generate_json_view(request: HttpRequest) -> HttpResponse:
    """Generate JSON view. GET /docs/operations/generate-json/ or POST to run index generation."""
    context: Dict[str, Any] = {}
    if request.method == "POST":
        selected = []
        if request.POST.get("generate_pages_index"):
            selected.append("pages")
        if request.POST.get("generate_endpoints_index"):
            selected.append("endpoints")
        if request.POST.get("generate_relationships_index"):
            selected.append("relationships")
        if request.POST.get("generate_postman_index"):
            selected.append("postman")
        if not selected:
            context["report"] = {"success": False, "results": {}, "message": "Select at least one index to generate."}
        else:
            context["report"] = _run_generate_indexes(selected)
    try:
        return render(request, "documentation/operations/generate_json.html", context)
    except Exception as e:
        logger.error("Error rendering generate JSON view: %s", e, exc_info=True)
        raise


def _run_generate_postman_collection(collection_name: str) -> Dict[str, Any]:
    """Generate a Postman collection (GraphQL API) and write to media/postman/collection/. Returns {success, path, collection_name, error}."""
    collection_name = (collection_name or "Contact360 API").strip() or "Contact360 API"
    try:
        base_dir = Path(settings.BASE_DIR)
        if str(base_dir) not in sys.path:
            sys.path.insert(0, str(base_dir))
        from scripts.generate_postman_collection import generate_collection
        collection = generate_collection()
        collection["info"]["name"] = collection_name
        safe_name = re.sub(r"[^\w\-]", "_", collection_name)
        filename = f"{safe_name}.postman_collection.json"
        postman_dir = get_postman_dir()
        collection_dir = postman_dir / "collection"
        collection_dir.mkdir(parents=True, exist_ok=True)
        out_path = collection_dir / filename
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(collection, f, indent=2, ensure_ascii=False)
        logger.info("Generated Postman collection: %s", out_path)
        return {"success": True, "path": str(out_path), "collection_name": collection_name, "filename": filename}
    except ImportError as e:
        logger.warning("Could not import generate_postman_collection: %s", e)
        return {"success": False, "error": f"Collection generator not available: {e}", "collection_name": collection_name}
    except Exception as e:
        logger.exception("generate_postman_collection")
        return {"success": False, "error": str(e), "collection_name": collection_name}


@login_required
def generate_postman_view(request: HttpRequest) -> HttpResponse:
    """Generate Postman view. GET /docs/operations/generate-postman/ or POST to generate collection."""
    context: Dict[str, Any] = {}
    if request.method == "POST":
        collection_name = request.POST.get("collection_name", "Contact360 API")
        context["report"] = _run_generate_postman_collection(collection_name)
    try:
        return render(request, "documentation/operations/generate_postman.html", context)
    except Exception as e:
        logger.error("Error rendering generate Postman view: %s", e, exc_info=True)
        raise


def _sync_one_resource_to_s3(resource_type: str) -> Dict[str, Any]:
    """Upload one resource type (pages, endpoints, relationships, postman) to S3. Returns result dict for API."""
    from apps.documentation.services.media_sync_service import MediaSyncService
    allowed = ("pages", "endpoints", "relationships", "postman")
    if resource_type not in allowed:
        return {"success": False, "error": f"Unknown resource type: {resource_type}", "resource_type": resource_type}
    try:
        svc = MediaSyncService()
        fn = getattr(svc, f"sync_{resource_type}_to_s3", None)
        if not fn:
            return {"success": False, "error": f"No sync for {resource_type}", "resource_type": resource_type}
        out = fn(dry_run=False)
        errors = out.get("errors", 0)
        return {
            "success": errors == 0,
            "resource_type": resource_type,
            "total_files": out.get("total_files", 0),
            "synced": out.get("synced", 0),
            "errors": errors,
            "error_details": out.get("error_details", [])[:15],
        }
    except Exception as e:
        logger.exception("sync_%s_to_s3", resource_type)
        return {"success": False, "resource_type": resource_type, "error": str(e)}


def _upload_file_list_for_resource(resource_type: str) -> Dict[str, Any]:
    """Return list of file relative_paths for a resource type (for per-file upload UI)."""
    from apps.documentation.services.media_file_manager import MediaFileManagerService
    allowed = ("pages", "endpoints", "relationships", "postman")
    if resource_type not in allowed:
        return {"resource_type": resource_type, "files": [], "error": f"Unknown resource type: {resource_type}"}
    try:
        mgr = MediaFileManagerService()
        items = mgr.scan_media_directory(resource_type)
        files = [{"relative_path": (item.get("relative_path") or "").replace("\\", "/"), "name": item.get("name", "")} for item in items if item.get("relative_path")]
        return {"resource_type": resource_type, "files": files}
    except Exception as e:
        logger.exception("upload_file_list %s", resource_type)
        return {"resource_type": resource_type, "files": [], "error": str(e)}


@login_required
@require_http_methods(["GET"])
def upload_file_list_api(request: HttpRequest, resource_type: str) -> JsonResponse:
    """GET /docs/api/operations/upload-file-list/<resource_type>/ – list files to upload for per-file progress."""
    result = _upload_file_list_for_resource(resource_type)
    return JsonResponse(result)


@login_required
@require_http_methods(["POST"])
def upload_to_s3_api(request: HttpRequest, resource_type: str) -> JsonResponse:
    """POST /docs/api/operations/upload-to-s3/<resource_type>/ – upload one folder to S3. Returns JSON for progress UI."""
    result = _sync_one_resource_to_s3(resource_type)
    return JsonResponse(result)


def _run_upload_to_s3(selected: list[str]) -> Dict[str, Any]:
    """Upload selected resource types (pages, endpoints, relationships, postman) to S3. Returns {success, results}."""
    from apps.documentation.services.media_sync_service import MediaSyncService
    svc = MediaSyncService()
    results: Dict[str, Any] = {}
    all_ok = True
    for name in selected:
        fn = getattr(svc, f"sync_{name}_to_s3", None)
        if not fn:
            results[name] = {"success": False, "error": f"Unknown resource type: {name}"}
            all_ok = False
            continue
        try:
            out = fn(dry_run=False)
            synced = out.get("synced", 0)
            errors = out.get("errors", 0)
            total = out.get("total_files", 0)
            results[name] = {
                "success": errors == 0,
                "total_files": total,
                "synced": synced,
                "errors": errors,
                "error_details": out.get("error_details", [])[:10],
            }
            if errors > 0:
                all_ok = False
        except Exception as e:
            logger.exception("sync_%s_to_s3", name)
            results[name] = {"success": False, "error": str(e)}
            all_ok = False
    return {"success": all_ok, "results": results}


@login_required
def upload_docs_view(request: HttpRequest) -> HttpResponse:
    """Upload docs view. GET /docs/operations/upload/ or POST to upload selected types to S3."""
    context: Dict[str, Any] = {}
    if request.method == "POST":
        selected = []
        if request.POST.get("upload_pages"):
            selected.append("pages")
        if request.POST.get("upload_endpoints"):
            selected.append("endpoints")
        if request.POST.get("upload_relationships"):
            selected.append("relationships")
        if request.POST.get("upload_postman"):
            selected.append("postman")
        if not selected:
            context["report"] = {"success": False, "results": {}, "message": "Select at least one resource type to upload."}
        else:
            context["report"] = _run_upload_to_s3(selected)
    try:
        return render(request, "documentation/operations/upload.html", context)
    except Exception as e:
        logger.error("Error rendering upload docs view: %s", e, exc_info=True)
        raise


def _run_seed_script(source: str) -> Dict[str, Any]:
    """Run scripts/seed_documentation_pages.py in subprocess. Returns {success, stdout, stderr, message}."""
    base_dir = Path(settings.BASE_DIR)
    script = base_dir / "scripts" / "seed_documentation_pages.py"
    if not script.exists():
        logger.warning("Seed script not found: %s", script)
        return {"success": False, "stdout": "", "stderr": "", "message": "Seed script not found."}
    args = [sys.executable, str(script)]
    env = {**os.environ, "DJANGO_SETTINGS_MODULE": os.environ.get("DJANGO_SETTINGS_MODULE", "config.settings")}
    try:
        result = subprocess.run(
            args,
            cwd=str(base_dir),
            capture_output=True,
            text=True,
            timeout=300,
            env=env,
        )
        report = {
            "success": result.returncode == 0,
            "stdout": (result.stdout or "").strip(),
            "stderr": (result.stderr or "").strip(),
            "returncode": result.returncode,
        }
        if result.returncode != 0 and report["stderr"]:
            report["message"] = "Seed script failed. See output below."
        elif result.returncode == 0:
            report["message"] = "Seeding completed. See output below."
        else:
            report["message"] = "Seeding completed." if result.returncode == 0 else "Seeding failed."
        return report
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "Seed script timed out after 300 seconds.", "message": "Seeding timed out."}
    except Exception as e:
        logger.exception("Error running seed script: %s", e)
        return {"success": False, "stdout": "", "stderr": str(e), "message": "Error running seed script."}


@login_required
def seed_documentation_view(request: HttpRequest) -> HttpResponse:
    """Seed documentation view. GET /docs/operations/seed/ or POST to run seeding."""
    context: Dict[str, Any] = {}
    if request.method == "POST":
        source = (request.POST.get("source") or "s3").strip()
        if source not in ("graphql", "lambda", "s3"):
            source = "s3"
        report = _run_seed_script(source)
        context["report"] = report
    try:
        return render(request, "documentation/operations/seed.html", context)
    except Exception as e:
        logger.error("Error rendering seed documentation view: %s", e, exc_info=True)
        raise


@login_required
def workflow_view(request: HttpRequest) -> HttpResponse:
    """Workflow view. GET /docs/operations/workflow/"""
    try:
        return render(request, "documentation/operations/workflow.html")
    except Exception as e:
        logger.error("Error rendering workflow view: %s", e, exc_info=True)
        raise


def _get_docs_status_context() -> Dict[str, Any]:
    """Build context for docs status page: health status from health_checks."""
    context: Dict[str, Any] = {}
    try:
        from apps.documentation.utils.health_checks import get_comprehensive_health_status
        context["health_status"] = get_comprehensive_health_status()
    except Exception as e:
        logger.warning("Failed to get health status for docs status view: %s", e)
        context["health_status"] = {"status": "unknown", "components": {}, "error": str(e)}
    return context


@login_required
def docs_status_view(request: HttpRequest) -> HttpResponse:
    """Documentation status view. GET /docs/operations/status/"""
    context = _get_docs_status_context()
    try:
        return render(request, "documentation/operations/status.html", context)
    except Exception as e:
        logger.error("Error rendering docs status view: %s", e, exc_info=True)
        raise


@login_required
def task_list_view(request: HttpRequest) -> HttpResponse:
    """Task list view. GET /docs/operations/tasks/"""
    try:
        return render(request, "documentation/operations/task_list.html")
    except Exception as e:
        logger.error("Error rendering task list view: %s", e, exc_info=True)
        raise


@login_required
def task_detail_view(request: HttpRequest, task_id: str) -> HttpResponse:
    """Task detail view. GET /docs/operations/tasks/<task_id>/"""
    if not task_id or not task_id.strip():
        logger.warning("Invalid task_id in task_detail_view")
        from django.shortcuts import redirect
        return redirect("documentation:operations_tasks")

    try:
        context: Dict[str, Any] = {"task_id": task_id.strip()}
        return render(request, "documentation/operations/task_detail.html", context)
    except Exception as e:
        logger.error("Error rendering task detail view for task_id %s: %s", task_id, e, exc_info=True)
        raise


@login_required
def media_manager_dashboard(request: HttpRequest) -> HttpResponse:
    """Media Manager dashboard – GitHub-style file browser for media/ JSON. GET /docs/media/manager/"""
    from apps.documentation.services.media_manager_service import MediaManagerService

    try:
        svc = MediaManagerService()
        sync_summary = svc.get_sync_summary()
        resource_types = ["pages", "endpoints", "relationships", "postman", "n8n", "project"]
        file_counts: Dict[str, int] = {
            rt: sync_summary.get("by_type", {}).get(rt, {}).get("total", 0) for rt in resource_types
        }
        context: Dict[str, Any] = {
            "sync_summary": sync_summary,
            "file_counts": file_counts,
            "resource_types": resource_types,
        }
        return render(request, "documentation/media_manager.html", context)
    except Exception as e:
        logger.error("Error rendering media manager dashboard: %s", e, exc_info=True)
        # Return empty context on error
        context: Dict[str, Any] = {
            "sync_summary": {},
            "file_counts": {},
            "resource_types": ["pages", "endpoints", "relationships", "postman", "n8n", "project"],
        }
        return render(request, "documentation/media_manager.html", context)
