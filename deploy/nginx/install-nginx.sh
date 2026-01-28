#!/bin/bash
set -e

PROJECT_DIR="/home/ubuntu/docsai"
NGINX_SITES_DIR="/etc/nginx/sites-available"
NGINX_ENABLED_DIR="/etc/nginx/sites-enabled"
HTTP_ONLY=false

for arg in "$@"; do
    case "$arg" in
        --http-only) HTTP_ONLY=true ;;
    esac
done

echo "Installing Nginx configuration..."
if [ "$HTTP_ONLY" = true ]; then
    echo "Mode: HTTP-only (no SSL, for IP-only deploy e.g. 34.201.10.84)"
fi

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root or with sudo"
    exit 1
fi

if [ -d "$PROJECT_DIR" ]; then
    cd "$PROJECT_DIR"
fi
if [ ! -f "deploy/nginx/docsai.conf" ]; then
    echo "Error: run from project root where deploy/nginx/ exists (e.g. $PROJECT_DIR)"
    exit 1
fi

if [ "$HTTP_ONLY" = true ]; then
    cp deploy/nginx/docsai-http-only.conf $NGINX_SITES_DIR/docsai.conf
else
    cp deploy/nginx/docsai.conf $NGINX_SITES_DIR/docsai.conf
fi
chmod 644 $NGINX_SITES_DIR/docsai.conf

# Create symlink
ln -sf $NGINX_SITES_DIR/docsai.conf $NGINX_ENABLED_DIR/docsai.conf

# Remove default config if exists
if [ -f $NGINX_ENABLED_DIR/default ]; then
    rm $NGINX_ENABLED_DIR/default
    echo "Removed default Nginx configuration"
fi

# Test Nginx configuration
echo "Testing Nginx configuration..."
nginx -t

# Reload Nginx
echo "Reloading Nginx..."
systemctl reload nginx

echo ""
echo "Nginx configuration installed successfully!"
if [ "$HTTP_ONLY" = true ]; then
    echo "HTTP-only mode: serving on port 80. No SSL."
    echo "Health check: curl http://34.201.10.84/api/v1/health/"
else
    echo "Don't forget to:"
    echo "1. Update server_name in docsai.conf with your domain"
    echo "2. Update SSL certificate paths after running SSL setup"
    echo "3. Run SSL setup script: bash deploy/ssl/setup-ssl.sh <domain> <email>"
fi
