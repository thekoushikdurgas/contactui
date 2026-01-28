"""Views for page operations."""

from __future__ import annotations

import json
import logging
import markdown
from typing import Any, Dict, List, Optional, Tuple

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.documentation.services import pages_service, endpoints_service, relationships_service
from apps.documentation.utils.api_responses import (
    APIResponse,
    error_response,
    not_found_response,
    server_error_response,
    success_response,
)
from apps.documentation.utils.rate_limiting import (
    rate_limit_create_endpoint,
    rate_limit_update_endpoint,
    rate_limit_delete_endpoint,
    rate_limit_list_endpoint,
)
from apps.documentation.utils.view_helpers import (
    parse_limit_offset,
    parse_json_body,
    validate_detail_tab,
)

logger = logging.getLogger(__name__)

DEFAULT_PAGE_LIMIT = 20
MAX_PAGE_LIMIT = 500
DEFAULT_OFFSET = 0
VALID_DETAIL_TABS = frozenset({"overview", "content", "relationships", "endpoints", "components", "access", "raw"})

# Use shared helper functions (Task 2.3.1)
# Wrapper functions for backward compatibility
def _parse_limit_offset(request: HttpRequest) -> Tuple[int, int]:
    """Parse limit/offset for pages (uses shared helper)."""
    return parse_limit_offset(request, DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT, DEFAULT_OFFSET)

