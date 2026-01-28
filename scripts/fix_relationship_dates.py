#!/usr/bin/env python3
"""
Fix date inconsistencies in relationship files.
Ensures updated_at >= created_at for all relationships.

Refactored to use context-aware utilities and shared validators.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

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

from scripts.utils.context import get_relationships_dir, get_logger
from scripts.utils.validators import load_json_file, validate_date_consistency

logger = get_logger(__name__)

def fix_date_inconsistencies(dry_run: bool = True) -> Dict[str, Any]:
    """Fix date inconsistencies in relationship files."""
    relationships_dir = get_relationships_dir()
    
    stats = {
        'files_checked': 0,
        'files_fixed': 0,
        'endpoints_fixed': 0,
        'pages_fixed': 0,
        'errors': []
    }
    
    print("=" * 80)
    print("Fix Relationship Date Inconsistencies")
    print("=" * 80)
    if dry_run:
        print("\n🔍 DRY RUN MODE - No files will be modified\n")
    else:
        print("\n⚠️  LIVE MODE - Files will be modified\n")
    
    # Fix by-page files
    by_page_dir = relationships_dir / 'by-page'
    if by_page_dir.exists():
        print(f"\n[1] Processing by-page files...")
        for file_path in by_page_dir.glob('*.json'):
            stats['files_checked'] += 1
            try:
                data, parse_error = load_json_file(file_path)
                if parse_error:
                    error_msg = f"Error loading {file_path.name}: {parse_error}"
                    stats['errors'].append(error_msg)
                    print(f"  ✗ {error_msg}")
                    continue
                
                if data is None:
                    error_msg = f"Failed to load JSON from {file_path.name}"
                    stats['errors'].append(error_msg)
                    print(f"  ✗ {error_msg}")
                    continue
                
                modified = False
                file_created = None
                file_updated = None
                
                # Parse file-level dates
                if 'created_at' in data:
                    file_created = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
                if 'updated_at' in data:
                    file_updated = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
                
                # Fix file-level date if needed using shared validator
                if 'created_at' in data and 'updated_at' in data:
                    is_valid, date_errors = validate_date_consistency(data.get('created_at'), data.get('updated_at'))
                    if not is_valid:
                        if not dry_run:
                            data['updated_at'] = data['created_at']
                        modified = True
                        print(f"  Fixed file-level date in {file_path.name}")
                
                # Fix endpoint dates using shared validator
                if 'endpoints' in data and isinstance(data['endpoints'], list):
                    for endpoint in data['endpoints']:
                        if 'created_at' in endpoint and 'updated_at' in endpoint:
                            is_valid, date_errors = validate_date_consistency(
                                endpoint.get('created_at'), endpoint.get('updated_at')
                            )
                            if not is_valid:
                                if not dry_run:
                                    endpoint['updated_at'] = endpoint['created_at']
                                modified = True
                                stats['endpoints_fixed'] += 1
                        
                        # Also ensure endpoint updated_at >= file created_at
                        if file_created and 'updated_at' in endpoint:
                            is_valid, date_errors = validate_date_consistency(
                                data.get('created_at'), endpoint.get('updated_at')
                            )
                            if not is_valid:
                                if not dry_run:
                                    endpoint['updated_at'] = data['created_at']
                                modified = True
                                stats['endpoints_fixed'] += 1
                
                if modified:
                    stats['files_fixed'] += 1
                    if not dry_run:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                            f.write('\n')
                        print(f"  ✓ Fixed {file_path.name}")
                    else:
                        print(f"  [DRY RUN] Would fix {file_path.name}")
            
            except Exception as e:
                error_msg = f"Error processing {file_path.name}: {e}"
                stats['errors'].append(error_msg)
                print(f"  ✗ {error_msg}")
    
    # Fix by-endpoint files
    by_endpoint_dir = relationships_dir / 'by-endpoint'
    if by_endpoint_dir.exists():
        print(f"\n[2] Processing by-endpoint files...")
        for file_path in by_endpoint_dir.glob('*.json'):
            stats['files_checked'] += 1
            try:
                data, parse_error = load_json_file(file_path)
                if parse_error:
                    error_msg = f"Error loading {file_path.name}: {parse_error}"
                    stats['errors'].append(error_msg)
                    print(f"  ✗ {error_msg}")
                    continue
                
                if data is None:
                    error_msg = f"Failed to load JSON from {file_path.name}"
                    stats['errors'].append(error_msg)
                    print(f"  ✗ {error_msg}")
                    continue
                
                modified = False
                file_created = None
                file_updated = None
                
                # Parse file-level dates
                if 'created_at' in data:
                    file_created = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
                if 'updated_at' in data:
                    file_updated = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
                
                # Fix file-level date if needed using shared validator
                if 'created_at' in data and 'updated_at' in data:
                    is_valid, date_errors = validate_date_consistency(data.get('created_at'), data.get('updated_at'))
                    if not is_valid:
                        if not dry_run:
                            data['updated_at'] = data['created_at']
                        modified = True
                        print(f"  Fixed file-level date in {file_path.name}")
                
                # Fix page dates using shared validator
                if 'pages' in data and isinstance(data['pages'], list):
                    for page in data['pages']:
                        if 'updated_at' in page and 'created_at' in data:
                            is_valid, date_errors = validate_date_consistency(
                                data.get('created_at'), page.get('updated_at')
                            )
                            if not is_valid:
                                if not dry_run:
                                    page['updated_at'] = data['created_at']
                                modified = True
                                stats['pages_fixed'] += 1
                
                if modified:
                    stats['files_fixed'] += 1
                    if not dry_run:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                            f.write('\n')
                        print(f"  ✓ Fixed {file_path.name}")
                    else:
                        print(f"  [DRY RUN] Would fix {file_path.name}")
            
            except Exception as e:
                error_msg = f"Error processing {file_path.name}: {e}"
                stats['errors'].append(error_msg)
                print(f"  ✗ {error_msg}")
    
    # Summary
    print("\n" + "=" * 80)
    print("Fix Summary")
    print("=" * 80)
    print(f"Files checked: {stats['files_checked']}")
    print(f"Files fixed: {stats['files_fixed']}")
    print(f"Endpoints fixed: {stats['endpoints_fixed']}")
    print(f"Pages fixed: {stats['pages_fixed']}")
    if stats['errors']:
        print(f"\nErrors: {len(stats['errors'])}")
        for error in stats['errors'][:10]:
            print(f"  ✗ {error}")
    
    return stats

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Fix date inconsistencies in relationship files')
    parser.add_argument('--apply', action='store_true', help='Actually apply fixes (default is dry-run)')
    args = parser.parse_args()
    
    stats = fix_date_inconsistencies(dry_run=not args.apply)
    sys.exit(0 if len(stats['errors']) == 0 else 1)
