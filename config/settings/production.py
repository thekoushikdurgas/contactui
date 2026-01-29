"""
Production settings for docsai project.

These settings are used when DJANGO_ENV=production
"""

from .base import *  # noqa

# Override base settings for production
DEBUG = False

# SSL/HTTPS: Set SECURE_SSL_REDIRECT=True only when serving over HTTPS (domain + SSL).
# For HTTP-only deploy (e.g. IP 34.201.10.84), set SECURE_SSL_REDIRECT=False in .env.prod.
USE_HTTPS = os.getenv('SECURE_SSL_REDIRECT', 'false').lower() == 'true'

# Security settings
SECURE_SSL_REDIRECT = USE_HTTPS
SESSION_COOKIE_SECURE = USE_HTTPS
CSRF_COOKIE_SECURE = USE_HTTPS
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HSTS (only when using HTTPS)
if USE_HTTPS:
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Email Backend (SMTP for production)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

# Logging - less verbose in production
LOGGING['handlers']['console']['level'] = 'WARNING'  # noqa
LOGGING['root']['level'] = 'INFO'  # noqa

# CORS - restrict in production
CORS_ALLOW_ALL_ORIGINS = False
# CORS_ALLOWED_ORIGINS should be set in environment variables

# Database connection pooling for production
if DATABASE_ENGINE == 'postgresql':
    DATABASES['default']['CONN_MAX_AGE'] = 600  # noqa
    DATABASES['default']['ATOMIC_REQUESTS'] = True  # noqa

# Static files - use S3 in production if configured, otherwise WhiteNoise
if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_STORAGE_BUCKET_NAME = S3_BUCKET_NAME
    AWS_S3_REGION_NAME = AWS_REGION
    AWS_S3_CUSTOM_DOMAIN = os.getenv('AWS_S3_CUSTOM_DOMAIN', '')
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_S3_FILE_OVERWRITE = False
    # Many modern S3 buckets have Object Ownership = "Bucket owner enforced",
    # which disables ACLs entirely. Setting AWS_DEFAULT_ACL would cause:
    #   AccessControlListNotSupported: The bucket does not allow ACLs
    # Use bucket policy/IAM for access instead of ACLs.
    AWS_DEFAULT_ACL = None
    STATIC_URL = f'https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/static/'
else:
    # Fallback to WhiteNoise
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    STATIC_URL = '/static/'

# Media files - use S3 in production if configured
if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_STORAGE_BUCKET_NAME = S3_BUCKET_NAME
    AWS_S3_REGION_NAME = AWS_REGION
    AWS_LOCATION = 'media'
    MEDIA_URL = f'https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/media/'
else:
    # Fallback to local storage
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

# File upload limits for production
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000
