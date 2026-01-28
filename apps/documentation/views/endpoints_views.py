"""Views for endpoint operations."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.documentation.services import endpoints_service, relationships_service, pages_service
from apps.documentation.utils.api_responses import (
    APIResponse,
    error_response,
    not_found_response,
    server_error_response,
    success_response,
)
from apps.documentation.utils.view_helpers import (
    parse_limit_offset,
    parse_json_body,
    validate_detail_tab,
)

logger = logging.getLogger(__name__)

DEFAULT_ENDPOINT_LIMIT = 20
MAX_ENDPOINT_LIMIT = 500
DEFAULT_OFFSET = 0
VALID_DETAIL_TABS = frozenset({"overview", "request", "response", "graphql", "relationships", "raw"})

# Use shared helper functions (Task 2.3.1)
def _parse_limit_offset(request: HttpRequest) -> Tuple[int, int]:
    """Parse limit/offset for endpoints (uses shared helper)."""
    return parse_limit_offset(request, DEFAULT_ENDPOINT_LIMIT, MAX_ENDPOINT_LIMIT, DEFAULT_OFFSET)

def _parse_json_body(request: HttpRequest) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Parse JSON body (uses shared helper)."""
    return parse_json_body(request)

def _validate_detail_tab(tab: Optional[str]) -> str:
    """Validate detail tab for endpoints (uses shared helper)."""
    return validate_detail_tab(tab, "endpoints")


def _validate_endpoint_id(endpoint_id: Optional[str]) -> Optional[str]:
    """Validate endpoint ID. Returns None if invalid."""
    if not endpoint_id or not endpoint_id.strip():
        return None
    return endpoint_id.strip()


@login_required
def endpoint_list_view(request):
    """List all endpoints."""
    # Use shared service instance
    
    try:
        method = request.GET.get('method')
        api_version = request.GET.get('api_version')
        limit = int(request.GET.get('limit', 20))
        offset = int(request.GET.get('offset', 0))
        
        result = endpoints_service.list_endpoints(
            method=method,
            api_version=api_version,
            limit=limit,
            offset=offset
        )
        
        context = {
            'endpoints': result.get('endpoints', []),
            'total': result.get('total', 0),
            'source': result.get('source', 'local')
        }
    except Exception as e:
        logger.error(f"Error listing endpoints: {e}", exc_info=True)
        messages.error(request, 'An error occurred while loading endpoints.')
        context = {'endpoints': [], 'total': 0, 'source': 'error'}
    
    return render(request, 'documentation/endpoints/list.html', context)


@login_required
def endpoint_detail_view(request: HttpRequest, endpoint_id: str) -> HttpResponse:
    """Get single endpoint detail with enhanced tabs and relationships. GET /docs/endpoints/<endpoint_id>/"""
    validated_id = _validate_endpoint_id(endpoint_id)
    if not validated_id:
        messages.error(request, "Endpoint ID is required.")
        return redirect("documentation:endpoints_list")

    active_tab = _validate_detail_tab(request.GET.get("tab"))

    try:
        endpoint = endpoints_service.get_endpoint(validated_id)
        if not endpoint:
            logger.warning("Endpoint not found: %s", validated_id)
            messages.error(request, "Endpoint not found.")
            return redirect("documentation:endpoints_list")

        # Format usage_context in relationships for display (replace underscores with spaces)
        if endpoint.get('used_by_pages'):
            for page_usage in endpoint['used_by_pages']:
                if page_usage.get('usage_context'):
                    page_usage['usage_context_display'] = page_usage['usage_context'].replace('_', ' ').title()

        # Fetch relationships for this endpoint
        endpoint_relationships = []
        endpoint_path = endpoint.get('endpoint_path') or endpoint_id
        endpoint_method = endpoint.get('method', 'QUERY')
        
        try:
            # Try to get relationships by endpoint path
            relationships_result = relationships_service.list_relationships(
                endpoint_id=endpoint_path,
                limit=100
            )
            endpoint_relationships = relationships_result.get('relationships', [])
        except Exception as e:
            logger.warning(f"Failed to load relationships for endpoint {endpoint_id}: {e}")

        # Get pages using this endpoint (if not already in used_by_pages)
        pages_using_endpoint = []
        if endpoint.get('used_by_pages'):
            pages_using_endpoint = endpoint['used_by_pages']
        else:
            # Try to find pages that use this endpoint
            try:
                all_pages = pages_service.list_pages(limit=1000)
                for page in all_pages.get('pages', []):
                    uses_endpoints = page.get('metadata', {}).get('uses_endpoints', [])
                    for ep_ref in uses_endpoints:
                        ep_id = ep_ref.get('endpoint_id') or ep_ref.get('endpoint_path')
                        if ep_id == endpoint_id or ep_id == endpoint_path:
                            pages_using_endpoint.append({
                                'page_id': page.get('page_id'),
                                'page_path': page.get('metadata', {}).get('route') or page.get('route'),
                                'page_title': page.get('metadata', {}).get('content_sections', {}).get('title'),
                                'usage_context': ep_ref.get('usage_context'),
                                'via_service': ep_ref.get('via_service'),
                                'via_hook': ep_ref.get('via_hook'),
                                'usage_type': ep_ref.get('usage_type'),
                            })
            except Exception as e:
                logger.debug(f"Could not load pages using endpoint {endpoint_id}: {e}")

        # Convert endpoint to JSON string for Raw JSON tab
        endpoint_json = json.dumps(endpoint, indent=2, default=str)

        context = {
            'endpoint': endpoint,
            'endpoint_json': endpoint_json,
            'active_tab': active_tab,
            'endpoint_relationships': endpoint_relationships,
            'relationships_count': len(endpoint_relationships),
            'pages_using_endpoint': pages_using_endpoint,
            'pages_count': len(pages_using_endpoint),
        }
    except Exception as e:
        logger.error(f"Error loading endpoint {endpoint_id}: {e}", exc_info=True)
        messages.error(request, 'An error occurred while loading the endpoint.')
        return redirect('documentation:endpoints_list')

    return render(request, 'documentation/endpoints/detail.html', context)


