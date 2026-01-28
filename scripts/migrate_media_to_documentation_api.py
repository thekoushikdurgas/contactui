"""
Migrate docs_ai_agent/media JSON files to match lambda/documentation.api storage contracts.

This script normalizes:
- pages JSONs (ids, metadata.s3_key, status/page_state, computed fields)
- endpoints JSONs (ids, method casing, required fields, page_count)
- relationships (regenerated from pages.metadata.uses_endpoints into by-page/by-endpoint + index.json)
- index.json files for pages/endpoints/relationships
- minimal Postman configuration wrapper (non-destructive to raw Postman JSON)

It is intentionally conservative:
- keeps existing non-canonical project/report JSONs untouched
- preserves unknown fields where possible
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

# Import shared utilities
from scripts.utils.upload_helpers import (
    sanitize_path,
    normalize_method,
    normalize_endpoint_path,
)
from scripts.utils.validators import load_json_file as shared_load_json_file


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_json_load(path: Path) -> Optional[Dict[str, Any]]:
    """Load JSON file safely - uses shared utility."""
    data, error = shared_load_json_file(path)
    return data if not error else None


def safe_json_dump(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def title_from_page_id(page_id: str) -> str:
    s = page_id.replace("_", " ").replace("-", " ").strip()
    s = " ".join([w for w in s.split(" ") if w])
    return s.title() if s else page_id


def derive_page_state_from_status(status: str) -> str:
    if status in ("published", "draft"):
        return status
    if status == "deleted":
        return "draft"
    return "development"


def derive_status_from_page_state(page_state: str) -> str:
    if page_state == "published":
        return "published"
    if page_state == "draft":
        return "draft"
    # coming_soon/development/test -> draft (validator only allows published/draft/deleted)
    return "draft"


# sanitize_path, normalize_method, normalize_endpoint_path are now imported from scripts.utils.upload_helpers


def generate_relationship_id(page_path: str, endpoint_path: str, method: str) -> str:
    return f"{sanitize_path(page_path)}_{sanitize_path(endpoint_path)}_{normalize_method(method)}"


@dataclass(frozen=True)
class PageInfo:
    page_id: str
    route: str
    title: str
    created_at: str
    last_updated: str


def normalize_page_doc(doc: Dict[str, Any], *, filename: str) -> Tuple[Dict[str, Any], List[str]]:
    issues: List[str] = []

    page_id = doc.get("page_id")
    if not isinstance(page_id, str) or not page_id:
        # best-effort derive from filename
        page_id = Path(filename).stem
        doc["page_id"] = page_id
        issues.append("missing page_id (derived from filename)")

    doc["_id"] = f"{page_id}-001"

    page_type = doc.get("page_type") or "docs"
    if page_type == "auth":
        page_type = "dashboard"
    doc["page_type"] = page_type

    created_at = doc.get("created_at")
    if not isinstance(created_at, str) or not created_at:
        created_at = iso_now()
        doc["created_at"] = created_at
        issues.append("missing created_at (set to now)")

    metadata = doc.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
        doc["metadata"] = metadata
        issues.append("missing metadata (created)")

    # Required metadata fields per PageSchemaValidator
    route = metadata.get("route")
    if not isinstance(route, str) or not route:
        route = doc.get("route") if isinstance(doc.get("route"), str) else ""
        metadata["route"] = route or "/"
        issues.append("missing metadata.route (set to '/')")

    metadata.setdefault("file_path", "")
    metadata.setdefault("purpose", "")
    metadata.setdefault("authentication", "Not specified")

    last_updated = metadata.get("last_updated")
    if not isinstance(last_updated, str) or not last_updated:
        metadata["last_updated"] = doc.get("updated_at") if isinstance(doc.get("updated_at"), str) else created_at
        issues.append("missing metadata.last_updated (derived)")

    # Ensure s3_key points to JSON file
    metadata["s3_key"] = f"data/pages/{page_id}.json"

    # status/page_state (validator requires status; index expects both)
    status = metadata.get("status")
    page_state = metadata.get("page_state")
    if not isinstance(page_state, str) or not page_state:
        if isinstance(status, str) and status:
            page_state = derive_page_state_from_status(status)
        else:
            page_state = "published"
        metadata["page_state"] = page_state
    if not isinstance(status, str) or not status:
        metadata["status"] = derive_status_from_page_state(page_state)
    else:
        # normalize status from page_state if invalid
        if status not in ("published", "draft", "deleted"):
            metadata["status"] = derive_status_from_page_state(page_state)

    # Normalize uses_endpoints
    uses_endpoints = metadata.get("uses_endpoints") or []
    if not isinstance(uses_endpoints, list):
        uses_endpoints = []
        issues.append("metadata.uses_endpoints not a list (reset)")
    normalized_uses: List[Dict[str, Any]] = []
    for i, ue in enumerate(uses_endpoints):
        if not isinstance(ue, dict):
            issues.append(f"metadata.uses_endpoints[{i}] not an object (skipped)")
            continue
        ep_path = ue.get("endpoint_path")
        method = normalize_method(ue.get("method"))
        api_version = ue.get("api_version")
        if not isinstance(api_version, str) or not api_version:
            api_version = "graphql" if method in ("QUERY", "MUTATION") else "v1"
        ep_path_norm = normalize_endpoint_path(api_version, ep_path)
        ue["endpoint_path"] = ep_path_norm
        ue["method"] = method
        ue["api_version"] = api_version
        ue.setdefault("via_service", "unknown")
        ue.setdefault("usage_type", "primary")
        ue.setdefault("usage_context", "data_fetching")
        normalized_uses.append(ue)
    metadata["uses_endpoints"] = normalized_uses
    metadata["endpoint_count"] = len(normalized_uses)
    metadata["api_versions"] = sorted({e.get("api_version") for e in normalized_uses if isinstance(e.get("api_version"), str)})

    # ui_components must be a list if present
    ui_components = metadata.get("ui_components") or []
    if not isinstance(ui_components, list):
        metadata["ui_components"] = []
        issues.append("metadata.ui_components not a list (reset)")

    return doc, issues


def normalize_endpoint_doc(doc: Dict[str, Any], *, filename: str) -> Tuple[Dict[str, Any], List[str]]:
    issues: List[str] = []
    endpoint_id = doc.get("endpoint_id")
    if not isinstance(endpoint_id, str) or not endpoint_id:
        endpoint_id = Path(filename).stem
        doc["endpoint_id"] = endpoint_id
        issues.append("missing endpoint_id (derived from filename)")

    doc["_id"] = f"{endpoint_id}-001"

    method = normalize_method(doc.get("method"))
    doc["method"] = method

    api_version = doc.get("api_version")
    if not isinstance(api_version, str) or not api_version:
        api_version = "graphql" if method in ("QUERY", "MUTATION") else "v1"
        doc["api_version"] = api_version

    endpoint_path = doc.get("endpoint_path")
    if not isinstance(endpoint_path, str) or not endpoint_path:
        doc["endpoint_path"] = ""
        issues.append("missing endpoint_path (set to empty)")
    else:
        doc["endpoint_path"] = normalize_endpoint_path(api_version, endpoint_path)

    doc.setdefault("authentication", "Not specified")
    doc.setdefault("description", "")

    created_at = doc.get("created_at")
    if not isinstance(created_at, str) or not created_at:
        created_at = iso_now()
        doc["created_at"] = created_at
        issues.append("missing created_at (set to now)")

    updated_at = doc.get("updated_at")
    if not isinstance(updated_at, str) or not updated_at:
        doc["updated_at"] = created_at
        issues.append("missing updated_at (set to created_at)")

    # Ensure at least one of router_file/service_file exists (validator requirement)
    if not doc.get("service_file") and not doc.get("router_file"):
        doc["router_file"] = "unknown"
        issues.append("missing router_file/service_file (set router_file='unknown')")

    # Endpoint state used by index filters (repository defaults to development)
    if not isinstance(doc.get("endpoint_state"), str) or not doc.get("endpoint_state"):
        doc["endpoint_state"] = "development"

    used_by_pages = doc.get("used_by_pages") or []
    if used_by_pages and not isinstance(used_by_pages, list):
        doc["used_by_pages"] = []
        issues.append("used_by_pages not a list (reset)")

    return doc, issues


def build_relationships_from_pages(
    pages: Dict[str, Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]], Dict[Tuple[str, str], List[Dict[str, Any]]]]:
    """Return (flat_relationships, by_page, by_endpoint)."""
    flat: List[Dict[str, Any]] = []
    by_page: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    by_endpoint: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)

    for page_id, page in pages.items():
        metadata = page.get("metadata", {}) if isinstance(page.get("metadata"), dict) else {}
        page_path = metadata.get("route") if isinstance(metadata.get("route"), str) else ""
        if not page_path:
            continue
        uses = metadata.get("uses_endpoints", []) if isinstance(metadata.get("uses_endpoints"), list) else []
        page_updated = metadata.get("last_updated") if isinstance(metadata.get("last_updated"), str) else page.get("created_at")
        page_title = title_from_page_id(page_id)
        for ue in uses:
            if not isinstance(ue, dict):
                continue
            endpoint_path = ue.get("endpoint_path")
            if not isinstance(endpoint_path, str) or not endpoint_path:
                continue
            method = normalize_method(ue.get("method"))
            api_version = ue.get("api_version") if isinstance(ue.get("api_version"), str) else "v1"
            endpoint_path = normalize_endpoint_path(api_version, endpoint_path)
            via_service = ue.get("via_service") if isinstance(ue.get("via_service"), str) else "unknown"
            via_hook = ue.get("via_hook") if isinstance(ue.get("via_hook"), str) else None
            usage_type = ue.get("usage_type") if isinstance(ue.get("usage_type"), str) else "primary"
            usage_context = ue.get("usage_context") if isinstance(ue.get("usage_context"), str) else "data_fetching"
            updated_at = ue.get("updated_at") if isinstance(ue.get("updated_at"), str) else page_updated

            rel = {
                "relationship_id": generate_relationship_id(page_path, endpoint_path, method),
                "page_path": page_path,
                "page_id": page_id,
                "endpoint_path": endpoint_path,
                "method": method,
                "api_version": api_version,
                "via_service": via_service,
                "via_hook": via_hook,
                "usage_type": usage_type,
                "usage_context": usage_context,
                "state": "development",
                "created_at": page.get("created_at") if isinstance(page.get("created_at"), str) else iso_now(),
                "updated_at": updated_at if isinstance(updated_at, str) else iso_now(),
            }

            flat.append(rel)
            by_page[page_path].append(
                {
                    "page_path": page_path,
                    "endpoint_path": endpoint_path,
                    "method": method,
                    "api_version": api_version,
                    "via_service": via_service,
                    "via_hook": via_hook,
                    "usage_type": usage_type,
                    "usage_context": usage_context,
                    "created_at": rel["created_at"],
                    "updated_at": rel["updated_at"],
                }
            )
            by_endpoint[(endpoint_path, method)].append(
                {
                    "page_path": page_path,
                    "page_title": page_title,
                    "via_service": via_service,
                    "via_hook": via_hook,
                    "usage_type": usage_type,
                    "usage_context": usage_context,
                    "updated_at": rel["updated_at"],
                }
            )

    # Deduplicate within groupings
    def uniq_dicts(items: List[Dict[str, Any]], key_fn) -> List[Dict[str, Any]]:
        seen = set()
        out = []
        for it in items:
            k = key_fn(it)
            if k in seen:
                continue
            seen.add(k)
            out.append(it)
        return out

    for page_path in list(by_page.keys()):
        by_page[page_path] = uniq_dicts(
            by_page[page_path],
            lambda r: (r.get("endpoint_path"), r.get("method"), r.get("usage_type"), r.get("usage_context"), r.get("via_service"), r.get("via_hook")),
        )

    for ep_key in list(by_endpoint.keys()):
        by_endpoint[ep_key] = uniq_dicts(
            by_endpoint[ep_key],
            lambda r: (r.get("page_path"), r.get("usage_type"), r.get("usage_context"), r.get("via_service"), r.get("via_hook")),
        )

    return flat, by_page, by_endpoint


def rebuild_pages_index(pages: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    index: Dict[str, Any] = {
        "version": "2.0",
        "last_updated": iso_now(),
        "total": 0,
        "pages": [],
        "indexes": {
            "by_type": {"docs": [], "marketing": [], "dashboard": []},
            "by_route": {},
            "by_status": {"published": [], "draft": [], "deleted": []},
            "by_page_state": {
                "coming_soon": [],
                "development": [],
                "draft": [],
                "test": [],
                "published": [],
            },
        },
        "statistics": {
            "total": 0,
            "by_type": {
                "docs": {"total": 0, "published": 0, "draft": 0, "deleted": 0},
                "marketing": {"total": 0, "published": 0, "draft": 0, "deleted": 0},
                "dashboard": {"total": 0, "published": 0, "draft": 0, "deleted": 0},
            },
            "by_status": {"published": 0, "draft": 0, "deleted": 0},
            "by_page_state": {"coming_soon": 0, "development": 0, "draft": 0, "test": 0, "published": 0},
        },
    }

    for page in pages:
        metadata = page.get("metadata", {}) if isinstance(page.get("metadata"), dict) else {}
        page_id = page.get("page_id")
        page_type = page.get("page_type", "docs")
        route = metadata.get("route", "")
        status = metadata.get("status", "published")
        page_state = metadata.get("page_state") or derive_page_state_from_status(status)
        entry = {
            "page_id": page_id,
            "page_type": page_type,
            "route": route,
            "status": status,
            "page_state": page_state,
            "_id": page.get("_id"),
            "created_at": page.get("created_at"),
            "access_control": page.get("access_control"),
            "metadata": {
                "route": metadata.get("route"),
                "file_path": metadata.get("file_path"),
                "purpose": metadata.get("purpose"),
                "s3_key": metadata.get("s3_key"),
                "status": status,
                "page_state": page_state,
                "authentication": metadata.get("authentication"),
                "authorization": metadata.get("authorization"),
                "last_updated": metadata.get("last_updated"),
                "versions": metadata.get("versions", []),
                "endpoint_count": metadata.get("endpoint_count", 0),
                "api_versions": metadata.get("api_versions", []),
                "uses_endpoints": metadata.get("uses_endpoints", []),
                "ui_components": metadata.get("ui_components", []),
            },
        }
        index["pages"].append(entry)

        if isinstance(page_id, str) and page_type in index["indexes"]["by_type"]:
            if page_id not in index["indexes"]["by_type"][page_type]:
                index["indexes"]["by_type"][page_type].append(page_id)
        if isinstance(route, str) and route:
            index["indexes"]["by_route"][route] = page_id
        if isinstance(page_id, str) and status in index["indexes"]["by_status"]:
            if page_id not in index["indexes"]["by_status"][status]:
                index["indexes"]["by_status"][status].append(page_id)
        if isinstance(page_id, str) and page_state in index["indexes"]["by_page_state"]:
            if page_id not in index["indexes"]["by_page_state"][page_state]:
                index["indexes"]["by_page_state"][page_state].append(page_id)

        if page_type in index["statistics"]["by_type"]:
            index["statistics"]["by_type"][page_type]["total"] += 1
            if status in ("published", "draft", "deleted"):
                index["statistics"]["by_type"][page_type][status] += 1
        if status in index["statistics"]["by_status"]:
            index["statistics"]["by_status"][status] += 1
        if page_state in index["statistics"]["by_page_state"]:
            index["statistics"]["by_page_state"][page_state] += 1

    index["total"] = len(index["pages"])
    index["statistics"]["total"] = len(index["pages"])
    return index


def rebuild_endpoints_index(endpoints: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    index: Dict[str, Any] = {
        "version": "2.0",
        "last_updated": iso_now(),
        "total": 0,
        "endpoints": [],
        "indexes": {
            "by_api_version": {},
            "by_method": {},
            "by_path_method": {},
            "by_endpoint_state": {"coming_soon": [], "development": [], "draft": [], "test": [], "published": []},
            "by_lambda_service": {},
        },
        "statistics": {
            "total": 0,
            "by_api_version": {},
            "by_method": {},
            "by_endpoint_state": {"coming_soon": 0, "development": 0, "draft": 0, "test": 0, "published": 0},
        },
    }

    def inc(d: Dict[str, int], k: str) -> None:
        d[k] = d.get(k, 0) + 1

    for ep in endpoints:
        endpoint_id = ep.get("endpoint_id")
        endpoint_path = ep.get("endpoint_path", "")
        method = ep.get("method", "GET")
        api_version = ep.get("api_version", "v1")
        endpoint_state = ep.get("endpoint_state", "development")
        lambda_services = ep.get("lambda_services") or {}
        primary = lambda_services.get("primary") if isinstance(lambda_services, dict) else None
        lambda_service_name = primary.get("service_name") if isinstance(primary, dict) else None

        entry = {
            "endpoint_id": endpoint_id,
            "endpoint_path": endpoint_path,
            "method": method,
            "api_version": api_version,
            "endpoint_state": endpoint_state,
            "lambda_service": lambda_service_name,
            "_id": ep.get("_id"),
            "router_file": ep.get("router_file"),
            "service_file": ep.get("service_file"),
            "service_methods": ep.get("service_methods", []),
            "repository_methods": ep.get("repository_methods", []),
            "authentication": ep.get("authentication"),
            "authorization": ep.get("authorization"),
            "rate_limit": ep.get("rate_limit"),
            "description": ep.get("description"),
            "graphql_operation": ep.get("graphql_operation"),
            "sql_file": ep.get("sql_file"),
            "page_count": ep.get("page_count", 0),
            "used_by_pages": ep.get("used_by_pages", []),
            "access_control": ep.get("access_control"),
            "lambda_services": ep.get("lambda_services"),
            "files": ep.get("files"),
            "methods": ep.get("methods"),
            "created_at": ep.get("created_at"),
            "updated_at": ep.get("updated_at"),
        }
        index["endpoints"].append(entry)

        if isinstance(endpoint_id, str):
            index["indexes"]["by_api_version"].setdefault(api_version, [])
            if endpoint_id not in index["indexes"]["by_api_version"][api_version]:
                index["indexes"]["by_api_version"][api_version].append(endpoint_id)
            index["indexes"]["by_method"].setdefault(method, [])
            if endpoint_id not in index["indexes"]["by_method"][method]:
                index["indexes"]["by_method"][method].append(endpoint_id)
            index["indexes"]["by_path_method"][f"{endpoint_path}:{method}"] = endpoint_id
            if endpoint_state in index["indexes"]["by_endpoint_state"]:
                if endpoint_id not in index["indexes"]["by_endpoint_state"][endpoint_state]:
                    index["indexes"]["by_endpoint_state"][endpoint_state].append(endpoint_id)
            if lambda_service_name:
                index["indexes"]["by_lambda_service"].setdefault(lambda_service_name, [])
                if endpoint_id not in index["indexes"]["by_lambda_service"][lambda_service_name]:
                    index["indexes"]["by_lambda_service"][lambda_service_name].append(endpoint_id)

        inc(index["statistics"]["by_api_version"], api_version)
        inc(index["statistics"]["by_method"], method)
        if endpoint_state in index["statistics"]["by_endpoint_state"]:
            index["statistics"]["by_endpoint_state"][endpoint_state] += 1

    index["total"] = len(index["endpoints"])
    index["statistics"]["total"] = len(index["endpoints"])
    return index


def rebuild_relationships_index(relationships: List[Dict[str, Any]]) -> Dict[str, Any]:
    idx: Dict[str, Any] = {
        "version": "2.0",
        "last_updated": iso_now(),
        "total": 0,
        "relationships": [],
        "indexes": {
            "by_page": {},
            "by_endpoint": {},
            "by_usage_type": {"primary": [], "secondary": [], "conditional": []},
            "by_usage_context": {"data_fetching": [], "data_mutation": [], "authentication": [], "analytics": []},
            "by_state": {"coming_soon": [], "development": [], "draft": [], "test": [], "published": []},
            "by_invocation_pattern": {},
            "by_postman_config_id": {},
            "by_lambda_service": {},
        },
        "statistics": {
            "total": 0,
            "unique_pages": 0,
            "unique_endpoints": 0,
            "by_api_version": {},
            "by_usage_type": {"primary": {"total": 0}, "secondary": {"total": 0}, "conditional": {"total": 0}},
            "by_usage_context": {
                "data_fetching": {"total": 0},
                "data_mutation": {"total": 0},
                "authentication": {"total": 0},
                "analytics": {"total": 0},
            },
            "by_state": {
                "coming_soon": {"total": 0},
                "development": {"total": 0},
                "draft": {"total": 0},
                "test": {"total": 0},
                "published": {"total": 0},
            },
        },
        "by_api_version": {},
    }

    def inc(d: Dict[str, int], k: str) -> None:
        d[k] = d.get(k, 0) + 1

    unique_pages = set()
    unique_endpoints = set()

    for rel in relationships:
        rid = rel.get("relationship_id") or generate_relationship_id(rel.get("page_path", ""), rel.get("endpoint_path", ""), rel.get("method", "GET"))
        rel["relationship_id"] = rid
        idx["relationships"].append(rel)

        page_path = rel.get("page_path", "")
        endpoint_key = f"{rel.get('endpoint_path', '')}:{rel.get('method', 'GET')}"
        usage_type = rel.get("usage_type", "primary")
        usage_context = rel.get("usage_context", "data_fetching")
        api_version = rel.get("api_version", "v1")
        state = rel.get("state", "development")

        if isinstance(page_path, str) and page_path:
            idx["indexes"]["by_page"].setdefault(page_path, [])
            idx["indexes"]["by_page"][page_path].append(rid)
            unique_pages.add(page_path)
        if isinstance(endpoint_key, str) and endpoint_key:
            idx["indexes"]["by_endpoint"].setdefault(endpoint_key, [])
            idx["indexes"]["by_endpoint"][endpoint_key].append(rid)
            unique_endpoints.add(endpoint_key)

        if usage_type in idx["indexes"]["by_usage_type"]:
            idx["indexes"]["by_usage_type"][usage_type].append(rid)
            idx["statistics"]["by_usage_type"][usage_type]["total"] += 1
        if usage_context in idx["indexes"]["by_usage_context"]:
            idx["indexes"]["by_usage_context"][usage_context].append(rid)
            idx["statistics"]["by_usage_context"][usage_context]["total"] += 1
        if state in idx["indexes"]["by_state"]:
            idx["indexes"]["by_state"][state].append(rid)
            idx["statistics"]["by_state"][state]["total"] += 1

        inc(idx["statistics"]["by_api_version"], api_version)
        idx["by_api_version"].setdefault(api_version, 0)
        idx["by_api_version"][api_version] += 1

    idx["total"] = len(idx["relationships"])
    idx["statistics"]["total"] = len(idx["relationships"])
    idx["statistics"]["unique_pages"] = len(unique_pages)
    idx["statistics"]["unique_endpoints"] = len(unique_endpoints)
    return idx


def write_relationship_files(
    relationships_dir: Path,
    by_page: Dict[str, List[Dict[str, Any]]],
    by_endpoint: Dict[Tuple[str, str], List[Dict[str, Any]]],
) -> None:
    by_page_dir = relationships_dir / "by-page"
    by_endpoint_dir = relationships_dir / "by-endpoint"
    by_page_dir.mkdir(parents=True, exist_ok=True)
    by_endpoint_dir.mkdir(parents=True, exist_ok=True)

    # Remove legacy root relationship JSON files (generated anew into by-page/by-endpoint)
    # Keep the index files which we'll overwrite separately.
    for p in relationships_dir.glob("*.json"):
        if p.name in ("index.json", "relationships_index.json"):
            continue
        p.unlink(missing_ok=True)

    # Remove existing generated files to avoid stale entries
    for p in list(by_page_dir.glob("*.json")):
        p.unlink(missing_ok=True)
    for p in list(by_endpoint_dir.glob("*.json")):
        p.unlink(missing_ok=True)

    now = iso_now()

    for page_path, endpoints in sorted(by_page.items(), key=lambda x: x[0]):
        payload = {
            "page_path": page_path,
            "endpoints": endpoints,
            "created_at": now,
            "updated_at": now,
        }
        safe_json_dump(by_page_dir / f"{sanitize_path(page_path)}.json", payload)

    for (endpoint_path, method), pages in sorted(by_endpoint.items(), key=lambda x: (x[0][0], x[0][1])):
        payload = {
            "endpoint_path": endpoint_path,
            "method": method,
            "pages": pages,
            "created_at": now,
            "updated_at": now,
        }
        safe_json_dump(by_endpoint_dir / f"{sanitize_path(endpoint_path)}_{method}.json", payload)


def ensure_postman_configuration(postman_dir: Path) -> None:
    """
    Create a minimal configuration wrapper that documentation.api can ingest.
    Does not modify raw Postman collection/environment JSON.
    """
    configs_dir = postman_dir / "configurations"
    configs_dir.mkdir(parents=True, exist_ok=True)
    config_id = "contact360"

    collections_dir = postman_dir / "collection"
    envs_dir = postman_dir / "environment"
    collections = sorted([p.name for p in collections_dir.glob("*.json")]) if collections_dir.exists() else []
    environments = sorted([p.name for p in envs_dir.glob("*.json")]) if envs_dir.exists() else []

    config = {
        "config_id": config_id,
        "name": "Contact360",
        "description": "Generated wrapper for Postman assets in docs_ai_agent/media/postman",
        "created_at": iso_now(),
        "updated_at": iso_now(),
        "state": "development",
        "collections": collections,
        "environments": environments,
        "default_collection": collections[0] if collections else None,
        "default_environment": environments[0] if environments else None,
        "endpoint_mappings": [],
        "test_suites": [],
        "metadata": {
            "source": "docs_ai_agent",
        },
    }
    safe_json_dump(configs_dir / f"{config_id}.json", config)

    index = {
        "version": "2.0",
        "last_updated": iso_now(),
        "total": 1,
        "configurations": [
            {
                "config_id": config_id,
                "name": config["name"],
                "state": config["state"],
                "created_at": config["created_at"],
                "updated_at": config["updated_at"],
            }
        ],
        "indexes": {
            "by_state": {"coming_soon": [], "development": [config_id], "draft": [], "test": [], "published": []},
        },
        "statistics": {"total": 1},
    }
    safe_json_dump(postman_dir / "index.json", index)


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate docs_ai_agent/media to documentation.api-compatible JSONs")
    parser.add_argument(
        "--media-root",
        default=None,
        help="Path to docs_ai_agent/media (defaults to repo/docs_ai_agent/media)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Compute changes but do not write files")
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    repo_root = script_path.parents[2]
    default_media_root = repo_root / "docs_ai_agent" / "media"
    media_root = Path(args.media_root).resolve() if args.media_root else default_media_root

    pages_dir = media_root / "pages"
    endpoints_dir = media_root / "endpoints"
    relationships_dir = media_root / "retations"
    postman_dir = media_root / "postman"

    if not pages_dir.exists() or not endpoints_dir.exists() or not relationships_dir.exists():
        print(f"Expected directories missing under: {media_root}")
        return 2

    # Import validators from lambda/documentation.api for verification
    validators_ok = False
    try:
        sys.path.insert(0, str(repo_root / "lambda" / "documentation.api"))
        from app.utils.schema_validators import PageSchemaValidator, EndpointSchemaValidator, RelationshipSchemaValidator  # type: ignore

        page_validator = PageSchemaValidator()
        endpoint_validator = EndpointSchemaValidator()
        relationship_validator = RelationshipSchemaValidator()
        validators_ok = True
    except Exception as e:
        print(f"Warning: failed to import schema validators (will skip validator checks): {e}")
        page_validator = None  # type: ignore
        endpoint_validator = None  # type: ignore
        relationship_validator = None  # type: ignore

    # Load and normalize pages
    pages: Dict[str, Dict[str, Any]] = {}
    page_issues: Dict[str, List[str]] = {}
    for p in sorted(pages_dir.glob("*.json")):
        if p.name in ("pages_index.json", "pages_index_example.json", "index.json"):
            continue
        doc = safe_json_load(p)
        if not isinstance(doc, dict) or "page_id" not in doc:
            continue
        norm, issues = normalize_page_doc(doc, filename=p.name)
        pid = norm.get("page_id")
        if isinstance(pid, str) and pid:
            pages[pid] = norm
            if issues:
                page_issues[p.name] = issues

    # Load and normalize endpoints (initial pass)
    endpoints: Dict[str, Dict[str, Any]] = {}
    endpoint_issues: Dict[str, List[str]] = {}
    for p in sorted(endpoints_dir.glob("*.json")):
        if p.name in ("endpoints_index.json", "index.json"):
            continue
        doc = safe_json_load(p)
        if not isinstance(doc, dict) or "endpoint_id" not in doc:
            continue
        norm, issues = normalize_endpoint_doc(doc, filename=p.name)
        eid = norm.get("endpoint_id")
        if isinstance(eid, str) and eid:
            endpoints[eid] = norm
            if issues:
                endpoint_issues[p.name] = issues

    # Rebuild relationships from pages uses_endpoints
    flat_rels, by_page, by_endpoint = build_relationships_from_pages(pages)

    # Rebuild endpoint used_by_pages from relationships
    endpoint_key_to_pages: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    for (endpoint_path, method), page_refs in by_endpoint.items():
        endpoint_key_to_pages[(endpoint_path, method)] = page_refs

    for eid, ep in endpoints.items():
        ep_path = ep.get("endpoint_path", "")
        method = ep.get("method", "GET")
        key = (ep_path, method)
        used_by = endpoint_key_to_pages.get(key, [])
        ep["used_by_pages"] = used_by
        ep["page_count"] = len(used_by)

    # Build indexes
    pages_index = rebuild_pages_index(pages.values())
    endpoints_index = rebuild_endpoints_index(endpoints.values())
    relationships_index = rebuild_relationships_index(flat_rels)

    if args.dry_run:
        print(f"DRY RUN: pages={len(pages)} endpoints={len(endpoints)} relationships={len(flat_rels)}")
        return 0

    # Write normalized pages/endpoints
    for pid, page in pages.items():
        safe_json_dump(pages_dir / f"{pid}.json", page)
    for eid, ep in endpoints.items():
        safe_json_dump(endpoints_dir / f"{eid}.json", ep)

    # Write index.json and also keep existing *_index.json in sync
    safe_json_dump(pages_dir / "index.json", pages_index)
    safe_json_dump(pages_dir / "pages_index.json", pages_index)

    safe_json_dump(endpoints_dir / "index.json", endpoints_index)
    safe_json_dump(endpoints_dir / "endpoints_index.json", endpoints_index)

    # Relationships: rewrite into by-page/by-endpoint + index.json
    write_relationship_files(relationships_dir, by_page, by_endpoint)
    safe_json_dump(relationships_dir / "index.json", relationships_index)
    safe_json_dump(relationships_dir / "relationships_index.json", relationships_index)

    # Minimal Postman wrapper/index
    ensure_postman_configuration(postman_dir)

    # Validator checks (best effort)
    if validators_ok:
        page_fail = 0
        for pid, page in pages.items():
            ok, errs = page_validator.validate(page)  # type: ignore
            if not ok:
                page_fail += 1
        endpoint_fail = 0
        for eid, ep in endpoints.items():
            ok, errs = endpoint_validator.validate(ep)  # type: ignore
            if not ok:
                endpoint_fail += 1
        rel_by_page_fail = 0
        rel_by_endpoint_fail = 0
        for page_path, endpoints_list in by_page.items():
            payload = {"page_path": page_path, "endpoints": endpoints_list, "created_at": iso_now(), "updated_at": iso_now()}
            ok, errs = relationship_validator.validate_by_page(payload)  # type: ignore
            if not ok:
                rel_by_page_fail += 1
        for (endpoint_path, method), pages_list in by_endpoint.items():
            payload = {"endpoint_path": endpoint_path, "method": method, "pages": pages_list, "created_at": iso_now(), "updated_at": iso_now()}
            ok, errs = relationship_validator.validate_by_endpoint(payload)  # type: ignore
            if not ok:
                rel_by_endpoint_fail += 1

        report = {
            "generated_at": iso_now(),
            "counts": {"pages": len(pages), "endpoints": len(endpoints), "relationships": len(flat_rels)},
            "validator_failures": {
                "pages": page_fail,
                "endpoints": endpoint_fail,
                "relationships_by_page": rel_by_page_fail,
                "relationships_by_endpoint": rel_by_endpoint_fail,
            },
            "notes": {
                "page_issue_files": len(page_issues),
                "endpoint_issue_files": len(endpoint_issues),
            },
        }
        safe_json_dump(media_root / "migration_report.json", report)

    print(f"Done. pages={len(pages)} endpoints={len(endpoints)} relationships={len(flat_rels)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

