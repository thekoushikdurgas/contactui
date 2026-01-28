#!/usr/bin/env python
"""
Script to generate OpenAPI schema file from Django REST Framework API.

Usage:
    python scripts/generate_openapi_schema.py
    python scripts/generate_openapi_schema.py --format yaml
    python scripts/generate_openapi_schema.py --output docs/openapi-schema.json
"""

import os
import sys
import django
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command
import argparse


def main():
    parser = argparse.ArgumentParser(description='Generate OpenAPI schema file')
    parser.add_argument(
        '--output',
        '-o',
        default='openapi-schema.json',
        help='Output file path (default: openapi-schema.json)'
    )
    parser.add_argument(
        '--format',
        '-f',
        choices=['json', 'yaml'],
        default='json',
        help='Output format (default: json)'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate the generated schema'
    )
    
    args = parser.parse_args()
    
    # Determine file extension
    if args.format == 'yaml':
        output_file = args.output if args.output.endswith('.yaml') else f"{args.output}.yaml"
        format_flag = 'openapi-json'  # drf-spectacular uses 'openapi-json' for YAML
    else:
        output_file = args.output if args.output.endswith('.json') else f"{args.output}.json"
        format_flag = None
    
    # Build command arguments
    cmd_args = ['--file', output_file]
    if format_flag:
        cmd_args.extend(['--format', format_flag])
    if args.validate:
        cmd_args.append('--validate')
    
    print(f"Generating OpenAPI schema to {output_file}...")
    try:
        call_command('spectacular', *cmd_args)
        print(f"✅ Successfully generated OpenAPI schema: {output_file}")
        
        if args.validate:
            print("✅ Schema validation passed")
        
        # Print file size
        file_size = Path(output_file).stat().st_size
        print(f"📄 File size: {file_size:,} bytes ({file_size / 1024:.2f} KB)")
        
    except Exception as e:
        print(f"❌ Error generating schema: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