@login_required
def endpoint_form_view(request: HttpRequest, endpoint_id: Optional[str] = None) -> HttpResponse:
    """Endpoint create/edit form - supports both basic and enhanced forms. GET/POST /docs/endpoints/create/ or /docs/endpoints/<endpoint_id>/edit/"""
    endpoint: Optional[Dict[str, Any]] = None
    is_edit = endpoint_id is not None

    if request.method == "POST":
        try:
            # Check if enhanced form data is present
            endpoint_data_json = request.POST.get("endpoint_data")
            if endpoint_data_json:
                # Enhanced form submission
                try:
                    endpoint_data = json.loads(endpoint_data_json)
                except json.JSONDecodeError as e:
                    logger.warning("Invalid JSON in endpoint form: %s", e)
                    messages.error(request, "Invalid form data format.")
                    return render(
                        request,
                        "documentation/endpoints/form_enhanced.html",
                        {
                            "endpoint": endpoint,
                            "is_edit": is_edit,
                            "active_tab": request.GET.get("tab", "basic"),
                        },
                    )
            else:
                # Collect form data from all tabs
                endpoint_data = {
                    "endpoint_id": request.POST.get("endpoint_id") or endpoint_id,
                    "endpoint_path": request.POST.get("endpoint_path", ""),
                    "method": request.POST.get("method", "QUERY"),
                    "description": request.POST.get("description", ""),
                    "api_version": request.POST.get("api_version", "v1"),
                    "endpoint_state": request.POST.get("endpoint_state", "development"),
                }

                # Collect advanced fields
                if request.POST.get("rate_limit"):
                    endpoint_data["rate_limit"] = request.POST.get("rate_limit")
                if request.POST.get("graphql_operation"):
                    endpoint_data["graphql_operation"] = request.POST.get("graphql_operation")
                if request.POST.get("sql_file"):
                    endpoint_data["sql_file"] = request.POST.get("sql_file")

                # Validate required fields
                if not endpoint_data.get("endpoint_id"):
                    messages.error(request, "Endpoint ID is required.")
                    return render(
                        request,
                        "documentation/endpoints/form_enhanced.html",
                        {
                            "endpoint": endpoint,
                            "is_edit": is_edit,
                            "active_tab": request.GET.get("tab", "basic"),
                        },
                    )

                if not endpoint_data.get("endpoint_path"):
                    messages.error(request, "Endpoint Path is required.")
                    return render(
                        request,
                        "documentation/endpoints/form_enhanced.html",
                        {
                            "endpoint": endpoint,
                            "is_edit": is_edit,
                            "active_tab": request.GET.get("tab", "basic"),
                        },
                    )

            if is_edit and endpoint_id:
                validated_id = _validate_endpoint_id(endpoint_id)
                if not validated_id:
                    messages.error(request, "Invalid endpoint ID.")
                    return redirect("documentation:endpoints_list")

                updated = endpoints_service.update_endpoint(validated_id, endpoint_data)
                if updated:
                    logger.info("Endpoint updated successfully: %s", validated_id)
                    messages.success(request, "Endpoint updated successfully.")
                    return redirect("documentation:endpoint_detail", endpoint_id=validated_id)
                else:
                    messages.error(request, "Failed to update endpoint.")
            else:
                created = endpoints_service.create_endpoint(endpoint_data)
                if created:
                    created_id = endpoint_data.get("endpoint_id")
                    logger.info("Endpoint created successfully: %s", created_id)
                    messages.success(request, "Endpoint created successfully.")
                    return redirect("documentation:endpoint_detail", endpoint_id=created_id)
                else:
                    messages.error(request, "Failed to create endpoint.")
        except Exception as e:
            logger.error("Error saving endpoint: %s", e, exc_info=True)
            messages.error(request, f"An error occurred: {str(e)}")

    if is_edit and endpoint_id:
        validated_id = _validate_endpoint_id(endpoint_id)
        if not validated_id:
            messages.error(request, "Invalid endpoint ID.")
            return redirect("documentation:endpoints_list")

        try:
            endpoint = endpoints_service.get_endpoint(validated_id)
            if not endpoint:
                logger.warning("Endpoint not found: %s", validated_id)
                messages.error(request, "Endpoint not found.")
                return redirect("documentation:endpoints_list")
        except Exception as e:
            logger.error("Error loading endpoint %s: %s", validated_id, e, exc_info=True)
            messages.error(request, "An error occurred while loading the endpoint.")
            return redirect("documentation:endpoints_list")

    # Check if enhanced form should be used
    use_enhanced = request.GET.get("enhanced", "true").lower() == "true"
    template_name = "documentation/endpoints/form_enhanced.html" if use_enhanced else "documentation/endpoints/form.html"

    # Get active tab from URL query parameter
    active_tab = request.GET.get("tab", "basic")

    # Convert endpoint to JSON string for JavaScript initialization
    endpoint_json = json.dumps(endpoint, indent=2, default=str) if endpoint else "{}"

    context: Dict[str, Any] = {
        "endpoint": endpoint,
        "endpoint_json": endpoint_json,
        "is_edit": is_edit,
        "active_tab": active_tab,
        "return_url": request.GET.get("return_url"),
    }

    return render(request, template_name, context)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def endpoint_create_api(request: HttpRequest) -> JsonResponse:
    """API endpoint to create a new endpoint. POST /docs/api/endpoints/create/"""
    data, error_msg = _parse_json_body(request)
    if error_msg:
        logger.warning("Invalid request body in endpoint_create_api: %s", error_msg)
        return error_response(message=error_msg, status_code=400).to_json_response()

    try:
        created = endpoints_service.create_endpoint(data)
        if created:
            logger.info("Endpoint created successfully: %s", data.get("endpoint_id"))
            return success_response(data=created, message="Endpoint created successfully", status_code=201).to_json_response()
        else:
            logger.error("Failed to create endpoint: %s", data.get("endpoint_id"))
            return server_error_response("Failed to create endpoint").to_json_response()
    except Exception as e:
        logger.error("Error creating endpoint: %s", e, exc_info=True)
        return server_error_response(f"Error creating endpoint: {str(e)}").to_json_response()


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def endpoint_draft_api(request: HttpRequest) -> JsonResponse:
    """API endpoint to save endpoint draft (auto-save functionality). POST /docs/api/endpoints/draft/"""
    try:
        data, error_msg = _parse_json_body(request)
        if error_msg:
            logger.warning("Invalid request body in endpoint_draft_api: %s", error_msg)
            return error_response(message=error_msg, status_code=400).to_json_response()

        if not data:
            logger.warning("Empty data in endpoint_draft_api")
            return error_response(message="Request body is required", status_code=400).to_json_response()

        # Mark as draft if not already set
        if "metadata" not in data:
            data["metadata"] = {}
        data["metadata"]["status"] = "draft"

        # For drafts, we can use update if endpoint_id exists, otherwise create
        endpoint_id = data.get("endpoint_id") or data.get("endpoint_path")

        if endpoint_id:
            # Update existing draft
            try:
                updated = endpoints_service.update_endpoint(endpoint_id, data)
                if updated:
                    logger.info("Endpoint draft updated: %s", endpoint_id)
                    return success_response(data=updated, message="Draft saved successfully").to_json_response()
                else:
                    logger.warning("Endpoint draft update returned None for: %s", endpoint_id)
                    return server_error_response("Failed to update draft").to_json_response()
            except Exception as e:
                logger.error("Error updating endpoint draft %s: %s", endpoint_id, e, exc_info=True)
                return server_error_response(f"Error updating draft: {str(e)}").to_json_response()
        else:
            # Create new draft
            try:
                created = endpoints_service.create_endpoint(data)
                if created:
                    logger.info("Endpoint draft created: %s", created.get("endpoint_id"))
                    return success_response(data=created, message="Draft saved successfully", status_code=201).to_json_response()
                else:
                    logger.warning("Endpoint draft creation returned None")
                    return server_error_response("Failed to create draft").to_json_response()
            except Exception as e:
                logger.error("Error creating endpoint draft: %s", e, exc_info=True)
                return server_error_response(f"Error creating draft: {str(e)}").to_json_response()

    except Exception as e:
        logger.error("Unexpected error in endpoint_draft_api: %s", e, exc_info=True)
        return server_error_response(f"Unexpected error: {str(e)}").to_json_response()


