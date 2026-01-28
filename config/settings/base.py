"""
Base Django settings for docsai project.

This file contains all common settings shared across all environments.
Environment-specific settings are in development.py, production.py, and testing.py.
"""

import os
import mimetypes
from pathlib import Path
from dotenv import load_dotenv

# Fix MIME types for Windows
mimetypes.add_type("text/css", ".css", True)
mimetypes.add_type("text/javascript", ".js", True)

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
# Override in environment-specific settings
DEBUG = False

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party apps
    'rest_framework',
    'drf_spectacular',  # OpenAPI 3.0 schema generation
    'corsheaders',
    'django_q',  # Django-Q2 for task queue
    'storages',  # Django-storages for S3 storage backend
    # Project apps
    'apps.core',
    'apps.api',  # API Gateway
    'apps.documentation',
    'apps.analytics',
    'apps.ai_agent',
    'apps.codebase',
    'apps.tasks',
    'apps.media',
    'apps.graph',
    'apps.test_runner',
    'apps.accessibility',
    'apps.roadmap',
    'apps.postman',
    'apps.templates',
    'apps.durgasman',
    'apps.architecture',
    'apps.database',
    'apps.json_store',
    'apps.operations',
    'apps.page_builder',
    'apps.knowledge',
    'apps.durgasflow',  # Workflow automation (n8n-like)
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.core.middleware.auth_middleware.Appointment360AuthMiddleware',
    'apps.core.middleware.super_admin_middleware.SuperAdminMiddleware',  # SuperAdmin-only access
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.security_middleware.SecurityHeadersMiddleware',  # Custom security headers
    'apps.documentation.middleware.api_tracking_middleware.ApiTrackingMiddleware',
    'apps.core.middleware.error_handler.ErrorHandlerMiddleware',
]

ROOT_URLCONF = 'docsai.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.navigation',
                'apps.core.context_processors.theme',
            ],
        },
    },
]

WSGI_APPLICATION = 'docsai.wsgi.application'

# Database
# Use SQLite by default for development, PostgreSQL for production
DATABASE_ENGINE = os.getenv('DATABASE_ENGINE', 'sqlite').lower()

if DATABASE_ENGINE == 'postgresql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DATABASE_NAME', 'docsai'),
            'USER': os.getenv('DATABASE_USER', 'postgres'),
            'PASSWORD': os.getenv('DATABASE_PASSWORD', ''),
            'HOST': os.getenv('DATABASE_HOST', 'localhost'),
            'PORT': os.getenv('DATABASE_PORT', '5432'),
            'OPTIONS': {
                'connect_timeout': 10,
            },
            'ATOMIC_REQUESTS': True,
            'CONN_MAX_AGE': 600,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = os.getenv('LANGUAGE_CODE', 'en-us')
TIME_ZONE = os.getenv('TIME_ZONE', 'UTC')
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files (User uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# File upload limits
DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.getenv('DATA_UPLOAD_MAX_MEMORY_SIZE', '10485760'))  # 10MB default
FILE_UPLOAD_MAX_MEMORY_SIZE = int(os.getenv('FILE_UPLOAD_MAX_MEMORY_SIZE', '10485760'))  # 10MB default
DATA_UPLOAD_MAX_NUMBER_FIELDS = int(os.getenv('DATA_UPLOAD_MAX_NUMBER_FIELDS', '1000'))

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'core.User'

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'apps.core.auth.appointment360_backend.Appointment360Backend',
    'django.contrib.auth.backends.ModelBackend',
]

# Redis Configuration (OPTIONAL - Currently using Local Memory Cache)
# Uncomment and set USE_REDIS_CACHE=True to use Redis instead of LocMemCache.
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB = int(os.getenv('REDIS_DB', '0'))
REDIS_URL = os.getenv('REDIS_URL', None)
USE_REDIS_CACHE = os.getenv('USE_REDIS_CACHE', 'False').lower() == 'true'

# Django-Q Configuration - Uses ORM (database) by default; Redis if USE_REDIS_CACHE
_q_cluster_config = {
    'name': 'docsai',
    'workers': int(os.getenv('DJANGO_Q_WORKERS', '4')),
    'recycle': int(os.getenv('DJANGO_Q_RECYCLE', '500')),
    'timeout': int(os.getenv('DJANGO_Q_TIMEOUT', '300')),
    'retry': int(os.getenv('DJANGO_Q_RETRY', '300')),
    'queue_limit': int(os.getenv('DJANGO_Q_QUEUE_LIMIT', '50')),
    'bulk': int(os.getenv('DJANGO_Q_BULK', '10')),
    'sync': False,
    'catch_up': False,
    'save_limit': int(os.getenv('DJANGO_Q_SAVE_LIMIT', '250')),
    'error_limit': int(os.getenv('DJANGO_Q_ERROR_LIMIT', '250')),
}

