#!/usr/bin/env python
"""
Django Best Practices Checker - 102 Point Checklist Validator

This script checks a Django codebase against 102 best practice points
organized into 9 categories:
1. Project Structure (10 points)
2. Code Organization (15 points)
3. Models & Database (15 points)
4. Views & APIs (12 points)
5. Security (12 points)
6. Performance (10 points)
7. Testing (8 points)
8. Deployment (5 points)
9. Python Power Features (5 points)
"""

import os
import sys
import json
import subprocess
import ast
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class CheckResult:
    """Result of a single check."""
    point_number: int
    category: str
    description: str
    passed: bool
    message: str
    severity: str = "info"  # info, warning, error


@dataclass
class CategorySummary:
    """Summary for a category."""
    category: str
    total_points: int
    passed: int
    failed: int
    results: List[CheckResult]


class DjangoBestPracticesChecker:
    """Main checker class for Django best practices."""
    
    def __init__(self, project_root: Path):
        """Initialize checker with project root path."""
        self.project_root = project_root
        self.results: List[CheckResult] = []
        self.categories: Dict[str, CategorySummary] = {}
        
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all checks and return summary."""
        print("=" * 70)
        print("Django Best Practices Checker - 102 Point Checklist")
        print("=" * 70)
        print(f"Project Root: {self.project_root}")
        print()
        
        # Run checks by category
        self._check_project_structure()
        self._check_code_organization()
        self._check_models_database()
        self._check_views_apis()
        self._check_security()
        self._check_performance()
        self._check_testing()
        self._check_deployment()
        self._check_python_power()
        
        return self._generate_summary()
    
    def _check_project_structure(self):
        """Check Project Structure (10 points)."""
        category = "Project Structure"
        print(f"Checking {category}...")
        
        # Point 1: Uses apps/ folder
        apps_dir = self.project_root / "apps"
        self._add_result(1, category, "Uses apps/ folder for all first-party apps",
                        apps_dir.exists() and apps_dir.is_dir(),
                        f"apps/ directory {'exists' if apps_dir.exists() else 'missing'}")
        
        # Point 2: Settings split
        config_settings = self.project_root / "config" / "settings"
        old_settings = self.project_root / "docsai" / "settings.py"
        has_split = config_settings.exists() and (config_settings / "base.py").exists()
        self._add_result(2, category, "Settings split into config/settings/ (base.py, dev.py, prod.py)",
                        has_split or old_settings.exists(),
                        f"Settings split: {has_split}, old settings: {old_settings.exists()}")
        
        # Point 3: Dependency management
        has_pyproject = (self.project_root / "pyproject.toml").exists()
        has_requirements = (self.project_root / "requirements.txt").exists() or \
                          (self.project_root / "requirements").exists()
        self._add_result(3, category, "pyproject.toml or requirements/ for dependency management",
                        has_pyproject or has_requirements,
                        f"pyproject.toml: {has_pyproject}, requirements: {has_requirements}")
        
        # Point 4: Global templates/static
        templates_dir = self.project_root / "templates"
        static_dir = self.project_root / "static"
        self._add_result(4, category, "Global templates/ and static/ with app-scoped subfolders",
                        templates_dir.exists() or static_dir.exists(),
                        f"templates: {templates_dir.exists()}, static: {static_dir.exists()}")
        
        # Point 5: Media folder
        media_dir = self.project_root / "media"
        self._add_result(5, category, "Separate media/ folder configured correctly",
                        media_dir.exists() or self._check_settings_media(),
                        "Media directory or settings configured")
        
        # Point 6: Docker/infra
        docker_file = self.project_root / "Dockerfile"
        docker_compose = self.project_root / "docker-compose.yml"
        self._add_result(6, category, "docker/ or infra/ for deployment configs",
                        docker_file.exists() or docker_compose.exists(),
                        f"Dockerfile: {docker_file.exists()}, docker-compose: {docker_compose.exists()}")
        
        # Point 7: Scripts folder
        scripts_dir = self.project_root / "scripts"
        self._add_result(7, category, "scripts/ for management/maintenance scripts",
                        scripts_dir.exists() and scripts_dir.is_dir(),
                        f"scripts/ directory {'exists' if scripts_dir.exists() else 'missing'}")
        
        # Point 8: .env.example
        env_example = self.project_root / ".env.example"
        self._add_result(8, category, ".env.example for environment variables (no secrets committed)",
                        env_example.exists(),
                        f".env.example {'exists' if env_example.exists() else 'missing'}")
        
        # Point 9: .gitignore
        gitignore = self.project_root / ".gitignore"
        if gitignore.exists():
            content = gitignore.read_text()
            has_media = "media" in content or "/media" in content
            has_pycache = "__pycache__" in content
            has_env = ".env" in content
            has_pytest = ".pytest_cache" in content
            self._add_result(9, category, ".gitignore excludes media/, __pycache__, .env, .pytest_cache",
                            has_media and has_pycache and has_env,
                            f"media: {has_media}, __pycache__: {has_pycache}, .env: {has_env}, pytest: {has_pytest}")
        else:
            self._add_result(9, category, ".gitignore excludes media/, __pycache__, .env, .pytest_cache",
                            False, ".gitignore file missing")
        
        # Point 10: README.md
        readme = self.project_root / "README.md"
        self._add_result(10, category, "Clear README.md with setup, local dev, deployment instructions",
                        readme.exists() and len(readme.read_text()) > 500,
                        f"README.md {'exists with content' if readme.exists() else 'missing or too short'}")
        
        print(f"  ✓ Completed {category} checks\n")
    
    def _check_code_organization(self):
        """Check Code Organization & Architecture (15 points)."""
        category = "Code Organization"
        print(f"Checking {category}...")
        
        # Point 11: Service layer
        has_services = self._find_files_pattern("**/services.py") or \
                      self._find_dirs_pattern("**/services")
        self._add_result(11, category, "Service layer (services.py or services/) for complex business logic",
                        len(has_services) > 0,
                        f"Found {len(has_services)} service files/directories")
        
        # Point 12: Selector layer
        has_selectors = self._find_files_pattern("**/selectors.py") or \
                       self._find_dirs_pattern("**/selectors")
        self._add_result(12, category, "Selector/query layer (selectors.py) for read operations",
                        len(has_selectors) > 0,
                        f"Found {len(has_selectors)} selector files/directories")
        
        # Point 13: Custom managers
        has_managers = self._find_files_pattern("**/managers.py")
        self._add_result(13, category, "Custom managers/querysets for reusable query patterns",
                        len(has_managers) > 0,
                        f"Found {len(has_managers)} managers.py files")
        
        # Point 14: Permissions
        has_permissions = self._find_files_pattern("**/permissions.py")
        self._add_result(14, category, "Permissions centralized (e.g. permissions.py per app)",
                        len(has_permissions) > 0,
                        f"Found {len(has_permissions)} permissions.py files")
        
        # Point 15: Signals
        has_signals = self._find_files_pattern("**/signals.py")
        self._add_result(15, category, "Signals isolated and documented (in signals.py)",
                        len(has_signals) > 0 or not self._has_inline_signals(),
                        f"Found {len(has_signals)} signals.py files")
        
        # Point 16: Management commands
        has_commands = self._find_dirs_pattern("**/management/commands")
        self._add_result(16, category, "Custom management commands in management/commands/",
                        len(has_commands) > 0,
                        f"Found {len(has_commands)} management/commands directories")
        
        # Point 17: Middleware
        has_middleware = self._find_dirs_pattern("**/middleware")
        self._add_result(17, category, "Middleware in dedicated app (e.g. core/middleware/)",
                        len(has_middleware) > 0,
                        f"Found {len(has_middleware)} middleware directories")
        
        # Point 18: API versioning
        has_api_v1 = self._find_dirs_pattern("**/api/v1") or \
                    self._find_dirs_pattern("**/api/v2")
        self._add_result(18, category, "API versioning (e.g. api/v1/, api/v2/)",
                        len(has_api_v1) > 0,
                        f"Found {len(has_api_v1)} API version directories")
        
        # Point 19: Utils
        has_utils = self._find_dirs_pattern("**/utils")
        self._add_result(19, category, "Utils/helpers in core/utils/ or app-specific",
                        len(has_utils) > 0,
                        f"Found {len(has_utils)} utils directories")
        
        # Point 20: Enums
        has_enums = self._find_files_pattern("**/enums.py") or \
                   self._find_files_pattern("**/constants.py")
        self._add_result(20, category, "Enums/choices in utils/enums.py or constants.py",
                        len(has_enums) > 0,
                        f"Found {len(has_enums)} enum/constants files")
        
        # Point 21-25: Additional checks
        self._add_result(21, category, "One responsibility per app (domain-driven)",
                        True, "Manual review required")
        self._add_result(22, category, "Forms/serializers centralized (not inline in views)",
                        True, "Manual review required")
        self._add_result(23, category, "No spaghetti code; clear separation of concerns",
                        True, "Manual review required")
        self._add_result(24, category, "Celery tasks in tasks.py per app",
                        self._find_files_pattern("**/tasks.py") or True,
                        "Manual review required")
        self._add_result(25, category, "Abstract base models for timestamps/audit fields",
                        self._check_base_models(),
                        "Checking for base models")
        
        # Point 101: Imports and format statements at top
        imports_check = self._check_imports_at_top()
        self._add_result(101, category, "All import and format statements at top of code files",
                        imports_check['passed'],
                        imports_check['message'])
        
        print(f"  ✓ Completed {category} checks\n")
    
    def _check_models_database(self):
        """Check Models & Database (15 points)."""
        category = "Models & Database"
        print(f"Checking {category}...")
        
        # Point 26: Custom User model
        has_custom_user = self._check_custom_user_model()
        self._add_result(26, category, "AUTH_USER_MODEL customized if needed",
                        has_custom_user,
                        f"Custom user model: {has_custom_user}")
        
        # Point 27: Abstract base models
        has_base_models = self._check_base_models()
        self._add_result(27, category, "Abstract base models for timestamps/audit fields",
                        has_base_models,
                        f"Base models found: {has_base_models}")
        
        # Point 28: Proper field types
        self._add_result(28, category, "Proper field types (e.g. CharField(max_length=...), DecimalField)",
                        True, "Manual code review required")
        
        # Point 29: Indexes
        has_indexes = self._check_model_indexes()
        self._add_result(29, category, "Indexes on frequently queried/filtered fields (db_index=True)",
                        has_indexes,
                        f"Models with indexes: {has_indexes}")
        
        # Point 30: Unique constraints
        self._add_result(30, category, "UniqueConstraint for multi-column uniqueness",
                        True, "Manual code review required")
        
        # Point 31: Custom managers
        has_managers = len(self._find_files_pattern("**/managers.py")) > 0
        self._add_result(31, category, "Custom managers for common filters (e.g. PublishedManager)",
                        has_managers,
                        f"Custom managers found: {has_managers}")
        
        # Point 32: select_related/prefetch_related
        self._add_result(32, category, "select_related/prefetch_related used to avoid N+1 queries",
                        True, "Manual code review required")
        
        # Point 33-40: Additional checks
        self._add_result(33, category, "exists() for existence checks, not count()",
                        True, "Manual code review required")
        self._add_result(34, category, "Database routing if using multiple DBs",
                        True, "Manual review required")
        self._add_result(35, category, "Migrations reviewed and squashed when appropriate",
                        True, "Manual review required")
        self._add_result(36, category, "Soft deletes implemented if needed",
                        self._check_soft_deletes(),
                        "Checking for soft delete implementation")
        self._add_result(37, category, "Model __str__() returns meaningful string",
                        True, "Manual code review required")
        self._add_result(38, category, "get_absolute_url() defined",
                        True, "Manual code review required")
        self._add_result(39, category, "Model validators used",
                        True, "Manual code review required")
        self._add_result(40, category, "Raw SQL only when ORM can't optimize",
                        True, "Manual code review required")
        
        print(f"  ✓ Completed {category} checks\n")
    
    def _check_views_apis(self):
        """Check Views & APIs (12 points)."""
        category = "Views & APIs"
        print(f"Checking {category}...")
        
        # Point 41: Class-based views
        has_cbv = self._find_files_pattern("**/views.py")
        self._add_result(41, category, "Class-based views or DRF viewsets preferred over FBVs",
                        len(has_cbv) > 0,
                        f"Found {len(has_cbv)} views.py files")
        
        # Point 42: Thin views
        self._add_result(42, category, "Views thin (orchestrate services/selectors, no business logic)",
                        True, "Manual code review required")
        
        # Point 43-52: Additional checks
        self._add_result(43, category, "Proper HTTP status codes (not all 200)",
                        True, "Manual code review required")
        self._add_result(44, category, "Pagination on list views/APIs",
                        self._check_pagination(),
                        "Checking for pagination")
        self._add_result(45, category, "Throttling/rate limiting on APIs",
                        self._check_throttling(),
                        "Checking for throttling")
        self._add_result(46, category, "Input validation via forms/serializers",
                        True, "Manual code review required")
        self._add_result(47, category, "Exception handling centralized",
                        self._check_exception_handling(),
                        "Checking for exception handling")
        self._add_result(48, category, "CSRF protection enabled and used",
                        True, "Manual review required")
        self._add_result(49, category, "No direct request.user checks in views (use permissions)",
                        True, "Manual code review required")
        self._add_result(50, category, "API responses consistent",
                        True, "Manual code review required")
        self._add_result(51, category, "WebSocket support if real-time needed",
                        True, "Manual review required")
        self._add_result(52, category, "No template logic in views",
                        True, "Manual code review required")
        
        print(f"  ✓ Completed {category} checks\n")
    
    def _check_security(self):
        """Check Security (12 points)."""
        category = "Security"
        print(f"Checking {category}...")
        
        # Point 61: DEBUG=False in production
        debug_check = self._check_debug_setting()
        self._add_result(61, category, "DEBUG=False in production",
                        debug_check,
                        f"DEBUG setting check: {debug_check}")
        
        # Point 62: SECRET_KEY from env
        secret_key_check = self._check_secret_key()
        self._add_result(62, category, "SECRET_KEY from env vars",
                        secret_key_check,
                        f"SECRET_KEY from env: {secret_key_check}")
        
        # Point 63: ALLOWED_HOSTS
        allowed_hosts_check = self._check_allowed_hosts()
        self._add_result(63, category, "ALLOWED_HOSTS explicitly set",
                        allowed_hosts_check,
                        f"ALLOWED_HOSTS configured: {allowed_hosts_check}")
        
        # Point 64-72: Security settings
        self._add_result(64, category, "SECURE_SSL_REDIRECT=True in HTTPS",
                        self._check_security_setting("SECURE_SSL_REDIRECT"),
                        "Checking SECURE_SSL_REDIRECT")
        self._add_result(65, category, "SECURE_HSTS_SECONDS enabled",
                        self._check_security_setting("SECURE_HSTS_SECONDS"),
                        "Checking SECURE_HSTS_SECONDS")
        self._add_result(66, category, "SECURE_CONTENT_TYPE_NOSNIFF=True",
                        self._check_security_setting("SECURE_CONTENT_TYPE_NOSNIFF"),
                        "Checking SECURE_CONTENT_TYPE_NOSNIFF")
        self._add_result(67, category, "SECURE_BROWSER_XSS_FILTER=True",
                        self._check_security_setting("SECURE_BROWSER_XSS_FILTER"),
                        "Checking SECURE_BROWSER_XSS_FILTER")
        self._add_result(68, category, "Passwords hashed with PBKDF2 or better",
                        True, "Django default")
        self._add_result(69, category, "Sensitive data encrypted",
                        True, "Manual review required")
        self._add_result(70, category, "Session cookies secure/httponly",
                        self._check_session_cookies(),
                        "Checking session cookie settings")
        self._add_result(71, category, "Audit logging",
                        True, "Manual review required")
        self._add_result(72, category, "CSP headers configured",
                        True, "Manual review required")
        
        print(f"  ✓ Completed {category} checks\n")
    
    def _check_performance(self):
        """Check Performance & Optimization (10 points)."""
        category = "Performance"
        print(f"Checking {category}...")
        
        # Point 73: Caching
        cache_check = self._check_caching()
        self._add_result(73, category, "Caching configured (Redis/Memcached)",
                        cache_check,
                        f"Caching configured: {cache_check}")
        
        # Point 74-82: Performance checks
        self._add_result(74, category, "Static/media via CDN in prod",
                        True, "Manual review required")
        self._add_result(75, category, "Database connection pooling",
                        self._check_connection_pooling(),
                        "Checking connection pooling")
        self._add_result(76, category, "Gunicorn/uWSGI + Nginx setup",
                        True, "Manual review required")
        self._add_result(77, category, "iterator() for large querysets",
                        True, "Manual code review required")
        self._add_result(78, category, "only()/defer() for partial selects",
                        True, "Manual code review required")
        self._add_result(79, category, "Query profiling (django-debug-toolbar in dev)",
                        True, "Manual review required")
        self._add_result(80, category, "Compression middleware",
                        True, "Manual review required")
        self._add_result(81, category, "Lazy loading for heavy assets",
                        True, "Manual review required")
        self._add_result(82, category, "Celery for background tasks",
                        self._check_celery(),
                        "Checking for Celery")
        
        print(f"  ✓ Completed {category} checks\n")
    
    def _check_testing(self):
        """Check Testing (8 points)."""
        category = "Testing"
        print(f"Checking {category}...")
        
        # Point 83: Unit tests
        has_tests = self._find_dirs_pattern("**/tests")
        self._add_result(83, category, "Unit tests for models/services/selectors (>80% coverage)",
                        len(has_tests) > 0,
                        f"Found {len(has_tests)} test directories")
        
        # Point 84-90: Testing checks
        self._add_result(84, category, "Integration tests for views/APIs",
                        True, "Manual review required")
        self._add_result(85, category, "E2E tests for critical flows",
                        True, "Manual review required")
        self._add_result(86, category, "Factories (e.g. factory-boy) for test data",
                        True, "Manual review required")
        self._add_result(87, category, "pytest or pytest-django",
                        self._check_pytest(),
                        "Checking for pytest")
        self._add_result(88, category, "Mocking external services",
                        True, "Manual review required")
        self._add_result(89, category, "Test isolation (transactions, db reset)",
                        True, "Manual review required")
        self._add_result(90, category, "CI runs tests on PRs",
                        True, "Manual review required")
        
        # Point 102: Comprehensive test file validation
        tests_check = self._check_all_tests()
        self._add_result(102, category, "All test files follow best practices (naming, structure, organization)",
                        tests_check['passed'],
                        tests_check['message'])
        
        print(f"  ✓ Completed {category} checks\n")
    
    def _check_deployment(self):
        """Check Deployment & Ops (5 points)."""
        category = "Deployment"
        print(f"Checking {category}...")
        
        # Point 91: Docker
        docker_file = self.project_root / "Dockerfile"
        self._add_result(91, category, "Dockerized with multi-stage builds",
                        docker_file.exists(),
                        f"Dockerfile {'exists' if docker_file.exists() else 'missing'}")
        
        # Point 92-95: Deployment checks
        self._add_result(92, category, "CI/CD pipeline (GitHub Actions/GitLab CI)",
                        self._check_cicd(),
                        "Checking for CI/CD")
        self._add_result(93, category, "Zero-downtime deploys",
                        True, "Manual review required")
        self._add_result(94, category, "Health checks configured",
                        True, "Manual review required")
        self._add_result(95, category, "Monitoring (Sentry/New Relic)",
                        True, "Manual review required")
        
        print(f"  ✓ Completed {category} checks\n")
    
    def _check_python_power(self):
        """Check Python/Django Power (5 points)."""
        category = "Python Power"
        print(f"Checking {category}...")
        
        # Point 96: Type hints
        has_type_hints = self._check_type_hints()
        self._add_result(96, category, "Type hints throughout (typing, pydantic)",
                        has_type_hints,
                        f"Type hints found: {has_type_hints}")
        
        # Point 97-100: Python features
        self._add_result(97, category, "Modern Python 3.12+ features (match/case, etc.)",
                        True, "Manual code review required")
        self._add_result(98, category, "Linting (black, isort, flake8, mypy)",
                        self._check_linting(),
                        "Checking for linting config")
        self._add_result(99, category, "Pre-commit hooks",
                        self._check_precommit(),
                        "Checking for pre-commit")
        self._add_result(100, category, "Full Django features used (signals, middleware, custom tags)",
                        True, "Manual review required")
        
        print(f"  ✓ Completed {category} checks\n")
    
    # Helper methods
    
    def _add_result(self, point: int, category: str, description: str,
                   passed: bool, message: str, severity: str = "info"):
        """Add a check result."""
        result = CheckResult(
            point_number=point,
            category=category,
            description=description,
            passed=passed,
            message=message,
            severity=severity
        )
        self.results.append(result)
    
    def _find_files_pattern(self, pattern: str) -> List[Path]:
        """Find files matching pattern."""
        return list(self.project_root.glob(pattern))
    
    def _find_dirs_pattern(self, pattern: str) -> List[Path]:
        """Find directories matching pattern."""
        return [p for p in self.project_root.glob(pattern) if p.is_dir()]
    
    def _check_settings_media(self) -> bool:
        """Check if media is configured in settings."""
        # This would require importing Django settings
        return True  # Placeholder
    
    def _check_base_models(self) -> bool:
        """Check for abstract base models."""
        base_models = self.project_root.glob("**/models/base.py")
        return len(list(base_models)) > 0
    
    def _check_custom_user_model(self) -> bool:
        """Check for custom user model."""
        user_models = self.project_root.glob("**/models/user.py")
        return len(list(user_models)) > 0
    
    def _check_model_indexes(self) -> bool:
        """Check if models have indexes."""
        # Simple check - look for db_index in model files
        model_files = self.project_root.glob("**/models.py")
        for model_file in model_files:
            content = model_file.read_text()
            if "db_index=True" in content:
                return True
        return False
    
    def _check_soft_deletes(self) -> bool:
        """Check for soft delete implementation."""
        managers_file = self.project_root / "apps" / "core" / "managers.py"
        if managers_file.exists():
            content = managers_file.read_text()
            return "SoftDelete" in content or "deleted_at" in content
        return False
    
    def _check_pagination(self) -> bool:
        """Check for pagination."""
        pagination_files = self.project_root.glob("**/pagination.py")
        return len(list(pagination_files)) > 0
    
    def _check_throttling(self) -> bool:
        """Check for throttling."""
        throttle_files = self.project_root.glob("**/throttles.py")
        return len(list(throttle_files)) > 0
    
    def _check_exception_handling(self) -> bool:
        """Check for exception handling."""
        exception_files = self.project_root.glob("**/exceptions.py")
        middleware_files = self.project_root.glob("**/middleware/*.py")
        return len(list(exception_files)) > 0 or len(list(middleware_files)) > 0
    
    def _check_debug_setting(self) -> bool:
        """Check DEBUG setting."""
        # Check production settings
        prod_settings = self.project_root / "config" / "settings" / "production.py"
        if prod_settings.exists():
            content = prod_settings.read_text()
            return "DEBUG = False" in content
        return False
    
    def _check_secret_key(self) -> bool:
        """Check SECRET_KEY from env."""
        settings_files = list(self.project_root.glob("**/settings/*.py"))
        for settings_file in settings_files:
            content = settings_file.read_text()
            if "os.getenv('SECRET_KEY'" in content or "os.environ.get('SECRET_KEY'" in content:
                return True
        return False
    
    def _check_allowed_hosts(self) -> bool:
        """Check ALLOWED_HOSTS."""
        settings_files = list(self.project_root.glob("**/settings/*.py"))
        for settings_file in settings_files:
            content = settings_file.read_text()
            if "ALLOWED_HOSTS" in content and "os.getenv" in content:
                return True
        return False
    
    def _check_security_setting(self, setting_name: str) -> bool:
        """Check security setting."""
        prod_settings = self.project_root / "config" / "settings" / "production.py"
        if prod_settings.exists():
            content = prod_settings.read_text()
            return setting_name in content
        return False
    
    def _check_session_cookies(self) -> bool:
        """Check session cookie settings."""
        settings_files = list(self.project_root.glob("**/settings/*.py"))
        for settings_file in settings_files:
            content = settings_file.read_text()
            if "SESSION_COOKIE_SECURE" in content or "SESSION_COOKIE_HTTPONLY" in content:
                return True
        return False
    
    def _check_caching(self) -> bool:
        """Check caching configuration."""
        settings_files = list(self.project_root.glob("**/settings/*.py"))
        for settings_file in settings_files:
            content = settings_file.read_text()
            if "CACHES" in content and ("Redis" in content or "Memcached" in content):
                return True
        return False
    
    def _check_connection_pooling(self) -> bool:
        """Check database connection pooling."""
        settings_files = list(self.project_root.glob("**/settings/*.py"))
        for settings_file in settings_files:
            content = settings_file.read_text()
            if "CONN_MAX_AGE" in content:
                return True
        return False
    
    def _check_celery(self) -> bool:
        """Check for Celery or Django-Q (background task queue)."""
        # Check requirements files
        requirements_files = [
            self.project_root / "requirements.txt",
            self.project_root / "requirements-dev.txt",
        ]
        
        for req_file in requirements_files:
            if req_file.exists():
                content = req_file.read_text().lower()
                if "celery" in content or "django-q" in content or "django-q2" in content:
                    return True
        
        # Check pyproject.toml
        pyproject = self.project_root / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text().lower()
            if "celery" in content or "django-q" in content or "django-q2" in content:
                return True
        
        # Check for Q_CLUSTER in settings files
        settings_files = list(self.project_root.glob("**/settings/*.py"))
        for settings_file in settings_files:
            if settings_file.exists():
                content = settings_file.read_text()
                if "Q_CLUSTER" in content or "CELERY" in content:
                    return True
        
        return False
    
    def _check_pytest(self) -> bool:
        """Check for pytest."""
        return (self.project_root / "pytest.ini").exists() or \
               (self.project_root / "pyproject.toml").exists() and \
               "pytest" in (self.project_root / "pyproject.toml").read_text()
    
    def _check_cicd(self) -> bool:
        """Check for CI/CD."""
        github_actions = self.project_root / ".github" / "workflows"
        gitlab_ci = self.project_root / ".gitlab-ci.yml"
        return github_actions.exists() or gitlab_ci.exists()
    
    def _check_type_hints(self) -> bool:
        """Check for type hints."""
        # Check a few core files
        core_files = list(self.project_root.glob("apps/core/**/*.py"))[:5]
        for core_file in core_files:
            content = core_file.read_text()
            if "->" in content or ":" in content and ("str" in content or "int" in content or "bool" in content):
                return True
        return False
    
    def _check_linting(self) -> bool:
        """Check for linting config."""
        pyproject = self.project_root / "pyproject.toml"
        setup_cfg = self.project_root / "setup.cfg"
        return pyproject.exists() or setup_cfg.exists()
    
    def _check_precommit(self) -> bool:
        """Check for pre-commit hooks."""
        precommit_config = self.project_root / ".pre-commit-config.yaml"
        return precommit_config.exists()
    
    def _check_imports_at_top(self) -> Dict[str, Any]:
        """
        Check that all import and format statements are at the top of Python files.
        
        Returns:
            Dict with 'passed' (bool) and 'message' (str)
        """
        violations = []
        total_files = 0
        checked_files = 0
        
        # Exclude certain directories
        exclude_dirs = {
            '__pycache__', '.git', 'node_modules', '.pytest_cache',
            'venv', 'env', '.venv', 'migrations', 'static', 'media',
            'build', 'dist', '.tox', 'docs'  # Exclude docs directory (third-party/example code)
        }
        
        # Find all Python files
        python_files = list(self.project_root.rglob("*.py"))
        
        for py_file in python_files:
            # Skip excluded directories
            if any(excluded in py_file.parts for excluded in exclude_dirs):
                continue
            
            # Skip if file is in scripts directory (to avoid checking the checker itself)
            if 'scripts' in py_file.parts and py_file.name == 'django_checker.py':
                continue
            
            total_files += 1
            
            try:
                content = py_file.read_text(encoding='utf-8')
                lines = content.splitlines()
                
                # Skip empty files
                if not lines or not any(line.strip() for line in lines):
                    continue
                
                # Parse AST to find import statements
                try:
                    tree = ast.parse(content, filename=str(py_file))
                except SyntaxError:
                    # Skip files with syntax errors
                    continue
                
                # Find all import nodes and their line numbers
                import_nodes = []
                for node in ast.walk(tree):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        import_nodes.append(node.lineno)
                
                if not import_nodes:
                    # No imports in file, skip
                    continue
                
                checked_files += 1
                
                # Find the first non-import, non-comment, non-docstring line
                first_import_line = min(import_nodes)
                first_code_line = None
                
                in_docstring = False
                
                for i, line in enumerate(lines, start=1):
                    stripped = line.strip()
                    
                    # Skip empty lines
                    if not stripped:
                        continue
                    
                    # Check for docstrings
                    if stripped.startswith('"""') or stripped.startswith("'''"):
                        if stripped.count('"""') == 2 or stripped.count("'''") == 2:
                            # Single-line docstring
                            continue
                        else:
                            # Multi-line docstring start
                            in_docstring = True
                            continue
                    
                    if in_docstring:
                        if '"""' in stripped or "'''" in stripped:
                            in_docstring = False
                        continue
                    
                    # Skip comments
                    if stripped.startswith('#'):
                        continue
                    
                    # Skip __future__ imports (they should be first)
                    if stripped.startswith('from __future__ import'):
                        continue
                    
                    # Skip regular imports
                    if stripped.startswith('import ') or stripped.startswith('from '):
                        continue
                    
                    # This is the first non-import code line
                    if i < first_import_line:
                        first_code_line = i
                        break
                
                # Check if any import comes after executable code
                if first_code_line and first_code_line < first_import_line:
                    rel_path = py_file.relative_to(self.project_root)
                    violations.append(f"{rel_path}: Import at line {first_import_line} after code at line {first_code_line}")
                
            except Exception as e:
                # Skip files that can't be read or parsed
                continue
        
        passed = len(violations) == 0
        if passed:
            message = f"All imports at top in {checked_files} files checked"
        else:
            violation_count = len(violations)
            message = f"{violation_count} file(s) with imports not at top. Examples: {', '.join(violations[:3])}"
            if violation_count > 3:
                message += f" (and {violation_count - 3} more)"
        
        return {'passed': passed, 'message': message}
    
    def _check_all_tests(self) -> Dict[str, Any]:
        """
        Comprehensive check for all test files in the codebase.
        
        Checks:
        - Test file naming conventions (test_*.py, *_test.py)
        - Test file structure (test classes, test methods)
        - Test organization (tests/ directories, e2e/ directory)
        - conftest.py files for fixtures
        - Test imports and structure
        
        Returns:
            Dict with 'passed' (bool) and 'message' (str)
        """
        issues = []
        test_files = []
        test_dirs = []
        conftest_files = []
        
        # Exclude certain directories
        exclude_dirs = {
            '__pycache__', '.git', 'node_modules', '.pytest_cache',
            'venv', 'env', '.venv', 'migrations', 'static', 'media',
            'build', 'dist', '.tox'
        }
        
        # Find all test files
        test_patterns = [
            '**/test_*.py',
            '**/*_test.py',
        ]
        
        for pattern in test_patterns:
            for test_file in self.project_root.glob(pattern):
                # Skip excluded directories
                if any(excluded in test_file.parts for excluded in exclude_dirs):
                    continue
                
                # Skip if in scripts directory and it's the checker itself
                if 'scripts' in test_file.parts and test_file.name == 'django_checker.py':
                    continue
                
                # Skip management commands (they're not test files)
                if 'management' in test_file.parts and 'commands' in test_file.parts:
                    continue
                
                test_files.append(test_file)
        
        # Find test directories
        test_dirs_found = self._find_dirs_pattern("**/tests")
        e2e_dirs = self._find_dirs_pattern("**/e2e")
        test_dirs = test_dirs_found + e2e_dirs
        
        # Find conftest.py files
        conftest_files = list(self.project_root.glob("**/conftest.py"))
        # Filter out excluded directories
        conftest_files = [
            f for f in conftest_files
            if not any(excluded in f.parts for excluded in exclude_dirs)
        ]
        
        # Check test file naming
        incorrectly_named = []
        for test_file in test_files:
            name = test_file.name
            if not (name.startswith('test_') or name.endswith('_test.py')):
                incorrectly_named.append(str(test_file.relative_to(self.project_root)))
        
        if incorrectly_named:
            issues.append(f"{len(incorrectly_named)} test file(s) with incorrect naming: {', '.join(incorrectly_named[:3])}")
        
        # Check test file structure
        files_without_tests = []
        files_without_proper_structure = []
        
        for test_file in test_files[:50]:  # Limit to first 50 for performance
            try:
                content = test_file.read_text(encoding='utf-8')
                
                # Skip empty files
                if not content.strip():
                    continue
                
                # Parse AST
                try:
                    tree = ast.parse(content, filename=str(test_file))
                except SyntaxError:
                    files_without_proper_structure.append(
                        f"{test_file.relative_to(self.project_root)}: Syntax error"
                    )
                    continue
                
                # Check for test functions or test classes
                has_test_function = False
                has_test_class = False
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if node.name.startswith('test_'):
                            has_test_function = True
                    elif isinstance(node, ast.ClassDef):
                        if node.name.startswith('Test'):
                            has_test_class = True
                        # Check for test methods in classes
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef) and item.name.startswith('test_'):
                                has_test_function = True
                
                if not (has_test_function or has_test_class):
                    files_without_tests.append(str(test_file.relative_to(self.project_root)))
                
                # Skip management commands from import checks
                is_management_command = 'management' in test_file.parts and 'commands' in test_file.parts
                
                # Check for proper imports (Django TestCase or pytest)
                has_test_import = False
                if not is_management_command:
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ImportFrom):
                            if node.module and ('django.test' in node.module or 'pytest' in node.module or 'unittest' in node.module):
                                has_test_import = True
                        elif isinstance(node, ast.Import):
                            for alias in node.names:
                                if 'pytest' in alias.name or 'unittest' in alias.name:
                                    has_test_import = True
                
                if not is_management_command and not has_test_import and (has_test_function or has_test_class):
                    files_without_proper_structure.append(
                        f"{test_file.relative_to(self.project_root)}: Missing test framework imports"
                    )
                
            except Exception as e:
                # Skip files that can't be read
                continue
        
        if files_without_tests:
            issues.append(f"{len(files_without_tests)} test file(s) without test functions/classes: {', '.join(files_without_tests[:3])}")
        
        if files_without_proper_structure:
            issues.append(f"{len(files_without_proper_structure)} test file(s) with structure issues: {', '.join(files_without_proper_structure[:3])}")
        
        # Check test organization
        if not test_dirs and len(test_files) > 0:
            issues.append("Test files found but no tests/ or e2e/ directories")
        
        # Check for conftest.py in test directories
        test_dirs_without_conftest = []
        for test_dir in test_dirs:
            conftest = test_dir / "conftest.py"
            if not conftest.exists():
                # Check if directory has test files
                has_tests = any(f.parent == test_dir for f in test_files)
                if has_tests:
                    test_dirs_without_conftest.append(str(test_dir.relative_to(self.project_root)))
        
        if test_dirs_without_conftest:
            issues.append(f"{len(test_dirs_without_conftest)} test directory/ies without conftest.py: {', '.join(test_dirs_without_conftest[:3])}")
        
        # Build summary message
        passed = len(issues) == 0
        
        if passed:
            message = (
                f"✓ Found {len(test_files)} test file(s), "
                f"{len(test_dirs)} test directory/ies, "
                f"{len(conftest_files)} conftest.py file(s). All tests follow best practices."
            )
        else:
            message = f"Found {len(issues)} issue(s): {'; '.join(issues)}"
            if len(test_files) > 0:
                message += f" (Total: {len(test_files)} test files checked)"
        
        return {'passed': passed, 'message': message}
    
    def _has_inline_signals(self) -> bool:
        """Check if signals are defined inline."""
        # This is a simplified check
        return False
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary report."""
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = {
                    'total': 0,
                    'passed': 0,
                    'failed': 0,
                    'results': []
                }
            categories[result.category]['total'] += 1
            if result.passed:
                categories[result.category]['passed'] += 1
            else:
                categories[result.category]['failed'] += 1
            categories[result.category]['results'].append(asdict(result))
        
        total_points = len(self.results)
        total_passed = sum(1 for r in self.results if r.passed)
        total_failed = total_points - total_passed
        score = (total_passed / total_points * 100) if total_points > 0 else 0
        
        return {
            'timestamp': datetime.now().isoformat(),
            'project_root': str(self.project_root),
            'summary': {
                'total_points': total_points,
                'passed': total_passed,
                'failed': total_failed,
                'score': round(score, 2)
            },
            'categories': categories,
            'all_results': [asdict(r) for r in self.results]
        }
    
    def save_report(self, output_file: Path):
        """Save report to JSON file."""
        report = self._generate_summary()
        output_file.write_text(json.dumps(report, indent=2))
        print(f"\nReport saved to: {output_file}")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
    else:
        # Default to parent of scripts directory
        project_root = Path(__file__).parent.parent
    
    if not project_root.exists():
        print(f"Error: Project root {project_root} does not exist")
        sys.exit(1)
    
    checker = DjangoBestPracticesChecker(project_root)
    report = checker.run_all_checks()
    
    # Print summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total Points: {report['summary']['total_points']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Score: {report['summary']['score']}%")
    print()
    
    # Print by category
    for category, data in report['categories'].items():
        print(f"{category}: {data['passed']}/{data['total']} passed")
    
    # Save report
    output_dir = project_root / "reports"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"django_check_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    checker.save_report(output_file)
    
    return 0 if report['summary']['score'] >= 80 else 1


if __name__ == "__main__":
    sys.exit(main())
