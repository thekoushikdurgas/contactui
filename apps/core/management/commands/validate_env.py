"""Management command to validate environment variables."""

import os
import re
import urllib.parse
from typing import List, Tuple, Optional
from django.core.management.base import BaseCommand
from django.conf import settings
import httpx


class Command(BaseCommand):
    help = 'Validate environment configuration with comprehensive checks'

    def __init__(self):
        super().__init__()
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-connectivity',
            action='store_true',
            help='Skip API connectivity checks',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed validation information',
        )

    def handle(self, *args, **options):
        """Validate environment variables with comprehensive checks."""
        self.skip_connectivity = options.get('skip_connectivity', False)
        self.verbose = options.get('verbose', False)
        
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('Environment Configuration Validation'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        
        # Validate all sections
        self._validate_django_settings()
        self._validate_database_config()
        self._validate_aws_s3_config()
        self._validate_graphql_config()
        self._validate_logs_api_config()
        self._validate_lambda_api_config()
        self._validate_ai_config()
        self._validate_storage_config()
        self._validate_cache_config()
        self._validate_django_q_config()
        
        # Connectivity checks (if not skipped)
        if not self.skip_connectivity:
            self._check_api_connectivity()
        
        # Report results
        self._report_results()
        
        # Exit with appropriate code
        if self.errors:
            exit(1)
        elif self.warnings:
            exit(0)
        else:
            exit(0)

    def _validate_django_settings(self):
        """Validate Django core settings."""
        self.stdout.write('\n[Django Settings]')
        
        # SECRET_KEY validation
        secret_key = getattr(settings, 'SECRET_KEY', '')
        if not secret_key:
            self.errors.append("SECRET_KEY is required and cannot be empty")
        elif secret_key == 'django-insecure-change-this-in-production':
            self.errors.append("SECRET_KEY must be changed from default value")
        elif len(secret_key) < 50:
            self.warnings.append("SECRET_KEY is shorter than recommended (should be at least 50 characters)")
        else:
            if self.verbose:
                self.info.append("SECRET_KEY is properly configured")
        
        # DEBUG validation
        debug = getattr(settings, 'DEBUG', False)
        if debug:
            self.warnings.append("DEBUG is True - should be False in production")
        else:
            if self.verbose:
                self.info.append("DEBUG is False (production mode)")
        
        # ALLOWED_HOSTS validation
        allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
        if not allowed_hosts or allowed_hosts == ['']:
            self.warnings.append("ALLOWED_HOSTS is empty - may cause issues in production")
        else:
            if self.verbose:
                self.info.append(f"ALLOWED_HOSTS configured: {', '.join(allowed_hosts)}")

    def _validate_database_config(self):
        """Validate database configuration."""
        self.stdout.write('\n[Database Configuration]')
        
        db_engine = getattr(settings, 'DATABASE_ENGINE', 'sqlite').lower()
        
        if db_engine == 'sqlite':
            if self.verbose:
                self.info.append("Using SQLite database (development)")
            db_path = settings.DATABASES['default']['NAME']
            db_dir = os.path.dirname(db_path) if db_path != ':memory:' else None
            if db_dir and not os.path.exists(db_dir):
                self.warnings.append(f"Database directory does not exist: {db_dir}")
        elif db_engine == 'postgresql':
            if self.verbose:
                self.info.append("Using PostgreSQL database (production)")
            db_config = settings.DATABASES['default']
            if not db_config.get('NAME'):
                self.errors.append("PostgreSQL DATABASE_NAME is required")
            if not db_config.get('USER'):
                self.errors.append("PostgreSQL DATABASE_USER is required")
        else:
            self.errors.append(f"Unknown DATABASE_ENGINE: {db_engine}")

    def _validate_aws_s3_config(self):
        """Validate AWS S3 configuration."""
        self.stdout.write('\n[AWS S3 Configuration]')
        
        access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', '')
        secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', '')
        region = getattr(settings, 'AWS_REGION', '')
        bucket = getattr(settings, 'S3_BUCKET_NAME', '')
        
        if access_key:
            # Validate access key format (starts with AKIA for IAM users)
            if not (access_key.startswith('AKIA') or len(access_key) >= 16):
                self.warnings.append("AWS_ACCESS_KEY_ID format may be invalid")
            
            if not secret_key:
                self.errors.append("AWS_SECRET_ACCESS_KEY is required when AWS_ACCESS_KEY_ID is set")
            elif len(secret_key) < 20:
                self.warnings.append("AWS_SECRET_ACCESS_KEY seems too short")
            
            if not region:
                self.warnings.append("AWS_REGION not set - defaulting to us-east-1")
            
            if not bucket:
                self.warnings.append("S3_BUCKET_NAME not set - S3 operations may fail")
            else:
                if self.verbose:
                    self.info.append(f"S3 bucket configured: {bucket}")
        else:
            self.warnings.append("AWS S3 not configured - S3 fallback will not work")

    def _validate_graphql_config(self):
        """Validate GraphQL configuration."""
        self.stdout.write('\n[GraphQL Configuration]')
        
        graphql_url = getattr(settings, 'APPOINTMENT360_GRAPHQL_URL', '')
        graphql_enabled = getattr(settings, 'GRAPHQL_AUTH_ENABLED', False)
        
        if graphql_url:
            # Validate URL format
            if not (graphql_url.startswith('http://') or graphql_url.startswith('https://')):
                self.errors.append(
                    f"APPOINTMENT360_GRAPHQL_URL must start with http:// or https://. Got: {graphql_url}"
                )
            else:
                try:
                    parsed = urllib.parse.urlparse(graphql_url)
                    if not parsed.netloc:
                        self.errors.append(f"Invalid APPOINTMENT360_GRAPHQL_URL format: {graphql_url}")
                    else:
                        if self.verbose:
                            self.info.append(f"GraphQL URL configured: {graphql_url}")
                        if self.verbose:
                            self.info.append("GraphQL authentication uses JWT tokens from authenticated sessions")
                except Exception as e:
                    self.errors.append(f"Invalid APPOINTMENT360_GRAPHQL_URL: {e}")
        else:
            self.warnings.append("APPOINTMENT360_GRAPHQL_URL not configured - GraphQL fallback will not work")

    def _validate_logs_api_config(self):
        """Validate Lambda Logs API configuration."""
        self.stdout.write('\n[Lambda Logs API Configuration]')
        logs_url = getattr(settings, 'LOGS_API_URL', '')
        logs_key = getattr(settings, 'LOGS_API_KEY', '')
        if logs_url:
            if not (logs_url.startswith('http://') or logs_url.startswith('https://')):
                self.errors.append(
                    f"LOGS_API_URL must start with http:// or https://. Got: {logs_url}"
                )
            elif logs_key:
                if self.verbose:
                    self.info.append("Lambda Logs API configured - admin logs will use REST API")
            else:
                self.warnings.append("LOGS_API_URL set but LOGS_API_KEY missing - admin logs will fall back to GraphQL")
        else:
            if self.verbose:
                self.info.append("LOGS_API_URL not configured - admin logs will use GraphQL")

    def _validate_lambda_api_config(self):
        """Validate Lambda AI API configuration (Documentation API removed)."""
        self.stdout.write('\n[Lambda AI API Configuration]')
        
        ai_url = getattr(settings, 'LAMBDA_AI_API_URL', '')
        ai_key = getattr(settings, 'LAMBDA_AI_API_KEY', '')
        
        if ai_url:
            if not (ai_url.startswith('http://') or ai_url.startswith('https://')):
                self.errors.append(
                    f"LAMBDA_AI_API_URL must start with http:// or https://. Got: {ai_url}"
                )
            else:
                if self.verbose:
                    self.info.append(f"Lambda AI API URL: {ai_url}")
            
            if not ai_key:
                self.warnings.append("LAMBDA_AI_API_KEY is missing - AI API calls may fail")
        else:
            self.warnings.append("LAMBDA_AI_API_URL not configured")

    def _validate_ai_config(self):
        """Validate AI service configuration."""
        self.stdout.write('\n[AI Service Configuration]')
        
        has_openai = bool(getattr(settings, 'OPENAI_API_KEY', ''))
        has_gemini = bool(getattr(settings, 'GEMINI_API_KEY', ''))
        has_lambda_ai = bool(getattr(settings, 'LAMBDA_AI_API_KEY', ''))
        
        # Check for placeholder values
        openai_key = getattr(settings, 'OPENAI_API_KEY', '')
        if openai_key and ('your-' in openai_key.lower() or 'placeholder' in openai_key.lower()):
            self.warnings.append("OPENAI_API_KEY appears to be a placeholder value")
            has_openai = False
        
        if has_openai:
            if self.verbose:
                self.info.append("OpenAI API configured")
        if has_gemini:
            if self.verbose:
                self.info.append("Google Gemini API configured")
        if has_lambda_ai:
            if self.verbose:
                self.info.append("Lambda AI API configured")
        
        if not (has_openai or has_gemini or has_lambda_ai):
            self.warnings.append("No AI service configured (OpenAI, Gemini, or Lambda AI) - AI features will not work")

    def _validate_storage_config(self):
        """Validate storage configuration."""
        self.stdout.write('\n[Storage Configuration]')
        
        use_local = getattr(settings, 'USE_LOCAL_JSON_FILES', True)
        
        if use_local:
            media_root = getattr(settings, 'MEDIA_ROOT', None)
            if not media_root:
                self.warnings.append("MEDIA_ROOT not configured - local JSON files may not work")
            elif not os.path.exists(media_root):
                self.warnings.append(f"MEDIA_ROOT directory does not exist: {media_root}")
                self.info.append(f"Create directory: mkdir -p {media_root}")
            else:
                # Check for required subdirectories
                required_dirs = ['pages', 'endpoints', 'relationships']
                for dir_name in required_dirs:
                    dir_path = os.path.join(media_root, dir_name)
                    if not os.path.exists(dir_path):
                        if self.verbose:
                            self.warnings.append(f"Recommended directory missing: {dir_path}")
                if self.verbose:
                    self.info.append(f"Local storage enabled: {media_root}")
        else:
            self.info.append("Local JSON files disabled - using cloud storage only")

    def _validate_cache_config(self):
        """Validate cache configuration (LocMemCache vs Redis)."""
        self.stdout.write('\n[Cache Configuration]')
        
        use_redis = getattr(settings, 'USE_REDIS_CACHE', False)
        caches = getattr(settings, 'CACHES', {})
        default_backend = caches.get('default', {}).get('BACKEND', '')
        
        if 'redis' in default_backend.lower():
            self.info.append("Cache backend: Redis (USE_REDIS_CACHE=True)")
            if self.verbose:
                loc = caches.get('default', {}).get('LOCATION', '')
                self.info.append(f"Redis location: {loc}")
        else:
            self.info.append("Cache backend: Local Memory Cache (LocMemCache) — no Redis required")
            if self.verbose:
                self.info.append("Set USE_REDIS_CACHE=True and configure Redis to use Redis cache")

    def _validate_django_q_config(self):
        """Validate Django-Q configuration."""
        self.stdout.write('\n[Django-Q Configuration]')
        
        q_config = getattr(settings, 'Q_CLUSTER', {})
        workers = q_config.get('workers', 4)
        broker = 'ORM (database)' if 'orm' in q_config else 'Redis'
        
        if workers < 1:
            self.warnings.append("DJANGO_Q_WORKERS should be at least 1")
        elif workers > 10:
            self.warnings.append("DJANGO_Q_WORKERS is high - ensure sufficient resources")
        else:
            if self.verbose:
                self.info.append(f"Django-Q workers: {workers}")
        
        self.info.append(f"Django-Q broker: {broker} (Redis requires USE_REDIS_CACHE=True)")

    def _check_api_connectivity(self):
        """Check API connectivity (optional, can be slow)."""
        self.stdout.write('\n[API Connectivity Checks]')
        self.stdout.write('(This may take a few seconds...)')
        
        # Check GraphQL API connectivity
        # Note: Full authentication requires JWT tokens from login, so we only check URL reachability
        graphql_url = getattr(settings, 'APPOINTMENT360_GRAPHQL_URL', '')
        
        if graphql_url:
            try:
                with httpx.Client(timeout=5) as client:
                    # Try a simple health check query (may require auth, but we're checking connectivity)
                    response = client.post(
                        graphql_url,
                        json={'query': '{ __typename }'},
                        headers={'Content-Type': 'application/json'}
                    )
                    # Accept any response (200, 400, 401) as "reachable"
                    # 401 means auth required, which is expected
                    if response.status_code in [200, 400, 401]:
                        if self.verbose:
                            self.info.append("✓ GraphQL API is reachable")
                    else:
                        self.warnings.append(f"GraphQL API returned unexpected status {response.status_code}")
            except httpx.TimeoutException:
                self.warnings.append("GraphQL API connection timeout - check URL and network")
            except Exception as e:
                self.warnings.append(f"GraphQL API connectivity check failed: {str(e)}")
        
    def _report_results(self):
        """Report validation results."""
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write('Validation Results')
        self.stdout.write('=' * 70)
        
        # Errors
        if self.errors:
            self.stdout.write(self.style.ERROR(f'\n❌ ERRORS ({len(self.errors)}):'))
            for error in self.errors:
                self.stdout.write(self.style.ERROR(f'  ✗ {error}'))
        
        # Warnings
        if self.warnings:
            self.stdout.write(self.style.WARNING(f'\n⚠️  WARNINGS ({len(self.warnings)}):'))
            for warning in self.warnings:
                self.stdout.write(self.style.WARNING(f'  ⚠ {warning}'))
        
        # Info (only if verbose)
        if self.verbose and self.info:
            self.stdout.write(self.style.SUCCESS(f'\nℹ️  INFO ({len(self.info)}):'))
            for info in self.info:
                self.stdout.write(f'  ℹ {info}')
        
        # Summary
        self.stdout.write('\n' + '-' * 70)
        if self.errors:
            self.stdout.write(self.style.ERROR(f'\n❌ Validation FAILED with {len(self.errors)} error(s)'))
            self.stdout.write(self.style.ERROR('Please fix the errors above before proceeding.'))
        elif self.warnings:
            self.stdout.write(self.style.WARNING(f'\n⚠️  Validation completed with {len(self.warnings)} warning(s)'))
            self.stdout.write(self.style.SUCCESS('No critical errors found, but review warnings above.'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ All configuration looks good!'))
        
        # Storage strategy summary
        self.stdout.write('\n' + '-' * 70)
        self.stdout.write('Storage Strategy Summary:')
        
        use_local = getattr(settings, 'USE_LOCAL_JSON_FILES', True)
        has_s3 = bool(getattr(settings, 'AWS_ACCESS_KEY_ID', ''))
        has_graphql = bool(getattr(settings, 'APPOINTMENT360_GRAPHQL_URL', ''))
        
        strategy_parts = []
        if use_local:
            strategy_parts.append('Local JSON (primary)')
        if has_s3:
            strategy_parts.append('S3 (fallback)')
        if has_graphql:
            strategy_parts.append('GraphQL (fallback)')
        
        if strategy_parts:
            self.stdout.write(f"  Strategy: {' → '.join(strategy_parts)}")
        else:
            self.stdout.write(self.style.WARNING("  ⚠ No storage strategy configured!"))
        
        # Cache summary
        caches = getattr(settings, 'CACHES', {})
        default_backend = caches.get('default', {}).get('BACKEND', '')
        cache_name = 'Redis' if 'redis' in default_backend.lower() else 'LocMemCache'
        self.stdout.write(f"  Cache: {cache_name} (set USE_REDIS_CACHE=True for Redis)")
        
        self.stdout.write('=' * 70 + '\n')
