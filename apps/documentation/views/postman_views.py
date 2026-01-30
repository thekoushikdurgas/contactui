"""Views for Postman operations."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from apps.documentation.services import postman_service, endpoints_service
from apps.documentation.utils.view_helpers import validate_detail_tab

logger = logging.getLogger(__name__)

VALID_DETAIL_TABS = frozenset({"overview", "collection", "requests", "environments", "mappings", "raw"})

# Use shared helper function (Task 2.3.1)
def _validate_detail_tab(tab: Optional[str]) -> str:
    """Validate detail tab for postman (uses shared helper)."""
    return validate_detail_tab(tab, "postman")


def _validate_postman_id(postman_id: Optional[str]) -> Optional[str]:
    """Validate Postman ID. Returns None if invalid."""
    if not postman_id or not postman_id.strip():
        return None
    return postman_id.strip()


def _safe_redirect_url(request: HttpRequest, default_name: str = "documentation:dashboard"):
    """Return redirect target: return_url if present and safe, else default."""
    return_url = request.GET.get("return_url") or request.POST.get("return_url", "")
    if return_url and return_url.startswith("/") and "//" not in return_url:
        from django.utils.http import url_has_allowed_host_and_scheme
        if url_has_allowed_host_and_scheme(return_url, allowed_hosts={request.get_host(), None}):
            return return_url
    return reverse(default_name)


@login_required
def postman_delete_view(request: HttpRequest, postman_id: str) -> HttpResponse:
    """Delete Postman configuration view. GET/POST /docs/postman/<postman_id>/delete/"""
    validated_id = _validate_postman_id(postman_id)
    if not validated_id:
        messages.error(request, "Invalid Postman configuration ID.")
        return redirect(_safe_redirect_url(request))

    if request.method == "POST":
        try:
            success = postman_service.delete_configuration(validated_id)
            if success:
                logger.info("Postman configuration deleted successfully: %s", validated_id)
                messages.success(request, "Postman configuration deleted successfully!")
            else:
                logger.warning("Failed to delete Postman configuration: %s", validated_id)
                messages.error(request, "Failed to delete Postman configuration.")
        except Exception as e:
            logger.error("Error deleting Postman configuration %s: %s", validated_id, e, exc_info=True)
            messages.error(request, "An error occurred while deleting the Postman configuration.")
        return redirect(_safe_redirect_url(request))

    try:
        postman_config = postman_service.get_configuration(validated_id)
        if not postman_config:
            logger.warning("Postman configuration not found for deletion: %s", validated_id)
            messages.error(request, "Postman configuration not found.")
            return redirect(_safe_redirect_url(request))
    except Exception as e:
        logger.error("Error loading Postman configuration %s: %s", validated_id, e, exc_info=True)
        messages.error(request, "An error occurred while loading the Postman configuration.")
        return redirect(_safe_redirect_url(request))

    return_url = request.GET.get("return_url", "")
    context: Dict[str, Any] = {
        "postman": postman_config,
        "postman_id": validated_id,
        "return_url": return_url,
    }
    return render(request, "documentation/postman/delete_confirm.html", context)


@login_required
def postman_detail_view(request: HttpRequest, postman_id: str) -> HttpResponse:
    """Get single Postman configuration detail with enhanced tabs and related data. GET /docs/postman/<postman_id>/"""
    validated_id = _validate_postman_id(postman_id)
    if not validated_id:
        messages.error(request, "Postman ID is required.")
        return redirect("documentation:dashboard")

    active_tab = _validate_detail_tab(request.GET.get("tab"))

    try:
        # Get Postman configuration
        postman_config = postman_service.get_configuration(validated_id)
        if not postman_config:
            logger.warning("Postman configuration not found: %s", validated_id)
            messages.error(request, "Postman configuration not found.")
            return redirect("documentation:dashboard")
        
        # Get collection data (if available)
        collection = None
        try:
            collection = postman_service.get_collection(postman_id)
        except Exception as e:
            logger.debug(f"Could not load collection for {postman_id}: {e}")
        
        # Extract items/requests from collection
        requests = []
        if collection and isinstance(collection, dict):
            items = collection.get('item', [])
            # Flatten items recursively
            def extract_requests(items_list, folder_path=''):
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
        
        # Get environments
        environments = []
        try:
            environments = postman_service.get_environments(postman_id)
        except Exception as e:
            logger.debug(f"Could not load environments for {postman_id}: {e}")
        
        # Get endpoint mappings
        endpoint_mappings = []
        try:
            endpoint_mappings = postman_service.get_endpoint_mappings(postman_id)
        except Exception as e:
            logger.debug(f"Could not load endpoint mappings for {postman_id}: {e}")
        
        # Get related endpoints (if mappings exist)
        related_endpoints = []
        if endpoint_mappings:
            for mapping in endpoint_mappings:
                endpoint_id = mapping.get('endpoint_id')
                if endpoint_id:
                    try:
                        endpoint = endpoints_service.get_endpoint(endpoint_id)
                        if endpoint:
                            related_endpoints.append(endpoint)
                    except Exception as e:
                        logger.debug(f"Could not load endpoint {endpoint_id}: {e}")
        
        # Extract variables from collection
        variables = []
        if collection and isinstance(collection, dict):
            variables = collection.get('variable', [])
        
        # Convert postman config to JSON string for Raw JSON tab
        postman_json = json.dumps(postman_config, indent=2, default=str)
        
        # Extract info from collection
        collection_info = {}
        if collection and isinstance(collection, dict):
            collection_info = collection.get('info', {})
        
        context = {
            'postman': postman_config,
            'postman_id': postman_id,
            'postman_json': postman_json,
            'active_tab': active_tab,
            'collection': collection,
            'collection_info': collection_info,
            'requests': requests,
            'requests_count': len(requests),
            'environments': environments,
            'environments_count': len(environments),
            'variables': variables,
            'variables_count': len(variables),
            'endpoint_mappings': endpoint_mappings,
            'mappings_count': len(endpoint_mappings),
            'related_endpoints': related_endpoints,
            'endpoints_count': len(related_endpoints),
        }
    except Exception as e:
        logger.error(f"Error loading Postman configuration {postman_id}: {e}", exc_info=True)
        messages.error(request, 'An error occurred while loading the Postman configuration.')
        return redirect('documentation:dashboard')
    
    return render(request, 'documentation/postman/detail.html', context)


@login_required
def postman_form_view(request: HttpRequest, postman_id: Optional[str] = None) -> HttpResponse:
    """Postman collection create/edit form with enhanced tabs and comprehensive data collection. GET/POST /docs/postman/create/ or /docs/postman/<postman_id>/edit/"""
    active_tab = request.GET.get("tab", "basic")
    return_url = request.GET.get("return_url")
    is_edit = postman_id is not None

    postman_config: Optional[Dict[str, Any]] = None
    collection: Optional[Dict[str, Any]] = None
    collection_json = "{}"
    postman_json = "{}"

    # Load postman configuration and collection if editing
    if is_edit and postman_id:
        validated_id = _validate_postman_id(postman_id)
        if not validated_id:
            messages.error(request, "Invalid Postman ID.")
            return redirect("documentation:dashboard")

        try:
            postman_config = postman_service.get_configuration(validated_id)
            if postman_config:
                postman_json = json.dumps(postman_config, indent=2, default=str)
            else:
                logger.warning("Postman configuration not found: %s", validated_id)
                messages.error(request, "Postman configuration not found.")
                return redirect("documentation:dashboard")

            collection = postman_service.get_collection(validated_id)
            if collection:
                collection_json = json.dumps(collection, indent=2, default=str)
        except Exception as e:
            logger.warning("Could not load postman %s: %s", validated_id, e)
            messages.error(request, "An error occurred while loading the Postman configuration.")
            return redirect("documentation:dashboard")
    
    if request.method == "POST":
        try:
            # Check if enhanced form data is present
            collection_data_json = request.POST.get("collection_data")
            if collection_data_json:
                # Enhanced form submission
                try:
                    collection_data = json.loads(collection_data_json)
                except json.JSONDecodeError as e:
                    logger.warning("Invalid JSON in postman form: %s", e)
                    messages.error(request, "Invalid form data format.")
                    return render(
                        request,
                        "documentation/postman/form_enhanced.html",
                        {
                            "postman": postman_config,
                            "collection": collection,
                            "collection_json": collection_json,
                            "postman_json": postman_json,
                            "is_edit": is_edit,
                            "active_tab": active_tab,
                            "return_url": return_url,
                            "collection_info": {},
                            "variables": [],
                            "variables_count": 0,
                        },
                    )
            else:
                # Collect form data from all tabs
                # Build collection structure
                info_data: Dict[str, Any] = {
                    "name": request.POST.get("collection_name", ""),
                    "description": request.POST.get("collection_description", ""),
                    "schema": request.POST.get(
                        "collection_schema",
                        "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
                    ),
                }

                if is_edit and postman_id:
                    validated_id = _validate_postman_id(postman_id)
                    if validated_id:
                        info_data["_postman_id"] = validated_id

                collection_data: Dict[str, Any] = {
                    "info": info_data,
                    "item": [],  # Items will be managed separately or via JSON
                    "variable": [],  # Variables will be managed separately or via JSON
                }

                # Add collection ID
                collection_id = request.POST.get("collection_id") or (postman_id if is_edit else None)
                if collection_id:
                    collection_data["id"] = collection_id
                    collection_data["_id"] = collection_id

            # Validate required fields
            if not collection_data.get("id") and not (is_edit and postman_id):
                messages.error(request, "Collection ID is required.")
                return render(
                    request,
                    "documentation/postman/form_enhanced.html",
                    {
                        "postman": postman_config,
                        "collection": collection,
                        "collection_json": collection_json,
                        "postman_json": postman_json,
                        "is_edit": is_edit,
                        "active_tab": request.GET.get("tab", "basic"),
                        "return_url": return_url,
                        "collection_info": {},
                        "variables": [],
                        "variables_count": 0,
                    },
                )

            collection_id = collection_data.get("id") or (postman_id if is_edit else None)
            if not collection_id:
                messages.error(request, "Collection ID is required.")
                return redirect("documentation:dashboard")

            if not collection_data.get("info", {}).get("name"):
                messages.error(request, "Collection name is required.")
                return render(
                    request,
                    "documentation/postman/form_enhanced.html",
                    {
                        "postman": postman_config,
                        "collection": collection,
                        "collection_json": collection_json,
                        "postman_json": postman_json,
                        "is_edit": is_edit,
                        "active_tab": request.GET.get("tab", "basic"),
                        "return_url": return_url,
                        "collection_info": {},
                        "variables": [],
                        "variables_count": 0,
                    },
                )

            # Save collection - repository expects collection data directly
            if is_edit and postman_id:
                validated_id = _validate_postman_id(postman_id)
                if not validated_id:
                    messages.error(request, "Invalid Postman ID.")
                    return redirect("documentation:dashboard")

                # Update existing collection
                updated = postman_service.repository.update_collection(validated_id, collection_data)
                if updated:
                    logger.info("Postman collection updated successfully: %s", validated_id)
                    messages.success(request, "Postman collection updated successfully.")
                    if return_url:
                        return redirect(return_url)
                    return redirect("documentation:postman_detail", postman_id=validated_id)
                else:
                    messages.error(request, "Failed to update Postman collection.")
            else:
                # Create new collection
                created = postman_service.repository.create_collection(collection_data)
                if created:
                    logger.info("Postman collection created successfully: %s", collection_id)
                    messages.success(request, "Postman collection created successfully.")
                    if return_url:
                        return redirect(return_url)
                    return redirect("documentation:postman_detail", postman_id=collection_id)
                else:
                    messages.error(request, "Failed to create Postman collection.")
        except Exception as e:
            logger.error("Error saving Postman collection: %s", e, exc_info=True)
            messages.error(request, f"An error occurred: {str(e)}")

    # Extract collection info for form
    collection_info: Dict[str, Any] = {}
    if collection and isinstance(collection, dict):
        collection_info = dict(collection.get("info", {}))

    # Extract variables for form
    variables: List[Dict[str, Any]] = []
    if collection and isinstance(collection, dict):
        variables = list(collection.get("variable", []))

    context: Dict[str, Any] = {
        "postman": postman_config,
        "postman_id": postman_id if is_edit else None,
        "collection": collection,
        "collection_info": collection_info,
        "collection_json": collection_json,
        "postman_json": postman_json,
        "variables": variables,
        "variables_count": len(variables),
        "is_edit": is_edit,
        "active_tab": active_tab,
        "return_url": return_url,
    }

    return render(request, "documentation/postman/form_enhanced.html", context)
