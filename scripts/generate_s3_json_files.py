#!/usr/bin/env python3
"""
Generate JSON files for S3 bucket seeding.

This script generates JSON files in the correct S3 structure format:
- data/pages/{page_id}.json - Page metadata files
- data/pages/index.json - Pages index
- data/endpoints/{endpoint_id}.json - Endpoint metadata files (optional)
- data/endpoints/index.json - Endpoints index (optional)
- data/relationships/ - Relationship files (optional)

The generated JSON files can be:
1. Saved locally to a directory for review
2. Uploaded directly to S3 bucket
3. Used for bulk seeding operations
"""

import asyncio
import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path for Lambda API imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Use context-aware utilities
from scripts.utils.context import (
    get_logger,
    get_settings,
    find_docs_directory,
    get_workspace_root,
)

logger = get_logger(__name__)
settings = get_settings()

# Output directory (relative to workspace root)
WORKSPACE_ROOT = get_workspace_root()
OUTPUT_DIR = WORKSPACE_ROOT / "docs_ai_agent" / "generated_json"


def parse_markdown_file(file_path: Path) -> Dict[str, Any]:
    """Parse markdown file and extract metadata."""
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise
    
    # Extract route (e.g., **Route:** `/about`)
    route_match = re.search(r'\*\*Route:\*\*\s*`?([^\n`]+)`?', content)
    route = route_match.group(1).strip() if route_match else "/"
    
    # Extract file path (e.g., **File:** `frontent/app/(marketing)/about/page.tsx`)
    file_match = re.search(r'\*\*File:\*\*\s*`?([^\n`]+)`?', content)
    file_path_str = file_match.group(1).strip() if file_match else ""
    
    # Extract authentication (e.g., **Authentication:** Not required (public marketing page))
    auth_match = re.search(r'\*\*Authentication:\*\*\s*([^\n]+)', content)
    authentication = auth_match.group(1).strip() if auth_match else "Not required"
    
    # Extract authorization (e.g., **Authorization:** Admin or Super Admin only)
    authz_match = re.search(r'\*\*Authorization:\*\*\s*([^\n]+)', content)
    authorization = authz_match.group(1).strip() if authz_match else None
    
    # Extract purpose (e.g., **Purpose:** Marketing page that tells the story...)
    purpose_match = re.search(r'\*\*Purpose:\*\*\s*([^\n]+)', content)
    purpose = purpose_match.group(1).strip() if purpose_match else ""
    
    # Determine page_type from file path or route
    page_type = "docs"
    if "(marketing)" in file_path_str.lower() or "/marketing" in route.lower():
        page_type = "marketing"
    elif "(dashboard)" in file_path_str.lower() or "/dashboard" in route.lower():
        page_type = "dashboard"
    
    # Generate page_id from filename (e.g., "about_page.md" -> "about_page")
    page_id = file_path.stem
    
    return {
        "page_id": page_id,
        "page_type": page_type,
        "route": route,
        "file_path": file_path_str,
        "authentication": authentication,
        "authorization": authorization,
        "purpose": purpose,
        "content": content,  # Full markdown content
    }


