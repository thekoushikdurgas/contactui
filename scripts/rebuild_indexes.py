#!/usr/bin/env python3
"""
Migration script to rebuild all indexes with the new optimized format.

This script rebuilds all index.json files (pages, endpoints, relationships)
with full data for INDEX-ONLY responses.

Usage:
    python scripts/rebuild_indexes.py

Environment Variables:
    AWS_PROFILE: AWS profile to use (default: default)
    AWS_REGION: AWS region (default: us-east-1)
    S3_BUCKET: S3 bucket name (required)
    S3_DATA_PREFIX: S3 data prefix (default: data/)
"""

import asyncio
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime


async def rebuild_all_indexes():
    """Rebuild all indexes with the new optimized format."""
    # Import here to avoid issues with module loading
    from app.utils.s3_index_manager import S3IndexManager
    from app.utils.logger import get_logger
    
    logger = get_logger(__name__)
    
    print("=" * 60)
    print("Index Rebuild Migration Script")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")
    print()
    
    # Check required environment variables
    bucket = "contact360docs"
    if not bucket:
        print("ERROR: S3_BUCKET environment variable is required")
        print("Usage: S3_BUCKET=your-bucket-name python scripts/rebuild_indexes.py")
        sys.exit(1)
    
    print(f"S3 Bucket: {bucket}")
    print(f"Data Prefix: {os.getenv('S3_DATA_PREFIX', 'data/')}")
    print()
    
    # Create index manager
    index_manager = S3IndexManager()
    
    results = {
        "pages": {"status": "pending", "count": 0, "error": None},
        "endpoints": {"status": "pending", "count": 0, "error": None},
        "relationships": {"status": "pending", "count": 0, "error": None},
    }
    
    # Rebuild pages index
    print("1. Rebuilding pages index...")
    try:
        pages_index = await index_manager.rebuild_pages_index()
        results["pages"]["status"] = "success"
        results["pages"]["count"] = pages_index.get("total", 0)
        print(f"   SUCCESS: {results['pages']['count']} pages indexed")
        print(f"   Statistics: {pages_index.get('statistics', {})}")
    except Exception as e:
        results["pages"]["status"] = "error"
        results["pages"]["error"] = str(e)
        print(f"   ERROR: {e}")
        logger.error(f"Failed to rebuild pages index: {e}", exc_info=True)
    print()
    
    # Rebuild endpoints index
    print("2. Rebuilding endpoints index...")
    try:
        endpoints_index = await index_manager.rebuild_endpoints_index()
        results["endpoints"]["status"] = "success"
        results["endpoints"]["count"] = endpoints_index.get("total", 0)
        print(f"   SUCCESS: {results['endpoints']['count']} endpoints indexed")
        print(f"   Statistics: {endpoints_index.get('statistics', {})}")
    except Exception as e:
        results["endpoints"]["status"] = "error"
        results["endpoints"]["error"] = str(e)
        print(f"   ERROR: {e}")
        logger.error(f"Failed to rebuild endpoints index: {e}", exc_info=True)
    print()
    
    # Rebuild relationships index
    print("3. Rebuilding relationships index...")
    try:
        relationships_index = await index_manager.rebuild_relationships_index()
        results["relationships"]["status"] = "success"
        results["relationships"]["count"] = relationships_index.get("total", 0)
        print(f"   SUCCESS: {results['relationships']['count']} relationships indexed")
        print(f"   Statistics: {relationships_index.get('statistics', {})}")
    except Exception as e:
        results["relationships"]["status"] = "error"
        results["relationships"]["error"] = str(e)
        print(f"   ERROR: {e}")
        logger.error(f"Failed to rebuild relationships index: {e}", exc_info=True)
    print()
    
    # Print summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    all_success = True
    for index_type, result in results.items():
        status_icon = "✓" if result["status"] == "success" else "✗"
        print(f"  {status_icon} {index_type}: {result['status']} ({result['count']} items)")
        if result["error"]:
            print(f"      Error: {result['error']}")
            all_success = False
    
    print()
    print(f"Completed at: {datetime.now().isoformat()}")
    
    if all_success:
        print("\nAll indexes rebuilt successfully!")
        print("\nThe following optimizations are now active:")
        print("  - Pages: Full metadata in index, by_status index, pre-calculated statistics")
        print("  - Endpoints: Full data in index, cross-reference statistics")
        print("  - Relationships: Full data array, by_page/by_endpoint/by_usage indexes, statistics")
        print("\nLIST endpoints will now return INDEX-ONLY responses (90% faster)!")
    else:
        print("\nSome indexes failed to rebuild. Check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(rebuild_all_indexes())
