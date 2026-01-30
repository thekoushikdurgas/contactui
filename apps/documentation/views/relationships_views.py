"""Views for relationship operations."""

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

from apps.documentation.services import relationships_service, pages_service, endpoints_service
from apps.documentation.utils.api_responses import (
    APIResponse,
    error_response,
    not_found_response,
    server_error_response,
    success_response,
)

logger = logging.getLogger(__name__)

DEFAULT_RELATIONSHIP_LIMIT = 20
MAX_RELATIONSHIP_LIMIT = 500
DEFAULT_OFFSET = 0
VALID_DETAIL_TABS = frozenset({"overview", "connection", "usage", "related", "raw"})


# Use shared helper functions (Task 2.3.1)
from apps.documentation.utils.view_helpers import (
    parse_limit_offset,
    parse_json_body,
    validate_detail_tab,
)

def _parse_limit_offset(request: HttpRequest) -> Tuple[int, int]:
    """Parse limit/offset for relationships (uses shared helper)."""
    return parse_limit_offset(request, DEFAULT_RELATIONSHIP_LIMIT, MAX_RELATIONSHIP_LIMIT, DEFAULT_OFFSET)

def _parse_json_body(request: HttpRequest) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Parse JSON body (uses shared helper)."""
    return parse_json_body(request)

def _validate_detail_tab(tab: Optional[str]) -> str:
    """Validate detail tab for relationships (uses shared helper)."""
    return validate_detail_tab(tab, "relationships")


def _validate_relationship_id(relationship_id: Optional[str]) -> Optional[str]:
    """Validate relationship ID. Returns None if invalid."""
    if not relationship_id or not relationship_id.strip():
        return None
    return relationship_id.strip()


def _safe_redirect_url(request: HttpRequest, default_name: str = "documentation:relationships_list"):
    """Return redirect target: return_url if present and safe, else default."""
    return_url = request.GET.get("return_url") or request.POST.get("return_url", "")
    if return_url and return_url.startswith("/") and "//" not in return_url:
        from django.utils.http import url_has_allowed_host_and_scheme
        if url_has_allowed_host_and_scheme(return_url, allowed_hosts={request.get_host(), None}):
            return return_url
    return reverse(default_name)


@login_required
def relationship_list_view(request):
    """List all relationships."""
    from apps.documentation.services import get_shared_local_storage
    local_storage = get_shared_local_storage()
    
    try:
        relationships_index = local_storage.get_index('relationships')
        relationships = relationships_index.get('relationships', [])
        
        # Apply filters if provided
        page_path = request.GET.get('page_path')
        endpoint_path = request.GET.get('endpoint_path')
        method = request.GET.get('method')
        
        filtered_relationships = relationships
        if page_path:
            filtered_relationships = [r for r in filtered_relationships if page_path in str(r)]
        if endpoint_path:
            filtered_relationships = [r for r in filtered_relationships if endpoint_path in str(r)]
        
        # Filter out relationships without valid relationship_id (empty string, None, or missing)
        filtered_relationships = [
            r for r in filtered_relationships 
            if r.get('relationship_id') and str(r.get('relationship_id')).strip()
        ]
        
        context = {
            'relationships': filtered_relationships[:50],  # Limit to 50
            'total': len(filtered_relationships),
            'source': 'local'
        }
    except Exception as e:
        logger.error(f"Error listing relationships: {e}", exc_info=True)
        messages.error(request, 'An error occurred while loading relationships.')
        context = {'relationships': [], 'total': 0, 'source': 'error'}
    
    return render(request, 'documentation/relationships/list.html', context)


@login_required
def relationship_detail_view(request: HttpRequest, relationship_id: str) -> HttpResponse:
    """Get single relationship detail with enhanced tabs and related data. GET /docs/relationships/<relationship_id>/"""
    validated_id = _validate_relationship_id(relationship_id)
    if not validated_id:
        messages.error(request, "Relationship ID is required.")
        return redirect("documentation:relationships_list")

    active_tab = _validate_detail_tab(request.GET.get("tab"))

    try:
        relationship = relationships_service.get_relationship(validated_id)
        if not relationship:
            logger.warning("Relationship not found: %s", validated_id)
            messages.error(request, "Relationship not found.")
            return redirect("documentation:relationships_list")
        
        # Format usage_context for display (replace underscores with spaces)
        if relationship.get('usage_context'):
            relationship['usage_context_display'] = relationship['usage_context'].replace('_', ' ').title()
        
        # Get linked page details
        linked_page = None
        page_id = relationship.get('page_id') or relationship.get('page_path')
        if page_id:
            try:
                linked_page = pages_service.get_page(page_id)
            except Exception as e:
                logger.debug(f"Could not load page {page_id}: {e}")
        
        # Get linked endpoint details
        linked_endpoint = None
        endpoint_id = relationship.get('endpoint_id') or relationship.get('endpoint_path')
        endpoint_method = relationship.get('method', 'QUERY')
        if endpoint_id:
            try:
                linked_endpoint = endpoints_service.get_endpoint(endpoint_id)
            except Exception as e:
                logger.debug(f"Could not load endpoint {endpoint_id}: {e}")
        
        # Get related relationships (same page or endpoint)
        related_relationships = []
        try:
            # Get relationships for the same page
            if page_id:
                page_rels_result = relationships_service.list_relationships(page_id=page_id, limit=100)
                for rel in page_rels_result.get('relationships', []):
                    if rel.get('relationship_id') != relationship_id:
                        related_relationships.append(rel)
            
            # Get relationships for the same endpoint
            if endpoint_id:
                endpoint_rels_result = relationships_service.list_relationships(endpoint_id=endpoint_id, limit=100)
                for rel in endpoint_rels_result.get('relationships', []):
                    if rel.get('relationship_id') != relationship_id:
                        # Avoid duplicates
                        if not any(r.get('relationship_id') == rel.get('relationship_id') for r in related_relationships):
                            related_relationships.append(rel)
        except Exception as e:
            logger.warning(f"Failed to load related relationships: {e}")
        
        # Convert relationship to JSON string for Raw JSON tab
        relationship_json = json.dumps(relationship, indent=2, default=str)
        
        context = {
            'relationship': relationship,
            'relationship_json': relationship_json,
            'active_tab': active_tab,
            'linked_page': linked_page,
            'linked_endpoint': linked_endpoint,
            'related_relationships': related_relationships,
            'related_count': len(related_relationships),
        }
    except Exception as e:
        logger.error(f"Error loading relationship {relationship_id}: {e}", exc_info=True)
        messages.error(request, 'An error occurred while loading the relationship.')
        return redirect('documentation:relationships_list')
    
    return render(request, 'documentation/relationships/detail.html', context)


@login_required
def relationship_form_view(request: HttpRequest, relationship_id: Optional[str] = None) -> HttpResponse:
    """Relationship create/edit form with enhanced tabs and comprehensive data collection. GET/POST /docs/relationships/create/ or /docs/relationships/<relationship_id>/edit/"""
    active_tab = request.GET.get("tab", "basic")
    return_url = request.GET.get("return_url")
    is_edit = relationship_id is not None

    relationship: Optional[Dict[str, Any]] = None
    relationship_json = "{}"

    # Load relationship if editing
    if is_edit and relationship_id:
        validated_id = _validate_relationship_id(relationship_id)
        if not validated_id:
            messages.error(request, "Invalid relationship ID.")
            return redirect("documentation:relationships_list")

        try:
            relationship = relationships_service.get_relationship(validated_id)
            if relationship:
                relationship_json = json.dumps(relationship, indent=2, default=str)
            else:
                logger.warning("Relationship not found: %s", validated_id)
                messages.error(request, "Relationship not found.")
                return redirect("documentation:relationships_list")
        except Exception as e:
            logger.warning("Could not load relationship %s: %s", validated_id, e)
            messages.error(request, "An error occurred while loading the relationship.")
            return redirect("documentation:relationships_list")
    
    if request.method == "POST":
        try:
            # Check if enhanced form data is present
            relationship_data_json = request.POST.get("relationship_data")
            if relationship_data_json:
                # Enhanced form submission
                try:
                    relationship_data = json.loads(relationship_data_json)
                except json.JSONDecodeError as e:
                    logger.warning("Invalid JSON in relationship form: %s", e)
                    messages.error(request, "Invalid form data format.")
                    return render(
                        request,
                        "documentation/relationships/form_enhanced.html",
                        {
                            "relationship": relationship,
                            "relationship_json": relationship_json,
                            "is_edit": is_edit,
                            "active_tab": active_tab,
                            "return_url": return_url,
                            "available_pages": [],
                            "available_endpoints": [],
                        },
                    )
            else:
                # Collect form data from all tabs
                relationship_data = {
                    "relationship_id": request.POST.get("relationship_id", ""),
                    "page_id": request.POST.get("page_id") or request.POST.get("page_path", ""),
                    "page_path": request.POST.get("page_path", ""),
                    "endpoint_id": request.POST.get("endpoint_id") or request.POST.get("endpoint_path", ""),
                    "endpoint_path": request.POST.get("endpoint_path", ""),
                    "method": request.POST.get("method", "QUERY"),
                    "usage_type": request.POST.get("usage_type", "primary"),
                    "usage_context": request.POST.get("usage_context", ""),
                    "via_service": request.POST.get("via_service", ""),
                    "via_hook": request.POST.get("via_hook", ""),
                    "description": request.POST.get("description", ""),
                    "state": request.POST.get("state", "draft"),
                    "relationship_type": request.POST.get("relationship_type", ""),
                }

            # Validate required fields
            if not relationship_data.get("relationship_id"):
                messages.error(request, "Relationship ID is required.")
                return render(
                    request,
                    "documentation/relationships/form_enhanced.html",
                    {
                        "relationship": relationship,
                        "relationship_json": relationship_json,
                        "is_edit": is_edit,
                        "active_tab": request.GET.get("tab", "basic"),
                        "return_url": return_url,
                        "available_pages": [],
                        "available_endpoints": [],
                    },
                )

            if not relationship_data.get("page_id") and not relationship_data.get("page_path"):
                messages.error(request, "Page ID or Page Path is required.")
                return render(
                    request,
                    "documentation/relationships/form_enhanced.html",
                    {
                        "relationship": relationship,
                        "relationship_json": relationship_json,
                        "is_edit": is_edit,
                        "active_tab": request.GET.get("tab", "connection"),
                        "return_url": return_url,
                        "available_pages": [],
                        "available_endpoints": [],
                    },
                )

            if not relationship_data.get("endpoint_id") and not relationship_data.get("endpoint_path"):
                messages.error(request, "Endpoint ID or Endpoint Path is required.")
                return render(
                    request,
                    "documentation/relationships/form_enhanced.html",
                    {
                        "relationship": relationship,
                        "relationship_json": relationship_json,
                        "is_edit": is_edit,
                        "active_tab": request.GET.get("tab", "connection"),
                        "return_url": return_url,
                        "available_pages": [],
                        "available_endpoints": [],
                    },
                )

            # Save relationship
            if is_edit and relationship_id:
                validated_id = _validate_relationship_id(relationship_id)
                if not validated_id:
                    messages.error(request, "Invalid relationship ID.")
                    return redirect("documentation:relationships_list")

                updated = relationships_service.update_relationship(validated_id, relationship_data)
                if updated:
                    logger.info("Relationship updated successfully: %s", validated_id)
                    messages.success(request, "Relationship updated successfully.")
                    if return_url:
                        return redirect(return_url)
                    return redirect("documentation:relationship_detail", relationship_id=validated_id)
                else:
                    messages.error(request, "Failed to update relationship.")
            else:
                created = relationships_service.create_relationship(relationship_data)
                if created:
                    created_id = relationship_data.get("relationship_id")
                    logger.info("Relationship created successfully: %s", created_id)
                    messages.success(request, "Relationship created successfully.")
                    if return_url:
                        return redirect(return_url)
                    return redirect("documentation:relationship_detail", relationship_id=created_id)
                else:
                    messages.error(request, "Failed to create relationship.")
        except Exception as e:
            logger.error("Error saving relationship: %s", e, exc_info=True)
            messages.error(request, f"An error occurred: {str(e)}")

    # Get available pages and endpoints for selection
    available_pages: List[Dict[str, Any]] = []
    available_endpoints: List[Dict[str, Any]] = []
    try:
        pages_result = pages_service.list_pages(limit=100)
        available_pages = list(pages_result.get("pages", []))
    except Exception as e:
        logger.debug("Could not load pages: %s", e)

    try:
        endpoints_result = endpoints_service.list_endpoints(limit=100)
        available_endpoints = list(endpoints_result.get("endpoints", []))
    except Exception as e:
        logger.debug("Could not load endpoints: %s", e)

    # Use enhanced form template
    template_name = "documentation/relationships/form_enhanced.html"

    context: Dict[str, Any] = {
        "relationship": relationship,
        "relationship_json": relationship_json,
        "is_edit": is_edit,
        "active_tab": active_tab,
        "return_url": return_url,
        "available_pages": available_pages,
        "available_endpoints": available_endpoints,
    }

    return render(request, template_name, context)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def relationship_create_api(request: HttpRequest) -> JsonResponse:
    """API endpoint to create a new relationship. POST /docs/api/relationships/create/"""
    data, error_msg = _parse_json_body(request)
    if error_msg:
        logger.warning("Invalid request body in relationship_create_api: %s", error_msg)
        return error_response(message=error_msg, status_code=400).to_json_response()

    try:
        created = relationships_service.create_relationship(data)
        if created:
            logger.info("Relationship created successfully: %s", data.get("relationship_id"))
            return success_response(data=created, message="Relationship created successfully", status_code=201).to_json_response()
        else:
            logger.error("Failed to create relationship: %s", data.get("relationship_id"))
            return server_error_response("Failed to create relationship").to_json_response()
    except Exception as e:
        logger.error("Error creating relationship: %s", e, exc_info=True)
        return server_error_response(f"Error creating relationship: {str(e)}").to_json_response()


@login_required
@require_http_methods(["PUT", "PATCH"])
@csrf_exempt
def relationship_update_api(request: HttpRequest, relationship_id: str) -> JsonResponse:
    """API endpoint to update a relationship. PUT/PATCH /docs/api/relationships/<relationship_id>/"""
    validated_id = _validate_relationship_id(relationship_id)
    if not validated_id:
        return error_response(message="Invalid relationship ID", status_code=400).to_json_response()

    data, error_msg = _parse_json_body(request)
    if error_msg:
        logger.warning("Invalid request body in relationship_update_api: %s", error_msg)
        return error_response(message=error_msg, status_code=400).to_json_response()

    try:
        updated = relationships_service.update_relationship(validated_id, data)
        if updated:
            logger.info("Relationship updated successfully: %s", validated_id)
            return success_response(data=updated, message="Relationship updated successfully").to_json_response()
        else:
            logger.warning("Relationship not found for update: %s", validated_id)
            return not_found_response("Relationship").to_json_response()
    except Exception as e:
        logger.error("Error updating relationship %s: %s", validated_id, e, exc_info=True)
        return server_error_response(f"Error updating relationship: {str(e)}").to_json_response()


@login_required
def relationship_delete_view(request: HttpRequest, relationship_id: str) -> HttpResponse:
    """Delete relationship view. GET/POST /docs/relationships/<relationship_id>/delete/"""
    validated_id = _validate_relationship_id(relationship_id)
    if not validated_id:
        messages.error(request, "Invalid relationship ID.")
        return redirect(_safe_redirect_url(request))

    if request.method == "POST":
        try:
            success = relationships_service.delete_relationship(validated_id)
            if success:
                logger.info("Relationship deleted successfully: %s", validated_id)
                messages.success(request, "Relationship deleted successfully!")
            else:
                logger.warning("Failed to delete relationship: %s", validated_id)
                messages.error(request, "Failed to delete relationship.")
        except Exception as e:
            logger.error("Error deleting relationship %s: %s", validated_id, e, exc_info=True)
            messages.error(request, "An error occurred while deleting the relationship.")
        return redirect(_safe_redirect_url(request))

    try:
        relationship = relationships_service.get_relationship(validated_id)
        if not relationship:
            logger.warning("Relationship not found for deletion: %s", validated_id)
            messages.error(request, "Relationship not found.")
            return redirect(_safe_redirect_url(request))
    except Exception as e:
        logger.error("Error loading relationship %s: %s", validated_id, e, exc_info=True)
        messages.error(request, "An error occurred while loading the relationship.")
        return redirect(_safe_redirect_url(request))

    return_url = request.GET.get("return_url", "")
    context: Dict[str, Any] = {
        "relationship": relationship,
        "return_url": return_url,
    }
    return render(request, "documentation/relationships/delete_confirm.html", context)


@login_required
@require_http_methods(["DELETE"])
@csrf_exempt
def relationship_delete_api(request: HttpRequest, relationship_id: str) -> JsonResponse:
    """API endpoint to delete a relationship. DELETE /docs/api/relationships/<relationship_id>/"""
    validated_id = _validate_relationship_id(relationship_id)
    if not validated_id:
        return error_response(message="Invalid relationship ID", status_code=400).to_json_response()

    try:
        deleted = relationships_service.delete_relationship(validated_id)
        if deleted:
            logger.info("Relationship deleted successfully: %s", validated_id)
            return success_response(message="Relationship deleted successfully").to_json_response()
        else:
            logger.warning("Relationship not found for deletion: %s", validated_id)
            return not_found_response("Relationship").to_json_response()
    except Exception as e:
        logger.error("Error deleting relationship %s: %s", validated_id, e, exc_info=True)
        return server_error_response(f"Error deleting relationship: {str(e)}").to_json_response()