def generate_page_json(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate page JSON file in S3 format."""
    now = datetime.now(timezone.utc).isoformat()
    
    page_json = {
        "_id": str(uuid.uuid4()),
        "page_id": parsed_data["page_id"],
        "page_type": parsed_data["page_type"],
        "metadata": {
            "route": parsed_data["route"],
            "file_path": parsed_data["file_path"],
            "purpose": parsed_data["purpose"],
            "s3_key": f"{settings.S3_DOCUMENTATION_PREFIX}{parsed_data['page_id']}.md",
            "status": "published",
            "authentication": parsed_data["authentication"],
            "authorization": parsed_data.get("authorization"),
            "last_updated": now,
            "uses_endpoints": [],
            "ui_components": [],
        },
        "created_at": now,
    }
    
    return page_json


def generate_pages_index(pages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate pages index JSON file."""
    now = datetime.now(timezone.utc).isoformat()
    
    index_data = {
        "version": "1.0",
        "last_updated": now,
        "total": len(pages),
        "pages": [],
        "indexes": {
            "by_type": {
                "docs": [],
                "marketing": [],
                "dashboard": [],
            },
            "by_route": {},
        },
    }
    
    for page in pages:
        page_id = page.get("page_id")
        page_type = page.get("page_type", "docs")
        route = page.get("metadata", {}).get("route", "")
        
        # Add to pages list
        index_data["pages"].append({
            "page_id": page_id,
            "page_type": page_type,
            "route": route,
        })
        
        # Add to type index
        if page_type in index_data["indexes"]["by_type"]:
            if page_id not in index_data["indexes"]["by_type"][page_type]:
                index_data["indexes"]["by_type"][page_type].append(page_id)
        
        # Add to route index
        if route:
            index_data["indexes"]["by_route"][route] = page_id
    
    return index_data


def generate_endpoint_json(endpoint_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate endpoint JSON file in S3 format."""
    now = datetime.now(timezone.utc).isoformat()
    
    # Generate endpoint_id if not provided
    if "endpoint_id" not in endpoint_data:
        endpoint_path = endpoint_data.get("endpoint_path", "")
        method = endpoint_data.get("method", "GET")
        api_version = endpoint_data.get("api_version", "v1")
        # Create endpoint_id: method_lowercase_path_without_slashes_version
        path_part = endpoint_path.strip("/").replace("/", "_").replace(":", "_") or "root"
        endpoint_data["endpoint_id"] = f"{method.lower()}_{path_part}_{api_version}"
    
    endpoint_json = {
        "_id": str(uuid.uuid4()),
        "endpoint_id": endpoint_data["endpoint_id"],
        "endpoint_path": endpoint_data.get("endpoint_path", ""),
        "method": endpoint_data.get("method", "GET"),
        "api_version": endpoint_data.get("api_version", "v1"),
        "router_file": endpoint_data.get("router_file", ""),
        "service_methods": endpoint_data.get("service_methods", []),
        "repository_methods": endpoint_data.get("repository_methods", []),
        "authentication": endpoint_data.get("authentication", "API Key"),
        "authorization": endpoint_data.get("authorization"),
        "rate_limit": endpoint_data.get("rate_limit"),
        "description": endpoint_data.get("description", ""),
        "used_by_pages": endpoint_data.get("used_by_pages", []),
        "page_count": len(endpoint_data.get("used_by_pages", [])),
        "created_at": endpoint_data.get("created_at", now),
        "updated_at": now,
    }
    
    return endpoint_json


def generate_endpoints_index(endpoints: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate endpoints index JSON file."""
    now = datetime.now(timezone.utc).isoformat()
    
    index_data = {
        "version": "1.0",
        "last_updated": now,
        "total": len(endpoints),
        "endpoints": [],
        "indexes": {
            "by_api_version": {},
            "by_method": {},
            "by_path_method": {},
        },
    }
    
    for endpoint in endpoints:
        endpoint_id = endpoint.get("endpoint_id")
        endpoint_path = endpoint.get("endpoint_path", "")
        method = endpoint.get("method", "GET")
        api_version = endpoint.get("api_version", "v1")
        
        # Add to endpoints list
        index_data["endpoints"].append({
            "endpoint_id": endpoint_id,
            "endpoint_path": endpoint_path,
            "method": method,
            "api_version": api_version,
        })
        
        # Update indexes
        if api_version not in index_data["indexes"]["by_api_version"]:
            index_data["indexes"]["by_api_version"][api_version] = []
        if endpoint_id not in index_data["indexes"]["by_api_version"][api_version]:
            index_data["indexes"]["by_api_version"][api_version].append(endpoint_id)
        
        if method not in index_data["indexes"]["by_method"]:
            index_data["indexes"]["by_method"][method] = []
        if endpoint_id not in index_data["indexes"]["by_method"][method]:
            index_data["indexes"]["by_method"][method].append(endpoint_id)
        
        path_method_key = f"{endpoint_path}:{method}"
        index_data["indexes"]["by_path_method"][path_method_key] = endpoint_id
    
    return index_data


def extract_endpoints_from_pages(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract endpoint references from page metadata."""
    endpoints = []
    endpoint_map = {}  # Track unique endpoints by path+method
    
    for page in pages:
        metadata = page.get("metadata", {})
        uses_endpoints = metadata.get("uses_endpoints", [])
        page_path = metadata.get("route", "")
        
        for endpoint_ref in uses_endpoints:
            endpoint_path = endpoint_ref.get("endpoint_path")
            method = endpoint_ref.get("method", "GET")
            api_version = endpoint_ref.get("api_version", "v1")
            
            if not endpoint_path:
                continue
            
            # Create unique key
            key = f"{endpoint_path}:{method}:{api_version}"
            
            if key not in endpoint_map:
                endpoint_data = {
                    "endpoint_path": endpoint_path,
                    "method": method,
                    "api_version": api_version,
                    "authentication": endpoint_ref.get("authentication", "API Key"),
                    "authorization": endpoint_ref.get("authorization"),
                    "description": endpoint_ref.get("description", ""),
                    "used_by_pages": [],
                }
                endpoint_map[key] = endpoint_data
                endpoints.append(endpoint_data)
            
            # Add page reference
            endpoint_map[key]["used_by_pages"].append({
                "page_path": page_path,
                "via_service": endpoint_ref.get("via_service"),
                "via_hook": endpoint_ref.get("via_hook"),
                "usage_type": endpoint_ref.get("usage_type", "primary"),
                "usage_context": endpoint_ref.get("usage_context", "data_fetching"),
            })
    
    return endpoints


def generate_relationship_json(
    page_path: str,
    endpoints: List[Dict[str, Any]],
    created_at: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate page relationship JSON file."""
    now = datetime.now(timezone.utc).isoformat()
    
    relationship_data = {
        "page_path": page_path,
        "endpoints": [],
        "created_at": created_at or now,
        "updated_at": now,
    }
    
    for endpoint_ref in endpoints:
        relationship_data["endpoints"].append({
            "endpoint_path": endpoint_ref.get("endpoint_path", ""),
            "method": endpoint_ref.get("method", "GET"),
            "api_version": endpoint_ref.get("api_version", "v1"),
            "via_service": endpoint_ref.get("via_service"),
            "via_hook": endpoint_ref.get("via_hook"),
            "usage_type": endpoint_ref.get("usage_type", "primary"),
            "usage_context": endpoint_ref.get("usage_context", "data_fetching"),
        })
    
    return relationship_data


def generate_endpoint_relationship_json(
    endpoint_path: str,
    method: str,
    pages: List[Dict[str, Any]],
    created_at: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate endpoint relationship JSON file."""
    now = datetime.now(timezone.utc).isoformat()
    
    relationship_data = {
        "endpoint_path": endpoint_path,
        "method": method,
        "pages": [],
        "created_at": created_at or now,
        "updated_at": now,
    }
    
    for page_ref in pages:
        relationship_data["pages"].append({
            "page_path": page_ref.get("page_path", ""),
            "via_service": page_ref.get("via_service"),
            "via_hook": page_ref.get("via_hook"),
            "usage_type": page_ref.get("usage_type", "primary"),
            "usage_context": page_ref.get("usage_context", "data_fetching"),
        })
    
    return relationship_data


def generate_relationships_index(
    by_page_count: int,
    by_endpoint_count: int,
) -> Dict[str, Any]:
    """Generate relationships index JSON file."""
    now = datetime.now(timezone.utc).isoformat()
    
    return {
        "version": "1.0",
        "last_updated": now,
        "total": by_page_count + by_endpoint_count,
        "by_api_version": {},
    }


def sanitize_path(path: str) -> str:
    """Sanitize path for use in S3 key."""
    return path.strip("/").replace("/", "_").replace(":", "_") or "root"


async def generate_json_files(
    output_dir: Path,
    docs_dir: Optional[Path] = None,
    upload_to_s3: bool = False,
    include_endpoints: bool = False,
    include_relationships: bool = False,
) -> Dict[str, Any]:
    """
    Generate JSON files for S3 seeding.
    
    Args:
        output_dir: Directory to save generated JSON files
        upload_to_s3: If True, upload files directly to S3
        include_endpoints: If True, generate endpoint JSON files
        include_relationships: If True, generate relationship JSON files
    
    Returns:
        Dictionary with generation statistics
    """
    print("=" * 60)
    print("S3 JSON Files Generator")
    print("=" * 60)
    
    stats = {
        "pages": {"generated": 0, "errors": 0},
        "endpoints": {"generated": 0, "errors": 0},
        "relationships": {"generated": 0, "errors": 0},
    }
    
    # Find docs directory
    if docs_dir is None:
        docs_dir = find_docs_directory()
        if docs_dir is None:
            print(f"\n❌ ERROR: Documentation directory not found")
            print(f"   Tried the following paths:")
            for path in POSSIBLE_DOCS_PATHS:
                print(f"     - {path}")
            print(f"\n   Please provide a custom path using --docs-dir option")
            print(f"   Example: --docs-dir D:\\code\\ayan\\contact360\\docs\\pages")
            return stats
    else:
        # Ensure docs_dir is a Path object
        if not isinstance(docs_dir, Path):
            docs_dir = Path(docs_dir)
        if not docs_dir.exists():
            print(f"\n❌ ERROR: Documentation directory not found: {docs_dir}")
            return stats
    
    print(f"\n📂 Using docs directory: {docs_dir}")
    
    # Create output directory structure
    pages_dir = output_dir / "data" / "pages"
    endpoints_dir = output_dir / "data" / "endpoints"
    relationships_dir = output_dir / "data" / "relationships"
    relationships_by_page_dir = relationships_dir / "by-page"
    relationships_by_endpoint_dir = relationships_dir / "by-endpoint"
    
    if not upload_to_s3:
        pages_dir.mkdir(parents=True, exist_ok=True)
        endpoints_dir.mkdir(parents=True, exist_ok=True)
        relationships_by_page_dir.mkdir(parents=True, exist_ok=True)
        relationships_by_endpoint_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Output directory: {output_dir}")
    else:
        print(f"☁️  Uploading directly to S3 bucket: {settings.S3_BUCKET_NAME}")
    
    # Exclude template, tracking, and index files
    exclude_patterns = [
        '_page_docs_template',
        'CSS_',
        'DOCUMENTATION_',
        'FINAL_',
        'IMPLEMENTATION_',
        'PROGRESS_',
        'page_docs_coverage',
        'sidebar_',
        'index.json',
        'pages_index.json',
        'endpoints_index.json',
        'schema.md',
        'README.md',
    ]
    
    # Try to find JSON files first (preferred - already in correct format)
    json_files = [
        f for f in docs_dir.glob("*.json")
        if not any(pattern in f.name for pattern in exclude_patterns)
    ]
    
    # Fallback to markdown files if no JSON files found
    markdown_files = [
        f for f in docs_dir.glob("*.md")
        if not any(pattern in f.name for pattern in exclude_patterns)
    ] if not json_files else []
    
    if not json_files and not markdown_files:
        print(f"\n⚠️  WARNING: No documentation files found in {docs_dir}")
        print(f"   Looking for: *.json or *.md files")
        return stats
    
    # Determine which files to process
    files_to_process = json_files if json_files else markdown_files
    file_type = "JSON" if json_files else "markdown"
    
    print(f"\n📁 Found {len(files_to_process)} {file_type} files to process\n")
    
    # Process pages
    pages_data = []
    for idx, file_path in enumerate(sorted(files_to_process), 1):
        try:
            if file_path.suffix == '.json':
                # Read and validate existing JSON file
                page_json = json.loads(file_path.read_text(encoding='utf-8'))
                # Validate required fields
                if not page_json.get("page_id"):
                    page_json["page_id"] = file_path.stem
                if not page_json.get("_id"):
                    page_json["_id"] = str(uuid.uuid4())
                if not page_json.get("created_at"):
                    page_json["created_at"] = datetime.now(timezone.utc).isoformat()
                pages_data.append(page_json)
            else:
                # Parse markdown file (legacy support)
                parsed = parse_markdown_file(file_path)
                page_json = generate_page_json(parsed)
                pages_data.append(page_json)
            
            # Save page JSON file
            page_id = page_json["page_id"]
            page_filename = f"{page_id}.json"
            page_path = pages_dir / page_filename
            
            if upload_to_s3:
                # Upload directly to S3
                from app.clients.s3_json_storage import S3JSONStorage
                storage = S3JSONStorage()
                s3_key = f"{settings.S3_DATA_PREFIX}pages/{page_id}.json"
                await storage.write_json(s3_key, page_json)
                print(f"[{idx:3d}/{len(files_to_process)}] ✅ Generated & uploaded: {page_id}")
            else:
                # Save locally
                page_path.write_text(json.dumps(page_json, indent=2, ensure_ascii=False), encoding='utf-8')
                print(f"[{idx:3d}/{len(files_to_process)}] ✅ Generated: {page_id}")
            
            stats["pages"]["generated"] += 1
            
        except Exception as e:
            stats["pages"]["errors"] += 1
            logger.error(f"Error processing {file_path.name}: {e}", exc_info=True)
            print(f"[{idx:3d}/{len(files_to_process)}] ❌ ERROR: {file_path.name}")
            print(f"      {str(e)}")
    
    # Generate pages index
    if pages_data:
        print(f"\n📋 Generating pages index...")
        index_data = generate_pages_index(pages_data)
        index_path = pages_dir / "index.json"
        
        if upload_to_s3:
            from app.clients.s3_json_storage import S3JSONStorage
            storage = S3JSONStorage()
            s3_key = f"{settings.S3_DATA_PREFIX}pages/index.json"
            await storage.write_json(s3_key, index_data)
            print(f"✅ Generated & uploaded: pages/index.json")
        else:
            index_path.write_text(json.dumps(index_data, indent=2, ensure_ascii=False), encoding='utf-8')
            print(f"✅ Generated: pages/index.json")
    
    # Generate endpoints (if requested)
    if include_endpoints:
        print(f"\n📡 Generating endpoint JSON files...")
        # TODO: Implement endpoint generation from analysis data
        print("⚠️  Endpoint generation not yet implemented")
    
    # Generate relationships (if requested)
    if include_relationships:
        print(f"\n🔗 Generating relationship JSON files...")
        # TODO: Implement relationship generation from analysis data
        print("⚠️  Relationship generation not yet implemented")
    
    # Summary
    print(f"\n{'='*60}")
    print("Generation Summary")
    print(f"{'='*60}")
    print(f"  ✅ Pages generated:  {stats['pages']['generated']}")
    print(f"  ❌ Pages errors:     {stats['pages']['errors']}")
    if include_endpoints:
        print(f"  ✅ Endpoints generated: {stats['endpoints']['generated']}")
        print(f"  ❌ Endpoints errors:    {stats['endpoints']['errors']}")
    if include_relationships:
        print(f"  ✅ Relationships generated: {stats['relationships']['generated']}")
        print(f"  ❌ Relationships errors:    {stats['relationships']['errors']}")
    
    if not upload_to_s3:
        print(f"\n📁 Generated files saved to: {output_dir}")
        print(f"   Structure:")
        print(f"   {output_dir}/")
        print(f"   ├── data/")
        print(f"   │   ├── pages/")
        print(f"   │   │   ├── {{page_id}}.json")
        print(f"   │   │   └── index.json")
        if include_endpoints:
            print(f"   │   ├── endpoints/")
            print(f"   │   │   ├── {{endpoint_id}}.json")
            print(f"   │   │   └── index.json")
        if include_relationships:
            print(f"   │   └── relationships/")
            print(f"   │       ├── by-page/{{sanitized_path}}.json")
            print(f"   │       ├── by-endpoint/{{path}}_{{method}}.json")
            print(f"   │       └── index.json")
    else:
        print(f"\n☁️  Files uploaded to S3 bucket: {settings.S3_BUCKET_NAME}")
        print(f"   S3 structure:")
        print(f"   s3://{settings.S3_BUCKET_NAME}/")
        print(f"   └── {settings.S3_DATA_PREFIX}")
        print(f"       ├── pages/")
        print(f"       │   ├── {{page_id}}.json")
        print(f"       │   └── index.json")
        if include_endpoints:
            print(f"       ├── endpoints/")
            print(f"       │   ├── {{endpoint_id}}.json")
            print(f"       │   └── index.json")
        if include_relationships:
            print(f"       └── relationships/")
            print(f"           ├── by-page/{{sanitized_path}}.json")
            print(f"           ├── by-endpoint/{{path}}_{{method}}.json")
            print(f"           └── index.json")
    
    print(f"{'='*60}\n")
    
    return stats


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate JSON files for S3 bucket seeding",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate JSON files locally
  python scripts/generate_s3_json_files.py --output-dir ./generated_json
  
  # Generate and upload directly to S3
  python scripts/generate_s3_json_files.py --upload-to-s3
  
  # Generate with endpoints and relationships
  python scripts/generate_s3_json_files.py --include-endpoints --include-relationships
        """
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(OUTPUT_DIR),
        help="Directory to save generated JSON files (default: ./generated_json)"
    )
    parser.add_argument(
        "--upload-to-s3",
        action="store_true",
        help="Upload generated JSON files directly to S3 bucket"
    )
    parser.add_argument(
        "--include-endpoints",
        action="store_true",
        help="Generate endpoint JSON files (requires analysis data)"
    )
    parser.add_argument(
        "--include-relationships",
        action="store_true",
        help="Generate relationship JSON files (requires analysis data)"
    )
    parser.add_argument(
        "--docs-dir",
        type=str,
        default=None,
        help="Custom path to documentation pages directory (default: auto-detect)"
    )
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    docs_dir = Path(args.docs_dir) if args.docs_dir else None
    
    try:
        stats = await generate_json_files(
            output_dir=output_dir,
            docs_dir=docs_dir,
            upload_to_s3=args.upload_to_s3,
            include_endpoints=args.include_endpoints,
            include_relationships=args.include_relationships,
        )
        
        if stats["pages"]["errors"] > 0:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Generation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logger.error(f"Fatal error in JSON generation script: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
