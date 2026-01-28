#!/bin/bash
set -e

DOMAIN=$1
EMAIL=$2

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    echo "Usage: ./setup-ssl.sh <domain> <email>"
    echo "Example: ./setup-ssl.sh example.com admin@example.com"
    exit 1
fi

echo "Setting up SSL for domain: $DOMAIN"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root or with sudo"
    exit 1
fi

# Install Certbot
echo "Installing Certbot..."
apt update
apt install -y certbot python3-certbot-nginx

# Create certbot directory
mkdir -p /var/www/certbot
chown www-data:www-data /var/www/certbot

# Get certificate
echo "Obtaining SSL certificate..."
certbot certonly --webroot \
    -w /var/www/certbot \
    -d $DOMAIN \
    -d www.$DOMAIN \
    --email $EMAIL \
    --agree-tos \
    --non-interactive

# Update Nginx config with SSL paths and domain
echo "Updating Nginx configuration..."
sed -i "s|your-domain.com|$DOMAIN|g" /etc/nginx/sites-available/docsai.conf

# Test Nginx config
echo "Testing Nginx configuration..."
nginx -t

# Reload Nginx
echo "Reloading Nginx..."
systemctl reload nginx

# Enable auto-renewal
echo "Enabling SSL certificate auto-renewal..."
systemctl enable certbot.timer
systemctl start certbot.timer

# Test renewal
echo "Testing certificate renewal..."
certbot renew --dry-run

echo ""
echo "SSL setup completed successfully!"
echo "Certificate location: /etc/letsencrypt/live/$DOMAIN/"
echo "Auto-renewal is enabled and will run automatically"