@login_required
@require_http_methods(["PUT", "PATCH"])
@csrf_exempt
def endpoint_update_api(request: HttpRequest, endpoint_id: str) -> JsonResponse:
    """API endpoint to update an endpoint. PUT/PATCH /docs/api/endpoints/<endpoint_id>/"""
    validated_id = _validate_endpoint_id(endpoint_id)
    if not validated_id:
        return error_response(message="Invalid endpoint ID", status_code=400).to_json_response()

    data, error_msg = _parse_json_body(request)
    if error_msg:
        logger.warning("Invalid request body in endpoint_update_api: %s", error_msg)
        return error_response(message=error_msg, status_code=400).to_json_response()

    try:
        updated = endpoints_service.update_endpoint(validated_id, data)
        if updated:
            logger.info("Endpoint updated successfully: %s", validated_id)
            return success_response(data=updated, message="Endpoint updated successfully").to_json_response()
        else:
            logger.warning("Endpoint not found for update: %s", validated_id)
            return not_found_response("Endpoint").to_json_response()
    except Exception as e:
        logger.error("Error updating endpoint %s: %s", validated_id, e, exc_info=True)
        return server_error_response(f"Error updating endpoint: {str(e)}").to_json_response()


@login_required
@require_http_methods(["DELETE"])
@csrf_exempt
def endpoint_delete_api(request: HttpRequest, endpoint_id: str) -> JsonResponse:
    """API endpoint to delete an endpoint. DELETE /docs/api/endpoints/<endpoint_id>/"""
    validated_id = _validate_endpoint_id(endpoint_id)
    if not validated_id:
        return error_response(message="Invalid endpoint ID", status_code=400).to_json_response()

    try:
        deleted = endpoints_service.delete_endpoint(validated_id)
        if deleted:
            logger.info("Endpoint deleted successfully: %s", validated_id)
            return success_response(message="Endpoint deleted successfully").to_json_response()
        else:
            logger.warning("Endpoint not found for deletion: %s", validated_id)
            return not_found_response("Endpoint").to_json_response()
    except Exception as e:
        logger.error("Error deleting endpoint %s: %s", validated_id, e, exc_info=True)
        return server_error_response(f"Error deleting endpoint: {str(e)}").to_json_response()


