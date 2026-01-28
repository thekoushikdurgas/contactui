# Advanced Production-Ready Django Project Structure

## Complete File Structure with Best Practices

```
my_project/
├── manage.py
├── README.md
├── .gitignore
├── .env.example
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── docker-compose.yml
├── Dockerfile
├── Makefile
│
├── config/
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   │   ├── testing.py
│   │   └── local.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   ├── celery.py
│   └── middleware.py
│
├── apps/
│   ├── __init__.py
│   ├── core/
│   │   ├── migrations/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── utils.py
│   │   ├── constants.py
│   │   ├── exceptions.py
│   │   ├── serializers.py
│   │   ├── managers.py
│   │   ├── signals.py
│   │   ├── middleware.py
│   │   ├── decorators.py
│   │   ├── permissions.py
│   │   ├── pagination.py
│   │   ├── filters.py
│   │   ├── throttles.py
│   │   ├── authentication.py
│   │   ├── validators.py
│   │   ├── management/
│   │   │   ├── commands/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── seed_db.py
│   │   │   │   └── cleanup_expired.py
│   │   │   └── __init__.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_models.py
│   │       └── test_utils.py
│   │
│   ├── users/
│   │   ├── migrations/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── viewsets.py
│   │   ├── urls.py
│   │   ├── services.py
│   │   ├── tasks.py
│   │   ├── signals.py
│   │   ├── permissions.py
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   ├── test_models.py
│   │   │   ├── test_views.py
│   │   │   ├── test_serializers.py
│   │   │   └── factories.py
│   │   ├── forms.py
│   │   ├── templates/
│   │   │   └── users/
│   │   │       ├── profile.html
│   │   │       └── registration.html
│   │   └── static/
│   │       └── users/
│   │           ├── css/
│   │           └── js/
│   │
│   ├── products/
│   │   ├── migrations/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── serializers.py
│   │   ├── viewsets.py
│   │   ├── urls.py
│   │   ├── services.py
│   │   ├── tasks.py
│   │   ├── signals.py
│   │   ├── filters.py
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   ├── test_models.py
│   │   │   ├── test_viewsets.py
│   │   │   └── factories.py
│   │   ├── templates/
│   │   │   └── products/
│   │   │       ├── list.html
│   │   │       └── detail.html
│   │   └── static/
│   │       └── products/
│   │           ├── css/
│   │           └── js/
│   │
│   ├── notifications/
│   │   ├── migrations/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── consumers.py
│   │   ├── routing.py
│   │   ├── services.py
│   │   ├── tasks.py
│   │   └── views.py
│   │
│   └── api/
│       ├── __init__.py
│       ├── urls.py
│       ├── serializers.py
│       ├── views.py
│       ├── permissions.py
│       ├── throttles.py
│       └── pagination.py
│
├── templates/
│   ├── base.html
│   ├── layout.html
│   ├── errors/
│   │   ├── 404.html
│   │   ├── 500.html
│   │   └── 503.html
│   └── includes/
│       ├── navbar.html
│       ├── footer.html
│       ├── pagination.html
│       └── messages.html
│
├── static/
│   ├── css/
│   │   ├── base.css
│   │   ├── styles.css
│   │   └── responsive.css
│   ├── js/
│   │   ├── base.js
│   │   ├── utils.js
│   │   ├── api-client.js
│   │   └── websocket-client.js
│   └── images/
│       └── logo.png
│
├── media/
│   └── uploads/
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── factories.py
│   ├── fixtures.py
│   ├── test_api.py
│   ├── test_integration.py
│   └── test_e2e.py
│
├── logs/
│   ├── .gitkeep
│   ├── django.log
│   ├── error.log
│   └── celery.log
│
├── scripts/
│   ├── entrypoint.sh
│   ├── migrate.sh
│   ├── seed_db.sh
│   ├── backup.sh
│   └── deploy.sh
│
├── docs/
│   ├── API.md
│   ├── SETUP.md
│   ├── DEPLOYMENT.md
│   ├── ARCHITECTURE.md
│   └── CONTRIBUTING.md
│
└── staticfiles/
```

---

## 1. Core Configuration Files

### `config/settings/base.py` - Base Settings