def _parse_json_body(request: HttpRequest) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Parse JSON body (uses shared helper)."""
    return parse_json_body(request)

def _validate_detail_tab(tab: Optional[str]) -> str:
    """Validate detail tab for pages (uses shared helper)."""
    return validate_detail_tab(tab, "pages")


@login_required
def page_list_view(request: HttpRequest) -> HttpResponse:
    """List all pages. GET /docs/pages/list/"""
    try:
        page_type = request.GET.get("page_type") or None
        status = request.GET.get("status") or None
        limit, offset = _parse_limit_offset(request)

        result = pages_service.list_pages(
            page_type=page_type,
            status=status,
            limit=limit,
            offset=offset,
        )

        context: Dict[str, Any] = {
            "pages": result.get("pages", []),
            "total": result.get("total", 0),
            "source": result.get("source", "local"),
            "empty_state_create_url": reverse("documentation:page_create"),
        }
    except Exception as e:
        logger.error("Error listing pages: %s", e, exc_info=True)
        messages.error(request, "An error occurred while loading pages.")
        context = {
            "pages": [],
            "total": 0,
            "source": "error",
            "empty_state_create_url": reverse("documentation:page_create"),
        }

    return render(request, "documentation/pages/list.html", context)


# Removed duplicate _validate_detail_tab - now using shared helper (Task 2.3.1)


@login_required
def page_detail_view(request: HttpRequest, page_id: str) -> HttpResponse:
    """Get single page detail with enhanced tabs and relationships. GET /docs/pages/<page_id>/"""
    if not page_id or not page_id.strip():
        messages.error(request, "Page ID is required.")
        return redirect("documentation:pages_list")

    active_tab = _validate_detail_tab(request.GET.get("tab"))

    try:
        page = pages_service.get_page(page_id)
        if not page:
            messages.error(request, "Page not found.")
            return redirect("documentation:pages_list")

        content = page.get("content", "")
        page_html = markdown.markdown(content, extensions=["fenced_code", "tables"])
        page_json = json.dumps(page, indent=2, default=str)

        page_route = page.get("metadata", {}).get("route") or page.get("route")
        page_path = page_route or page_id
        page_relationships: List[Dict[str, Any]] = []

        try:
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

        context: Dict[str, Any] = {
            "page": page,
            "page_html": page_html,
            "page_json": page_json,
            "active_tab": active_tab,
            "page_relationships": page_relationships,
            "relationships_by_type": relationships_by_type,
            "relationships_count": len(page_relationships),
            "endpoints_used": endpoints_used,
            "endpoints_count": len(endpoints_used),
        }
    except Exception as e:
        logger.error("Error loading page %s: %s", page_id, e, exc_info=True)
        messages.error(request, "An error occurred while loading the page.")
        return redirect("documentation:pages_list")

    return render(request, "documentation/pages/detail.html", context)


def _collect_form_page_data(request: HttpRequest, page_id: Optional[str]) -> Optional[Dict[str, Any]]:
    """Collect page form data from POST (non-JSON). Returns None if validation fails."""
    page_data: Dict[str, Any] = {
        "page_id": request.POST.get("page_id") or page_id,
        "page_type": request.POST.get("page_type", "docs"),
        "content": request.POST.get("content", ""),
        "metadata": {},
    }
    meta = page_data["metadata"]
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
    if not page_data.get("page_id"):
        return None
    if not meta.get("route"):
        return None
    return page_data


@login_required
def page_form_view(request: HttpRequest, page_id: Optional[str] = None) -> HttpResponse:
    """Page create/edit form. GET/POST /docs/pages/create/ or /docs/pages/<page_id>/edit/"""
    page: Optional[Dict[str, Any]] = None
    is_edit = page_id is not None
    active_tab = request.GET.get("tab", "basic") or "basic"

    if request.method == "POST":
        try:
            page_data: Optional[Dict[str, Any]] = None
            raw = request.POST.get("page_data")
            if raw:
                try:
                    page_data = json.loads(raw)
                except json.JSONDecodeError:
                    messages.error(request, "Invalid form data format.")
                    return _form_render(request, page, is_edit, active_tab)
            else:
                page_data = _collect_form_page_data(request, page_id)
                if not page_data:
                    if not (request.POST.get("page_id") or page_id):
                        messages.error(request, "Page ID is required.")
                        err_tab = "basic"
                    else:
                        messages.error(request, "Route is required.")
                        err_tab = "metadata"
                    return _form_render(request, page, is_edit, err_tab)

            return_url = request.GET.get("return_url") or request.POST.get("return_url")

            if page_id:
                updated = pages_service.update_page(page_id, page_data)
                if updated:
                    messages.success(request, "Page updated successfully.")
                    return redirect(return_url) if return_url else redirect("documentation:page_detail", page_id=page_id)
                messages.error(request, "Failed to update page.")
            else:
                created = pages_service.create_page(page_data)
                if created:
                    messages.success(request, "Page created successfully.")
                    pid = page_data.get("page_id")
                    return redirect(return_url) if return_url else redirect("documentation:page_detail", page_id=pid)
                messages.error(request, "Failed to create page.")
        except Exception as e:
            logger.error("Error saving page: %s", e, exc_info=True)
            messages.error(request, "An error occurred: %s" % (e,))

    if page_id:
        try:
            page = pages_service.get_page(page_id)
            if not page:
                messages.error(request, "Page not found.")
                return redirect("documentation:pages_list")
        except Exception as e:
            logger.error("Error loading page %s: %s", page_id, e, exc_info=True)
            messages.error(request, "An error occurred while loading the page.")
            return redirect("documentation:pages_list")

    use_enhanced = request.GET.get("enhanced", "true").lower() == "true"
    template_name = "documentation/pages/form_enhanced.html" if use_enhanced else "documentation/pages/form.html"
    available_endpoints: List[Dict[str, Any]] = []
    try:
        ep_result = endpoints_service.list_endpoints(limit=100)
        available_endpoints = ep_result.get("endpoints", [])
    except Exception as e:
        logger.warning("Failed to load endpoints for form: %s", e)

    page_json = json.dumps(page) if page else "{}"
    context: Dict[str, Any] = {
        "page": page,
        "page_json": page_json,
        "is_edit": is_edit,
        "active_tab": active_tab,
        "available_endpoints": available_endpoints,
        "return_url": request.GET.get("return_url"),
    }
    return render(request, template_name, context)


def _form_render(
    request: HttpRequest,
    page: Optional[Dict[str, Any]],
    is_edit: bool,
    active_tab: str,
) -> HttpResponse:
    """Render form template with common context (e.g. validation errors)."""
    use_enhanced = request.GET.get("enhanced", "true").lower() == "true"
    template_name = "documentation/pages/form_enhanced.html" if use_enhanced else "documentation/pages/form.html"
    context: Dict[str, Any] = {
        "page": page,
        "page_json": json.dumps(page) if page else "{}",
        "is_edit": is_edit,
        "active_tab": active_tab,
        "available_endpoints": [],
        "return_url": request.GET.get("return_url"),
    }
    return render(request, template_name, context)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
@rate_limit_create_endpoint()  # 50 requests/hour per user
def page_create_api(request: HttpRequest) -> JsonResponse:
    """API endpoint to create a new page. POST /docs/api/pages/"""
    data, err = _parse_json_body(request)
    if err:
        return error_response(err, status_code=400).to_json_response()
    try:
        created = pages_service.create_page(data)
        if created:
            return APIResponse(success=True, data=created, status_code=201).to_json_response()
        return server_error_response("Failed to create page").to_json_response()
    except Exception as e:
        logger.error("Error creating page: %s", e, exc_info=True)
        return server_error_response(str(e)).to_json_response()


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def page_draft_api(request: HttpRequest) -> JsonResponse:
    """API endpoint to save page draft (auto-save). POST /docs/api/pages/draft/"""
    data, err = _parse_json_body(request)
    if err:
        return error_response(err, status_code=400).to_json_response()
    if "metadata" not in data:
        data["metadata"] = {}
    data["metadata"]["status"] = "draft"
    page_id = data.get("page_id") or data.get("metadata", {}).get("route")
    try:
        if page_id:
            updated = pages_service.update_page(page_id, data)
            if updated:
                return success_response(updated, message="Draft saved successfully").to_json_response()
        else:
            created = pages_service.create_page(data)
            if created:
                return APIResponse(
                    success=True,
                    data=created,
                    message="Draft saved successfully",
                    status_code=201,
                ).to_json_response()
        return server_error_response("Failed to save draft").to_json_response()
    except Exception as e:
        logger.error("Error saving page draft: %s", e, exc_info=True)
        return server_error_response(str(e)).to_json_response()


@login_required
@require_http_methods(["PUT", "PATCH"])
@csrf_exempt
@rate_limit_update_endpoint()  # 100 requests/hour per user
def page_update_api(request: HttpRequest, page_id: str) -> JsonResponse:
    """API endpoint to update a page. PUT/PATCH /docs/api/pages/<page_id>/"""
    if not page_id or not page_id.strip():
        return error_response("Page ID is required", status_code=400).to_json_response()
    data, err = _parse_json_body(request)
    if err:
        return error_response(err, status_code=400).to_json_response()
    try:
        updated = pages_service.update_page(page_id, data)
        if updated:
            return success_response(updated).to_json_response()
        return not_found_response("Page").to_json_response()
    except Exception as e:
        logger.error("Error updating page %s: %s", page_id, e, exc_info=True)
        return server_error_response(str(e)).to_json_response()


@login_required
@require_http_methods(["DELETE"])
@csrf_exempt
@rate_limit_delete_endpoint()  # 50 requests/hour per user
def page_delete_api(request: HttpRequest, page_id: str) -> JsonResponse:
    """API endpoint to delete a page. DELETE /docs/api/pages/<page_id>/delete/"""
    if not page_id or not page_id.strip():
        return error_response("Page ID is required", status_code=400).to_json_response()
    try:
        deleted = pages_service.delete_page(page_id)
        if deleted:
            return success_response(None, message="Page deleted successfully").to_json_response()
        return not_found_response("Page").to_json_response()
    except Exception as e:
        logger.error("Error deleting page %s: %s", page_id, e, exc_info=True)
        return server_error_response(str(e)).to_json_response()
