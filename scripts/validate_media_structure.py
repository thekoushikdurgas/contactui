#!/usr/bin/env python3
"""
Validate media directory structure and JSON files.
Identifies errors and warnings in postman and relationships directories.

Refactored to use shared validation logic and context-aware utilities.
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup Django environment if needed
if "DJANGO_SETTINGS_MODULE" not in os.environ:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "docs_ai_agent.settings")
    try:
        import django
        django.setup()
    except (ImportError, RuntimeError):
        pass

from scripts.utils.context import (
    get_media_root,
    get_postman_dir,
    get_relationships_dir,
    get_logger,
)
from scripts.utils.validators import (
    load_json_file,
    validate_relationship_by_page,
    validate_relationship_by_endpoint,
    ValidationError,
)

logger = get_logger(__name__)


def validate_json_file(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate a JSON file for syntax errors.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    data, parse_error = load_json_file(file_path)
    
    if parse_error:
        errors.append(parse_error)
        return False, errors
    
    return True, []


def validate_postman_index(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate postman index.json file.
    
    Args:
        file_path: Path to index.json file
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    errors = []
    warnings = []
    
    try:
        data, parse_error = load_json_file(file_path)
        
        if parse_error:
            errors.append(parse_error)
            return False, errors
        
        if data is None:
            errors.append("Failed to load JSON")
            return False, errors
        
        # Required fields
        required_fields = ["version", "last_updated", "total", "configurations"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        if "configurations" in data and isinstance(data["configurations"], list):
            for idx, config in enumerate(data["configurations"]):
                config_required = ["config_id", "name", "state", "created_at", "updated_at"]
                for field in config_required:
                    if field not in config:
                        errors.append(f"Configuration[{idx}] missing required field: {field}")
        
        return len(errors) == 0, errors + warnings
    
    except Exception as e:
        return False, [f"Error validating file: {e}"]


def main():
    """Main validation function."""
    print("=" * 80)
    print("Media Directory Structure Validation")
    print("=" * 80)
    
    media_root = get_media_root()
    postman_dir = get_postman_dir()
    relationships_dir = get_relationships_dir()
    
    all_errors = []
    all_warnings = []
    
    # Check directory naming
    print("\n[1] Checking directory structure...")
    if relationships_dir.name == "relationship":
        all_warnings.append("Directory named 'relationship' (typo) - should be 'relationships'")
        print("  ⚠️  WARNING: Directory is named 'relationship' instead of 'relationships'")
    else:
        print(f"  ✓ Directory name is correct: {relationships_dir.name}")
    
    # Validate Postman files
    print("\n[2] Validating Postman files...")
    if postman_dir.exists():
        index_file = postman_dir / "index.json"
        if index_file.exists():
            is_valid, issues = validate_postman_index(index_file)
            if is_valid:
                print(f"  ✓ {index_file.name} is valid")
            else:
                for issue in issues:
                    if "error" in issue.lower() or "missing" in issue.lower():
                        all_errors.append(f"Postman/{index_file.name}: {issue}")
                        print(f"  ✗ ERROR: {issue}")
                    else:
                        all_warnings.append(f"Postman/{index_file.name}: {issue}")
                        print(f"  ⚠️  WARNING: {issue}")
        
        # Check collection files
        collection_dir = postman_dir / "collection"
        if collection_dir.exists():
            for file_path in collection_dir.glob("*.json"):
                is_valid, issues = validate_json_file(file_path)
                if is_valid:
                    print(f"  ✓ {file_path.name} (JSON valid)")
                else:
                    for issue in issues:
                        all_errors.append(f"Postman/collection/{file_path.name}: {issue}")
                        print(f"  ✗ ERROR: {issue}")
    else:
        all_warnings.append(f"Postman directory does not exist: {postman_dir}")
        print("  ⚠️  WARNING: Postman directory not found")
    
    # Validate Relationships files
    print("\n[3] Validating Relationships files...")
    if relationships_dir.exists():
        # Validate index
        index_file = relationships_dir / "index.json"
        if index_file.exists():
            is_valid, issues = validate_json_file(index_file)
            if is_valid:
                print(f"  ✓ {index_file.name} (JSON valid)")
            else:
                for issue in issues:
                    all_errors.append(f"Relationships/{index_file.name}: {issue}")
                    print(f"  ✗ ERROR: {issue}")
        
        # Validate by-page files
        by_page_dir = relationships_dir / "by-page"
        if by_page_dir.exists():
            page_files = list(by_page_dir.glob("*.json"))
            print(f"  Validating {len(page_files)} by-page files...")
            for file_path in page_files:
                # Load file first
                data, parse_error = load_json_file(file_path)
                if parse_error:
                    all_errors.append(f"Relationships/by-page/{file_path.name}: {parse_error}")
                    print(f"    ✗ ERROR: {parse_error}")
                    continue
                
                if data is None:
                    all_errors.append(f"Relationships/by-page/{file_path.name}: Failed to load JSON")
                    print(f"    ✗ ERROR: Failed to load JSON")
                    continue
                
                # Validate using shared validator
                is_valid, validation_errors = validate_relationship_by_page(data)
                
                if is_valid and not validation_errors:
                    print(f"    ✓ {file_path.name}")
                else:
                    for error in validation_errors:
                        if "error" in error.message.lower() or "missing" in error.message.lower():
                            all_errors.append(f"Relationships/by-page/{file_path.name}: {error.message}")
                            print(f"    ✗ ERROR: {error.message}")
                        else:
                            all_warnings.append(f"Relationships/by-page/{file_path.name}: {error.message}")
                            print(f"    ⚠️  WARNING: {error.message}")
        
        # Validate by-endpoint files
        by_endpoint_dir = relationships_dir / "by-endpoint"
        if by_endpoint_dir.exists():
            endpoint_files = list(by_endpoint_dir.glob("*.json"))
            print(f"  Validating {len(endpoint_files)} by-endpoint files...")
            for file_path in endpoint_files:
                # Load file first
                data, parse_error = load_json_file(file_path)
                if parse_error:
                    all_errors.append(f"Relationships/by-endpoint/{file_path.name}: {parse_error}")
                    print(f"    ✗ ERROR: {parse_error}")
                    continue
                
                if data is None:
                    all_errors.append(f"Relationships/by-endpoint/{file_path.name}: Failed to load JSON")
                    print(f"    ✗ ERROR: Failed to load JSON")
                    continue
                
                # Validate using shared validator
                is_valid, validation_errors = validate_relationship_by_endpoint(data)
                
                if is_valid and not validation_errors:
                    print(f"    ✓ {file_path.name}")
                else:
                    for error in validation_errors:
                        if "error" in error.message.lower() or "missing" in error.message.lower():
                            all_errors.append(f"Relationships/by-endpoint/{file_path.name}: {error.message}")
                            print(f"    ✗ ERROR: {error.message}")
                        else:
                            all_warnings.append(f"Relationships/by-endpoint/{file_path.name}: {error.message}")
                            print(f"    ⚠️  WARNING: {error.message}")
    else:
        all_errors.append(f"Relationships directory does not exist: {relationships_dir}")
        print("  ✗ ERROR: Relationships directory not found")
    
    # Summary
    print("\n" + "=" * 80)
    print("Validation Summary")
    print("=" * 80)
    print(f"Total Errors: {len(all_errors)}")
    print(f"Total Warnings: {len(all_warnings)}")
    
    if all_errors:
        print("\nErrors:")
        for error in all_errors[:20]:  # Show first 20
            print(f"  ✗ {error}")
        if len(all_errors) > 20:
            print(f"  ... and {len(all_errors) - 20} more errors")
    
    if all_warnings:
        print("\nWarnings:")
        for warning in all_warnings[:20]:  # Show first 20
            print(f"  ⚠️  {warning}")
        if len(all_warnings) > 20:
            print(f"  ... and {len(all_warnings) - 20} more warnings")
    
    if not all_errors and not all_warnings:
        print("\n✓ All files validated successfully!")
    
    # Export validation report (JSON)
    report = {
        "errors": all_errors,
        "warnings": all_warnings,
        "summary": {
            "total_errors": len(all_errors),
            "total_warnings": len(all_warnings),
        },
    }
    
    report_path = media_root / "validation_report.json"
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n📄 Validation report saved to: {report_path}")
    except Exception as e:
        logger.warning(f"Failed to save validation report: {e}")
    
    return len(all_errors) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