```python
from pathlib import Path
import os
from dotenv import load_dotenv
import logging

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Django Apps
DJANGO_APPS = [
    'daphne',  # For async support and channels
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

# Third-party Apps
THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'django_filters',
    'corsheaders',
    'channels',
    'drf_spectacular',  # API documentation
    'django_celery_beat',
    'django_celery_results',
]

# Local Apps
LOCAL_APPS = [
    'apps.core',
    'apps.users',
    'apps.products',
    'apps.notifications',
    'apps.api',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'config.middleware.CustomExceptionMiddleware',
]

ROOT_URLCONF = 'config.urls'

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
            ],
        },
    },
]

# Database
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.getenv('DB_NAME', 'mydb'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'password'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'ATOMIC_REQUESTS': True,
        'CONN_MAX_AGE': 600,
    }
}

# Authentication
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'apps.core.pagination.StandardPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# CORS
CORS_ALLOWED_ORIGINS = os.getenv(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:3000,http://localhost:8000'
).split(',')
CORS_ALLOW_CREDENTIALS = True

# JWT Configuration
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'ALGORITHM': 'HS256',
}

# Caching
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {'max_connections': 50},
        }
    }
}

# Session
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Celery
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://127.0.0.1:6379/2')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# Celery Beat Schedule
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'cleanup-expired-tokens': {
        'task': 'apps.core.tasks.cleanup_expired_tokens',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    'sync-external-data': {
        'task': 'apps.products.tasks.sync_external_products',
        'schedule': timedelta(hours=6),
    },
}

# Channels
ASGI_APPLICATION = 'config.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [(os.getenv('REDIS_HOST', '127.0.0.1'), int(os.getenv('REDIS_PORT', 6379)))],
        },
    },
}

# Static Files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media Files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'error.log',
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file', 'error_file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Default Primary Key
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
```

### `config/settings/development.py`

```python
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

# Install Debug Toolbar in development
INSTALLED_APPS += ['debug_toolbar', 'django_extensions']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1', 'localhost']

# Email Backend (Console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging
LOGGING['handlers']['console']['level'] = 'DEBUG'
LOGGING['root']['level'] = 'DEBUG'
```

### `config/settings/production.py`

```python
from .base import *

DEBUG = False

# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_SECURITY_POLICY = {
    'default-src': ("'self'",),
    'script-src': ("'self'",),
}

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')

# Logging
LOGGING['handlers']['console']['level'] = 'WARNING'
LOGGING['root']['level'] = 'INFO'
```

---

## 2. Core App Files

### `apps/core/models.py` - Abstract Base Models

```python
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser

class TimeStampedModel(models.Model):
    """Abstract base model with timestamp fields"""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']

class ActiveModel(models.Model):
    """Abstract model with is_active field"""
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        abstract = True

class SoftDeleteModel(models.Model):
    """Abstract model with soft delete functionality"""
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        abstract = True

    def soft_delete(self):
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.save()

class UUIDModel(models.Model):
    """Abstract model with UUID primary key"""
    import uuid
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True

class BaseModel(TimeStampedModel, ActiveModel, UUIDModel):
    """Complete base model combining all features"""
    class Meta:
        abstract = True
        ordering = ['-created_at']

class CustomUser(AbstractUser):
    """Extended User model"""
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-created_at']
```

### `apps/core/managers.py` - Custom Managers

```python
from django.db import models
from django.utils import timezone

class ActiveManager(models.Manager):
    """Manager for active objects only"""
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

class SoftDeleteManager(models.Manager):
    """Manager for non-deleted objects"""
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)
    
    def deleted(self):
        return super().get_queryset().filter(deleted_at__isnull=False)

class ArchiveManager(models.Manager):
    """Manager with archive functionality"""
    def archived(self):
        return self.filter(archived=True)
    
    def active(self):
        return self.filter(archived=False)
```

### `apps/core/serializers.py` - Base Serializers

```python
from rest_framework import serializers

class BaseSerializer(serializers.ModelSerializer):
    """Base serializer with common functionality"""
    created_at = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')
    updated_at = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')

    class Meta:
        fields = ('id', 'created_at', 'updated_at')

class DynamicFieldsSerializer(serializers.ModelSerializer):
    """Serializer that allows dynamic field selection"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        request = self.context.get('request')
        if request:
            fields = request.query_params.get('fields')
            if fields:
                allowed = set(fields.split(','))
                existing = set(self.fields.keys())
                for field_name in existing - allowed:
                    self.fields.pop(field_name)
```