if USE_REDIS_CACHE and (REDIS_URL or (REDIS_HOST and REDIS_PORT)):
    if REDIS_URL:
        _q_cluster_config['redis'] = REDIS_URL
    else:
        _q_cluster_config['redis'] = {
            'host': REDIS_HOST,
            'port': REDIS_PORT,
            'db': REDIS_DB,
        }
else:
    _q_cluster_config['orm'] = 'default'

Q_CLUSTER = _q_cluster_config

# Django cache - Local Memory Cache by default (per-process, no Redis required)
# Set USE_REDIS_CACHE=True and configure Redis to use Redis instead.
_redis_location = None
if USE_REDIS_CACHE and (REDIS_URL or (REDIS_HOST and REDIS_PORT)):
    _redis_location = REDIS_URL or f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

if _redis_location:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": _redis_location,
            "OPTIONS": {
                "socket_connect_timeout": 5,
                "socket_keepalive": True,
            },
            "KEY_PREFIX": "docsai",
            "TIMEOUT": 300,  # 5 minutes default
        },
        "long_term": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": _redis_location,
            "OPTIONS": {
                "socket_connect_timeout": 5,
                "socket_keepalive": True,
            },
            "KEY_PREFIX": "docsai_long",
            "TIMEOUT": 3600,  # 1 hour for long-term cache
        },
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "docsai-default",
            "TIMEOUT": 300,  # 5 minutes default
        }
    }

# Local JSON Files Configuration
USE_LOCAL_JSON_FILES = os.getenv('USE_LOCAL_JSON_FILES', 'True').lower() == 'true'

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'contact360docs')
S3_DATA_PREFIX = os.getenv('S3_DATA_PREFIX', 'data/')
S3_DOCUMENTATION_PREFIX = os.getenv('S3_DOCUMENTATION_PREFIX', 'documentation/')

# Lambda API Configuration
# LAMBDA_DOCUMENTATION_API_* removed - services now use local/S3/GraphQL directly
# Only AI API settings remain (used by AI agent)
LAMBDA_AI_API_URL = os.getenv('LAMBDA_AI_API_URL', 'https://aziwa531nl.execute-api.us-east-1.amazonaws.com')
LAMBDA_AI_API_KEY = os.getenv('LAMBDA_AI_API_KEY', '')

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# Google Gemini AI Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

# Appointment360 GraphQL Configuration
APPOINTMENT360_GRAPHQL_URL = os.getenv('APPOINTMENT360_GRAPHQL_URL', 'http://34.229.94.175/graphql')
GRAPHQL_TIMEOUT = int(os.getenv('GRAPHQL_TIMEOUT', '30'))

# GraphQL Configuration Validation
def validate_graphql_config():
    """Validate GraphQL configuration settings."""
    errors = []
    
    if APPOINTMENT360_GRAPHQL_URL:
        if not (APPOINTMENT360_GRAPHQL_URL.startswith('http://') or 
                APPOINTMENT360_GRAPHQL_URL.startswith('https://')):
            errors.append(
                f"APPOINTMENT360_GRAPHQL_URL must start with http:// or https://. "
                f"Got: {APPOINTMENT360_GRAPHQL_URL}"
            )
    
    if GRAPHQL_TIMEOUT < 1 or GRAPHQL_TIMEOUT > 300:
        errors.append(
            f"GRAPHQL_TIMEOUT must be between 1 and 300 seconds. "
            f"Got: {GRAPHQL_TIMEOUT}"
        )
    
    return len(errors) == 0, errors

GRAPHQL_ENABLED = bool(APPOINTMENT360_GRAPHQL_URL)
GRAPHQL_USE_FALLBACK = not GRAPHQL_ENABLED
GRAPHQL_AUTH_ENABLED = os.getenv('GRAPHQL_AUTH_ENABLED', 'True').lower() == 'true'
S3_AUTH_STORAGE_ENABLED = os.getenv('S3_AUTH_STORAGE_ENABLED', 'False').lower() == 'true'

# SuperAdmin Middleware Configuration
SUPER_ADMIN_ONLY_ENABLED = os.getenv('SUPER_ADMIN_ONLY_ENABLED', 'True').lower() == 'true'
SUPER_ADMIN_CACHE_TTL = int(os.getenv('SUPER_ADMIN_CACHE_TTL', '300'))  # 5 minutes default

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 1 day
SESSION_COOKIE_HTTPONLY = True
# SESSION_COOKIE_SECURE set in environment-specific settings
SESSION_SAVE_EVERY_REQUEST = True

# Login/Logout URLs
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

