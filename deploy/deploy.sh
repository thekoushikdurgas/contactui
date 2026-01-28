#!/bin/bash
set -e

# Master deployment script for Django DocsAI on EC2/Ubuntu
# Usage:
#   With domain + SSL: ./deploy/deploy.sh <domain> <email>
#   IP-only (no SSL):  ./deploy/deploy.sh --http-only

HTTP_ONLY=false
DOMAIN=""
EMAIL=""

for arg in "$@"; do
    case "$arg" in
        --http-only) HTTP_ONLY=true ;;
        *) [ -z "$DOMAIN" ] && DOMAIN="$arg" || [ -z "$EMAIL" ] && EMAIL="$arg" ;;
    esac
done

if [ "$HTTP_ONLY" = false ] && { [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; }; then
    echo "Usage:"
    echo "  With SSL:   ./deploy/deploy.sh <domain> <email>"
    echo "  IP-only:    ./deploy/deploy.sh --http-only"
    echo "Example:      ./deploy/deploy.sh example.com admin@example.com"
    echo "              ./deploy/deploy.sh --http-only"
    exit 1
fi

echo "=========================================="
echo "Django DocsAI Deployment Script"
echo "=========================================="
if [ "$HTTP_ONLY" = true ]; then
    echo "Mode: HTTP-only (no SSL, for 34.201.10.84)"
else
    echo "Domain: $DOMAIN"
    echo "Email: $EMAIL"
fi
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root or with sudo"
    exit 1
fi

PROJECT_DIR="/var/www/docsai"

echo "Step 1: Installing system dependencies..."
apt update
apt install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    postgresql-client \
    nginx \
    git \
    curl \
    wget \
    build-essential \
    libpq-dev

if [ "$HTTP_ONLY" = false ]; then
    apt install -y certbot python3-certbot-nginx
fi

echo ""
echo "Step 2: Setting up project directory..."
if [ ! -d "$PROJECT_DIR" ]; then
    mkdir -p $PROJECT_DIR
    echo "Created project directory: $PROJECT_DIR"
fi

echo ""
echo "Step 3: Installing systemd services..."
cd $PROJECT_DIR
if [ -f "deploy/systemd/install-systemd.sh" ]; then
    bash deploy/systemd/install-systemd.sh
else
    echo "Warning: install-systemd.sh not found, skipping systemd setup"
fi

echo ""
echo "Step 4: Installing Nginx configuration..."
if [ -f "deploy/nginx/install-nginx.sh" ]; then
    if [ "$HTTP_ONLY" = true ]; then
        bash deploy/nginx/install-nginx.sh --http-only
    else
        bash deploy/nginx/install-nginx.sh
    fi
else
    echo "Warning: install-nginx.sh not found, skipping Nginx setup"
fi

if [ "$HTTP_ONLY" = false ] && [ -n "$DOMAIN" ] && [ -n "$EMAIL" ]; then
    echo ""
    echo "Step 5: Setting up SSL/TLS..."
    if [ -f "deploy/ssl/setup-ssl.sh" ]; then
        bash deploy/ssl/setup-ssl.sh "$DOMAIN" "$EMAIL"
    else
        echo "Warning: setup-ssl.sh not found, skipping SSL setup"
    fi
else
    echo ""
    echo "Step 5: Skipping SSL (--http-only or no domain/email)"
fi

echo ""
echo "Step 6: Installing log rotation..."
if [ -f "deploy/logrotate/install-logrotate.sh" ]; then
    bash deploy/logrotate/install-logrotate.sh
else
    echo "Warning: install-logrotate.sh not found, skipping logrotate setup"
fi

echo ""
echo "Step 7: Collecting static files..."
cd $PROJECT_DIR
if [ -d "venv" ]; then
    source venv/bin/activate
    python manage.py collectstatic --noinput
    echo "Static files collected successfully"
else
    echo "Warning: Virtual environment not found, skipping collectstatic"
fi

echo ""
echo "Step 8: Running database migrations..."
if [ -d "venv" ]; then
    python manage.py migrate --noinput
    echo "Migrations completed successfully"
else
    echo "Warning: Virtual environment not found, skipping migrations"
fi

echo ""
echo "Step 9: Verifying services..."
systemctl status gunicorn.service --no-pager || echo "Gunicorn service not running"
systemctl status nginx --no-pager || echo "Nginx not running"

echo ""
echo "=========================================="
echo "Deployment completed!"
echo "=========================================="
echo ""
if [ "$HTTP_ONLY" = true ]; then
    echo "Next steps:"
    echo "1. Verify: curl http://34.201.10.84/api/v1/health/"
    echo "2. Logs:   sudo journalctl -u gunicorn -f"
    echo "3. Nginx:  sudo tail -f /var/log/nginx/docsai_error.log"
    echo "4. Superuser: cd $PROJECT_DIR && source venv/bin/activate && python manage.py createsuperuser"
else
    echo "Next steps:"
    echo "1. Verify: curl https://$DOMAIN/api/v1/health/"
    echo "2. Logs:   sudo journalctl -u gunicorn -f"
    echo "3. Nginx:  sudo tail -f /var/log/nginx/docsai_error.log"
    echo "4. Superuser: cd $PROJECT_DIR && source venv/bin/activate && python manage.py createsuperuser"
fi
