#!/bin/bash

# Post-Deployment Verification Script for DocsAI (Django)
# Verifies that deployment was successful on EC2

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration - DocsAI uses Gunicorn (Unix socket), Nginx on 80, health at /api/v1/health/
SERVICE_NAME="gunicorn"
SERVER_IP="${SERVER_IP:-34.201.10.84}"
HEALTH_PATH="/api/v1/health/"
TIMEOUT=10

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
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

test_endpoint() {
    local url=$1
    local expected_status=${2:-200}
    response=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "$url" 2>/dev/null || echo "000")
    if [ "$response" = "$expected_status" ]; then
        return 0
    else
        return 1
    fi
}

print_header "Post-Deployment Verification (DocsAI)"

# Phase 1: Service Status
print_header "Phase 1: Service Status"

if sudo systemctl is-active --quiet $SERVICE_NAME 2>/dev/null; then
    print_success "Service '$SERVICE_NAME' is running"
    STATUS=$(sudo systemctl is-active $SERVICE_NAME 2>/dev/null || echo "unknown")
    print_info "Service status: $STATUS"
else
    print_error "Service '$SERVICE_NAME' is not running"
    print_info "Check with: sudo systemctl status $SERVICE_NAME"
fi

if sudo systemctl is-enabled --quiet $SERVICE_NAME 2>/dev/null; then
    print_success "Service '$SERVICE_NAME' is enabled (will start on boot)"
else
    print_warning "Service '$SERVICE_NAME' is not enabled"
    print_info "Enable with: sudo systemctl enable $SERVICE_NAME"
fi

if sudo systemctl is-active --quiet nginx 2>/dev/null; then
    print_success "Nginx is running"
else
    print_error "Nginx is not running"
    print_info "Check with: sudo systemctl status nginx"
fi

# Phase 2: Socket and Port (DocsAI uses Unix socket, not port 8000)
print_header "Phase 2: Socket and Port Availability"

if [ -S /run/gunicorn.sock ] 2>/dev/null || [ -e /run/gunicorn.sock ]; then
    print_success "Gunicorn socket exists: /run/gunicorn.sock"
else
    print_error "Gunicorn socket not found at /run/gunicorn.sock"
    print_info "Check with: ls -la /run/gunicorn.sock"
fi

if sudo lsof -i :80 >/dev/null 2>&1; then
    print_success "Port 80 is in use (Nginx is listening)"
else
    print_warning "Port 80 is not in use"
fi

# Phase 3: Health Endpoint (via Nginx on port 80)
print_header "Phase 3: Health Endpoint"

if test_endpoint "http://localhost${HEALTH_PATH}" 200; then
    print_success "Health endpoint responding at http://localhost${HEALTH_PATH}"
    HEALTH_RESPONSE=$(curl -s --max-time $TIMEOUT "http://localhost${HEALTH_PATH}" 2>/dev/null || echo "{}")
    if echo "$HEALTH_RESPONSE" | grep -q "success"; then
        print_success "Health check returns success"
    else
        print_info "Health response: ${HEALTH_RESPONSE:0:200}..."
    fi
else
    print_error "Health endpoint not responding at http://localhost${HEALTH_PATH}"
    print_info "Ensure Nginx is proxying to Gunicorn and app is running"
fi

# Phase 4: External health (if SERVER_IP set)
if [ -n "$SERVER_IP" ] && [ "$SERVER_IP" != "localhost" ]; then
    if test_endpoint "http://${SERVER_IP}${HEALTH_PATH}" 200; then
        print_success "Health endpoint responding on $SERVER_IP"
    else
        print_warning "Health endpoint not responding on $SERVER_IP (check firewall/security group)"
    fi
fi

# Phase 5: Database health endpoint (optional)
if test_endpoint "http://localhost/api/v1/health/database/" 200; then
    print_success "Database health endpoint responding"
else
    print_info "Database health endpoint not checked or not available"
fi

# Phase 6: Service Logs
print_header "Phase 6: Service Logs"

print_info "Checking recent Gunicorn logs for errors..."
RECENT_ERRORS=$(sudo journalctl -u $SERVICE_NAME --since "5 minutes ago" --no-pager 2>/dev/null | grep -i "error\|exception\|traceback" | wc -l || echo "0")
if [ "$RECENT_ERRORS" -eq 0 ]; then
    print_success "No recent errors in Gunicorn logs"
