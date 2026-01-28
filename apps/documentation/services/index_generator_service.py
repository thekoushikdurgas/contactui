"""Index Generator – rebuild local media/ index.json for pages, endpoints, postman, relationships."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.core.cache import cache

from apps.documentation.utils.paths import (
    get_endpoints_dir,
    get_media_root,
    get_pages_dir,
    get_postman_dir,
    get_relationships_dir,
    list_directory_files,
)

logger = logging.getLogger(__name__)

INDEX_EXCLUSIONS: Set[str] = {
    "index.json",
    "pages_index.json",
    "endpoints_index.json",
    "postman_index.json",
    "relationships_index.json",
}


class IndexGeneratorService:
    """Generate index.json under media/ for each resource type."""

    def __init__(self) -> None:
        self.media_root = get_media_root()
        self.max_workers = 4  # Default number of parallel workers
    
    def _process_file_parallel(self, file_info: Dict[str, Any], resource_type: str) -> Optional[Dict[str, Any]]:
        """
        Process a single file and extract index data.
        
        Args:
            file_info: File information dict with 'path', 'name', etc.
            resource_type: Type of resource ('pages', 'endpoints', etc.)
            
        Returns:
            Extracted index data or None if processing failed
        """
        try:
            with open(file_info["path"], "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Ensure data is a dictionary
            if not isinstance(data, dict):
                logger.warning("index %s skip %s: data is not a dictionary", resource_type, file_info["path"])
                return None
            
            if resource_type == 'pages':
                pid = data.get("page_id") or Path(file_info["path"]).stem
                ptype = data.get("page_type", "docs")
                metadata = data.get("metadata")
                route = (metadata.get("route", "") if isinstance(metadata, dict) else "") if metadata else ""
                return {
                    "page_id": pid,
                    "page_type": ptype,
                    "route": route,
                    "file_name": file_info["name"],
                    "data": data
                }
            elif resource_type == 'endpoints':
                eid = data.get("endpoint_id") or Path(file_info["path"]).stem
                method = data.get("method", "GET")
                api_version = data.get("api_version", "v1")
                path = data.get("endpoint_path") or data.get("path", "")
                return {
                    "endpoint_id": eid,
                    "method": method,
                    "api_version": api_version,
                    "path": path,
                    "file_name": file_info["name"],
                    "data": data
                }
            elif resource_type == 'relationships':
                return {
                    "data": data,
                    "file_name": file_info["name"]
                }
            return None
        except Exception as e:
            logger.warning("index %s skip %s: %s", resource_type, file_info["path"], e)
            return None

    def generate_pages_index(self, use_parallel: bool = True) -> Dict[str, Any]:
        """
        Write media/pages/index.json. Returns {success, index_path, total, error}.
        
        Args:
            use_parallel: If True, process files in parallel (default: True)
        """
        try:
            pages_dir = get_pages_dir()
            if not pages_dir.exists():
                return {"success": False, "error": "Pages directory does not exist"}
            files = list_directory_files(pages_dir, extensions=[".json"], exclude_files=INDEX_EXCLUSIONS)
            
            pages: List[Dict[str, Any]] = []
            indexes: Dict[str, Any] = {"by_type": {"docs": [], "marketing": [], "dashboard": []}, "by_route": {}}
            stats: Dict[str, Any] = {"total": 0, "by_type": {"docs": 0, "marketing": 0, "dashboard": 0}}
            
            if use_parallel and len(files) > 10:
                # Process files in parallel for better performance
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    futures = {
                        executor.submit(self._process_file_parallel, fi, 'pages'): fi
                        for fi in files
                    }
                    
                    for future in as_completed(futures):
                        result = future.result()
                        if result:
                            pid = result["page_id"]
                            ptype = result["page_type"]
                            route = result["route"]
                            pages.append({
                                "page_id": pid,
                                "page_type": ptype,
                                "route": route,
                                "file_name": result["file_name"]
                            })
                            if ptype in indexes["by_type"] and pid not in indexes["by_type"][ptype]:
                                indexes["by_type"][ptype].append(pid)
                            if route:
                                indexes["by_route"][route] = pid
                            stats["total"] += 1
                            if ptype in stats["by_type"]:
                                stats["by_type"][ptype] += 1
            else:
                # Sequential processing for small datasets
                for fi in files:
                    result = self._process_file_parallel(fi, 'pages')
                    if result:
                        pid = result["page_id"]
                        ptype = result["page_type"]
                        route = result["route"]
                        pages.append({
                            "page_id": pid,
                            "page_type": ptype,
                            "route": route,
                            "file_name": result["file_name"]
                        })
                        if ptype in indexes["by_type"] and pid not in indexes["by_type"][ptype]:
                            indexes["by_type"][ptype].append(pid)
                        if route:
                            indexes["by_route"][route] = pid
                        stats["total"] += 1
                        if ptype in stats["by_type"]:
                            stats["by_type"][ptype] += 1
            index_file = pages_dir / "index.json"
            if index_file.exists():
                index_file.unlink()
            payload = {
                "version": "2.0",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "total": len(pages),
                "pages": pages,
                "indexes": indexes,
                "statistics": stats,
            }
            with open(index_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            logger.info("Generated pages index with %d pages", len(pages))
            return {"success": True, "index_path": str(index_file.relative_to(self.media_root)), "total": len(pages)}
        except Exception as e:
            logger.exception("generate_pages_index")
            return {"success": False, "error": str(e)}

    def generate_endpoints_index(self, use_parallel: bool = True) -> Dict[str, Any]:
        """
        Write media/endpoints/index.json.
        
        Args:
            use_parallel: If True, process files in parallel (default: True)
        """
        try:
            endpoints_dir = get_endpoints_dir()
            if not endpoints_dir.exists():
                return {"success": False, "error": "Endpoints directory does not exist"}
            files = list_directory_files(endpoints_dir, extensions=[".json"], exclude_files=INDEX_EXCLUSIONS)
            endpoints = []
            indexes: Dict[str, Any] = {"by_method": {}, "by_api_version": {}, "by_path": {}}
            stats: Dict[str, Any] = {"total": 0, "by_method": {}, "by_api_version": {}}
            
            if use_parallel and len(files) > 10:
                # Process files in parallel
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    futures = {
                        executor.submit(self._process_file_parallel, fi, 'endpoints'): fi
                        for fi in files
                    }
                    
                    for future in as_completed(futures):
                        result = future.result()
                        if result:
                            eid = result["endpoint_id"]
                            method = result["method"]
                            api_version = result["api_version"]
                            path = result["path"]
                            endpoints.append({
                                "endpoint_id": eid,
                                "method": method,
                                "api_version": api_version,
                                "path": path,
                                "file_name": result["file_name"]
                            })
                            indexes["by_method"].setdefault(method, []).append(eid)
                            indexes["by_api_version"].setdefault(api_version, []).append(eid)
                            if path:
                                indexes["by_path"][path] = eid
                            stats["total"] += 1
                            stats["by_method"][method] = stats["by_method"].get(method, 0) + 1
                            stats["by_api_version"][api_version] = stats["by_api_version"].get(api_version, 0) + 1
            else:
                # Sequential processing
                for fi in files:
                    result = self._process_file_parallel(fi, 'endpoints')
                    if result:
                        eid = result["endpoint_id"]
                        method = result["method"]
                        api_version = result["api_version"]
                        path = result["path"]
                        endpoints.append({
                            "endpoint_id": eid,
                            "method": method,
                            "api_version": api_version,
                            "path": path,
                            "file_name": result["file_name"]
                        })
                        indexes["by_method"].setdefault(method, []).append(eid)
                        indexes["by_api_version"].setdefault(api_version, []).append(eid)
                        if path:
                            indexes["by_path"][path] = eid
                        stats["total"] += 1
                        stats["by_method"][method] = stats["by_method"].get(method, 0) + 1
                        stats["by_api_version"][api_version] = stats["by_api_version"].get(api_version, 0) + 1
            index_file = endpoints_dir / "index.json"
            if index_file.exists():
                index_file.unlink()
            payload = {
                "version": "2.0",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "total": len(endpoints),
                "endpoints": endpoints,
                "indexes": indexes,
                "statistics": stats,
            }
            with open(index_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            logger.info("Generated endpoints index with %d endpoints", len(endpoints))
            return {"success": True, "index_path": str(index_file.relative_to(self.media_root)), "total": len(endpoints)}
        except Exception as e:
            logger.exception("generate_endpoints_index")
            return {"success": False, "error": str(e)}

    def generate_postman_index(self) -> Dict[str, Any]:
        """Write media/postman/index.json from collection, environment, configurations."""
        try:
            postman_dir = get_postman_dir()
            if not postman_dir.exists():
                return {"success": False, "error": "Postman directory does not exist"}
            collections = []
            environments = []
            configurations = []
            for sub, key in [("collection", "collections"), ("environment", "environments"), ("configurations", "configurations")]:
                d = postman_dir / sub
                if not d.exists():
                    continue
                files = list_directory_files(d, extensions=[".json"], exclude_files=INDEX_EXCLUSIONS)
                for fi in files:
                    try:
                        with open(fi["path"], "r", encoding="utf-8") as f:
                            data = json.load(f)
                        if sub == "collection":
                            name = (data.get("info") or {}).get("name") or Path(fi["path"]).stem
                            collections.append({"collection_id": name, "file_name": fi["name"], "type": "collection"})
                        elif sub == "environment":
                            name = data.get("name") or Path(fi["path"]).stem
                            environments.append({"environment_id": name, "file_name": fi["name"], "type": "environment"})
                        else:
                            cid = data.get("config_id") or data.get("name") or Path(fi["path"]).stem
                            configurations.append({"config_id": cid, "name": data.get("name", cid), "state": data.get("state", "development"), "file_name": fi["name"]})
                    except Exception as e:
                        logger.warning("index postman %s skip %s: %s", sub, fi["path"], e)
            indexes = {"by_state": {"coming_soon": [], "development": [], "draft": [], "test": [], "published": []}}
            for c in configurations:
                s = c.get("state", "development")
                if s in indexes["by_state"] and c["config_id"] not in indexes["by_state"][s]:
                    indexes["by_state"][s].append(c["config_id"])
            stats = {"total": len(configurations), "collections": len(collections), "environments": len(environments), "configurations": len(configurations)}
            payload = {
                "version": "2.0",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "total": len(configurations),
                "collections": collections,
                "environments": environments,
                "configurations": configurations,
                "indexes": indexes,
                "statistics": stats,
            }
            index_file = postman_dir / "index.json"
            if index_file.exists():
                index_file.unlink()
            with open(index_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            logger.info("Generated postman index: %d collections, %d envs, %d configs", len(collections), len(environments), len(configurations))
            return {"success": True, "index_path": str(index_file.relative_to(self.media_root)), "total": len(configurations), "collections": len(collections), "environments": len(environments)}
        except Exception as e:
            logger.exception("generate_postman_index")
            return {"success": False, "error": str(e)}

    def generate_relationships_index(self) -> Dict[str, Any]:
        """Write media/relationships/index.json from by-page and by-endpoint."""
        try:
            rel_dir = get_relationships_dir()
            if not rel_dir.exists():
                return {"success": False, "error": "Relationships directory does not exist"}
            relationships: List[Dict[str, Any]] = []
            for sub in ("by-endpoint", "by-page"):
                d = rel_dir / sub
                if not d.exists():
                    continue
                files = list_directory_files(d, extensions=[".json"], exclude_files=INDEX_EXCLUSIONS)
                for fi in files:
                    try:
                        with open(fi["path"], "r", encoding="utf-8") as f:
                            data = json.load(f)
                        if isinstance(data, list):
                            relationships.extend(data)
                        else:
                            relationships.append(data)
                    except Exception as e:
                        logger.warning("index relationships %s skip %s: %s", sub, fi["path"], e)
            indexes: Dict[str, Any] = {"by_page": {}, "by_endpoint": {}, "by_usage_type": {"primary": [], "secondary": [], "conditional": []}}
            stats: Dict[str, Any] = {"total": len(relationships)}
            for r in relationships:
                pp = r.get("page_path")
                ep = r.get("endpoint_path")
                if pp:
                    indexes["by_page"].setdefault(pp, []).append(r.get("relationship_id", ""))
                if ep:
                    key = f"{ep}:{r.get('method', 'GET')}"
                    indexes["by_endpoint"].setdefault(key, []).append(r.get("relationship_id", ""))
            payload = {
                "version": "2.0",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "total": len(relationships),
                "relationships": relationships,
                "indexes": indexes,
                "statistics": stats,
            }
            index_file = rel_dir / "index.json"
            if index_file.exists():
                index_file.unlink()
            with open(index_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            logger.info("Generated relationships index with %d entries", len(relationships))
            return {"success": True, "index_path": str(index_file.relative_to(self.media_root)), "total": len(relationships)}
        except Exception as e:
            logger.exception("generate_relationships_index")
            return {"success": False, "error": str(e)}

    def generate_all_indexes(self, parallel: bool = True, max_workers: int = 4) -> Dict[str, Any]:
        """
        Run all four generators in parallel or sequentially.
        
        Args:
            parallel: If True, generate indexes in parallel (default: True)
            max_workers: Maximum number of parallel workers (default: 4)
            
        Returns:
            Dictionary with {success, results, error}
        """
        generators = [
            ("pages", self.generate_pages_index),
            ("endpoints", self.generate_endpoints_index),
            ("postman", self.generate_postman_index),
            ("relationships", self.generate_relationships_index),
        ]
        
        if parallel:
            # Generate indexes in parallel
            results = {}
            ok = True
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_name = {
                    executor.submit(fn): name
                    for name, fn in generators
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_name):
                    name = future_to_name[future]
                    try:
                        out = future.result()
                        results[name] = out
                        if not out.get("success"):
                            ok = False
                    except Exception as e:
                        logger.error(f"Error generating {name} index: {e}", exc_info=True)
                        results[name] = {"success": False, "error": str(e)}
                        ok = False
            
            logger.info(f"Generated all indexes in parallel: {len([r for r in results.values() if r.get('success')])}/{len(results)} successful")
            return {"success": ok, "results": results}
        else:
            # Sequential generation (original behavior)
            results = {}
            ok = True
            for name, fn in generators:
                out = fn()
                results[name] = out
                if not out.get("success"):
                    ok = False
            return {"success": ok, "results": results}
