"""Documentation operations views."""

from __future__ import annotations

import logging
from typing import Any, Dict

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

logger = logging.getLogger(__name__)


@login_required
def operations_dashboard(request: HttpRequest) -> HttpResponse:
    """Operations dashboard view. GET /docs/operations/dashboard/"""
    try:
        return render(request, "documentation/operations/dashboard.html")
    except Exception as e:
        logger.error("Error rendering operations dashboard: %s", e, exc_info=True)
        raise


@login_required
def analyze_docs_view(request: HttpRequest) -> HttpResponse:
    """Analyze documentation view. GET /docs/operations/analyze/"""
    try:
        return render(request, "documentation/operations/analyze.html")
    except Exception as e:
        logger.error("Error rendering analyze docs view: %s", e, exc_info=True)
        raise


@login_required
def validate_docs_view(request: HttpRequest) -> HttpResponse:
    """Validate documentation view. GET /docs/operations/validate/"""
    try:
        return render(request, "documentation/operations/validate.html")
    except Exception as e:
        logger.error("Error rendering validate docs view: %s", e, exc_info=True)
        raise


@login_required
def generate_json_view(request: HttpRequest) -> HttpResponse:
    """Generate JSON view. GET /docs/operations/generate-json/"""
    try:
        return render(request, "documentation/operations/generate_json.html")
    except Exception as e:
        logger.error("Error rendering generate JSON view: %s", e, exc_info=True)
        raise


@login_required
def generate_postman_view(request: HttpRequest) -> HttpResponse:
    """Generate Postman view. GET /docs/operations/generate-postman/"""
    try:
        return render(request, "documentation/operations/generate_postman.html")
    except Exception as e:
        logger.error("Error rendering generate Postman view: %s", e, exc_info=True)
        raise


@login_required
def upload_docs_view(request: HttpRequest) -> HttpResponse:
    """Upload docs view. GET /docs/operations/upload/"""
    try:
        return render(request, "documentation/operations/upload.html")
    except Exception as e:
        logger.error("Error rendering upload docs view: %s", e, exc_info=True)
        raise


@login_required
def seed_documentation_view(request: HttpRequest) -> HttpResponse:
    """Seed documentation view. GET /docs/operations/seed/"""
    try:
        return render(request, "documentation/operations/seed.html")
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


@login_required
def docs_status_view(request: HttpRequest) -> HttpResponse:
    """Documentation status view. GET /docs/operations/status/"""
    try:
        return render(request, "documentation/operations/status.html")
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
        return redirect("documentation:task_list")

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