### `apps/core/signals.py` - Django Signals

```python
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.core.mail import send_mail
from apps.users.models import CustomUser

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """Create user profile on user creation"""
    if created:
        # Send welcome email
        send_mail(
            'Welcome to our platform',
            f'Hello {instance.first_name}, welcome!',
            'noreply@example.com',
            [instance.email],
        )
        # Clear cache
        cache.delete(f'user_{instance.id}')

@receiver(post_save, sender=CustomUser)
def update_user_cache(sender, instance, **kwargs):
    """Update user cache on save"""
    cache.set(f'user_{instance.id}', instance, timeout=3600)
```

### `apps/core/permissions.py` - DRF Permissions

```python
from rest_framework import permissions

class IsOwner(permissions.BasePermission):
    """Permission to check if user is owner"""
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user

class IsAdmin(permissions.BasePermission):
    """Permission to check if user is admin"""
    def has_permission(self, request, view):
        return request.user and request.user.is_staff

class IsOwnerOrReadOnly(permissions.BasePermission):
    """Allow owner to edit, others can read"""
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user
```

### `apps/core/pagination.py` - Pagination

```python
from rest_framework.pagination import PageNumberPagination

class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    page_size_query_description = 'Number of results per page'
    max_page_size = 100
    page_query_description = 'Page number'

class LargePagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100

class SmallPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50
```

### `apps/core/throttles.py` - Custom Throttles

```python
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class BurstRateThrottle(UserRateThrottle):
    scope = 'burst'

class SustainedRateThrottle(UserRateThrottle):
    scope = 'sustained'

class CustomAnonThrottle(AnonRateThrottle):
    scope = 'anon'
```

### `apps/core/filters.py` - Custom Filters

```python
import django_filters
from django_filters.rest_framework import DjangoFilterBackend

class BaseFilterSet(django_filters.FilterSet):
    """Base filter with common fields"""
    created_at_from = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte'
    )
    created_at_to = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte'
    )
    is_active = django_filters.BooleanFilter()
    
    class Meta:
        fields = ['is_active']
```

### `apps/core/tasks.py` - Celery Tasks

```python
from celery import shared_task
from django.utils import timezone
from django.contrib.auth.models import Token
import logging

logger = logging.getLogger(__name__)

@shared_task
def cleanup_expired_tokens():
    """Clean up expired authentication tokens"""
    try:
        deleted_count, _ = Token.objects.filter(
            created_at__lt=timezone.now() - timezone.timedelta(days=30)
        ).delete()
        logger.info(f'Cleaned up {deleted_count} expired tokens')
        return {'status': 'success', 'deleted': deleted_count}
    except Exception as e:
        logger.error(f'Error cleaning up tokens: {str(e)}')
        return {'status': 'error', 'error': str(e)}

@shared_task(bind=True, max_retries=3)
def send_async_email(self, email_id):
    """Send email asynchronously with retry logic"""
    try:
        # email logic here
        pass
    except Exception as exc:
        logger.error(f'Failed to send email {email_id}: {str(exc)}')
        # Exponential backoff retry
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

### `apps/core/decorators.py` - Decorators

```python
from functools import wraps
from django.core.cache import cache
from rest_framework.response import Response
from django.utils.decorators import method_decorator

def cache_response(timeout=300):
    """Decorator to cache view response"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            cache_key = f"{view_func.__name__}_{request.user.id}_{request.get_full_path()}"
            cached_response = cache.get(cache_key)
            if cached_response:
                return cached_response
            response = view_func(request, *args, **kwargs)
            cache.set(cache_key, response, timeout)
            return response
        return wrapper
    return decorator

def rate_limit(rate):
    """Decorator for rate limiting"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Rate limiting logic
            return func(*args, **kwargs)
        return wrapper
    return decorator

def log_action(action_type):
    """Decorator to log user actions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.info(f'Action: {action_type}')
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

---

## 3. Users App Example

### `apps/users/models.py`

```python
from django.db import models
from apps.core.models import BaseModel, CustomUser

class UserProfile(BaseModel):
    """Extended user profile"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    website = models.URLField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    verified = models.BooleanField(default=False)
    notifications_enabled = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f'{self.user.get_full_name()} Profile'
```

### `apps/users/serializers.py`

```python
from rest_framework import serializers
from apps.core.serializers import BaseSerializer
from apps.users.models import CustomUser, UserProfile

class UserProfileSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = UserProfile
        fields = BaseSerializer.Meta.fields + [
            'user', 'phone', 'bio', 'website', 'location', 'verified'
        ]

class CustomUserSerializer(BaseSerializer):
    profile = UserProfileSerializer(read_only=True)
    
    class Meta(BaseSerializer.Meta):
        model = CustomUser
        fields = BaseSerializer.Meta.fields + [
            'username', 'email', 'first_name', 'last_name', 'profile'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'profile']
```

### `apps/users/services.py` - Business Logic Layer

```python
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class UserService:
    """Service layer for user operations"""
    
    @staticmethod
    @transaction.atomic
    def create_user(email, password, first_name, last_name, **kwargs):
        """Create user with profile"""
        if User.objects.filter(email=email).exists():
            raise ValidationError('Email already exists')
        
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            username=email.split('@')[0],
        )
        return user
    
    @staticmethod
    def update_user_profile(user, **kwargs):
        """Update user profile"""
        profile = user.profile
        for field, value in kwargs.items():
            if hasattr(profile, field):
                setattr(profile, field, value)
        profile.save()
        return profile
```

### `apps/users/tasks.py` - Async Tasks

```python
from celery import shared_task
from django.core.mail import send_mail
from apps.users.models import CustomUser
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_welcome_email(user_id):
    """Send welcome email to new user"""
    try:
        user = CustomUser.objects.get(id=user_id)
        send_mail(
            'Welcome!',
            f'Hello {user.first_name}, welcome to our platform!',
            'noreply@example.com',
            [user.email],
        )
        logger.info(f'Welcome email sent to {user.email}')
    except CustomUser.DoesNotExist:
        logger.error(f'User {user_id} not found')

@shared_task
def send_password_reset_email(user_id, reset_token):
    """Send password reset email"""
    try:
        user = CustomUser.objects.get(id=user_id)
        send_mail(
            'Password Reset',
            f'Click here to reset: http://example.com/reset/{reset_token}',
            'noreply@example.com',
            [user.email],
        )
    except CustomUser.DoesNotExist:
        logger.error(f'User {user_id} not found')
```

### `apps/users/viewsets.py` - DRF ViewSets

```python
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.users.models import CustomUser, UserProfile
from apps.users.serializers import CustomUserSerializer, UserProfileSerializer
from apps.users.services import UserService
from apps.users.tasks import send_welcome_email
from apps.core.permissions import IsOwner

class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for user operations"""
    queryset = CustomUser.objects.prefetch_related('profile')
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['email', 'first_name', 'last_name']
    ordering_fields = ['created_at', 'email']
    ordering = ['-created_at']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return CustomUser.objects.all()
        return CustomUser.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Get current user"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def create_user(self, request):
        """Create new user"""
        try:
            user = UserService.create_user(**request.data)
            send_welcome_email.delay(user.id)
            return Response(
                CustomUserSerializer(user).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def update_profile(self, request):
        """Update user profile"""
        profile = UserService.update_user_profile(request.user, **request.data)
        return Response(UserProfileSerializer(profile).data)
```

---

## 4. Advanced Features

### `apps/notifications/consumers.py` - WebSocket Consumers

```python
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from asgiref.sync import sync_to_async
import json

class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for real-time notifications"""
    
    async def connect(self):
        self.user = self.scope['user']
        
        if self.user.is_anonymous:
            await self.close(code=4401)
            return
        
        self.group_name = f"notifications_{self.user.id}"
        
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    async def receive_json(self, content):
        message_type = content.get('type')
        
        if message_type == 'mark_as_read':
            await self.mark_notification_as_read(content.get('notification_id'))
    
    async def notify(self, event):
        await self.send_json({
            'type': 'notification',
            'data': event['data']
        })
    
    @database_sync_to_async
    def mark_notification_as_read(self, notification_id):
        # Mark notification as read in DB
        pass
```

### `apps/notifications/routing.py`

```python
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
]
```

### `config/asgi.py` - ASGI Configuration

```python
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

django_asgi_app = get_asgi_application()

from apps.notifications.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
```

### `config/celery.py` - Celery Configuration

```python
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

