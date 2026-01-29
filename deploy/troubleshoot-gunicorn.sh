#!/bin/bash
# Troubleshooting script for Gunicorn service issues

set -e

PROJECT_DIR="/home/ubuntu/docsai"
SERVICE_NAME="gunicorn"

echo "=========================================="
echo "Gunicorn Troubleshooting Script"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root or with sudo"
    exit 1
fi

cd "$PROJECT_DIR" || {
    echo "ERROR: Cannot access $PROJECT_DIR"
    exit 1
}

echo "1. Checking service status..."
systemctl status $SERVICE_NAME.service --no-pager || true
echo ""

echo "2. Checking recent logs (last 50 lines)..."
journalctl -u $SERVICE_NAME.service -n 50 --no-pager || true
echo ""

echo "3. Checking socket file..."
if [ -S /run/gunicorn.sock ]; then
    ls -la /run/gunicorn.sock
    echo "Socket exists ✓"
else
    echo "WARNING: Socket file /run/gunicorn.sock does not exist"
fi
echo ""

echo "4. Checking socket service..."
systemctl status $SERVICE_NAME.socket --no-pager || true
echo ""

echo "5. Checking environment file..."
if [ -f "$PROJECT_DIR/.env.prod" ]; then
    echo ".env.prod exists ✓"
    ls -la "$PROJECT_DIR/.env.prod"
    echo "Checking if readable by ubuntu user..."
    sudo -u ubuntu test -r "$PROJECT_DIR/.env.prod" && echo "Readable ✓" || echo "NOT readable ✗"
else
    echo "ERROR: .env.prod not found!"
fi
echo ""

echo "6. Checking virtual environment..."
if [ -d "$PROJECT_DIR/venv" ]; then
    echo "Virtual environment exists ✓"
    if [ -f "$PROJECT_DIR/venv/bin/gunicorn" ]; then
        echo "Gunicorn binary exists ✓"
        "$PROJECT_DIR/venv/bin/gunicorn" --version || true
    else
        echo "ERROR: Gunicorn binary not found!"
    fi
else
    echo "ERROR: Virtual environment not found!"
fi
echo ""

echo "7. Testing Gunicorn configuration import..."
if [ -d "$PROJECT_DIR/venv" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
    if python -c "import config.gunicorn.production" 2>&1; then
        echo "Gunicorn config import successful ✓"
    else
        echo "ERROR: Cannot import config.gunicorn.production"
        echo "Python path:"
        python -c "import sys; print('\n'.join(sys.path))" || true
    fi
    deactivate
fi
echo ""

echo "8. Testing WSGI application import..."
if [ -d "$PROJECT_DIR/venv" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
    export DJANGO_ENV=production
    if python -c "from config.wsgi import application" 2>&1; then
        echo "WSGI application import successful ✓"
    else
        echo "ERROR: Cannot import WSGI application"
    fi
    deactivate
fi
echo ""

echo "9. Checking log directory..."
if [ -d "/var/log/django" ]; then
    echo "Log directory exists ✓"
    ls -la /var/log/django/ || true
else
    echo "WARNING: Log directory /var/log/django does not exist"
fi
echo ""

echo "10. Testing manual Gunicorn start (dry-run)..."
if [ -d "$PROJECT_DIR/venv" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
    export DJANGO_ENV=production
    export PATH="$PROJECT_DIR/venv/bin:$PATH"
    export PYTHONPATH="$PROJECT_DIR"
    
    echo "Attempting to start Gunicorn manually (will timeout after 5 seconds)..."
    timeout 5 "$PROJECT_DIR/venv/bin/gunicorn" \
        --config config.gunicorn.production \
        --bind unix:/run/gunicorn.sock \
        config.wsgi:application \
        2>&1 || echo "Manual start test completed (timeout expected)"
    
    deactivate
fi
echo ""

echo "11. Checking systemd service file..."
if [ -f "/etc/systemd/system/$SERVICE_NAME.service" ]; then
    echo "Service file exists ✓"
    echo "Contents:"
    cat "/etc/systemd/system/$SERVICE_NAME.service"
else
    echo "ERROR: Service file not found!"
fi
echo ""

echo "12. Checking socket file..."
if [ -f "/etc/systemd/system/$SERVICE_NAME.socket" ]; then
    echo "Socket file exists ✓"
    echo "Contents:"
    cat "/etc/systemd/system/$SERVICE_NAME.socket"
else
    echo "ERROR: Socket file not found!"
fi
echo ""

echo "=========================================="
echo "Troubleshooting Summary"
echo "=========================================="
echo ""
echo "Common fixes:"
echo "1. Restart socket: sudo systemctl restart $SERVICE_NAME.socket"
echo "2. Restart service: sudo systemctl restart $SERVICE_NAME.service"
echo "3. Reload systemd: sudo systemctl daemon-reload"
echo "4. Check full logs: sudo journalctl -u $SERVICE_NAME.service -f"
echo "5. Fix permissions: sudo chown ubuntu:ubuntu $PROJECT_DIR/.env.prod && sudo chmod 600 $PROJECT_DIR/.env.prod"
echo ""
