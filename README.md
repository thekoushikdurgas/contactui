# Django Docs AI Agent

A comprehensive Django application for managing documentation, API endpoints, and AI-powered features with a modern web interface.

## 📋 Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Local Development](#local-development)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Deployment](#deployment)
- [Management Commands](#management-commands)
- [Troubleshooting](#troubleshooting)

## ✨ Features

- **Documentation Management**: Create, edit, and manage documentation pages
- **API Endpoint Management**: Import and manage API endpoints from Postman collections
- **AI Integration**: AI-powered features with OpenAI and Google Gemini support
- **Media Management**: Unified dashboard for managing files across local storage, S3, and GraphQL
- **Media Manager Dashboard**: Service-based dashboard for managing documentation resources (pages, endpoints, relationships, Postman) with direct service calls
- **Background Tasks**: Django-Q integration for async task processing
- **REST API**: Comprehensive REST API with DRF
- **Modern UI**: Responsive web interface with dark/light theme support
- **Best Practices**: Follows Django best practices with 96%+ compliance score

## 🔧 Prerequisites

- **Python**: 3.8 or higher
- **Database**: SQLite (default for development) or PostgreSQL 12+ (for production)
- **Virtual Environment**: Recommended (Python venv)
- **Optional**:
  - Redis (for caching and Django-Q)
  - AWS Account (for S3 integration)
  - Node.js (for frontend asset compilation)

## 🚀 Quick Start

### 1. Clone and Navigate

```bash
cd contact360/docsai
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 4. Environment Configuration

```bash
# Copy environment template
cp .env.example .env  # Linux/Mac
copy .env.example .env  # Windows

# Generate Django secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Edit .env and set your SECRET_KEY and other variables
```

### 5. Database Setup

**For Development (SQLite - Default):**
```bash
# No database configuration needed! SQLite is used automatically.
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

**For Production (PostgreSQL):**
```bash
# Set DATABASE_ENGINE=postgresql in .env
# Create database
createdb docsai

# Run migrations
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 6. Validate Environment

```bash
python manage.py validate_env
```

### 7. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 8. Start Development Server

```bash
# Starts both Django server and Django-Q cluster
python manage.py runserver
```

Visit `http://localhost:8000` and log in with your superuser credentials.

## 💻 Local Development

### Environment Variables

Set the Django environment:

```bash
# Windows
set DJANGO_ENV=development

# Linux/Mac
export DJANGO_ENV=development
```

Or explicitly set the settings module:

```bash
# Windows
set DJANGO_SETTINGS_MODULE=config.settings.development

# Linux/Mac
export DJANGO_SETTINGS_MODULE=config.settings.development
```

### Running Servers Separately

If you prefer to run Django server and Django-Q worker separately:

```bash
# Terminal 1: Start Django-Q worker
python manage.py qcluster

# Terminal 2: Start Django server
python manage.py runserver
```

### Development Server Options

```bash
# Custom port
python manage.py runserver 8080

# All interfaces
python manage.py runserver 0.0.0.0:8000

# Only Django server (skip Q cluster)
python manage.py runserver --skip-qcluster

# Only Q cluster (skip server)
python manage.py runserver --skip-server

# Disable auto-reloader
python manage.py runserver --noreload
```

## 📁 Project Structure

```
contact360/docsai/
├── apps/                    # Django applications
│   ├── core/               # Core app (models, services, utilities)
│   ├── documentation/      # Documentation management
│   ├── ai_agent/          # AI agent features
│   ├── api/               # API gateway (centralized routing)
│   └── ...                # Other feature-specific apps
├── config/                 # Configuration
│   └── settings/          # Environment-based settings
│       ├── base.py        # Common settings
│       ├── development.py # Development settings
│       ├── production.py  # Production settings
│       ├── staging.py     # Staging settings
│       └── testing.py     # Test settings
├── scripts/               # Utility scripts
│   ├── django_checker.py  # Best practices checker
│   └── tests/            # Script tests
├── templates/             # Global templates
├── static/                # Static files (CSS, JS)
├── media/                 # User uploads
├── logs/                  # Application logs
├── reports/               # Best practices check reports
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
├── pyproject.toml         # Linting/formatting config
├── pytest.ini             # Pytest configuration
├── .env.example           # Environment variables template
└── README.md              # This file
```

## ⚙️ Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | Generated key |
| `DJANGO_ENV` | Environment selection | `development`, `staging`, `production`, `testing` |

### Database Configuration

**SQLite (Default for Development):**
- No configuration needed! SQLite is used automatically.

**PostgreSQL (Production):**
```env
DATABASE_ENGINE=postgresql
DATABASE_NAME=docsai
DATABASE_USER=postgres
DATABASE_PASSWORD=your-password
DATABASE_HOST=localhost
DATABASE_PORT=5432
```

### Recommended Environment Variables

| Variable | Description | Impact if Missing |
|----------|-------------|-------------------|
| `AWS_ACCESS_KEY_ID` | AWS access key | S3 features disabled |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | S3 features disabled |
| `S3_BUCKET_NAME` | S3 bucket name | File storage disabled |
| `OPENAI_API_KEY` | OpenAI API key | AI features use fallback |
| `GOOGLE_API_KEY` | Google Gemini API key | AI features use fallback |
| `REDIS_URL` | Redis connection URL | Uses in-memory cache |

See `.env.example` for a complete list of available configuration options.

## 🗄️ Database Setup

### Development (SQLite)

SQLite is the default database for development. No setup required:

```bash
python manage.py migrate
python manage.py createsuperuser
```

### Production (PostgreSQL)

1. Install PostgreSQL
2. Create database:
   ```bash
   createdb docsai
   ```
3. Set environment variables in `.env`:
   ```env
   DATABASE_ENGINE=postgresql
   DATABASE_NAME=docsai
   DATABASE_USER=postgres
   DATABASE_PASSWORD=your-password
   DATABASE_HOST=localhost
   DATABASE_PORT=5432
   ```
4. Run migrations:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

## 🏃 Running the Application

### Development Mode

```bash
# Start both server and worker (recommended)
python manage.py runserver

# Or run separately
python manage.py qcluster      # Terminal 1
python manage.py runserver     # Terminal 2
```

### Production Mode

```bash
# Set production environment
export DJANGO_ENV=production

# Collect static files
python manage.py collectstatic --noinput

# Run with Gunicorn (example)
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

## 🧪 Testing

### Run All Tests

```bash
# Using pytest (recommended)
pytest

# Using Django test runner
python manage.py test
```

### Run Specific Tests

```bash
# Specific app
pytest apps/documentation/tests/

# Specific test file
pytest apps/documentation/tests/test_views.py

# Specific test
pytest apps/documentation/tests/test_views.py::TestDashboardViews
```

### Test Coverage

```bash
# Run with coverage
pytest --cov=apps --cov-report=html

# View coverage report
# Open htmlcov/index.html in browser
```

## 🔍 Code Quality

### Best Practices Checker

```bash
# Full check
python manage.py check_best_practices

# Category-specific
python manage.py check_best_practices --category "Security"

# Save report
python manage.py check_best_practices --output reports/check.json
```

### Linting and Formatting

```bash
# Format code with black
black .

# Sort imports with isort
isort .

# Lint with ruff
ruff check .

# Type checking with mypy
mypy apps/
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## 🚢 Deployment

### Docker Deployment

```bash
# Build image
docker build -t docsai .

# Run container
docker run -p 8000:8000 --env-file .env docsai
```

### EC2 Deployment (Ubuntu)

For **EC2 Ubuntu** (e.g. **34.201.10.84**):

1. Use the **[EC2 runbook](docs/deployment/DEPLOY_EC2_34.201.10.84.md)** for step-by-step setup (Gunicorn, Nginx, systemd, optional SSL).
2. Copy **`.env.prod.example`** to **`.env.prod`** on the server and fill in production values.
3. **HTTP-only** (no domain): `sudo ./deploy/deploy.sh --http-only`
4. **With domain + SSL**: `sudo ./deploy/deploy.sh <domain> <email>`
5. **GitHub Actions**: Configure `EC2_SSH_PRIVATE_KEY`, `EC2_HOST`, `EC2_USER` secrets, then push to `main` or run **Deploy to EC2** manually. See **[GITHUB_ACTIONS_DEPLOY](docs/deployment/GITHUB_ACTIONS_DEPLOY.md)**.

Health check: `curl http://34.201.10.84/api/v1/health/`

### Environment Setup

1. Set `DJANGO_ENV=production` in `.env`
2. Set `DEBUG=False` in `.env`
3. Configure `ALLOWED_HOSTS` in production settings
4. Set up PostgreSQL database
5. Configure static file serving (CDN recommended)
6. Set up SSL/HTTPS
7. Configure monitoring (Sentry, etc.)

### Health Checks

```bash
# Check application health
curl http://localhost:8000/api/v1/health/

# Check environment
python manage.py validate_env
```

## 📝 Management Commands

### Database Operations

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations
python manage.py sqlmigrate <app> <migration>
```

### User Management

```bash
python manage.py createsuperuser
python manage.py changepassword <username>
```

### Static Files

```bash
python manage.py collectstatic --noinput
python manage.py collectstatic --clear
```

### Background Tasks

```bash
python manage.py qcluster          # Start Q cluster
python manage.py qmonitor          # Monitor Q tasks
```

### Environment Validation

```bash
python manage.py validate_env
python manage.py validate_env --verbose
python manage.py validate_env --skip-connectivity
```

### Best Practices Checker

```bash
python manage.py check_best_practices
python manage.py check_best_practices --category "Security"
python manage.py check_best_practices --output reports/check.json
```

## 🐛 Troubleshooting

### Settings Not Loading

- Check `DJANGO_ENV` or `DJANGO_SETTINGS_MODULE` is set
- Verify `config/settings/<env>.py` exists
- Check for import errors in settings files

### Import Errors

- Verify virtual environment is activated
- Check Python path: `python -c "import sys; print(sys.path)"`
- Verify all dependencies installed: `pip list`

### Database Connection Issues

- Check `DATABASE_ENGINE` in `.env`
- Verify database credentials
- Test connection: `python manage.py dbshell`

### Migration Issues

- Check migration status: `python manage.py showmigrations`
- Review migration files: `apps/<app>/migrations/`
- Fake migration if needed: `python manage.py migrate --fake`

### Best Practices Check Fails

- Review report: `reports/django_check_report_*.json`
- Run category-specific checks
- Check `COMPLETION_STATUS.md` for details

## 📊 Media Manager Dashboard

The Media Manager Dashboard provides a unified interface for managing documentation resources using direct service calls.

### Features

- **Service-based Architecture**: Direct method calls, no HTTP overhead
- **119 Endpoint Functionalities**: Complete API parity with Lambda API
- **Tab-based Interface**: Pages, Endpoints, Relationships, Postman
- **View Modes**: List and Grid views
- **Filtering & Search**: Resource-specific filters with real-time search
- **Pagination**: Client-side pagination
- **Dark Mode**: Full dark mode support
- **Responsive Design**: Mobile-first approach

### Access

Navigate to `/docs/media-manager/` after logging in.

### Documentation

- [Media Manager Dashboard Guide](docs/MEDIA_MANAGER_DASHBOARD_GUIDE.md) - Complete implementation guide
- [Media Manager Dashboard API](docs/MEDIA_MANAGER_DASHBOARD_API.md) - API reference
- [Media Manager Routes](docs/MEDIA_MANAGER_ROUTES.md) - Route documentation
- [Service Methods Audit](docs/SERVICE_METHODS_AUDIT.md) - Service methods reference

## 📚 Additional Resources

- [Settings Documentation](config/settings/README.md)
- [API Gateway Documentation](apps/api/README.md)
- [Completion Status](COMPLETION_STATUS.md)
- [Project Complete Summary](PROJECT_COMPLETE.md)

## 📄 License

[Add your license information here]

## 🤝 Contributing

[Add your contributing guidelines here]

## 👥 Authors

[Add author information here]

---

**Last Updated**: 2026-01-26  
**Django Version**: 4.2.7  
**Python Version**: 3.8+  
**Best Practices Score**: 96.81% (91/94 points)