else
    print_warning "Found $RECENT_ERRORS recent errors in Gunicorn logs"
    print_info "View logs: sudo journalctl -u $SERVICE_NAME -n 50"
fi

# Phase 7: Nginx Logs
print_header "Phase 7: Nginx Logs"

if [ -f "/var/log/nginx/docsai_error.log" ]; then
    NGINX_ERRORS=$(sudo tail -100 /var/log/nginx/docsai_error.log 2>/dev/null | grep -i "error" | wc -l || echo "0")
    if [ "$NGINX_ERRORS" -eq 0 ]; then
        print_success "No recent errors in Nginx docsai_error.log"
    else
        print_warning "Found $NGINX_ERRORS recent errors in Nginx docsai_error.log"
        print_info "View logs: sudo tail -f /var/log/nginx/docsai_error.log"
    fi
elif [ -f "/var/log/nginx/error.log" ]; then
    NGINX_ERRORS=$(sudo tail -100 /var/log/nginx/error.log 2>/dev/null | grep -i "error" | wc -l || echo "0")
    if [ "$NGINX_ERRORS" -eq 0 ]; then
        print_success "No recent errors in Nginx error.log"
    else
        print_warning "Found $NGINX_ERRORS recent errors in Nginx error.log"
    fi
else
    print_warning "Nginx error log not found"
fi

# Phase 8: System Resources
print_header "Phase 8: System Resources"

if command_exists free; then
    MEMORY_USAGE=$(free 2>/dev/null | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}' || echo "0")
    print_info "Memory usage: ${MEMORY_USAGE}%"
    if command_exists bc; then
        if [ "$(echo "$MEMORY_USAGE > 90" | bc 2>/dev/null)" = "1" ]; then
            print_warning "Memory usage is high (>90%)"
        else
            print_success "Memory usage is acceptable"
        fi
    fi
fi

DISK_USAGE=$(df -h / 2>/dev/null | awk 'NR==2 {print $5}' | sed 's/%//' || echo "0")
print_info "Disk usage: ${DISK_USAGE}%"
if [ "$DISK_USAGE" -gt 90 ] 2>/dev/null; then
    print_warning "Disk usage is high (>90%)"
else
    print_success "Disk usage is acceptable"
fi

# Phase 9: Database connectivity (optional - if .env.prod and psql)
PROJECT_DIR="${PROJECT_DIR:-/home/ubuntu/docsai}"
if [ -f "$PROJECT_DIR/.env.prod" ] && command_exists psql; then
    set -a
    source "$PROJECT_DIR/.env.prod" 2>/dev/null || true
    set +a
    if [ "${DATABASE_ENGINE:-}" = "postgresql" ] && [ -n "$DATABASE_HOST" ] && [ -n "$DATABASE_NAME" ]; then
        print_info "Testing database connectivity..."
        export PGPASSWORD="${DATABASE_PASSWORD:-}"
        if timeout 5 psql -h "$DATABASE_HOST" -p "${DATABASE_PORT:-5432}" -U "$DATABASE_USER" -d "$DATABASE_NAME" -c "SELECT 1;" >/dev/null 2>&1; then
            print_success "Database is reachable"
        else
            print_warning "Cannot connect to database (may be expected)"
        fi
        unset PGPASSWORD
    fi
fi

# Summary
print_header "Verification Summary"

print_info "Gunicorn Status: $(sudo systemctl is-active $SERVICE_NAME 2>/dev/null || echo 'unknown')"
print_info "Nginx Status: $(sudo systemctl is-active nginx 2>/dev/null || echo 'unknown')"
print_info "Health Endpoint: $(test_endpoint "http://localhost${HEALTH_PATH}" 200 && echo 'OK' || echo 'FAILED')"

echo ""
print_success "Post-deployment verification complete!"
print_info "If all checks passed, your DocsAI deployment is successful."
print_info ""
print_info "Useful commands:"
print_info "  Gunicorn logs: sudo journalctl -u $SERVICE_NAME -f"
print_info "  Nginx logs:    sudo tail -f /var/log/nginx/docsai_error.log"
print_info "  Restart:       sudo systemctl restart $SERVICE_NAME"
print_info "  Status:        sudo systemctl status $SERVICE_NAME"
