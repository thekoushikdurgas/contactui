# Django Settings Configuration

This directory contains environment-specific Django settings files.

## Structure

- `base.py` - Common settings shared across all environments
- `development.py` - Local development settings (DEBUG=True, relaxed security)
- `staging.py` - Staging/pre-production environment settings
- `production.py` - Production settings with full security hardening
- `testing.py` - Test environment settings (in-memory DB, fast tests)
- `local.py` - Local overrides (gitignored, for personal customizations)

## Usage

### Environment Variable

Set `DJANGO_ENV` environment variable to select the settings:

```bash
# Development (default)
export DJANGO_ENV=development
python manage.py runserver

# Staging
export DJANGO_ENV=staging
python manage.py runserver

# Production
export DJANGO_ENV=production
python manage.py runserver

# Testing
export DJANGO_ENV=testing
pytest
```

### Direct Module Path

You can also specify the settings module directly:

```bash
# Development
DJANGO_SETTINGS_MODULE=config.settings.development python manage.py runserver

# Production
DJANGO_SETTINGS_MODULE=config.settings.production python manage.py runserver
```

## Settings Files

### base.py

Contains all common settings:

- Installed apps
- Middleware
- Database configuration
- Static/media files
- Logging
- DRF configuration
- CORS settings
- Third-party service configurations (AWS, GraphQL, Lambda, AI)

### development.py

Development-specific overrides:

- `DEBUG = True`
- `ALLOWED_HOSTS = ['*']`
- Console email backend
- Debug toolbar (if installed)
- Verbose logging
- Relaxed security settings

### staging.py

Staging environment settings:

- `DEBUG = False`
- Security headers enabled
- SMTP email backend
- Production-like security with shorter HSTS

### production.py

Production settings with full security:

- `DEBUG = False`
- All security headers enabled
- Long HSTS duration
- SMTP email
- Connection pooling
- Restricted CORS

### testing.py

Test environment optimizations:

- In-memory SQLite database
- Faster password hashing
- Dummy cache
- Disabled logging
- Test-specific configurations

### local.py

Personal local overrides (not committed to git):

- Copy from `local.py.example` (if exists)
- Add your personal customizations
- Never commit this file

## Environment Variables

Key environment variables used across settings:

### Django Core

- `SECRET_KEY` - Django secret key (required)
- `DEBUG` - Debug mode (True/False)
- `ALLOWED_HOSTS` - Comma-separated list of allowed hosts
- `DJANGO_ENV` - Environment name (development/staging/production/testing)

### Database

- `DATABASE_ENGINE` - Database type (sqlite/postgresql)
- `DATABASE_NAME` - Database name
- `DATABASE_USER` - Database user
- `DATABASE_PASSWORD` - Database password
- `DATABASE_HOST` - Database host
- `DATABASE_PORT` - Database port

### AWS S3

- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `AWS_REGION` - AWS region
- `S3_BUCKET_NAME` - S3 bucket name

### Cache & Redis (Optional)

- `USE_REDIS_CACHE` - Enable Redis cache (True/False, default: False)
  - When `False`: Uses Django LocMemCache (per-process, no Redis required)
  - When `True`: Requires Redis configuration below
- `REDIS_HOST` - Redis host (only if USE_REDIS_CACHE=True)
- `REDIS_PORT` - Redis port (only if USE_REDIS_CACHE=True)
- `REDIS_DB` - Redis database number (only if USE_REDIS_CACHE=True)
- `REDIS_URL` - Full Redis URL (alternative to host/port/db, only if USE_REDIS_CACHE=True)

### Email

- `EMAIL_HOST` - SMTP host
- `EMAIL_PORT` - SMTP port
- `EMAIL_USE_TLS` - Use TLS (True/False)
- `EMAIL_HOST_USER` - SMTP username
- `EMAIL_HOST_PASSWORD` - SMTP password

### GraphQL

- `APPOINTMENT360_GRAPHQL_URL` - GraphQL endpoint URL
- `GRAPHQL_AUTH_ENABLED` - Enable GraphQL auth (True/False)

**Note:** Authentication uses JWT tokens from login sessions. No API key is required. Tokens are automatically extracted from request cookies or Authorization headers.

### Lambda APIs

- `LAMBDA_DOCUMENTATION_API_URL` - Documentation API URL
- `LAMBDA_DOCUMENTATION_API_KEY` - Documentation API key
- `LAMBDA_AI_API_URL` - AI API URL
- `LAMBDA_AI_API_KEY` - AI API key

### AI Services

- `OPENAI_API_KEY` - OpenAI API key
- `GEMINI_API_KEY` - Google Gemini API key

## Validation

Settings are validated on startup. Run comprehensive validation:

```bash
python manage.py validate_env
```

## Migration from Old Settings

If you're migrating from `docsai/settings.py`:

1. The old file still exists as a backward-compatibility shim
2. It imports from `config.settings` automatically
3. Update imports gradually:
   - Old: `from docsai.settings import ...`
   - New: `from django.conf import settings` (preferred)
   - Or: `from config.settings.base import ...` (if needed)

## Best Practices

1. **Never commit secrets** - Use environment variables
2. **Use local.py for personal overrides** - Don't modify base files
3. **Test all environments** - Ensure settings work in dev/staging/prod
4. **Validate on startup** - Run `validate_env` before deployment
5. **Document custom settings** - Add comments for non-standard configurations

## Troubleshooting

### Settings not loading

- Check `DJANGO_SETTINGS_MODULE` environment variable
- Verify `DJANGO_ENV` is set correctly
- Check for import errors in settings files

### Security warnings

- Run `python manage.py check --deploy` for production checks
- Review security settings in `production.py`
- Ensure `DEBUG=False` in production

### Database connection issues

- Verify database environment variables
- Check `DATABASE_ENGINE` is set correctly
- Test connection with `python manage.py dbshell`
