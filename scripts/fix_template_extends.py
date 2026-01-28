#!/usr/bin/env python
"""
Script to fix template extends statements.
Changes {% extends "documentation/base.html" %} to {% extends "base.html" %}
"""

import os
import re
from pathlib import Path

def fix_template_file(file_path: Path):
    """Fix extends statement in a template file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix {% extends "documentation/base.html" %} to {% extends "base.html" %}
        patterns = [
            (r'{%\s*extends\s+["\']documentation/base\.html["\']\s*%}', r'{% extends "base.html" %}'),
            (r'{%\s*extends\s+["\']documentation/base\.html["\']\s*%}', r"{% extends 'base.html' %}"),
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to fix all template files."""
    base_dir = Path(__file__).parent.parent
    templates_dir = base_dir / 'templates' / 'documentation' / 'media_manager'
    
    if not templates_dir.exists():
        print(f"Templates directory not found: {templates_dir}")
        return
    
    updated_files = []
    total_files = 0
    
    # Process all HTML files
    for html_file in templates_dir.rglob('*.html'):
        total_files += 1
        if fix_template_file(html_file):
            updated_files.append(html_file.relative_to(base_dir))
    
    print(f"Processed {total_files} template files")
    if updated_files:
        print(f"Updated {len(updated_files)} files:")
        for file in updated_files:
            print(f"  - {file}")
    else:
        print("No files needed updating")

if __name__ == '__main__':
    main()
