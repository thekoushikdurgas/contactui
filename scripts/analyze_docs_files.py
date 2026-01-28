#!/usr/bin/env python3
"""
Analyze and validate all documentation JSON files.

This script scans all JSON files in docs/pages/, docs/endpoints/, and docs/retations/
and validates them against their respective schemas.

Refactored to use shared validators and context-aware utilities.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add parent directory to path for Lambda API imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Use context-aware utilities and shared validators
from scripts.utils.context import (
    get_pages_dir,
    get_endpoints_dir,
    get_relationships_dir,
    get_logger,
    get_media_root,
)
from scripts.utils.validators import (
    load_json_file,
    validate_with_schema,
    validate_relationship_by_page,
    validate_relationship_by_endpoint,
    ValidationError,
    get_validator,
)
from scripts.utils.upload_helpers import get_exclude_files

logger = get_logger(__name__)

# Get directories using context-aware utilities
PAGES_DIR = get_pages_dir()
ENDPOINTS_DIR = get_endpoints_dir()
RELATIONSHIPS_DIR = get_relationships_dir()
RELATIONSHIPS_BY_PAGE_DIR = RELATIONSHIPS_DIR / "by-page"
MEDIA_ROOT = get_media_root()

# Files to exclude from analysis
EXCLUDE_FILES = get_exclude_files()


def analyze_pages() -> Dict[str, Any]:
    """Analyze all page JSON files."""
    print("\n" + "=" * 60)
    print("Analyzing Pages")
    print("=" * 60)
    
    if not PAGES_DIR.exists():
        print(f"❌ Pages directory not found: {PAGES_DIR}")
        return {"valid": 0, "invalid": 0, "errors": [], "files": []}
    
    validator = PageSchemaValidator()
    results = {
        "valid": 0,
        "invalid": 0,
        "errors": [],
        "files": [],
        "duplicate_ids": [],
    }
    
    page_ids = set()
    json_files = [
        f for f in PAGES_DIR.glob("*.json")
        if f.name not in EXCLUDE_FILES and not f.name.endswith("_index.json")
    ]
    
    print(f"\n📁 Found {len(json_files)} page files to analyze\n")
    
    for file_path in sorted(json_files):
        file_name = file_path.name
        data, parse_error = load_json_file(file_path)
        
        if parse_error:
            results["invalid"] += 1
            results["errors"].append({
                "file": file_name,
                "type": "parse_error",
                "error": parse_error,
            })
            print(f"❌ {file_name}: {parse_error}")
            continue
        
        # Validate schema with robust error handling
        is_valid = True
        validation_errors = []
        try:
            if validator and hasattr(validator, 'validate'):
                validation_result = validator.validate(data)
                if isinstance(validation_result, tuple) and len(validation_result) == 2:
                    is_valid, validation_errors = validation_result
                    # Ensure validation_errors is always a list
                    if validation_errors is None:
                        validation_errors = []
                    elif not isinstance(validation_errors, list):
                        validation_errors = list(validation_errors) if validation_errors else []
                else:
                    # Unexpected return format
                    is_valid = True
                    validation_errors = []
            else:
                # Validator not available, skip validation
                is_valid = True
                validation_errors = []
        except Exception as e:
            # If validation fails with exception, log and treat as invalid
            logger.error(f"Validation error for {file_name}: {e}", exc_info=True)
            is_valid = False
            validation_errors = [ValidationError("validation", f"Validation error: {str(e)}")]
        
        # Check for duplicate page_id
        page_id = data.get("page_id") if data else None
        if page_id:
            if page_id in page_ids:
                results["duplicate_ids"].append({
                    "file": file_name,
                    "page_id": page_id,
                })
            else:
                page_ids.add(page_id)
        
        file_result = {
            "file": file_name,
            "valid": is_valid,
            "page_id": page_id,
            "errors": [e.to_dict() for e in (validation_errors or [])],
        }
        results["files"].append(file_result)
        
        if is_valid:
            results["valid"] += 1
            print(f"✅ {file_name}")
        else:
            results["invalid"] += 1
            error_count = len(validation_errors or [])
            print(f"❌ {file_name}: {error_count} validation error(s)")
            if validation_errors:
                for error in validation_errors[:3]:  # Show first 3 errors
                    print(f"   - {error.field}: {error.message}")
                if error_count > 3:
                    print(f"   ... and {error_count - 3} more error(s)")
    
    return results


def analyze_endpoints() -> Dict[str, Any]:
    """Analyze all endpoint JSON files."""
    print("\n" + "=" * 60)
    print("Analyzing Endpoints")
    print("=" * 60)
    
    if not ENDPOINTS_DIR.exists():
        print(f"❌ Endpoints directory not found: {ENDPOINTS_DIR}")
        return {"valid": 0, "invalid": 0, "errors": [], "files": []}
    
    validator = get_validator("endpoints")
    results = {
        "valid": 0,
        "invalid": 0,
        "errors": [],
        "files": [],
        "duplicate_ids": [],
    }
    
    endpoint_ids = set()
    json_files = [
        f for f in ENDPOINTS_DIR.glob("*.json")
        if f.name not in EXCLUDE_FILES and not f.name.endswith("_index.json")
    ]
    
    print(f"\n📁 Found {len(json_files)} endpoint files to analyze\n")
    
    for file_path in sorted(json_files):
        file_name = file_path.name
        data, parse_error = load_json_file(file_path)
        
        if parse_error:
            results["invalid"] += 1
            results["errors"].append({
                "file": file_name,
                "type": "parse_error",
                "error": parse_error,
            })
            print(f"❌ {file_name}: {parse_error}")
            continue
        
        # Validate schema using shared validator
        is_valid, validation_errors = validate_with_schema(data, "endpoints", validator)
        
        # Check for duplicate endpoint_id
        endpoint_id = data.get("endpoint_id") if data else None
        if endpoint_id:
            if endpoint_id in endpoint_ids:
                results["duplicate_ids"].append({
                    "file": file_name,
                    "endpoint_id": endpoint_id,
                })
            else:
                endpoint_ids.add(endpoint_id)
        
        file_result = {
            "file": file_name,
            "valid": is_valid,
            "endpoint_id": endpoint_id,
            "errors": [e.to_dict() for e in (validation_errors or [])],
        }
        results["files"].append(file_result)
        
        if is_valid:
            results["valid"] += 1
            print(f"✅ {file_name}")
        else:
            results["invalid"] += 1
            error_count = len(validation_errors or [])
            print(f"❌ {file_name}: {error_count} validation error(s)")
            if validation_errors:
                for error in validation_errors[:3]:  # Show first 3 errors
                    print(f"   - {error.field}: {error.message}")
                if error_count > 3:
                    print(f"   ... and {error_count - 3} more error(s)")
    
    return results


def analyze_relationships() -> Dict[str, Any]:
    """Analyze all relationship JSON files."""
    print("\n" + "=" * 60)
    print("Analyzing Relationships")
    print("=" * 60)
    
    if not RELATIONSHIPS_DIR.exists():
        print(f"❌ Relationships directory not found: {RELATIONSHIPS_DIR}")
        return {"valid": 0, "invalid": 0, "errors": [], "files": []}
    
    results = {
        "valid": 0,
        "invalid": 0,
        "errors": [],
        "files": [],
        "by_page": {"valid": 0, "invalid": 0},
        "by_endpoint": {"valid": 0, "invalid": 0},
    }
    
    # Analyze by-page relationships
    if RELATIONSHIPS_BY_PAGE_DIR.exists():
        by_page_files = list(RELATIONSHIPS_BY_PAGE_DIR.glob("*.json"))
        print(f"\n📁 Found {len(by_page_files)} by-page relationship files\n")
        
        for file_path in sorted(by_page_files):
            file_name = f"by-page/{file_path.name}"
            data, parse_error = load_json_file(file_path)
            
            if parse_error:
                results["invalid"] += 1
                results["by_page"]["invalid"] += 1
                results["errors"].append({
                    "file": file_name,
                    "type": "parse_error",
                    "error": parse_error,
                })
                print(f"❌ {file_name}: {parse_error}")
                continue
            
            # Validate using shared validator
            is_valid, validation_errors = validate_relationship_by_page(data)
            
            file_result = {
                "file": file_name,
                "type": "by-page",
                "valid": is_valid,
                "errors": [e.to_dict() for e in (validation_errors or [])],
            }
            results["files"].append(file_result)
            
            if is_valid:
                results["valid"] += 1
                results["by_page"]["valid"] += 1
                print(f"✅ {file_name}")
            else:
                results["invalid"] += 1
                results["by_page"]["invalid"] += 1
                error_count = len(validation_errors or [])
                print(f"❌ {file_name}: {error_count} validation error(s)")
                if validation_errors:
                    for error in validation_errors[:3]:
                        print(f"   - {error.field}: {error.message}")
                if error_count > 3:
                    print(f"   ... and {error_count - 3} more error(s)")
    
    # Analyze by-endpoint relationships
    by_endpoint_files = [
        f for f in RELATIONSHIPS_DIR.glob("*.json")
        if f.name.startswith("by-endpoint_") and f.name not in EXCLUDE_FILES
    ]
    print(f"\n📁 Found {len(by_endpoint_files)} by-endpoint relationship files\n")
    
    for file_path in sorted(by_endpoint_files):
        file_name = file_path.name
        data, parse_error = load_json_file(file_path)
        
        if parse_error:
            results["invalid"] += 1
            results["by_endpoint"]["invalid"] += 1
            results["errors"].append({
                "file": file_name,
                "type": "parse_error",
                "error": parse_error,
            })
            print(f"❌ {file_name}: {parse_error}")
            continue
        
        # Validate using shared validator
        is_valid, validation_errors = validate_relationship_by_endpoint(data)
        
        file_result = {
            "file": file_name,
            "type": "by-endpoint",
            "valid": is_valid,
            "errors": [e.to_dict() for e in (validation_errors or [])],
        }
        results["files"].append(file_result)
        
        if is_valid:
            results["valid"] += 1
            results["by_endpoint"]["valid"] += 1
            print(f"✅ {file_name}")
        else:
            results["invalid"] += 1
            results["by_endpoint"]["invalid"] += 1
            error_count = len(validation_errors or [])
            print(f"❌ {file_name}: {error_count} validation error(s)")
            if validation_errors:
                for error in validation_errors[:3]:
                    print(f"   - {error.field}: {error.message}")
            if error_count > 3:
                print(f"   ... and {error_count - 3} more error(s)")
    
    return results


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Analyze and validate documentation JSON files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output JSON report file path (default: print to console only)",
    )
    
    parser.add_argument(
        "--pages-only",
        action="store_true",
        help="Analyze only pages",
    )
    
    parser.add_argument(
        "--endpoints-only",
        action="store_true",
        help="Analyze only endpoints",
    )
    
    parser.add_argument(
        "--relationships-only",
        action="store_true",
        help="Analyze only relationships",
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Documentation Files Analysis")
    print("=" * 60)
    print(f"\n📂 Media root: {MEDIA_ROOT}")
    
    report = {
        "pages": {},
        "endpoints": {},
        "relationships": {},
        "summary": {},
    }
    
    # Analyze pages
    if not args.endpoints_only and not args.relationships_only:
        report["pages"] = analyze_pages()
    
    # Analyze endpoints
    if not args.pages_only and not args.relationships_only:
        report["endpoints"] = analyze_endpoints()
    
    # Analyze relationships
    if not args.pages_only and not args.endpoints_only:
        report["relationships"] = analyze_relationships()
    
    # Generate summary
    pages_summary = report.get("pages", {})
    endpoints_summary = report.get("endpoints", {})
    relationships_summary = report.get("relationships", {})
    
    total_valid = (
        pages_summary.get("valid", 0) +
        endpoints_summary.get("valid", 0) +
        relationships_summary.get("valid", 0)
    )
    total_invalid = (
        pages_summary.get("invalid", 0) +
        endpoints_summary.get("invalid", 0) +
        relationships_summary.get("invalid", 0)
    )
    
    report["summary"] = {
        "total_valid": total_valid,
        "total_invalid": total_invalid,
        "total_files": total_valid + total_invalid,
        "pages": {
            "valid": pages_summary.get("valid", 0),
            "invalid": pages_summary.get("invalid", 0),
        },
        "endpoints": {
            "valid": endpoints_summary.get("valid", 0),
            "invalid": endpoints_summary.get("invalid", 0),
        },
        "relationships": {
            "valid": relationships_summary.get("valid", 0),
            "invalid": relationships_summary.get("invalid", 0),
        },
    }
    
    # Print summary
    print("\n" + "=" * 60)
    print("Analysis Summary")
    print("=" * 60)
    print(f"  ✅ Valid files:   {total_valid}")
    print(f"  ❌ Invalid files: {total_invalid}")
    print(f"  📄 Total files:    {total_valid + total_invalid}")
    print(f"\n  Pages:        {pages_summary.get('valid', 0)} valid, {pages_summary.get('invalid', 0)} invalid")
    print(f"  Endpoints:    {endpoints_summary.get('valid', 0)} valid, {endpoints_summary.get('invalid', 0)} invalid")
    print(f"  Relationships: {relationships_summary.get('valid', 0)} valid, {relationships_summary.get('invalid', 0)} invalid")
    
    # Check for duplicate IDs
    pages_duplicates = pages_summary.get("duplicate_ids", [])
    endpoints_duplicates = endpoints_summary.get("duplicate_ids", [])
    
    if pages_duplicates:
        print(f"\n  ⚠️  Found {len(pages_duplicates)} duplicate page_id(s)")
        for dup in pages_duplicates[:5]:
            print(f"     - {dup['page_id']} in {dup['file']}")
    
    if endpoints_duplicates:
        print(f"\n  ⚠️  Found {len(endpoints_duplicates)} duplicate endpoint_id(s)")
        for dup in endpoints_duplicates[:5]:
            print(f"     - {dup['endpoint_id']} in {dup['file']}")
    
    # Save report if output specified
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f"\n📄 Report saved to: {output_path}")
    
    print("=" * 60 + "\n")
    
    # Exit with error code if invalid files found
    if total_invalid > 0:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
