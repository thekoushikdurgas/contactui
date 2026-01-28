#!/usr/bin/env python3
"""
Unified script to upload all documentation files to Lambda Documentation API.

This script orchestrates the upload of pages, endpoints, and relationships
from the media/ directory to Lambda API (which handles S3 storage).

Refactored to use context-aware utilities and improved error handling.
"""

import sys
import os
from pathlib import Path
from typing import Any, Dict, List

# Add parent directory to path for Django imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup Django environment if needed
if "DJANGO_SETTINGS_MODULE" not in os.environ:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        import django
        django.setup()
    except (ImportError, RuntimeError):
        pass

from scripts.upload_docs_pages_to_s3 import upload_pages
from scripts.upload_docs_endpoints_to_s3 import upload_endpoints
from scripts.upload_docs_relationships_to_s3 import upload_relationships
from scripts.utils.context import get_media_root, get_logger

logger = get_logger(__name__)

MEDIA_ROOT = get_media_root()


def rebuild_indexes(
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Rebuild all indexes using Lambda API.
    
    Args:
        dry_run: If True, don't actually rebuild
        
    Returns:
        Dictionary with rebuild statistics
    """
    print("\n" + "=" * 60)
    print("Rebuilding Indexes")
    print("=" * 60)
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - Indexes would be rebuilt\n")
        return {"rebuilt": 0, "errors": 0}
    
    # Try to initialize IndexManagementClient
    try:
        from apps.documentation.services.index_management_client import IndexManagementClient
        index_client = IndexManagementClient()
    except ImportError:
        logger.warning("IndexManagementClient not available - index rebuilding will be skipped")
        return {"rebuilt": 0, "errors": 0, "error_details": [{"error": "IndexManagementClient not available"}]}
    
    stats = {
        "rebuilt": 0,
        "errors": 0,
        "error_details": [],
    }
    
    index_types = ['pages', 'endpoints', 'relationships', 'postman']
    
    for index_type in index_types:
        print(f"\n📄 Rebuilding {index_type} index...")
        try:
            if index_type == 'pages':
                response = index_client.rebuild_pages_index_v1()
            elif index_type == 'endpoints':
                response = index_client.rebuild_endpoints_index_v1()
            elif index_type == 'relationships':
                response = index_client.rebuild_relationships_index_v1()
            elif index_type == 'postman':
                response = index_client.rebuild_postman_index_v1()
            else:
                continue
            
            if response:
                stats["rebuilt"] += 1
                print(f"  ✅ Rebuilt: {index_type} index")
            else:
                stats["errors"] += 1
                stats["error_details"].append({
                    "type": index_type,
                    "error": "Rebuild returned None"
                })
                print(f"  ❌ Failed: {index_type} index")
        except Exception as e:
            stats["errors"] += 1
            error_msg = f"Rebuild failed: {str(e)}"
            stats["error_details"].append({
                "type": index_type,
                "error": error_msg,
            })
            logger.error(f"Failed to rebuild {index_type} index: {e}", exc_info=True)
            print(f"  ❌ {index_type} index: {error_msg}")
    
    return stats


def upload_all_docs(
    pages_only: bool = False,
    endpoints_only: bool = False,
    relationships_only: bool = False,
    skip_indexes: bool = False,
    dry_run: bool = False,
    mode: str = "upsert",
) -> Dict[str, Any]:
    """
    Upload all documentation files to Lambda Documentation API.
    
    Args:
        pages_only: Only upload pages
        endpoints_only: Only upload endpoints
        relationships_only: Only upload relationships
        skip_indexes: Skip rebuilding indexes
        dry_run: If True, don't actually upload
        mode: Import mode - "upsert" (default), "create_only", or "update_only"
        
    Returns:
        Dictionary with overall statistics
    """
    print("=" * 60)
    print("Upload All Documentation Files to Lambda API")
    print("=" * 60)
    print(f"\n📂 Media root: {MEDIA_ROOT}")
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No files will be uploaded\n")
    
    overall_stats = {
        "pages": {},
        "endpoints": {},
        "relationships": {},
        "indexes": {},
        "summary": {},
    }
    
    # Upload pages
    if not endpoints_only and not relationships_only:
        print("\n" + "=" * 60)
        print("PHASE 1: Uploading Pages")
        print("=" * 60)
        try:
            overall_stats["pages"] = upload_pages(
                dry_run=dry_run,
                mode=mode,
                batch_size=50,  # Use default batch size
            )
        except Exception as e:
            logger.error(f"Error uploading pages: {e}", exc_info=True)
            overall_stats["pages"] = {"created": 0, "updated": 0, "errors": 1, "error_details": [{"error": str(e)}]}
    
    # Upload endpoints
    if not pages_only and not relationships_only:
        print("\n" + "=" * 60)
        print("PHASE 2: Uploading Endpoints")
        print("=" * 60)
        try:
            overall_stats["endpoints"] = upload_endpoints(
                dry_run=dry_run,
                mode=mode,
                batch_size=50,  # Use default batch size
            )
        except Exception as e:
            logger.error(f"Error uploading endpoints: {e}", exc_info=True)
            overall_stats["endpoints"] = {"created": 0, "updated": 0, "errors": 1, "error_details": [{"error": str(e)}]}
    
    # Upload relationships
    if not pages_only and not endpoints_only:
        print("\n" + "=" * 60)
        print("PHASE 3: Uploading Relationships")
        print("=" * 60)
        try:
            overall_stats["relationships"] = upload_relationships(
                dry_run=dry_run,
                mode=mode,
                batch_size=50,  # Use default batch size
            )
        except Exception as e:
            logger.error(f"Error uploading relationships: {e}", exc_info=True)
            overall_stats["relationships"] = {"created": 0, "updated": 0, "errors": 1, "error_details": [{"error": str(e)}]}
    
    # Rebuild indexes (Lambda API handles index management)
    if not skip_indexes and not dry_run:
        overall_stats["indexes"] = rebuild_indexes(dry_run=dry_run)
    
    # Calculate summary
    pages_stats = overall_stats.get("pages", {})
    endpoints_stats = overall_stats.get("endpoints", {})
    relationships_stats = overall_stats.get("relationships", {})
    indexes_stats = overall_stats.get("indexes", {})
    
    overall_stats["summary"] = {
        "total_created": (
            pages_stats.get("created", 0) +
            endpoints_stats.get("created", 0) +
            relationships_stats.get("created", 0)
        ),
        "total_updated": (
            pages_stats.get("updated", 0) +
            endpoints_stats.get("updated", 0) +
            relationships_stats.get("updated", 0)
        ),
        "total_errors": (
            pages_stats.get("errors", 0) +
            endpoints_stats.get("errors", 0) +
            relationships_stats.get("errors", 0) +
            indexes_stats.get("errors", 0)
        ),
        "pages": {
            "created": pages_stats.get("created", 0),
            "updated": pages_stats.get("updated", 0),
            "errors": pages_stats.get("errors", 0),
        },
        "endpoints": {
            "created": endpoints_stats.get("created", 0),
            "updated": endpoints_stats.get("updated", 0),
            "errors": endpoints_stats.get("errors", 0),
        },
        "relationships": {
            "created": relationships_stats.get("created", 0),
            "updated": relationships_stats.get("updated", 0),
            "errors": relationships_stats.get("errors", 0),
        },
        "indexes": {
            "rebuilt": indexes_stats.get("rebuilt", 0),
            "errors": indexes_stats.get("errors", 0),
        },
    }
    
    # Print overall summary
    print("\n" + "=" * 60)
    print("Overall Upload Summary")
    print("=" * 60)
    summary = overall_stats["summary"]
    print(f"  ➕ Created:   {summary['total_created']}")
    print(f"  🔄 Updated:   {summary['total_updated']}")
    print(f"  ❌ Errors:    {summary['total_errors']}")
    print(f"\n  Pages:        {summary['pages']['created']} created, {summary['pages']['updated']} updated, {summary['pages']['errors']} errors")
    print(f"  Endpoints:    {summary['endpoints']['created']} created, {summary['endpoints']['updated']} updated, {summary['endpoints']['errors']} errors")
    print(f"  Relationships: {summary['relationships']['created']} created, {summary['relationships']['updated']} updated, {summary['relationships']['errors']} errors")
    print(f"  Indexes:      {summary['indexes']['rebuilt']} rebuilt, {summary['indexes']['errors']} errors")
    print("=" * 60 + "\n")
    
    return overall_stats


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Upload all documentation files from media/ to Lambda Documentation API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload everything
  python scripts/upload_all_docs_to_s3.py
  
  # Dry run (see what would be uploaded)
  python scripts/upload_all_docs_to_s3.py --dry-run
  
  # Upload only pages
  python scripts/upload_all_docs_to_s3.py --pages-only
  
  # Use create_only mode
  python scripts/upload_all_docs_to_s3.py --mode create_only
  
  # Skip index rebuilding
  python scripts/upload_all_docs_to_s3.py --skip-indexes
        """
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be uploaded without actually uploading",
    )
    
    parser.add_argument(
        "--mode",
        type=str,
        default="upsert",
        choices=["upsert", "create_only", "update_only"],
        help="Import mode: upsert (create or update), create_only, or update_only (default: upsert)",
    )
    
    parser.add_argument(
        "--pages-only",
        action="store_true",
        help="Upload only pages",
    )
    
    parser.add_argument(
        "--endpoints-only",
        action="store_true",
        help="Upload only endpoints",
    )
    
    parser.add_argument(
        "--relationships-only",
        action="store_true",
        help="Upload only relationships",
    )
    
    parser.add_argument(
        "--skip-indexes",
        action="store_true",
        help="Skip rebuilding indexes",
    )
    
    args = parser.parse_args()
    
    try:
        stats = upload_all_docs(
            pages_only=args.pages_only,
            endpoints_only=args.endpoints_only,
            relationships_only=args.relationships_only,
            skip_indexes=args.skip_indexes,
            dry_run=args.dry_run,
            mode=args.mode,
        )
        
        if stats["summary"]["total_errors"] > 0:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Upload interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logger.error(f"Fatal error in upload script: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