# Email Configuration (override in environment-specific settings)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(parents=True, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'structured': {
            'format': '{levelname} {asctime} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'structured',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django-error.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
            'level': 'ERROR',
        },
        's3_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 's3.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': LOG_LEVEL,
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'apps.core.services.s3_service': {
            'handlers': ['console', 's3_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'botocore': {'level': 'WARNING', 'propagate': False},
        'boto3': {'level': 'WARNING', 'propagate': False},
        'urllib3': {'level': 'WARNING', 'propagate': False},
    },
}

# Django REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'apps.core.pagination.StandardResultsSetPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'EXCEPTION_HANDLER': 'apps.api.exception_handlers.custom_exception_handler',
    # OpenAPI Schema Configuration
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# drf-spectacular Configuration
SPECTACULAR_SETTINGS = {
    'TITLE': 'DocsAI API',
    'DESCRIPTION': (
        'REST API v1 for DocsAI: 110 GET endpoints (pages, endpoints, relationships, postman, index) '
        'plus health and dashboard. Backed by UnifiedStorage (Local → S3 → GraphQL). '
        'See /api/v1/ for all routes.'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': r'/api/v1/',
    'SERVERS': [
        {'url': 'http://127.0.0.1:8000', 'description': 'Local development'},
    ],
    'COMPONENT_SPLIT_REQUEST': True,
    'COMPONENT_NO_READ_ONLY_REQUIRED': True,
    # API Versioning
    'SCHEMA_PATH_PREFIX_TRIM': True,
    # Authentication
    'AUTHENTICATION_WHITELIST': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    # Tags (for OpenAPI docs grouping)
    'TAGS': [
        {'name': 'Health', 'description': 'Service info and health checks'},
        {'name': 'Pages', 'description': 'Documentation pages (20 GETs)'},
        {'name': 'Endpoints', 'description': 'API endpoints (28 GETs)'},
        {'name': 'Relationships', 'description': 'Page–endpoint relationships (38 GETs)'},
        {'name': 'Postman', 'description': 'Postman configurations (14 GETs)'},
        {'name': 'Index', 'description': 'Index read and validate (8 GETs)'},
        {'name': 'Dashboard', 'description': 'Dashboard pagination (4 GETs)'},
        {'name': 'Media', 'description': 'Media file management'},
        {'name': 'Operations', 'description': 'System operations'},
    ],
    # Response examples
    'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],
    'SERVE_AUTHENTICATION': None,  # Allow unauthenticated access to schema/docs
    # Swagger UI settings
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'displayOperationId': True,
        'defaultModelsExpandDepth': 2,
        'defaultModelExpandDepth': 2,
        'docExpansion': 'none',
        'filter': True,
        'showExtensions': True,
        'showCommonExtensions': True,
    },
    # Redoc settings
    'REDOC_UI_SETTINGS': {
        'hideDownloadButton': False,
        'hideHostname': False,
        'hideLoading': False,
        'hideSingleRequestSample': False,
        'expandResponses': '200,201',
        'pathInMiddlePanel': True,
        'requiredPropsFirst': True,
        'sortPropsAlphabetically': False,
        'payloadSampleIdx': 0,
        'theme': {
            'colors': {
                'primary': {
                    'main': '#32329f'
                }
            }
        }
    },
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

CORS_ALLOW_CREDENTIALS = True

# API request tracking (for /api/docs/ per-endpoint statistics)
API_TRACKING_ENABLED = True
API_TRACKING_PATH_PREFIX = '/api/v1/'

# ============================================================================
# Startup Configuration Validation
# ============================================================================
def validate_startup_config():
    """
    Validate critical configuration settings on startup.
    Logs warnings for non-critical issues, raises errors for critical problems.
    """
    import warnings
    import urllib.parse
    from pathlib import Path
    
    errors = []
    warnings_list = []
    
    # Critical: SECRET_KEY validation
    if not SECRET_KEY or SECRET_KEY == 'django-insecure-change-this-in-production':
        errors.append(
            "SECRET_KEY is required and must be changed from default. "
            "Generate one with: python -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\""
        )
    elif len(SECRET_KEY) < 50:
        warnings_list.append(
            f"SECRET_KEY is shorter than recommended (current: {len(SECRET_KEY)} chars, recommended: 50+). "
            "Consider generating a longer key for better security."
        )
    
    # Warning: ALLOWED_HOSTS empty
    if not ALLOWED_HOSTS or ALLOWED_HOSTS == ['']:
        warnings_list.append(
            "ALLOWED_HOSTS is empty. This may cause issues in production. "
            "Set ALLOWED_HOSTS in your .env file."
        )
    
    # AWS S3 configuration validation
    if AWS_ACCESS_KEY_ID:
        if not AWS_SECRET_ACCESS_KEY:
            errors.append(
                "AWS_ACCESS_KEY_ID is set but AWS_SECRET_ACCESS_KEY is missing. "
                "Both are required for S3 operations."
            )
        if not S3_BUCKET_NAME:
            warnings_list.append("S3_BUCKET_NAME is not set. S3 operations may fail.")
    else:
        warnings_list.append(
            "AWS S3 not configured. S3 fallback will not work. "
            "Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in .env if needed."
        )
    
    # GraphQL URL validation
    if APPOINTMENT360_GRAPHQL_URL:
        if not (APPOINTMENT360_GRAPHQL_URL.startswith('http://') or 
                APPOINTMENT360_GRAPHQL_URL.startswith('https://')):
            errors.append(
                f"APPOINTMENT360_GRAPHQL_URL must start with http:// or https://. "
                f"Got: {APPOINTMENT360_GRAPHQL_URL}"
            )
        else:
            try:
                parsed = urllib.parse.urlparse(APPOINTMENT360_GRAPHQL_URL)
                if not parsed.netloc:
                    errors.append(f"Invalid APPOINTMENT360_GRAPHQL_URL format: {APPOINTMENT360_GRAPHQL_URL}")
            except Exception as e:
                errors.append(f"Invalid APPOINTMENT360_GRAPHQL_URL: {e}")
        
        # Note: GraphQL authentication now uses JWT tokens from authenticated sessions
        # No API key is required - tokens are extracted from request cookies/headers
    
    # Lambda API URL validation
    # LAMBDA_DOCUMENTATION_API_* validation removed - no longer used
    
    if LAMBDA_AI_API_URL:
        if not (LAMBDA_AI_API_URL.startswith('http://') or LAMBDA_AI_API_URL.startswith('https://')):
            errors.append(
                f"LAMBDA_AI_API_URL must start with http:// or https://. Got: {LAMBDA_AI_API_URL}"
            )
        if not LAMBDA_AI_API_KEY:
            warnings_list.append("LAMBDA_AI_API_KEY is missing. Lambda AI API calls may fail.")
    
    # AI service validation
    openai_key = os.getenv('OPENAI_API_KEY', '')
    if openai_key and ('your-' in openai_key.lower() or 'placeholder' in openai_key.lower()):
        warnings_list.append(
            "OPENAI_API_KEY appears to be a placeholder value. "
            "Replace with actual API key or remove if not using OpenAI."
        )
    
    has_ai = bool(openai_key and 'your-' not in openai_key.lower()) or \
             bool(os.getenv('GEMINI_API_KEY', '')) or \
             bool(LAMBDA_AI_API_KEY)
    
    if not has_ai:
        warnings_list.append(
            "No AI service configured (OpenAI, Gemini, or Lambda AI). "
            "AI features will not work. Configure at least one AI service."
        )
    
    # Local storage validation
    if USE_LOCAL_JSON_FILES:
        if not MEDIA_ROOT:
            warnings_list.append("MEDIA_ROOT not configured - local JSON files may not work")
        elif not Path(MEDIA_ROOT).exists():
            warnings_list.append(
                f"MEDIA_ROOT directory does not exist: {MEDIA_ROOT}. "
                f"Create it with: mkdir -p {MEDIA_ROOT}"
            )
    
    # Database validation
    if DATABASE_ENGINE == 'postgresql':
        db_config = DATABASES.get('default', {})
        if not db_config.get('NAME'):
            errors.append("PostgreSQL DATABASE_NAME is required when DATABASE_ENGINE=postgresql")
        if not db_config.get('USER'):
            errors.append("PostgreSQL DATABASE_USER is required when DATABASE_ENGINE=postgresql")
    
    # Report errors (critical - will prevent startup in strict mode)
    if errors:
        error_msg = "\n".join([f"  ✗ {error}" for error in errors])
        full_error = (
            "\n" + "=" * 70 + "\n"
            "CRITICAL CONFIGURATION ERRORS DETECTED\n"
            "=" * 70 + "\n" +
            error_msg + "\n" +
            "=" * 70 + "\n"
            "Please fix these errors before starting the application.\n"
            "Run 'python manage.py validate_env' for detailed validation.\n"
            "See docs/ENV_VARIABLES.md for configuration help.\n"
        )
        
        if not DEBUG or os.getenv('STRICT_CONFIG_VALIDATION', 'False').lower() == 'true':
            raise ValueError(full_error)
        else:
            warnings.warn(full_error, UserWarning)
    
    # Report warnings (non-critical)
    if warnings_list:
        for warning in warnings_list:
            warnings.warn(f"Configuration Warning: {warning}", UserWarning)
    
    return len(errors) == 0

# Run validation on startup (only in main process, not in reloader)
if os.environ.get("RUN_MAIN") == "true":
    try:
        validate_startup_config()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Startup validation failed: {e}", exc_info=True)
