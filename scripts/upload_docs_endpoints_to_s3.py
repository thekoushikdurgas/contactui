#!/usr/bin/env python3
"""
Upload all endpoint JSON files from media/endpoints/ to Lambda Documentation API.

This script reads all JSON files from media/endpoints/, validates them,
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
from scripts.utils.context import get_endpoints_dir, get_logger
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


class EndpointsUploadScript(BaseUploadScript):
    """Script to upload endpoints to Lambda Documentation API."""
    
    def __init__(self):
        """Initialize endpoints upload script."""
        super().__init__(
            script_name="upload_docs_endpoints_to_s3",
            description="Upload documentation endpoints from media/endpoints/ to Lambda Documentation API",
        )
        self.api_client = None
        self.mode = "upsert"
        self.endpoints_dir = None
    
    def setup(self) -> None:
        """Setup script - initialize API client."""
        super().setup()
        
        # External Documentation API client removed; use Django docs UI or S3 directly.
        self.api_client = None
        logger.info("Upload via external API disabled; use Django docs UI or upload to S3 directly.")
        
        # Get endpoints directory
        self.endpoints_dir = get_endpoints_dir()
        
        if not self.endpoints_dir.exists():
            logger.error(f"Endpoints directory not found: {self.endpoints_dir}")
            raise FileNotFoundError(f"Endpoints directory not found: {self.endpoints_dir}")
    
    def add_arguments(self, parser) -> None:
        """Add script-specific arguments."""
        super().add_arguments(parser)
        # Mode and batch-size are already added by BaseUploadScript
    
    def process_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]]:
        """
        Process a single endpoint item (not used in batch mode).
        
        Args:
            item: Endpoint data dictionary
            
        Returns:
            Processing result dictionary
        """
        # This is handled by process_batch for endpoints
        return None
    
    def process_batch(
        self,
        batch: List[Dict[str, Any]],
        batch_num: int,
        total_batches: int,
    ) -> Dict[str, Any]:
        """
        Process a batch of endpoints.
        
        Args:
            batch: List of endpoint data dictionaries
            batch_num: Current batch number
            total_batches: Total number of batches
            
        Returns:
            Batch processing results
        """
        if self.dry_run:
            print(f"\n[DRY RUN] Would upload batch {batch_num}/{total_batches} ({len(batch)} endpoints)")
            return {"created": 0, "updated": 0, "errors": 0, "skipped": 0}
        
        if not self.api_client:
            error_msg = "Upload via external API is disabled; use Django docs UI or S3."
            self.log_error(Exception(error_msg), context="batch processing")
            return {"created": 0, "updated": 0, "errors": len(batch), "skipped": 0}
        
        # Try to call import_endpoints_v1 if it exists, otherwise use individual calls
        try:
            if hasattr(self.api_client, "import_endpoints_v1"):
                response = self.api_client.import_endpoints_v1(batch, mode=self.mode)
            else:
                # Fallback: use individual create/update calls
                response = self._import_endpoints_individual(batch)
            
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
                for endpoint in batch:
                    self.log_error(
                        Exception(error_msg),
                        context="batch upload",
                        item=endpoint.get("endpoint_id", "unknown"),
                    )
                return {"created": 0, "updated": 0, "errors": len(batch), "skipped": 0}
        except Exception as e:
            self.log_error(e, context=f"batch {batch_num}")
            return {"created": 0, "updated": 0, "errors": len(batch), "skipped": 0}
    
    def _import_endpoints_individual(self, batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Import endpoints using individual create/update calls (fallback).
        
        Args:
            batch: List of endpoint data dictionaries
            
        Returns:
            Import results dictionary
        """
        created = 0
        updated = 0
        errors = 0
        error_details = []
        
        for endpoint_data in batch:
            endpoint_id = endpoint_data.get("endpoint_id")
            if not endpoint_id:
                errors += 1
                error_details.append({"endpoint_id": "unknown", "error": "Missing endpoint_id"})
                continue
            
            try:
                # Try to get existing endpoint
                existing = self.api_client.get_endpoint_v1(endpoint_id)
                
                if existing:
                    # Update existing - Note: update_endpoint_v1 may not exist, using create as fallback
                    if hasattr(self.api_client, "update_endpoint_v1"):
                        result = self.api_client.update_endpoint_v1(endpoint_id, endpoint_data)
                    else:
                        # Fallback: try create (may fail if exists)
                        result = self.api_client.create_endpoint_v1(endpoint_data) if hasattr(self.api_client, "create_endpoint_v1") else None
                    
                    if result:
                        updated += 1
                    else:
                        errors += 1
                        error_details.append({"endpoint_id": endpoint_id, "error": "Update failed"})
                else:
                    # Create new
                    if hasattr(self.api_client, "create_endpoint_v1"):
                        result = self.api_client.create_endpoint_v1(endpoint_data)
                    else:
                        result = None
                    
                    if result:
                        created += 1
                    else:
                        errors += 1
                        error_details.append({"endpoint_id": endpoint_id, "error": "Create failed"})
            except Exception as e:
                errors += 1
                error_details.append({"endpoint_id": endpoint_id, "error": str(e)})
                self.log_error(e, context="individual import", item=endpoint_id)
        
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
            f for f in self.endpoints_dir.glob("*.json")
            if f.name not in EXCLUDE_FILES
        ]
        
        if not json_files:
            self.logger.warning(f"No JSON files found in {self.endpoints_dir}")
            return {"total": 0, "processed": 0, "errors": 0}
        
        self.logger.info(f"Found {len(json_files)} endpoint files to process")
        self.stats["total"] = len(json_files)
        
        # Load and normalize all files
        endpoints_data = []
        for idx, file_path in enumerate(sorted(json_files), 1):
            self.print_progress(idx, len(json_files), "endpoints")
            
            try:
                # Load and validate file
                normalized, error_msg, validation_errors = load_and_validate_file(
                    file_path,
                    resource_type="endpoints",
                    required_fields=["endpoint_id"],
                )
                
                if normalized:
                    endpoints_data.append(normalized)
                    if self.dry_run:
                        endpoint_id = normalized.get("endpoint_id", "unknown")
                        print(f"  [DRY RUN] Would import: {endpoint_id}")
                    else:
                        endpoint_id = normalized.get("endpoint_id", "unknown")
                        print(f"  ✓ Loaded: {endpoint_id}")
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
        
        if not endpoints_data:
            self.logger.warning("No valid endpoints to upload")
            return self.stats
        
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would import {len(endpoints_data)} endpoints using mode={self.mode}")
            self.stats["processed"] = len(endpoints_data)
            return self.stats
        
        # Process in batches
        self.stats["processed"] = len(endpoints_data)
        self.process_in_batches(endpoints_data, batch_size=self.batch_size)
        
        return self.stats


def upload_endpoints(
    dry_run: bool = False,
    mode: str = "upsert",
    batch_size: int = 50,
) -> Dict[str, Any]:
    """
    Upload all endpoint files to Lambda Documentation API.
    
    This function is kept for backward compatibility.
    
    Args:
        dry_run: If True, don't actually upload, just show what would be uploaded
        mode: Import mode - "upsert" (default), "create_only", or "update_only"
        batch_size: Number of files to process in each batch
        
    Returns:
        Dictionary with upload statistics
    """
    script = EndpointsUploadScript()
    args = type("Args", (), {
        "dry_run": dry_run,
        "mode": mode,
        "batch_size": batch_size,
        "verbose": False,
    })()
    return script.run(args)


def main():
    """Main entry point."""
    script = EndpointsUploadScript()
    script.main()


if __name__ == "__main__":
    main()
