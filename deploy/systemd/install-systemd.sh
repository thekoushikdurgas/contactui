#!/bin/bash
set -e

PROJECT_DIR="/home/ubuntu/docsai"
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

# Fix .env.prod permissions if it exists (must be readable by ubuntu user)
if [ -f "$PROJECT_DIR/.env.prod" ]; then
    chown ubuntu:ubuntu "$PROJECT_DIR/.env.prod"
    chmod 600 "$PROJECT_DIR/.env.prod"
    echo "Fixed permissions for .env.prod"
else
    echo "WARNING: .env.prod not found at $PROJECT_DIR/.env.prod"
    echo "The service may fail to start without proper environment configuration"
fi

# Verify Gunicorn config can be imported
echo "Verifying Gunicorn configuration..."
cd "$PROJECT_DIR"
if [ -d "venv" ]; then
    source venv/bin/activate
    if python -c "import config.gunicorn.production" 2>/dev/null; then
        echo "Gunicorn configuration verified ✓"
    else
        echo "WARNING: Could not import config.gunicorn.production"
        echo "This may cause the service to fail. Checking Python path..."
        python -c "import sys; print('Python path:', sys.path)" || true
    fi
    deactivate
else
    echo "WARNING: Virtual environment not found. Cannot verify Gunicorn config."
fi

# Copy socket file
cp deploy/systemd/gunicorn.socket $SYSTEMD_DIR/
chmod 644 $SYSTEMD_DIR/gunicorn.socket

# Copy service file
cp deploy/systemd/gunicorn.service $SYSTEMD_DIR/
chmod 644 $SYSTEMD_DIR/gunicorn.service

# If Type=notify fails, we can use the simple version
# Uncomment the following lines if you encounter issues:
# echo "Using Type=simple service file (more compatible)"
# cp deploy/systemd/gunicorn.service.simple $SYSTEMD_DIR/gunicorn.service
# chmod 644 $SYSTEMD_DIR/gunicorn.service

# Reload systemd
systemctl daemon-reload

# Enable socket
systemctl enable gunicorn.socket

# Start socket
systemctl start gunicorn.socket

# Enable service
systemctl enable gunicorn.service

# Start service
echo "Starting Gunicorn service..."
if systemctl start gunicorn.service; then
    echo "Gunicorn service started successfully"
else
    echo "ERROR: Failed to start Gunicorn service"
    echo ""
    echo "Checking service status..."
    systemctl status gunicorn.service --no-pager || true
    echo ""
    echo "Recent Gunicorn logs:"
    journalctl -u gunicorn.service -n 50 --no-pager || true
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Check logs: sudo journalctl -u gunicorn -f"
    echo "2. Verify Python path: cd $PROJECT_DIR && source venv/bin/activate && python -c 'import config.gunicorn.production'"
    echo "3. Test Gunicorn manually: cd $PROJECT_DIR && source venv/bin/activate && gunicorn --config config.gunicorn.production config.wsgi:application --bind unix:/run/gunicorn.sock"
    exit 1
fi

# Wait a moment for service to initialize
sleep 2

# Check status
echo "Checking service status..."
if systemctl is-active --quiet gunicorn.service; then
    echo "Gunicorn service is running ✓"
    systemctl status gunicorn.service --no-pager
else
    echo "WARNING: Gunicorn service may not be running properly"
    systemctl status gunicorn.service --no-pager || true
    echo ""
    echo "Recent logs:"
    journalctl -u gunicorn.service -n 30 --no-pager || true
fi

echo ""
echo "Systemd services installed!"
echo "To view logs: sudo journalctl -u gunicorn -f"
echo "To restart: sudo systemctl restart gunicorn"
