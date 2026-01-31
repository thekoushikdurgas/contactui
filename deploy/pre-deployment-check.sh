#!/bin/bash

# Pre-Deployment Validation Script for DocsAI (Django)
# Validates environment and configuration before deployment to EC2

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration - DocsAI default path; override with PROJECT_DIR env var
APP_DIR="${PROJECT_DIR:-/home/ubuntu/docsai}"
ENV_FILE=".env.prod"
ERRORS=0
WARNINGS=0

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
    ((ERRORS++))
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
    ((WARNINGS++))
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

print_header "Pre-Deployment Validation (DocsAI)"

# Phase 1: System Requirements
print_header "Phase 1: System Requirements"

if command_exists python3; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_success "Python 3 installed: $PYTHON_VERSION"
else
    print_error "Python 3 not found"
fi

if command_exists nginx; then
    NGINX_VERSION=$(nginx -v 2>&1 | awk '{print $3}' | cut -d'/' -f2)
    print_success "Nginx installed: $NGINX_VERSION"
else
    print_warning "Nginx not installed (will be installed by deployment script)"
fi

if command_exists git; then
    print_success "Git installed"
else
    print_error "Git not found"
fi

if command_exists curl; then
    print_success "curl installed"
else
    print_warning "curl not found"
fi

# Phase 2: Application Directory
print_header "Phase 2: Application Directory"

if [ -d "$APP_DIR" ]; then
    print_success "Application directory exists: $APP_DIR"
    cd "$APP_DIR"
else
    print_error "Application directory not found: $APP_DIR"
    print_info "Please clone the repository first: git clone <repo-url> $APP_DIR"
    exit 1
fi

if [ -f "manage.py" ]; then
    print_success "manage.py found"
else
    print_error "manage.py not found"
fi

# Phase 3: Virtual Environment
print_header "Phase 3: Virtual Environment"

if [ -d "venv" ]; then
    print_success "Virtual environment exists"
    if [ -f "venv/bin/activate" ]; then
        print_success "Virtual environment is valid"
        source venv/bin/activate 2>/dev/null || true
    else
        print_error "Virtual environment is invalid"
    fi
else
    print_warning "Virtual environment not found (will be created by full-deploy.sh)"
fi

# Phase 4: Dependencies
print_header "Phase 4: Dependencies"

if [ -f "requirements.txt" ]; then
    print_success "requirements.txt found"
    if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
        source venv/bin/activate 2>/dev/null || true
        print_info "Checking installed packages..."
        if pip show django >/dev/null 2>&1; then
            print_success "Django installed"
        else
            print_warning "Django not installed (run: pip install -r requirements.txt)"
        fi
        if pip show gunicorn >/dev/null 2>&1; then
            print_success "Gunicorn installed"
        else
            print_warning "Gunicorn not installed (run: pip install -r requirements.txt)"
        fi
    fi
else
    print_error "requirements.txt not found"
fi

# Phase 5: Environment Configuration (.env.prod)
print_header "Phase 5: Environment Configuration"

if [ -f "$ENV_FILE" ]; then
    print_success "$ENV_FILE exists"
    PERMS=$(stat -c "%a" "$ENV_FILE" 2>/dev/null || echo "unknown")
    if [ "$PERMS" = "600" ]; then
        print_success "$ENV_FILE permissions are secure (600)"
    else
        print_warning "$ENV_FILE permissions are $PERMS (should be 600)"
        if chmod 600 "$ENV_FILE" 2>/dev/null; then
            print_success "Permissions fixed to 600"
        elif sudo chmod 600 "$ENV_FILE" 2>/dev/null; then
            print_success "Permissions fixed to 600 (using sudo)"
        else
            print_info "Fix manually: chmod 600 $ENV_FILE"
        fi
    fi
    set -a
    source "$ENV_FILE" 2>/dev/null || true
    set +a
    if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "django-insecure-change-this-in-production" ]; then
        print_error "SECRET_KEY is not set or using default value"
    else
        print_success "SECRET_KEY is set"
    fi
    if [ "$DJANGO_ENV" = "production" ]; then
        print_success "DJANGO_ENV is set to production"
    else
        print_warning "DJANGO_ENV is not production (current: ${DJANGO_ENV:-unset})"
    fi
    if [ "$DEBUG" = "False" ] || [ "$DEBUG" = "false" ]; then
        print_success "DEBUG is disabled"
    else
        print_warning "DEBUG is enabled (should be False in production)"
    fi
    if [ -n "$ALLOWED_HOSTS" ]; then
        print_success "ALLOWED_HOSTS is set"
    else
        print_warning "ALLOWED_HOSTS is not set"
    fi
    if [ "${DATABASE_ENGINE:-sqlite}" = "postgresql" ]; then
        if [ -n "$DATABASE_NAME" ] && [ -n "$DATABASE_USER" ] && [ -n "$DATABASE_HOST" ]; then
            print_success "PostgreSQL database settings present"
        else
            print_error "PostgreSQL selected but DATABASE_NAME/USER/HOST missing"
        fi
    fi
