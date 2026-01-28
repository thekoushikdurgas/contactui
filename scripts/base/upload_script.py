"""Base upload script class for upload operations."""

import asyncio
from typing import Any, Dict, List, Optional

from scripts.base.base_script import BaseScript


class BaseUploadScript(BaseScript):
    """
    Base class for upload scripts.
    
    Extends BaseScript with:
    - Batch processing utilities
    - Retry logic framework
    - Error recovery patterns
    - Upload progress tracking
    """
    
    def __init__(self, script_name: str, description: str = ""):
        """Initialize upload script."""
        super().__init__(script_name, description)
        self.batch_size = 50
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        
    def _initialize_stats(self) -> None:
        """Initialize upload-specific statistics."""
        super()._initialize_stats()
        self.stats.update({
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "batches": 0,
            "batch_errors": 0,
        })
    
    def add_arguments(self, parser) -> None:
        """Add upload-specific arguments."""
        super().add_arguments(parser)
        parser.add_argument(
            "--batch-size",
            type=int,
            default=50,
            help="Number of items to process in each batch (default: 50)",
        )
        parser.add_argument(
            "--mode",
            type=str,
            default="upsert",
            choices=["upsert", "create_only", "update_only"],
            help="Import mode: upsert (create or update), create_only, or update_only (default: upsert)",
        )
        parser.add_argument(
            "--skip-existing",
            action="store_true",
            help="Skip files that already exist",
        )
    
    def process_batch(
        self,
        batch: List[Any],
        batch_num: int,
        total_batches: int,
    ) -> Dict[str, Any]:
        """
        Process a batch of items.
        
        Args:
            batch: List of items to process
            batch_num: Current batch number (1-indexed)
            total_batches: Total number of batches
            
        Returns:
            Dictionary with batch processing results
        """
        print(f"\n📦 Processing batch {batch_num}/{total_batches} ({len(batch)} items)...")
        
        batch_stats = {
            "created": 0,
            "updated": 0,
            "errors": 0,
            "skipped": 0,
        }
        
        for item in batch:
            try:
                result = self.process_item(item)
                if result:
                    if result.get("created"):
                        batch_stats["created"] += 1
                    elif result.get("updated"):
                        batch_stats["updated"] += 1
                    elif result.get("skipped"):
                        batch_stats["skipped"] += 1
            except Exception as e:
                batch_stats["errors"] += 1
                self.log_error(e, context="batch processing", item=str(item))
        
        # Update overall stats
        self.stats["created"] += batch_stats["created"]
        self.stats["updated"] += batch_stats["updated"]
        self.stats["skipped"] += batch_stats["skipped"]
        self.stats["errors"] += batch_stats["errors"]
        self.stats["batches"] += 1
        
        if batch_stats["errors"] > 0:
            self.stats["batch_errors"] += 1
        
        print(
            f"  ✓ Created: {batch_stats['created']}, "
            f"Updated: {batch_stats['updated']}, "
            f"Skipped: {batch_stats['skipped']}, "
            f"Errors: {batch_stats['errors']}"
        )
        
        return batch_stats
    
    def process_item(self, item: Any) -> Optional[Dict[str, Any]]:
        """
        Process a single item - must be implemented by subclasses.
        
        Args:
            item: Item to process
            
        Returns:
            Dictionary with processing result or None
        """
        raise NotImplementedError("Subclasses must implement process_item")
    
    def process_in_batches(
        self,
        items: List[Any],
        batch_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Process items in batches.
        
        Args:
            items: List of items to process
            batch_size: Batch size (defaults to self.batch_size)
            
        Returns:
            Dictionary with overall processing results
        """
        batch_size = batch_size or self.batch_size
        total_batches = (len(items) + batch_size - 1) // batch_size
        
        print(f"\n📊 Processing {len(items)} items in {total_batches} batch(es)")
        
        for batch_start in range(0, len(items), batch_size):
            batch = items[batch_start:batch_start + batch_size]
            batch_num = (batch_start // batch_size) + 1
            
            try:
                self.process_batch(batch, batch_num, total_batches)
            except Exception as e:
                self.log_error(e, context=f"batch {batch_num}")
                self.stats["batch_errors"] += 1
        
        return self.stats
    
    async def process_batch_async(
        self,
        batch: List[Any],
        batch_num: int,
        total_batches: int,
    ) -> Dict[str, Any]:
        """
        Process a batch of items asynchronously.
        
        Args:
            batch: List of items to process
            batch_num: Current batch number (1-indexed)
            total_batches: Total number of batches
            
        Returns:
            Dictionary with batch processing results
        """
        print(f"\n📦 Processing batch {batch_num}/{total_batches} ({len(batch)} items)...")
        
        batch_stats = {
            "created": 0,
            "updated": 0,
            "errors": 0,
            "skipped": 0,
        }
        
        for item in batch:
            try:
                result = await self.process_item_async(item)
                if result:
                    if result.get("created"):
                        batch_stats["created"] += 1
                    elif result.get("updated"):
                        batch_stats["updated"] += 1
                    elif result.get("skipped"):
                        batch_stats["skipped"] += 1
            except Exception as e:
                batch_stats["errors"] += 1
                self.log_error(e, context="batch processing", item=str(item))
        
        # Update overall stats
        self.stats["created"] += batch_stats["created"]
        self.stats["updated"] += batch_stats["updated"]
        self.stats["skipped"] += batch_stats["skipped"]
        self.stats["errors"] += batch_stats["errors"]
        self.stats["batches"] += 1
        
        if batch_stats["errors"] > 0:
            self.stats["batch_errors"] += 1
        
        print(
            f"  ✓ Created: {batch_stats['created']}, "
            f"Updated: {batch_stats['updated']}, "
            f"Skipped: {batch_stats['skipped']}, "
            f"Errors: {batch_stats['errors']}"
        )
        
        return batch_stats
    
    async def process_item_async(self, item: Any) -> Optional[Dict[str, Any]]:
        """
        Process a single item asynchronously - must be implemented by subclasses.
        
        Args:
            item: Item to process
            
        Returns:
            Dictionary with processing result or None
        """
        raise NotImplementedError("Subclasses must implement process_item_async")
    
    async def process_in_batches_async(
        self,
        items: List[Any],
        batch_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Process items in batches asynchronously.
        
        Args:
            items: List of items to process
            batch_size: Batch size (defaults to self.batch_size)
            
        Returns:
            Dictionary with overall processing results
        """
        batch_size = batch_size or self.batch_size
        total_batches = (len(items) + batch_size - 1) // batch_size
        
        print(f"\n📊 Processing {len(items)} items in {total_batches} batch(es)")
        
        for batch_start in range(0, len(items), batch_size):
            batch = items[batch_start:batch_start + batch_size]
            batch_num = (batch_start // batch_size) + 1
            
            try:
                await self.process_batch_async(batch, batch_num, total_batches)
            except Exception as e:
                self.log_error(e, context=f"batch {batch_num}")
                self.stats["batch_errors"] += 1
        
        return self.stats
