import re
from pathlib import Path
from typing import Any, Dict

from django.core.management.base import BaseCommand
from django.conf import settings

from apps.documentation.services.pages_service import PagesService

class Command(BaseCommand):
    help = 'Import documentation pages from markdown files'

    def handle(self, *args, **options):
        # Calculate paths
        # BASE_DIR is usually contact360/docsai/
        base_dir = Path(settings.BASE_DIR)
        
        # Go up to repo root: contact360/docsai -> contact360 -> repo_root
        repo_root = base_dir.parent.parent
        
        # Target: docs/docs_ai_agent/docs/pages
        pages_dir = repo_root / 'docs' / 'docs_ai_agent' / 'docs' / 'pages'
        
        if not pages_dir.exists():
            self.stdout.write(self.style.ERROR(f'Pages directory not found: {pages_dir}'))
            return

        service = PagesService()
        
        files = sorted(pages_dir.glob('*.md'))
        self.stdout.write(f"Found {len(files)} markdown files in {pages_dir}")
        
        success_count = 0
        
        for file_path in files:
            filename = file_path.name
            # Parse filename: 01-core-login.md
            match = re.match(r'(\d+)-([a-z0-9]+)-(.*)\.md', filename)
            
            if not match:
                # Handle special files or skip
                if filename == 'README.md':
                    continue
                self.stdout.write(self.style.WARNING(f'Skipping invalid filename pattern: {filename}'))
                continue
                
            order = int(match.group(1))
            app_label = match.group(2)
            slug = match.group(3)
            
            # Construct a unique page_id
            page_id = f"{app_label}_{slug}".replace('-', '_')
            
            try:
                content = file_path.read_text(encoding='utf-8')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error reading {filename}: {e}'))
                continue
            
            # Extract title
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else slug.replace('-', ' ').title()
            
            # Prepare page data
            page_data = {
                "page_id": page_id,
                "title": title,
                "content": content,
                "page_type": "documentation",
                "app_label": app_label,
                "status": "published",
                "order": order,
                "metadata": {
                    "source_file": filename,
                    "slug": slug,
                    "route": f"/docs/{app_label}/{slug}",
                    "last_imported": str(file_path.stat().st_mtime)
                }
            }
            
            try:
                # Check if exists (update) or create
                existing = service.get_page(page_id)
                if existing:
                    service.update_page(page_id, page_data)
                    self.stdout.write(self.style.SUCCESS(f'Updated: {page_id}'))
                else:
                    service.create_page(page_data)
                    self.stdout.write(self.style.SUCCESS(f'Created: {page_id}'))
                success_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error saving {page_id}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully imported {success_count} pages.'))
