#!/usr/bin/env python3
"""
Upload all page JSON files from media/pages/ to Lambda Documentation API.

This script reads all JSON files from media/pages/, validates them,
and uploads them using the Lambda API import endpoint (which handles S3 storage).

Refactored to use BaseUploadScript and shared utilities.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

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

from scripts.base.upload_script import BaseUploadScript
from scripts.utils.context import get_pages_dir, get_logger
from scripts.utils.upload_helpers import (
    load_and_validate_file,
    get_exclude_files,
    normalize_for_lambda,
)
from scripts.utils.config import get_config

logger = get_logger(__name__)
config = get_config()

# Files to exclude
EXCLUDE_FILES = get_exclude_files()


class PagesUploadScript(BaseUploadScript):
    """Script to upload pages to Lambda Documentation API."""
    
    def __init__(self):
        """Initialize pages upload script."""
        super().__init__(
            script_name="upload_docs_pages_to_s3",
            description="Upload documentation pages from media/pages/ to Lambda Documentation API",
        )
        self.api_client = None
        self.mode = "upsert"
        self.pages_dir = None
    
    def setup(self) -> None:
        """Setup script - initialize API client."""
        super().setup()
        
        # External Documentation API client removed; use Django docs UI or S3 directly.
        self.api_client = None
        logger.info("Upload via external API disabled; use Django docs UI or upload to S3 directly.")
        
        # Get pages directory
        self.pages_dir = get_pages_dir()
        
        if not self.pages_dir.exists():
            logger.error(f"Pages directory not found: {self.pages_dir}")
            raise FileNotFoundError(f"Pages directory not found: {self.pages_dir}")
    
    def add_arguments(self, parser) -> None:
        """Add script-specific arguments."""
        super().add_arguments(parser)
        # Mode and batch-size are already added by BaseUploadScript
    
    def process_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a single page item (not used in batch mode).
        
        Args:
            item: Page data dictionary
            
        Returns:
            Processing result dictionary
        """
        # This is handled by process_batch for pages
        return None
    
    def process_batch(
        self,
        batch: List[Dict[str, Any]],
        batch_num: int,
        total_batches: int,
    ) -> Dict[str, Any]:
        """
        Process a batch of pages.
        
        Args:
            batch: List of page data dictionaries
            batch_num: Current batch number
            total_batches: Total number of batches
            
        Returns:
            Batch processing results
        """
        if self.dry_run:
            print(f"\n[DRY RUN] Would upload batch {batch_num}/{total_batches} ({len(batch)} pages)")
            return {"created": 0, "updated": 0, "errors": 0, "skipped": 0}
        
        if not self.api_client:
            error_msg = "Upload via external API is disabled; use Django docs UI or S3."
            self.log_error(Exception(error_msg), context="batch processing")
            return {"created": 0, "updated": 0, "errors": len(batch), "skipped": 0}
        
        # Try to call import_pages_v1 if it exists, otherwise use individual calls
        try:
            if hasattr(self.api_client, "import_pages_v1"):
                response = self.api_client.import_pages_v1(batch, mode=self.mode)
            else:
                # Fallback: use individual create/update calls
                response = self._import_pages_individual(batch)
            
            if response:
                batch_created = response.get("created", 0)
                batch_updated = response.get("updated", 0)
                batch_errors = response.get("errors", 0)
                
                if response.get("error_details"):
                    for error_detail in response["error_details"]:
                        self.errors.append(error_detail)
                
                return {
                    "created": batch_created,
                    "updated": batch_updated,
                    "errors": batch_errors,
                    "skipped": 0,
                }
            else:
                # API returned None
                error_msg = "Import returned None"
                for page in batch:
                    self.log_error(Exception(error_msg), context="batch upload", item=page.get("page_id", "unknown"))
                return {"created": 0, "updated": 0, "errors": len(batch), "skipped": 0}
        except Exception as e:
            self.log_error(e, context=f"batch {batch_num}")
            return {"created": 0, "updated": 0, "errors": len(batch), "skipped": 0}
    
    def _import_pages_individual(self, batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Import pages using individual create/update calls (fallback).
        
        Args:
            batch: List of page data dictionaries
            
        Returns:
            Import results dictionary
        """
        created = 0
        updated = 0
        errors = 0
        error_details = []
        
        for page_data in batch:
            page_id = page_data.get("page_id")
            if not page_id:
                errors += 1
                error_details.append({"page_id": "unknown", "error": "Missing page_id"})
                continue
            
            try:
                # Try to get existing page
                existing = self.api_client.get_page_v1(page_id)
                
                if existing:
                    # Update existing
                    result = self.api_client.update_page_v1(page_id, page_data)
                    if result:
                        updated += 1
                    else:
                        errors += 1
                        error_details.append({"page_id": page_id, "error": "Update failed"})
                else:
                    # Create new
                    result = self.api_client.create_page_v1(page_data)
                    if result:
                        created += 1
                    else:
                        errors += 1
                        error_details.append({"page_id": page_id, "error": "Create failed"})
            except Exception as e:
                errors += 1
                error_details.append({"page_id": page_id, "error": str(e)})
                self.log_error(e, context="individual import", item=page_id)
        
        return {
            "created": created,
            "updated": updated,
            "errors": errors,
            "error_details": error_details,
        }
    
    def run(self, args) -> Dict[str, Any]:
        """
        Run the upload script.
        
        Args:
            args: Parsed command-line arguments
            
        Returns:
            Dictionary with execution statistics
        """
        self.mode = args.mode
        self.batch_size = args.batch_size
        
        # Get all JSON files
        json_files = [
            f for f in self.pages_dir.glob("*.json")
            if f.name not in EXCLUDE_FILES
        ]
        
        if not json_files:
            self.logger.warning(f"No JSON files found in {self.pages_dir}")
            return {"total": 0, "processed": 0, "errors": 0}
        
        self.logger.info(f"Found {len(json_files)} page files to process")
        self.stats["total"] = len(json_files)
        
        # Load and normalize all files
        pages_data = []
        for idx, file_path in enumerate(sorted(json_files), 1):
            self.print_progress(idx, len(json_files), "pages")
            
            try:
                # Load and validate file
                normalized, error_msg, validation_errors = load_and_validate_file(
                    file_path,
                    resource_type="pages",
                    required_fields=["page_id"],
                )
                
                if normalized:
                    pages_data.append(normalized)
                    if self.dry_run:
                        page_id = normalized.get("page_id", "unknown")
                        print(f"  [DRY RUN] Would import: {page_id}")
                    else:
                        page_id = normalized.get("page_id", "unknown")
                        print(f"  ✓ Loaded: {page_id}")
                else:
                    self.stats["errors"] += 1
                    self.log_error(
                        Exception(error_msg or "Validation failed"),
                        context="file loading",
                        item=file_path.name,
                    )
                    if validation_errors:
                        for ve in validation_errors:
                            self.log_error(
                                Exception(ve.message),
                                context=f"validation: {ve.field}",
                                item=file_path.name,
                            )
            except Exception as e:
                self.stats["errors"] += 1
                self.log_error(e, context="file processing", item=file_path.name)
        
        if not pages_data:
            self.logger.warning("No valid pages to upload")
            return self.stats
        
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would import {len(pages_data)} pages using mode={self.mode}")
            self.stats["processed"] = len(pages_data)
            return self.stats
        
        # Process in batches
        self.stats["processed"] = len(pages_data)
        self.process_in_batches(pages_data, batch_size=self.batch_size)
        
        return self.stats


def upload_pages(
    dry_run: bool = False,
    mode: str = "upsert",
    batch_size: int = 50,
) -> Dict[str, Any]:
    """
    Upload all page files to Lambda Documentation API.
    
    This function is kept for backward compatibility.
    
    Args:
        dry_run: If True, don't actually upload, just show what would be uploaded
        mode: Import mode - "upsert" (default), "create_only", or "update_only"
        batch_size: Number of files to process in each batch
        
    Returns:
        Dictionary with upload statistics
    """
    script = PagesUploadScript()
    args = type("Args", (), {
        "dry_run": dry_run,
        "mode": mode,
        "batch_size": batch_size,
        "verbose": False,
    })()
    return script.run(args)


def main():
    """Main entry point."""
    script = PagesUploadScript()
    script.main()


if __name__ == "__main__":
    main()
