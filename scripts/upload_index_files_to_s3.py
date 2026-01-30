#!/usr/bin/env python3
"""
Upload index files from docs/ to S3.

This script reads index files from docs/pages/, docs/endpoints/, and docs/relationship/
and uploads them to S3 after validation.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict

# Add parent directory to path for Lambda API imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Use context-aware utilities
from scripts.utils.context import (
    get_pages_dir,
    get_endpoints_dir,
    get_relationships_dir,
    get_logger,
    get_settings,
)

logger = get_logger(__name__)
settings = get_settings()

# Get directories using context-aware utilities
PAGES_DIR = get_pages_dir()
ENDPOINTS_DIR = get_endpoints_dir()
RELATIONSHIPS_DIR = get_relationships_dir()

# Try to import S3JSONStorage (may not be available in Django context)
try:
    from app.clients.s3_json_storage import S3JSONStorage
except ImportError:
    # Fallback: use Django S3Service if available
    try:
        from apps.core.services import S3Service
        # Create a wrapper to match S3JSONStorage interface
        class S3JSONStorage:
            def __init__(self):
                self.service = S3Service()
            
            async def upload_file(self, local_path, s3_key):
                self.service.upload_file(str(local_path), s3_key)
            
            async def list_files(self, prefix, max_keys=None):
                return self.service.list_files(prefix, max_keys)
    except ImportError:
        raise ImportError("S3 storage not available. Install Lambda API or Django app.")


def validate_index_structure(index_data: Dict[str, Any], index_type: str) -> tuple[bool, str | None]:
    """Validate index file structure."""
    # Check required fields
    if "version" not in index_data:
        return False, "Missing 'version' field"
    if "last_updated" not in index_data:
        return False, "Missing 'last_updated' field"
    if "total" not in index_data:
        return False, "Missing 'total' field"
    
    # Type-specific validation
    if index_type == "pages":
        if "pages" not in index_data:
            return False, "Missing 'pages' array"
        if "indexes" not in index_data:
            return False, "Missing 'indexes' object"
        if "by_type" not in index_data.get("indexes", {}):
            return False, "Missing 'indexes.by_type' object"
        if "by_route" not in index_data.get("indexes", {}):
            return False, "Missing 'indexes.by_route' object"
        
        # Check total matches pages length
        pages_list = index_data.get("pages", [])
        if index_data.get("total") != len(pages_list):
            return False, f"total ({index_data.get('total')}) does not match pages array length ({len(pages_list)})"
    
    elif index_type == "endpoints":
        if "endpoints" not in index_data:
            return False, "Missing 'endpoints' array"
        if "indexes" not in index_data:
            return False, "Missing 'indexes' object"
        if "by_api_version" not in index_data.get("indexes", {}):
            return False, "Missing 'indexes.by_api_version' object"
        if "by_method" not in index_data.get("indexes", {}):
            return False, "Missing 'indexes.by_method' object"
        if "by_path_method" not in index_data.get("indexes", {}):
            return False, "Missing 'indexes.by_path_method' object"
        
        # Check total matches endpoints length
        endpoints_list = index_data.get("endpoints", [])
        if index_data.get("total") != len(endpoints_list):
            return False, f"total ({index_data.get('total')}) does not match endpoints array length ({len(endpoints_list)})"
    
    elif index_type == "relationships":
        if "by_api_version" not in index_data:
            return False, "Missing 'by_api_version' object"
    
    return True, None


async def upload_index_files(dry_run: bool = False) -> Dict[str, Any]:
    """
    Upload index files to S3.
    
    Args:
        dry_run: If True, don't actually upload, just show what would be uploaded
        
    Returns:
        Dictionary with upload statistics
    """
    print("=" * 60)
    print("Upload Index Files to S3")
    print("=" * 60)
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No files will be uploaded\n")
    
    storage = S3JSONStorage()
    stats = {
        "uploaded": 0,
        "errors": 0,
        "error_details": [],
    }
    
    index_files = [
        ("pages", PAGES_DIR / "pages_index.json", f"{settings.S3_DATA_PREFIX}pages/index.json"),
        ("endpoints", ENDPOINTS_DIR / "endpoints_index.json", f"{settings.S3_DATA_PREFIX}endpoints/index.json"),
        ("relationships", RELATIONSHIPS_DIR / "relationships_index.json", f"{settings.S3_DATA_PREFIX}relationships/index.json"),
    ]
    
    for index_type, index_path, s3_key in index_files:
        print(f"\n📄 Processing {index_type} index...")
        
        if not index_path.exists():
            stats["errors"] += 1
            error_msg = f"Index file not found: {index_path}"
            stats["error_details"].append({
                "file": index_path.name,
                "type": index_type,
                "error": error_msg,
            })
            print(f"  ❌ {index_path.name}: {error_msg}")
            continue
        
        # Load and validate index file
        try:
            content = index_path.read_text(encoding='utf-8')
            index_data = json.loads(content)
        except json.JSONDecodeError as e:
            stats["errors"] += 1
            error_msg = f"Invalid JSON: {str(e)}"
            stats["error_details"].append({
                "file": index_path.name,
                "type": index_type,
                "error": error_msg,
            })
            print(f"  ❌ {index_path.name}: {error_msg}")
            continue
        except Exception as e:
            stats["errors"] += 1
            error_msg = f"Error reading file: {str(e)}"
            stats["error_details"].append({
                "file": index_path.name,
                "type": index_type,
                "error": error_msg,
            })
            print(f"  ❌ {index_path.name}: {error_msg}")
            continue
        
        # Validate structure
        is_valid, error_msg = validate_index_structure(index_data, index_type)
        if not is_valid:
            stats["errors"] += 1
            stats["error_details"].append({
                "file": index_path.name,
                "type": index_type,
                "error": error_msg,
            })
            print(f"  ❌ {index_path.name}: {error_msg}")
            continue
        
        if dry_run:
            print(f"  [DRY RUN] Would upload: {index_path.name} -> {s3_key}")
            print(f"            Total: {index_data.get('total', 0)}")
        else:
            try:
                await storage.write_json(s3_key, index_data)
                stats["uploaded"] += 1
                print(f"  ✅ Uploaded: {index_path.name} (total: {index_data.get('total', 0)})")
            except Exception as e:
                stats["errors"] += 1
                error_msg = f"Upload failed: {str(e)}"
                stats["error_details"].append({
                    "file": index_path.name,
                    "type": index_type,
                    "error": error_msg,
                })
                logger.error(f"Failed to upload {index_path.name}: {e}", exc_info=True)
                print(f"  ❌ {index_path.name}: {error_msg}")
    
    # Summary
    print(f"\n{'='*60}")
    print("Upload Summary")
    print(f"{'='*60}")
    print(f"  ✅ Uploaded:   {stats['uploaded']}")
    print(f"  ❌ Errors:    {stats['errors']}")
    print(f"\n  📦 S3 Bucket: {settings.S3_BUCKET_NAME}")
    print(f"  📂 S3 Prefix: {settings.S3_DATA_PREFIX}")
    
    if stats["error_details"]:
        print(f"\n{'='*60}")
        print("Error Details:")
        print(f"{'='*60}")
        for error in stats["error_details"]:
            print(f"  ❌ {error['file']} ({error['type']}): {error['error']}")
    
    print(f"{'='*60}\n")
    
    return stats


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Upload index files from docs/ to S3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be uploaded without actually uploading",
    )
    
    args = parser.parse_args()
    
    try:
        stats = await upload_index_files(dry_run=args.dry_run)
        
        if stats["errors"] > 0:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Upload interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logger.error(f"Fatal error in upload script: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
