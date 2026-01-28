#!/usr/bin/env python
"""
Test runner script for Documentation AI project.

Provides convenient commands to run different test suites:
- Unit tests
- Integration tests
- E2E tests
- All tests
- With coverage

Usage:
    python scripts/run_tests.py [options]
    python scripts/run_tests.py --unit
    python scripts/run_tests.py --integration
    python scripts/run_tests.py --e2e
    python scripts/run_tests.py --all
    python scripts/run_tests.py --coverage
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return True if successful."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            print(f"\n❌ {description} failed!")
            return False
        print(f"\n✅ {description} passed!")
        return True
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print(f"Please install pytest: pip install pytest pytest-django")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run test suites")
    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run unit tests only"
    )
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run integration tests only"
    )
    parser.add_argument(
        "--e2e",
        action="store_true",
        help="Run E2E tests only"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all tests"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run tests with coverage report"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--fail-fast",
        "-x",
        action="store_true",
        help="Stop on first failure"
    )
    parser.add_argument(
        "--path",
        type=str,
        help="Run tests in specific path"
    )
    
    args = parser.parse_args()
    
    # Base pytest command
    base_cmd = ["pytest"]
    
    if args.verbose:
        base_cmd.append("-v")
    
    if args.fail_fast:
        base_cmd.append("-x")
    
    # Determine what to run
    if args.path:
        test_path = args.path
        cmd = base_cmd + [test_path]
        description = f"Tests in {test_path}"
    elif args.unit:
        cmd = base_cmd + [
            "apps/documentation/tests/test_utils_*.py",
            "apps/documentation/tests/test_*_views.py",
            "-m", "not e2e", "-m", "not integration"
        ]
        description = "Unit tests"
    elif args.integration:
        cmd = base_cmd + [
            "apps/documentation/tests/test_api_*.py",
            "apps/documentation/tests/test_workflows.py",
            "-m", "integration"
        ]
        description = "Integration tests"
    elif args.e2e:
        cmd = base_cmd + [
            "e2e/",
            "-m", "e2e"
        ]
        description = "E2E tests"
    elif args.all:
        cmd = base_cmd + [
            "apps/documentation/tests/",
            "e2e/",
        ]
        description = "All tests"
    else:
        # Default: run all tests except E2E
        cmd = base_cmd + [
            "apps/documentation/tests/",
            "-m", "not e2e"
        ]
        description = "All tests (excluding E2E)"
    
    # Add coverage if requested
    if args.coverage:
        cmd.extend([
            "--cov=apps",
            "--cov-report=html",
            "--cov-report=term",
            "--cov-report=xml"
        ])
        description += " with coverage"
    
    # Run tests
    success = run_command(cmd, description)
    
    if args.coverage and success:
        print("\n" + "="*60)
        print("Coverage Report")
        print("="*60)
        print("HTML report generated in: htmlcov/index.html")
        print("XML report generated in: coverage.xml")
        print("="*60)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
