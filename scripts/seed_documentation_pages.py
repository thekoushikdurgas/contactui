"""Seed script to populate S3 with documentation page content from markdown files."""

import asyncio
import os
import re
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone

# Add parent directory to path for Lambda API imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Use context-aware utilities
from scripts.utils.context import (
    find_docs_directory,
    get_logger,
    get_settings,
)

logger = get_logger(__name__)
settings = get_settings()

# Find docs directory using context-aware utility
DOCS_DIR = find_docs_directory() or (Path(__file__).parent.parent.parent / "docs" / "pages")

# Try to import Lambda API dependencies (may not be available in Django context)
try:
    from app.services.documentation_service import DocumentationService
    from app.services.s3_service import S3Service
    from app.repositories.repository_factory import get_documentation_repository
except ImportError:
    # Fallback for Django context - use Django services
    try:
        from apps.core.services import S3Service
        from apps.documentation.services.operations import DocumentationOperationsService
        
        class DocumentationService:
            def __init__(self):
                self.operations_service = DocumentationOperationsService()
        
        def get_documentation_repository():
            return None  # Not needed in Django context
    except ImportError:
        raise ImportError("Documentation services not available. Install Lambda API or Django app.")


def parse_markdown_file(file_path: Path) -> dict:
    """Parse markdown file and extract metadata (without content)."""
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
    
    # Generate page_id from filename (e.g., "about_page.md" -> "about_page")
    page_id = file_path.stem
    
    return {
        "page_id": page_id,
        "metadata": {
            "route": route,
            "file_path": file_path_str,
            "authentication": authentication,
            "authorization": authorization,
            "purpose": purpose,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    }


async def seed_documentation():
    """Seed all documentation pages to S3 via DocumentationService."""
    print("=" * 60)
    print("Documentation Pages Seeding Script")
    print("=" * 60)
    
    # Check if DOCS_DIR exists
    docs_dir = find_docs_directory()
    if docs_dir is None:
        print(f"\n❌ ERROR: Documentation directory not found")
        print(f"   Tried the following paths:")
        for path in POSSIBLE_DOCS_PATHS:
            print(f"     - {path}")
        print(f"\n   Please ensure the docs directory exists at one of these locations")
        return
    
    DOCS_DIR = docs_dir
    print(f"\n📂 Using docs directory: {DOCS_DIR}")
    
    # Exclude template and tracking files
    exclude_patterns = [
        '_page_docs_template',
        'CSS_',
        'DOCUMENTATION_',
        'FINAL_',
        'IMPLEMENTATION_',
        'PROGRESS_',
        'page_docs_coverage',
        'sidebar_'
    ]
    
    markdown_files = [
        f for f in DOCS_DIR.glob("*.md")
        if not any(pattern in f.name for pattern in exclude_patterns)
    ]
    
    if not markdown_files:
        print(f"\n⚠️  WARNING: No markdown files found in {DOCS_DIR}")
        return
    
    print(f"\n📁 Found {len(markdown_files)} documentation files to seed")
    print(f"📂 Directory: {DOCS_DIR}\n")
    
    # Initialize services
    repository = get_documentation_repository()
    service = DocumentationService(repository=repository)
    
    # Using S3 storage backend
    print(f"✅ Using S3 storage backend\n")
    
    # Test S3 bucket connection and verify/create bucket
    s3_service = S3Service()
    try:
        print("🔍 Checking S3 bucket...")
        bucket_exists = await s3_service.bucket_exists()
        
        if bucket_exists:
            print(f"✅ S3 bucket '{settings.S3_BUCKET_NAME}' exists and is accessible\n")
        else:
            print(f"⚠️  S3 bucket '{settings.S3_BUCKET_NAME}' does not exist")
            print("📦 Attempting to create bucket...")
            try:
                created = await s3_service.create_bucket()
                if created:
                    print(f"✅ S3 bucket '{settings.S3_BUCKET_NAME}' created successfully\n")
                else:
                    print(f"❌ Failed to create S3 bucket '{settings.S3_BUCKET_NAME}'\n")
                    return
            except Exception as e:
                print(f"❌ Failed to create S3 bucket: {e}")
                print("\nPlease check:")
                print("  - AWS credentials are configured (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)")
                print("  - AWS_REGION environment variable is set correctly")
                print("  - IAM permissions allow bucket creation")
                print("  - Bucket name is valid and available")
                return
    except Exception as e:
        print(f"❌ S3 bucket check failed: {e}")
        print("\nPlease check:")
        print("  - S3_BUCKET_NAME environment variable is set")
        print("  - AWS credentials are configured")
        print("  - AWS_REGION matches the bucket region")
        print("  - IAM permissions allow bucket access")
        return
    
    created_count = 0
    updated_count = 0
    error_count = 0
    errors = []
    
    for idx, file_path in enumerate(sorted(markdown_files), 1):
        try:
            # Read markdown content
            content = file_path.read_text(encoding='utf-8')
            
            # Parse metadata
            data = parse_markdown_file(file_path)
            page_id = data["page_id"]
            
            # Check if page exists
            existing = await repository.get_by_page_id(page_id)
            
            if existing:
                print(f"[{idx:3d}/{len(markdown_files)}] 🔄 Updating: {page_id}")
                # Update existing page
                update_data = {
                    "metadata": data["metadata"],
                    "content": content
                }
                await service.update_page(page_id, update_data)
                updated_count += 1
            else:
                print(f"[{idx:3d}/{len(markdown_files)}] ➕ Creating: {page_id}")
                # Create new page
                page_data = {
                    "page_id": page_id,
                    "metadata": data["metadata"],
                    "content": content
                }
                await service.create_page(page_data)
                created_count += 1
                
        except Exception as e:
            error_count += 1
            error_msg = f"{file_path.name}: {str(e)}"
            errors.append(error_msg)
            logger.error(f"Error processing {file_path.name}: {e}", exc_info=True)
            print(f"[{idx:3d}/{len(markdown_files)}] ❌ ERROR: {file_path.name}")
            print(f"      {str(e)}")
    
    # Summary
    print(f"\n{'='*60}")
    print("Seeding Summary")
    print(f"{'='*60}")
    print(f"  ✅ Created:  {created_count}")
    print(f"  🔄 Updated:  {updated_count}")
    print(f"  ❌ Errors:   {error_count}")
    print(f"  📄 Total:    {len(markdown_files)}")
    print(f"\n  📦 S3 Bucket:  {settings.S3_BUCKET_NAME}")
    print(f"  🌍 AWS Region: {settings.AWS_REGION}")
    print(f"  📂 S3 Prefix:  {settings.S3_DOCUMENTATION_PREFIX}")
    print(f"  📂 Data Prefix: {settings.S3_DATA_PREFIX}")
    
    if errors:
        print(f"\n{'='*60}")
        print("Errors Details:")
        print(f"{'='*60}")
        for error in errors:
            print(f"  ❌ {error}")
    
    print(f"{'='*60}\n")


async def main():
    """Main entry point."""
    try:
        await seed_documentation()
    except KeyboardInterrupt:
        print("\n\n⚠️  Seeding interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logger.error(f"Fatal error in seeding script: {e}", exc_info=True)
        raise
    finally:
        # No cleanup needed for S3
        pass


if __name__ == "__main__":
    asyncio.run(main())
