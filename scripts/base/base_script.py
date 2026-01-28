"""Base script class for common script patterns."""

import argparse
import sys
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from scripts.utils.context import get_logger, get_settings


class BaseScript(ABC):
    """
    Base class for all scripts with common patterns.
    
    Provides:
    - Common initialization (logging, config, error handling)
    - Dry-run support pattern
    - Progress reporting utilities
    - Statistics tracking
    - Standardized argument parsing
    """
    
    def __init__(self, script_name: str, description: str = ""):
        """
        Initialize base script.
        
        Args:
            script_name: Name of the script for logging and display
            description: Description of what the script does
        """
        self.script_name = script_name
        self.description = description
        self.logger = get_logger(f"scripts.{script_name}")
        self.settings = get_settings()
        self.dry_run = False
        self.stats: Dict[str, Any] = {}
        self.start_time: Optional[float] = None
        self.errors: List[Dict[str, Any]] = []
        
    def setup(self) -> None:
        """Setup script - override in subclasses for custom setup."""
        self.logger.info(f"Starting {self.script_name}")
        self.start_time = time.time()
        self._initialize_stats()
    
    def _initialize_stats(self) -> None:
        """Initialize statistics dictionary."""
        self.stats = {
            "total": 0,
            "processed": 0,
            "success": 0,
            "errors": 0,
            "skipped": 0,
            "start_time": datetime.now().isoformat(),
        }
    
    def parse_arguments(self, args: Optional[List[str]] = None) -> argparse.Namespace:
        """
        Parse command-line arguments with common options.
        
        Args:
            args: Optional list of arguments (defaults to sys.argv[1:])
            
        Returns:
            Parsed arguments namespace
        """
        parser = argparse.ArgumentParser(
            description=self.description or f"{self.script_name} script",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        
        # Common arguments
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without actually doing it",
        )
        
        parser.add_argument(
            "--verbose",
            "-v",
            action="store_true",
            help="Enable verbose output",
        )
        
        # Add script-specific arguments
        self.add_arguments(parser)
        
        parsed_args = parser.parse_args(args)
        self.dry_run = parsed_args.dry_run
        
        if parsed_args.verbose:
            self.logger.setLevel("DEBUG")
        
        return parsed_args
    
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """
        Add script-specific arguments.
        
        Override in subclasses to add custom arguments.
        
        Args:
            parser: Argument parser instance
        """
        pass
    
    def print_header(self, title: Optional[str] = None) -> None:
        """
        Print script header.
        
        Args:
            title: Optional title (defaults to script_name)
        """
        title = title or self.script_name
        print("=" * 60)
        print(title)
        print("=" * 60)
        if self.description:
            print(f"\n{self.description}\n")
        if self.dry_run:
            print("🔍 DRY RUN MODE - No changes will be made\n")
        print(f"Started at: {datetime.now().isoformat()}\n")
    
    def print_progress(self, current: int, total: int, item_name: str = "item") -> None:
        """
        Print progress information.
        
        Args:
            current: Current item number
            total: Total number of items
            item_name: Name of the item type
        """
        percentage = (current / total * 100) if total > 0 else 0
        print(f"[{current:3d}/{total:3d}] ({percentage:5.1f}%) Processing {item_name}...", end="\r")
        if current == total:
            print()  # New line when complete
    
    def log_error(self, error: Exception, context: str = "", item: Optional[str] = None) -> None:
        """
        Log an error and add to errors list.
        
        Args:
            error: Exception instance
            context: Additional context string
            item: Optional item identifier (e.g., filename)
        """
        error_msg = str(error)
        if context:
            error_msg = f"{context}: {error_msg}"
        
        error_dict = {
            "error": error_msg,
            "error_type": type(error).__name__,
            "context": context,
        }
        
        if item:
            error_dict["item"] = item
        
        self.errors.append(error_dict)
        self.stats["errors"] = self.stats.get("errors", 0) + 1
        
        self.logger.error(error_msg, exc_info=True)
    
    def print_summary(self) -> None:
        """Print execution summary."""
        if self.start_time:
            duration = time.time() - self.start_time
            self.stats["duration_seconds"] = duration
            self.stats["end_time"] = datetime.now().isoformat()
        
        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)
        
        for key, value in self.stats.items():
            if key not in ("start_time", "end_time", "duration_seconds"):
                print(f"  {key.capitalize()}: {value}")
        
        if self.start_time:
            print(f"  Duration: {duration:.2f}s")
        
        if self.errors:
            print(f"\n  Errors: {len(self.errors)}")
            for error in self.errors[:10]:  # Show first 10 errors
                item = error.get("item", "unknown")
                error_msg = error.get("error", "Unknown error")
                print(f"    - {item}: {error_msg}")
            if len(self.errors) > 10:
                print(f"    ... and {len(self.errors) - 10} more error(s)")
        
        print("=" * 60 + "\n")
    
    @abstractmethod
    def run(self, args: argparse.Namespace) -> Dict[str, Any]:
        """
        Run the script - must be implemented by subclasses.
        
        Args:
            args: Parsed command-line arguments
            
        Returns:
            Dictionary with execution results/statistics
        """
        pass
    
    def execute(self, args: Optional[List[str]] = None) -> int:
        """
        Execute the script with argument parsing and error handling.
        
        Args:
            args: Optional list of arguments (defaults to sys.argv[1:])
            
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            self.setup()
            parsed_args = self.parse_arguments(args)
            self.print_header()
            
            result = self.run(parsed_args)
            
            # Update stats from result if provided
            if isinstance(result, dict):
                self.stats.update(result)
            
            self.print_summary()
            
            # Return error code if there were errors
            if self.stats.get("errors", 0) > 0:
                return 1
            
            return 0
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Script interrupted by user")
            self.logger.warning("Script interrupted by user")
            return 1
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
            self.logger.error(f"Fatal error in {self.script_name}: {e}", exc_info=True)
            return 1
        finally:
            self.cleanup()
    
    def cleanup(self) -> None:
        """Cleanup resources - override in subclasses if needed."""
        pass
    
    def main(self) -> None:
        """Main entry point - calls execute and exits."""
        exit_code = self.execute()
        sys.exit(exit_code)
