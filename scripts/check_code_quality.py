#!/usr/bin/env python
"""
Code quality check script.

Runs all code quality checks:
- Ruff linting
- Black formatting check
- isort import check
- mypy type checking

Usage:
    python scripts/check_code_quality.py
    python scripts/check_code_quality.py --fix  # Auto-fix issues
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str, fix: bool = False) -> bool:
    """Run a command and return True if successful."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(cmd, check=False, capture_output=False)
        if result.returncode != 0:
            if not fix:
                print(f"\n❌ {description} failed!")
                return False
        else:
            print(f"\n✅ {description} passed!")
        return True
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print(f"Please install the required tool: {cmd[0]}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run code quality checks")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-fix issues where possible"
    )
    parser.add_argument(
        "--skip-mypy",
        action="store_true",
        help="Skip mypy type checking (can be slow)"
    )
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Path to check (default: current directory)"
    )
    
    args = parser.parse_args()
    
    base_path = Path(args.path)
    if not base_path.exists():
        print(f"Error: Path {base_path} does not exist")
        sys.exit(1)
    
    checks_passed = []
    checks_failed = []
    
    # Ruff linting
    ruff_cmd = ["ruff", "check", str(base_path)]
    if args.fix:
        ruff_cmd.append("--fix")
    
    if run_command(ruff_cmd, "Ruff linting", args.fix):
        checks_passed.append("Ruff")
    else:
        checks_failed.append("Ruff")
    
    # Ruff formatting
    ruff_format_cmd = ["ruff", "format", str(base_path)]
    if not args.fix:
        ruff_format_cmd.append("--check")
    
    if run_command(ruff_format_cmd, "Ruff formatting", args.fix):
        checks_passed.append("Ruff Format")
    else:
        checks_failed.append("Ruff Format")
    
    # Black formatting check
    black_cmd = ["black", str(base_path), "--line-length=88"]
    if not args.fix:
        black_cmd.append("--check")
    
    if run_command(black_cmd, "Black formatting", args.fix):
        checks_passed.append("Black")
    else:
        checks_failed.append("Black")
    
    # isort import check
    isort_cmd = ["isort", str(base_path), "--profile=black", "--line-length=88"]
    if not args.fix:
        isort_cmd.append("--check-only")
    
    if run_command(isort_cmd, "isort import sorting", args.fix):
        checks_passed.append("isort")
    else:
        checks_failed.append("isort")
    
    # mypy type checking (optional, can be slow)
    if not args.skip_mypy:
        mypy_cmd = ["mypy", str(base_path)]
        if run_command(mypy_cmd, "mypy type checking", False):
            checks_passed.append("mypy")
        else:
            checks_failed.append("mypy")
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Passed: {len(checks_passed)}")
    for check in checks_passed:
        print(f"   - {check}")
    
    if checks_failed:
        print(f"\n❌ Failed: {len(checks_failed)}")
        for check in checks_failed:
            print(f"   - {check}")
        print(f"\n💡 Tip: Run with --fix to auto-fix issues")
        sys.exit(1)
    else:
        print("\n🎉 All checks passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