@login_required
def endpoint_delete_view(request: HttpRequest, endpoint_id: str) -> HttpResponse:
    """Delete endpoint view. GET/POST /docs/endpoints/<endpoint_id>/delete/"""
    validated_id = _validate_endpoint_id(endpoint_id)
    if not validated_id:
        messages.error(request, "Invalid endpoint ID.")
        return redirect("documentation:endpoints_list")

    if request.method == "POST":
        try:
            success = endpoints_service.delete_endpoint(validated_id)
            if success:
                logger.info("Endpoint deleted successfully: %s", validated_id)
                messages.success(request, "Endpoint deleted successfully!")
            else:
                logger.warning("Failed to delete endpoint: %s", validated_id)
                messages.error(request, "Failed to delete endpoint.")
        except Exception as e:
            logger.error("Error deleting endpoint %s: %s", validated_id, e, exc_info=True)
            messages.error(request, "An error occurred while deleting the endpoint.")
        return redirect("documentation:endpoints_list")

    try:
        endpoint = endpoints_service.get_endpoint(validated_id)
        if not endpoint:
            logger.warning("Endpoint not found for deletion: %s", validated_id)
            messages.error(request, "Endpoint not found.")
            return redirect("documentation:endpoints_list")
    except Exception as e:
        logger.error("Error loading endpoint %s: %s", validated_id, e, exc_info=True)
        messages.error(request, "An error occurred while loading the endpoint.")
        return redirect("documentation:endpoints_list")

    context: Dict[str, Any] = {
        "endpoint": endpoint,
    }
    return render(request, "documentation/endpoints/delete_confirm.html", context)
