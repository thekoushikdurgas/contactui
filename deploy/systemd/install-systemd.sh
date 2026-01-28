#!/bin/bash
set -e

PROJECT_DIR="/var/www/docsai"
SYSTEMD_DIR="/etc/systemd/system"

echo "Installing systemd service files..."

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root or with sudo"
    exit 1
fi

# Run from project root (required for deploy/systemd/* paths)
if [ -d "$PROJECT_DIR" ]; then
    cd "$PROJECT_DIR"
fi
if [ ! -f "deploy/systemd/gunicorn.service" ]; then
    echo "Error: run from project root (e.g. $PROJECT_DIR) where deploy/systemd/ exists"
    exit 1
fi

# Create log directory for Gunicorn
mkdir -p /var/log/django
chown ubuntu:www-data /var/log/django
chmod 755 /var/log/django

# Copy socket file
cp deploy/systemd/gunicorn.socket $SYSTEMD_DIR/
chmod 644 $SYSTEMD_DIR/gunicorn.socket

# Copy service file
cp deploy/systemd/gunicorn.service $SYSTEMD_DIR/
chmod 644 $SYSTEMD_DIR/gunicorn.service

# Reload systemd
systemctl daemon-reload

# Enable socket
systemctl enable gunicorn.socket

# Start socket
systemctl start gunicorn.socket

# Enable service
systemctl enable gunicorn.service

# Start service
systemctl start gunicorn.service

# Check status
echo "Checking service status..."
systemctl status gunicorn.service --no-pager

echo ""
echo "Systemd services installed and started successfully!"
echo "To view logs: sudo journalctl -u gunicorn -f"
echo "To restart: sudo systemctl restart gunicorn"