else
    print_warning "$ENV_FILE not found (create from .env.prod.example for first deploy)"
    print_info "Create with: cp .env.prod.example $ENV_FILE"
fi

# Phase 6: Database Connection (optional)
print_header "Phase 6: Database Connection"

if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE" 2>/dev/null || true
    set +a
    if [ "${DATABASE_ENGINE:-sqlite}" = "postgresql" ] && [ -n "$DATABASE_HOST" ] && [ -n "$DATABASE_PORT" ]; then
        print_info "Testing database connectivity..."
        if timeout 5 bash -c "echo > /dev/tcp/$DATABASE_HOST/$DATABASE_PORT" 2>/dev/null; then
            print_success "Database host is reachable: $DATABASE_HOST:$DATABASE_PORT"
        else
            print_warning "Cannot reach database host: $DATABASE_HOST:$DATABASE_PORT"
            print_info "Ensure security groups/firewall allow access from this host"
        fi
        if command_exists psql; then
            export PGPASSWORD="${DATABASE_PASSWORD:-}"
            if timeout 5 psql -h "$DATABASE_HOST" -p "${DATABASE_PORT:-5432}" -U "$DATABASE_USER" -d "$DATABASE_NAME" -c "SELECT 1;" >/dev/null 2>&1; then
                print_success "Database connection successful (psql)"
            else
                print_info "psql connection failed (app will verify on startup)"
            fi
            unset PGPASSWORD
        fi
    else
        print_info "Using SQLite or database not configured; skipping DB connectivity check"
    fi
fi

# Phase 7: Required Deploy Files
print_header "Phase 7: Required Files"

REQUIRED_FILES=(
    "manage.py"
    "requirements.txt"
    "deploy/systemd/gunicorn.service"
    "deploy/systemd/gunicorn.socket"
    "deploy/systemd/gunicorn-start.sh"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        print_success "$file exists"
    else
        print_error "$file not found"
    fi
done

if [ -f "deploy/nginx/docsai-http-only.conf" ] || [ -f "deploy/nginx/docsai.conf" ]; then
    print_success "Nginx configuration file exists"
else
    print_error "Neither deploy/nginx/docsai-http-only.conf nor deploy/nginx/docsai.conf found"
fi

# Phase 8: Service Configuration
print_header "Phase 8: Service Configuration"

if [ -f "deploy/systemd/gunicorn.service" ]; then
    print_success "Systemd service file exists"
    if grep -q "$APP_DIR" deploy/systemd/gunicorn.service 2>/dev/null; then
        print_success "Service file contains correct app directory"
    else
        print_warning "Service file may need path updates (expected: $APP_DIR)"
    fi
fi

if command_exists nginx; then
    if [ -f "deploy/nginx/docsai-http-only.conf" ]; then
        if sudo nginx -t 2>/dev/null; then
            print_success "Nginx configuration is valid"
        else
            print_warning "Nginx test failed (config may not be installed yet)"
        fi
    fi
fi

# Phase 9: Gunicorn config (optional)
if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    source venv/bin/activate 2>/dev/null || true
    if python -c "import config.gunicorn.production" 2>/dev/null; then
        print_success "Gunicorn production config loads"
    else
        print_warning "Could not import config.gunicorn.production (check PYTHONPATH when running)"
    fi
fi

# Phase 10: Security Checks
print_header "Phase 10: Security Checks"

if [ -f "$ENV_FILE" ]; then
    if [ -f ".gitignore" ] && (grep -q "^\.env\.prod$" .gitignore || grep -q "\.env\.prod" .gitignore); then
        print_success ".env.prod is in .gitignore"
    else
        print_warning ".env.prod may not be in .gitignore"
    fi
    if [ -n "$SECRET_KEY" ] && [ "$SECRET_KEY" = "django-insecure-change-this-in-production" ]; then
        print_error "SECRET_KEY must be changed from default"
    fi
fi

# Summary
print_header "Validation Summary"

echo -e "Errors: ${RED}$ERRORS${NC}"
echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"

if [ $ERRORS -eq 0 ]; then
    print_success "Pre-deployment validation passed!"
    if [ $WARNINGS -gt 0 ]; then
        print_warning "Please review warnings before deploying"
    fi
    exit 0
else
    print_error "Pre-deployment validation failed!"
    print_info "Please fix errors before deploying"
    exit 1
fi