app = Celery('my_project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
```

---

## 5. Requirements Files

### `requirements.txt`

```
Django==4.2.0
djangorestframework==3.14.0
django-filter==23.1
django-cors-headers==3.14.0
djangorestframework-simplejwt==5.2.2
drf-spectacular==0.26.1
channels==4.0.0
channels-redis==4.1.0
celery==5.2.7
django-celery-beat==2.4.0
django-celery-results==2.5.0
redis==4.5.4
psycopg2-binary==2.9.6
django-redis==5.2.0
python-dotenv==1.0.0
Pillow==9.5.0
requests==2.31.0
```

### `Makefile`

```makefile
.PHONY: help migrate makemigrations runserver shell test lint format clean

help:
	@echo "Available commands:"
	@echo "  make migrate           - Run migrations"
	@echo "  make makemigrations    - Create migrations"
	@echo "  make runserver         - Run development server"
	@echo "  make shell             - Django shell"
	@echo "  make test              - Run tests"
	@echo "  make lint              - Run linting"
	@echo "  make format            - Format code"
	@echo "  make clean             - Clean cache and temp files"

migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations

runserver:
	python manage.py runserver

shell:
	python manage.py shell

test:
	pytest tests/

lint:
	flake8 apps/
	black --check apps/

format:
	black apps/

clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '*.egg-info' -exec rm -rf {} +
```

### `docker-compose.yml`

```yaml
version: '3.9'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: mydb
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    ports:
      - "8000:8000"
    environment:
      DEBUG: 'True'
      DB_ENGINE: django.db.backends.postgresql
      DB_NAME: mydb
      DB_USER: postgres
      DB_PASSWORD: postgres
      DB_HOST: db
      REDIS_URL: redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - .:/app

  celery:
    build: .
    command: celery -A config worker -l info
    environment:
      DEBUG: 'True'
      CELERY_BROKER_URL: redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - .:/app

  celery-beat:
    build: .
    command: celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    environment:
      CELERY_BROKER_URL: redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - .:/app

volumes:
  postgres_data:
```

---

## 6. Environment File

### `.env.example`

```bash
# Django
SECRET_KEY=your-super-secret-key-change-this
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=mydb
DB_USER=postgres
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# JWT
JWT_ALGORITHM=HS256
```

---

## 7. Testing Setup

### `tests/conftest.py` - Pytest Configuration

```python
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def authenticated_user():
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )

@pytest.fixture
def authenticated_client(api_client, authenticated_user):
    api_client.force_authenticate(user=authenticated_user)
    return api_client

@pytest.fixture
def admin_user():
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123'
    )
```

### `tests/test_api.py` - API Tests

```python
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

User = get_user_model()

@pytest.mark.django_db
def test_user_list(authenticated_client):
    response = authenticated_client.get('/api/users/')
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
def test_user_creation(api_client):
    data = {
        'email': 'newuser@example.com',
        'password': 'testpass123',
        'first_name': 'Test',
        'last_name': 'User'
    }
    response = api_client.post('/api/users/create/', data)
    assert response.status_code == status.HTTP_201_CREATED
```

---

## 8. Management Commands

### `apps/core/management/commands/seed_db.py`

```python
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from faker import Faker

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = 'Seed database with sample data'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=10)

    def handle(self, *args, **options):
        count = options['count']
        
        for _ in range(count):
            User.objects.create_user(
                username=fake.user_name(),
                email=fake.email(),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {count} users')
        )
```

---

## Key Features Implemented

✅ **Async Support** - Django 4.2+ async views and Channels WebSockets  
✅ **Celery** - Background tasks with priority queues and scheduling  
✅ **Caching** - Redis-backed caching for performance  
✅ **Real-time** - WebSocket support via Channels  
✅ **REST API** - DRF with JWT authentication  
✅ **Pagination** - Multiple pagination strategies  
✅ **Filtering** - Advanced filtering and searching  
✅ **Throttling** - Rate limiting per user/IP  
✅ **Testing** - Pytest integration with fixtures  
✅ **Logging** - Comprehensive logging setup  
✅ **Signals** - Django signals for auto-actions  
✅ **Permissions** - Custom permission classes  
✅ **Docker** - Production-ready containers  
✅ **Environment** - 12-factor app configuration  
✅ **Abstract Models** - DRY model inheritance  

---

## Quick Start Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Run Celery worker
celery -A config worker -l info

# Run Celery Beat
celery -A config beat -l info

# Run tests
pytest tests/

# Docker
docker-compose up -d
```

This structure provides enterprise-grade organization with all modern Django best practices!