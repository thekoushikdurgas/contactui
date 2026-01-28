#!/usr/bin/env python3
"""
Script to fix invalid routes in S3 page data.

This script:
1. Finds all pages with invalid routes (not starting with '/')
2. Fixes the routes by generating valid routes from page_id
3. Updates the pages in S3
4. Rebuilds the index

Refactored to use context-aware utilities and shared validators.

Usage:
    python scripts/fix_invalid_routes.py [--dry-run]

Environment Variables:
    AWS_PROFILE: AWS profile to use (default: default)
    AWS_REGION: AWS region (default: us-east-1)
    S3_BUCKET: S3 bucket name (required)
    S3_DATA_PREFIX: S3 data prefix (default: data/)
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.utils.context import get_logger, get_settings
from scripts.utils.validators import validate_route

logger = get_logger(__name__)
settings = get_settings()


def generate_valid_route_from_page_id(page_id: str) -> str:
    """
    Generate a valid route from page_id.
    
    Examples:
        "dashboard_error_page" -> "/dashboard-error"
        "error_page" -> "/error"
        "about_page" -> "/about"
    """
    if not page_id or page_id == "unknown":
        return "/"
    
    # Remove "_page" suffix if present
    route = page_id.replace("_page", "")
    # Replace underscores with hyphens
    route = route.replace("_", "-")
    # Ensure it starts with '/'
    if not route.startswith("/"):
        route = "/" + route
    
    return route


def is_valid_route(route: Any) -> bool:
    """Check if route is valid (starts with '/' and is a string)."""
    is_valid, errors = validate_route(route)
    return is_valid


async def fix_invalid_routes(dry_run: bool = False) -> Dict[str, Any]:
    """
    Fix invalid routes in all pages.
    
    Args:
        dry_run: If True, don't actually update files, just report what would be fixed
        
    Returns:
        Dictionary with statistics about the fix operation
    """
    print("=" * 60)
    print("Fix Invalid Routes Script")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print()
    
    # Try to import Lambda API components
    try:
        from app.clients.s3_json_storage import S3JSONStorage
        from app.repositories.s3_documentation_repository import S3DocumentationRepository
        from app.utils.s3_index_manager import S3IndexManager
        
        storage = S3JSONStorage()
        repository = S3DocumentationRepository(storage=storage)
        index_manager = S3IndexManager(storage=storage)
    except ImportError:
        logger.error("Lambda API components not available - this script requires Lambda API")
        raise ImportError("Lambda API components (S3JSONStorage, etc.) are required for this script")
    
    stats = {
        "total_pages": 0,
        "pages_with_invalid_routes": 0,
        "pages_fixed": 0,
        "pages_errors": 0,
        "fixed_pages": [],
        "errors": [],
    }
    
    # Get all page files
    pages_prefix = f"{settings.S3_DATA_PREFIX}pages/"
    page_files = await storage.list_json_files(pages_prefix)
    
    # Filter out index.json
    page_files = [f for f in page_files if not f.endswith("index.json")]
    stats["total_pages"] = len(page_files)
    
    print(f"Found {stats['total_pages']} page files to check")
    print()
    
    # Check each page
    for page_key in page_files:
        try:
            page_data = await storage.read_json(page_key)
            if not page_data:
                continue
            
            page_id = page_data.get("page_id", "unknown")
            metadata = page_data.get("metadata", {})
            route = metadata.get("route") or page_data.get("route", "")
            
            # Check if route is invalid
            if not is_valid_route(route):
                stats["pages_with_invalid_routes"] += 1
                
                # Generate valid route
                new_route = generate_valid_route_from_page_id(page_id)
                
                print(f"  ❌ {page_id}: invalid route '{route}' -> '{new_route}'")
                
                if not dry_run:
                    try:
                        # Update the route in metadata
                        if "metadata" not in page_data:
                            page_data["metadata"] = {}
                        
                        page_data["metadata"]["route"] = new_route
                        # Also update top-level route if it exists
                        if "route" in page_data:
                            page_data["route"] = new_route
                        
                        # Update last_updated timestamp
                        if "metadata" in page_data:
                            page_data["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()
                        
                        # Write updated page back to S3
                        await storage.write_json(page_key, page_data)
                        
                        stats["pages_fixed"] += 1
                        stats["fixed_pages"].append({
                            "page_id": page_id,
                            "old_route": route,
                            "new_route": new_route,
                        })
                        print(f"     ✓ Fixed and saved")
                    except Exception as e:
                        stats["pages_errors"] += 1
                        stats["errors"].append({
                            "page_id": page_id,
                            "error": str(e),
                        })
                        print(f"     ✗ Error fixing: {e}")
                        logger.error(f"Error fixing route for {page_id}: {e}", exc_info=True)
                else:
                    stats["pages_fixed"] += 1
                    stats["fixed_pages"].append({
                        "page_id": page_id,
                        "old_route": route,
                        "new_route": new_route,
                    })
                    print(f"     [DRY RUN] Would fix")
        except Exception as e:
            stats["pages_errors"] += 1
            stats["errors"].append({
                "page_key": page_key,
                "error": str(e),
            })
            logger.error(f"Error processing {page_key}: {e}", exc_info=True)
    
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"  Total pages checked:     {stats['total_pages']}")
    print(f"  Pages with invalid routes: {stats['pages_with_invalid_routes']}")
    print(f"  Pages fixed:            {stats['pages_fixed']}")
    print(f"  Errors:                 {stats['pages_errors']}")
    print()
    
    if stats["fixed_pages"]:
        print("Fixed pages:")
        for fix in stats["fixed_pages"]:
            print(f"  - {fix['page_id']}: '{fix['old_route']}' -> '{fix['new_route']}'")
        print()
    
    if stats["errors"]:
        print("Errors:")
        for error in stats["errors"][:10]:
            page_id = error.get("page_id", error.get("page_key", "unknown"))
            print(f"  - {page_id}: {error['error']}")
        if len(stats["errors"]) > 10:
            print(f"  ... and {len(stats['errors']) - 10} more error(s)")
        print()
    
    # Rebuild index if pages were fixed
    if not dry_run and stats["pages_fixed"] > 0:
        print("Rebuilding pages index...")
        try:
            await index_manager.rebuild_pages_index()
            print("  ✓ Index rebuilt successfully")
        except Exception as e:
            print(f"  ✗ Error rebuilding index: {e}")
            logger.error(f"Error rebuilding index: {e}", exc_info=True)
    
    print(f"Completed at: {datetime.now().isoformat()}")
    print("=" * 60)
    
    return stats


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Fix invalid routes in S3 page data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fixed without actually updating files",
    )
    
    args = parser.parse_args()
    
    try:
        stats = await fix_invalid_routes(dry_run=args.dry_run)
        
        if stats["pages_errors"] > 0:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Script interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logger.error(f"Fatal error in fix_invalid_routes script: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
