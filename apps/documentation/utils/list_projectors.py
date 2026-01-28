"""
List-item (summary) projectors for DocsAI resources.

Goal: list endpoints should return lightweight items by default, while detail endpoints
return full documents. Use the query param `expand=full` to opt into full items.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


def should_expand_full(query_params: Any) -> bool:
    """
    Returns True when the caller requested full expansion.

    Supports either a Django request (`request.GET`) or a dict-like mapping.
    """
    try:
        expand = query_params.get("expand")
    except Exception:
        expand = None
    return str(expand or "").lower() == "full"


def _safe_get(d: Optional[Dict[str, Any]], *keys: str) -> Any:
    cur: Any = d or {}
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur


def to_page_list_item(page: Dict[str, Any]) -> Dict[str, Any]:
    md = page.get("metadata") if isinstance(page.get("metadata"), dict) else {}
    return {
        "page_id": page.get("page_id"),
        "page_type": page.get("page_type"),
        "route": md.get("route") or page.get("route"),
        "title": md.get("title") or _safe_get(md, "content_sections", "title"),
        "status": md.get("status"),
        "updated_at": page.get("updated_at") or md.get("updated_at"),
        "created_at": page.get("created_at") or md.get("created_at"),
    }


def to_endpoint_list_item(endpoint: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "endpoint_id": endpoint.get("endpoint_id"),
        "method": (endpoint.get("method") or "").upper() or None,
        "api_version": endpoint.get("api_version"),
        "endpoint_path": endpoint.get("endpoint_path") or endpoint.get("path"),
        "state": endpoint.get("endpoint_state") or endpoint.get("state"),
        "description": endpoint.get("description") or endpoint.get("summary"),
    }


def to_relationship_list_item(rel: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "relationship_id": rel.get("relationship_id"),
        "page_id": rel.get("page_id") or rel.get("page_path"),
        "endpoint_path": rel.get("endpoint_path"),
        "method": (rel.get("method") or "").upper() or None,
        "usage_type": rel.get("usage_type"),
        "usage_context": rel.get("usage_context"),
        "state": rel.get("relationship_state") or rel.get("state"),
    }


def to_postman_list_item(cfg: Dict[str, Any]) -> Dict[str, Any]:
    md = cfg.get("metadata") if isinstance(cfg.get("metadata"), dict) else {}
    return {
        "config_id": cfg.get("config_id") or cfg.get("id"),
        "name": cfg.get("name") or md.get("name"),
        "state": cfg.get("state") or md.get("state"),
        "collection_id": _safe_get(cfg, "collection", "id") or _safe_get(cfg, "collection", "collection_id"),
        "updated_at": cfg.get("updated_at") or md.get("updated_at"),
    }

