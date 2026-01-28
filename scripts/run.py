#!/usr/bin/env python3
"""
Unified script runner for documentation scripts.

Provides script discovery, help system, and execution monitoring.

Usage:
    python scripts/run.py <script_name> [args...]
    python scripts/run.py --list
    python scripts/run.py --help <script_name>
"""

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR.parent))


class ScriptRunner:
    """Unified script runner with discovery and help system."""
    
    def __init__(self):
        """Initialize script runner."""
        self.scripts_dir = SCRIPTS_DIR
        self.scripts = self._discover_scripts()
    
    def _discover_scripts(self) -> Dict[str, Path]:
        """
        Discover available scripts in scripts directory.
        
        Returns:
            Dictionary mapping script names to file paths
        """
        scripts = {}
        
        for file_path in self.scripts_dir.glob("*.py"):
            if file_path.name.startswith("_"):
                continue
            if file_path.name == "run.py":
                continue
            
            script_name = file_path.stem
            scripts[script_name] = file_path
        
        return scripts
    
    def list_scripts(self) -> None:
        """List all available scripts."""
        print("Available Scripts:")
        print("=" * 60)
        
        # Categorize scripts
        categories = {
            "Upload": ["upload_all_docs_to_s3", "upload_docs_pages_to_s3", "upload_docs_endpoints_to_s3", 
                      "upload_docs_relationships_to_s3", "upload_index_files_to_s3", "upload_json_to_s3"],
            "Analysis": ["analyze_docs_files", "validate_media_structure"],
            "Migration": ["migrate_media_to_documentation_api", "fix_invalid_routes", "fix_relationship_dates"],
            "Generation": ["generate_s3_json_files", "generate_postman_collection", "build_complete_collection", 
                          "add_response_examples"],
            "Management": ["seed_documentation_pages", "rebuild_indexes"],
            "Other": [],
        }
        
        categorized = {cat: [] for cat in categories}
        uncategorized = []
        
        for script_name in sorted(self.scripts.keys()):
            found = False
            for category, names in categories.items():
                if script_name in names:
                    categorized[category].append(script_name)
                    found = True
                    break
            if not found:
                uncategorized.append(script_name)
        
        for category, scripts_list in categorized.items():
            if scripts_list:
                print(f"\n{category}:")
                for script_name in sorted(scripts_list):
                    print(f"  - {script_name}")
        
        if uncategorized:
            print(f"\nOther:")
            for script_name in sorted(uncategorized):
                print(f"  - {script_name}")
        
        print(f"\nTotal: {len(self.scripts)} scripts")
    
    def get_script_help(self, script_name: str) -> Optional[str]:
        """
        Get help text for a script.
        
        Args:
            script_name: Name of the script
            
        Returns:
            Help text or None if script not found
        """
        if script_name not in self.scripts:
            return None
        
        script_path = self.scripts[script_name]
        
        # Try to get docstring from script
        try:
            spec = importlib.util.spec_from_file_location(script_name, script_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, "__doc__") and module.__doc__:
                    return module.__doc__.strip()
        except Exception:
            pass
        
        # Fallback: read first few lines
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                doc_lines = []
                in_docstring = False
                for line in lines[:50]:  # Read first 50 lines
                    if '"""' in line or "'''" in line:
                        in_docstring = not in_docstring
                        doc_lines.append(line)
                        if not in_docstring and doc_lines:
                            break
                    elif in_docstring:
                        doc_lines.append(line)
                
                if doc_lines:
                    return "".join(doc_lines).strip('"""').strip("'''").strip()
        except Exception:
            pass
        
        return f"Script: {script_name}\nNo documentation available."
    
    def run_script(self, script_name: str, args: List[str]) -> int:
        """
        Run a script with arguments.
        
        Args:
            script_name: Name of the script
            args: Arguments to pass to the script
            
        Returns:
            Exit code from script execution
        """
        if script_name not in self.scripts:
            print(f"Error: Script '{script_name}' not found")
            print(f"\nAvailable scripts:")
            for name in sorted(self.scripts.keys()):
                print(f"  - {name}")
            return 1
        
        script_path = self.scripts[script_name]
        
        # Import and run the script
        try:
            spec = importlib.util.spec_from_file_location(script_name, script_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                
                # Set sys.argv to include script name and args
                original_argv = sys.argv
                sys.argv = [script_path.name] + args
                
                try:
                    spec.loader.exec_module(module)
                    
                    # Try to call main() if it exists
                    if hasattr(module, "main"):
                        import asyncio
                        if asyncio.iscoroutinefunction(module.main):
                            exit_code = asyncio.run(module.main())
                        else:
                            exit_code = module.main()
                        return exit_code if isinstance(exit_code, int) else 0
                    else:
                        print(f"Script '{script_name}' has no main() function")
                        return 1
                finally:
                    sys.argv = original_argv
            else:
                print(f"Error: Could not load script '{script_name}'")
                return 1
        except Exception as e:
            print(f"Error running script '{script_name}': {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    def main(self) -> int:
        """Main entry point for script runner."""
        parser = argparse.ArgumentParser(
            description="Unified script runner for documentation scripts",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        
        parser.add_argument(
            "script",
            nargs="?",
            help="Script name to run",
        )
        
        parser.add_argument(
            "--list",
            "-l",
            action="store_true",
            help="List all available scripts",
        )
        
        parser.add_argument(
            "--help-script",
            help="Show help for a specific script",
        )
        
        parser.add_argument(
            "script_args",
            nargs=argparse.REMAINDER,
            help="Arguments to pass to the script",
        )
        
        args = parser.parse_args()
        
        if args.list:
            self.list_scripts()
            return 0
        
        if args.help_script:
            help_text = self.get_script_help(args.help_script)
            if help_text:
                print(help_text)
            else:
                print(f"Script '{args.help_script}' not found")
                return 1
            return 0
        
        if not args.script:
            parser.print_help()
            print("\nUse --list to see available scripts")
            return 1
        
        # Run the script
        return self.run_script(args.script, args.script_args)


def main():
    """Main entry point."""
    runner = ScriptRunner()
    exit_code = runner.main()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
