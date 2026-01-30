#!/usr/bin/env python3
"""
Upload all relationship JSON files from media/relationship/ to Lambda Documentation API.

This script reads by-page and by-endpoint relationship files,
validates them, and uploads them using the Lambda API import endpoint.

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
from scripts.utils.context import get_relationships_dir, get_logger
from scripts.utils.upload_helpers import (
    load_json_file,
    get_exclude_files,
    normalize_for_lambda,
)
from scripts.utils.config import get_config

logger = get_logger(__name__)
config = get_config()

# Files to exclude
EXCLUDE_FILES = get_exclude_files()


class RelationshipsUploadScript(BaseUploadScript):
    """Script to upload relationships to Lambda Documentation API."""
    
    def __init__(self):
        """Initialize relationships upload script."""
        super().__init__(
            script_name="upload_docs_relationships_to_s3",
            description="Upload documentation relationships from media/relationship/ to Lambda Documentation API",
        )
        self.api_client = None
        self.mode = "upsert"
        self.relationships_dir = None
    
    def setup(self) -> None:
        """Setup script - initialize API client."""
        super().setup()
        
        # External Documentation API client removed; use Django docs UI or S3 directly.
        self.api_client = None
        logger.info("Upload via external API disabled; use Django docs UI or upload to S3 directly.")
        
        # Get relationships directory
        self.relationships_dir = get_relationships_dir()
        
        if not self.relationships_dir.exists():
            logger.error(f"Relationships directory not found: {self.relationships_dir}")
            raise FileNotFoundError(f"Relationships directory not found: {self.relationships_dir}")
    
    def add_arguments(self, parser) -> None:
        """Add script-specific arguments."""
        super().add_arguments(parser)
        # Mode and batch-size are already added by BaseUploadScript
    
    def process_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a single relationship item (not used in batch mode).
        
        Args:
            item: Relationship data dictionary
            
        Returns:
            Processing result dictionary
        """
        # This is handled by process_batch for relationships
        return None
    
    def _extract_relationships_from_file(self, relationship_data: Any, file_path: Path) -> List[Dict[str, Any]]:
        """
        Extract individual relationships from various file formats.
        
        Args:
            relationship_data: Parsed JSON data (dict, list, or by-page/by-endpoint format)
            file_path: Path to the file (for context)
            
        Returns:
            List of individual relationship dictionaries
        """
        relationships = []
        
        if isinstance(relationship_data, dict):
            if "page_path" in relationship_data and "endpoints" in relationship_data:
                # By-page format: {"page_path": "...", "endpoints": [...]}
                page_path = relationship_data["page_path"]
                for endpoint_data in relationship_data.get("endpoints", []):
                    rel_data = {
                        "page_path": page_path,
                        "endpoint_path": endpoint_data.get("endpoint_path"),
                        "method": endpoint_data.get("method"),
                        "api_version": endpoint_data.get("api_version", "v1"),
                        "usage_type": endpoint_data.get("usage_type", "primary"),
                        "usage_context": endpoint_data.get("usage_context", "data_fetching"),
                        **{k: v for k, v in endpoint_data.items() if k not in ["endpoint_path", "method"]},
                    }
                    normalized = normalize_for_lambda(rel_data, "relationships")
                    if normalized:
                        relationships.append(normalized)
            elif "endpoint_path" in relationship_data and "pages" in relationship_data:
                # By-endpoint format: {"endpoint_path": "...", "pages": [...]}
                endpoint_path = relationship_data["endpoint_path"]
                method = relationship_data.get("method", "GET")
                for page_data in relationship_data.get("pages", []):
                    rel_data = {
                        "page_path": page_data.get("page_path"),
                        "endpoint_path": endpoint_path,
                        "method": method,
                        "api_version": relationship_data.get("api_version", "v1"),
                        "usage_type": page_data.get("usage_type", "primary"),
                        "usage_context": page_data.get("usage_context", "data_fetching"),
                        **{k: v for k, v in page_data.items() if k not in ["page_path"]},
                    }
                    normalized = normalize_for_lambda(rel_data, "relationships")
                    if normalized:
                        relationships.append(normalized)
            else:
                # Single relationship object
                normalized = normalize_for_lambda(relationship_data, "relationships")
                if normalized:
                    relationships.append(normalized)
        elif isinstance(relationship_data, list):
            # List of relationships
            for rel_data in relationship_data:
                normalized = normalize_for_lambda(rel_data, "relationships")
                if normalized:
                    relationships.append(normalized)
        
        return relationships
    
    def process_batch(
        self,
        batch: List[Dict[str, Any]],
        batch_num: int,
        total_batches: int,
    ) -> Dict[str, Any]:
        """
        Process a batch of relationships.
        
        Args:
            batch: List of relationship data dictionaries
            batch_num: Current batch number
            total_batches: Total number of batches
            
        Returns:
            Batch processing results
        """
        if self.dry_run:
            print(f"\n[DRY RUN] Would upload batch {batch_num}/{total_batches} ({len(batch)} relationships)")
            return {"created": 0, "updated": 0, "errors": 0, "skipped": 0}
        
        if not self.api_client:
            error_msg = "Upload via external API is disabled; use Django docs UI or S3."
            self.log_error(Exception(error_msg), context="batch processing")
            return {"created": 0, "updated": 0, "errors": len(batch), "skipped": 0}
        
        # Try to call import_relationships_v1 if it exists, otherwise use individual calls
        try:
            if hasattr(self.api_client, "import_relationships_v1"):
                response = self.api_client.import_relationships_v1(batch, mode=self.mode)
            else:
                # Fallback: use individual create calls
                response = self._import_relationships_individual(batch)
            
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
                for rel in batch:
                    rel_id = f"{rel.get('page_path', 'unknown')}_{rel.get('endpoint_path', 'unknown')}"
                    self.log_error(Exception(error_msg), context="batch upload", item=rel_id)
                return {"created": 0, "updated": 0, "errors": len(batch), "skipped": 0}
        except Exception as e:
            self.log_error(e, context=f"batch {batch_num}")
            return {"created": 0, "updated": 0, "errors": len(batch), "skipped": 0}
    
    def _import_relationships_individual(self, batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Import relationships using individual create calls (fallback).
        
        Args:
            batch: List of relationship data dictionaries
            
        Returns:
            Import results dictionary
        """
        created = 0
        updated = 0
        errors = 0
        error_details = []
        
        for rel_data in batch:
            try:
                # Try to create relationship
                # Note: Lambda API may not have create_relationship_v1, this is a fallback
                if hasattr(self.api_client, "create_relationship_v1"):
                    result = self.api_client.create_relationship_v1(rel_data)
                    if result:
                        created += 1
                    else:
                        errors += 1
                        rel_id = f"{rel_data.get('page_path', 'unknown')}_{rel_data.get('endpoint_path', 'unknown')}"
                        error_details.append({"relationship_id": rel_id, "error": "Create failed"})
                else:
                    # No create method available
                    errors += 1
                    rel_id = f"{rel_data.get('page_path', 'unknown')}_{rel_data.get('endpoint_path', 'unknown')}"
                    error_details.append({"relationship_id": rel_id, "error": "Create method not available"})
            except Exception as e:
                errors += 1
                rel_id = f"{rel_data.get('page_path', 'unknown')}_{rel_data.get('endpoint_path', 'unknown')}"
                error_details.append({"relationship_id": rel_id, "error": str(e)})
                self.log_error(e, context="individual import", item=rel_id)
        
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
        
        # Get all JSON files (including subdirectories)
        json_files = []
        for pattern in ["*.json", "by-page/*.json", "by-endpoint/*.json"]:
            json_files.extend([
                f for f in self.relationships_dir.glob(pattern)
                if f.name not in EXCLUDE_FILES
            ])
        
        if not json_files:
            self.logger.warning(f"No JSON files found in {self.relationships_dir}")
            return {"total": 0, "processed": 0, "errors": 0}
        
        self.logger.info(f"Found {len(json_files)} relationship files to process")
        self.stats["total"] = len(json_files)
        
        # Load and normalize all files
        relationships_data = []
        for idx, file_path in enumerate(sorted(json_files), 1):
            self.print_progress(idx, len(json_files), "relationships")
            
            try:
                # Load JSON file
                relationship_data, parse_error = load_json_file(file_path)
                
                if parse_error:
                    self.stats["errors"] += 1
                    self.log_error(
                        Exception(parse_error),
                        context="file loading",
                        item=file_path.name,
                    )
                    continue
                
                if relationship_data is None:
                    self.stats["errors"] += 1
                    self.log_error(
                        Exception("Failed to load JSON"),
                        context="file loading",
                        item=file_path.name,
                    )
                    continue
                
                # Extract relationships from various formats
                extracted = self._extract_relationships_from_file(relationship_data, file_path)
                
                if extracted:
                    relationships_data.extend(extracted)
                    if self.dry_run:
                        print(f"  [DRY RUN] Would import {len(extracted)} relationship(s) from: {file_path.name}")
                    else:
                        print(f"  ✓ Loaded {len(extracted)} relationship(s) from: {file_path.name}")
                else:
                    self.stats["errors"] += 1
                    self.log_error(
                        Exception("No relationships extracted from file"),
                        context="relationship extraction",
                        item=file_path.name,
                    )
            except Exception as e:
                self.stats["errors"] += 1
                self.log_error(e, context="file processing", item=file_path.name)
        
        if not relationships_data:
            self.logger.warning("No valid relationships to upload")
            return self.stats
        
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would import {len(relationships_data)} relationships using mode={self.mode}")
            self.stats["processed"] = len(relationships_data)
            return self.stats
        
        # Process in batches
        self.stats["processed"] = len(relationships_data)
        self.process_in_batches(relationships_data, batch_size=self.batch_size)
        
        return self.stats


def upload_relationships(
    dry_run: bool = False,
    mode: str = "upsert",
    batch_size: int = 50,
) -> Dict[str, Any]:
    """
    Upload all relationship files to Lambda Documentation API.
    
    This function is kept for backward compatibility.
    
    Args:
        dry_run: If True, don't actually upload, just show what would be uploaded
        mode: Import mode - "upsert" (default), "create_only", or "update_only"
        batch_size: Number of files to process in each batch
        
    Returns:
        Dictionary with upload statistics
    """
    script = RelationshipsUploadScript()
    args = type("Args", (), {
        "dry_run": dry_run,
        "mode": mode,
        "batch_size": batch_size,
        "verbose": False,
    })()
    return script.run(args)


def main():
    """Main entry point."""
    script = RelationshipsUploadScript()
    script.main()


if __name__ == "__main__":
    main()
