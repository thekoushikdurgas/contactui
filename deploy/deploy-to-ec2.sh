#!/bin/bash

# DocsAI (Django) - EC2 Automated Deployment Script
# Runs: pre-deployment check → full-deploy.sh → post-deployment verify
# Usage: sudo bash deploy/deploy-to-ec2.sh [OPTIONS]
# Options: same as full-deploy.sh (--http-only, --ip, --domain, --email, --interactive, --skip-db-setup, --skip-ssl, -h)

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Resolve project directory from script location (so it works when run from any path)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

log() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_err() { echo -e "${RED}[ERROR]${NC} $1"; }

# Require root (full-deploy.sh requires sudo)
if [ "$EUID" -ne 0 ]; then
    log_err "This script must be run as root or with sudo"
    echo "Usage: sudo bash deploy/deploy-to-ec2.sh [OPTIONS]"
    echo "Options: --http-only [--ip IP] | --domain DOMAIN --email EMAIL | --interactive | --skip-db-setup | --skip-ssl | -h"
    exit 1
fi

log "DocsAI EC2 Deployment (pre-check → full-deploy → post-verify)"
log "Project directory: $PROJECT_DIR"
echo ""

# Step 1: Pre-deployment check
log "Step 1: Running pre-deployment check..."
export PROJECT_DIR
if ! bash "$PROJECT_DIR/deploy/pre-deployment-check.sh"; then
    log_warn "Pre-deployment check reported errors."
    read -p "Continue with deployment anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_err "Deployment aborted. Fix errors and run again."
        exit 1
    fi
fi

# Step 2: Full deployment
log "Step 2: Running full deployment..."
export PROJECT_DIR
if ! bash "$PROJECT_DIR/deploy/full-deploy.sh" "$@"; then
    log_err "Full deployment failed."
    exit 1
fi

# Step 3: Post-deployment verify
log "Step 3: Running post-deployment verification..."
# Export SERVER_IP for post script (from metadata or default)
if [ -z "$SERVER_IP" ]; then
    SERVER_IP=$(curl -s --connect-timeout 2 http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "34.201.10.84")
fi
export SERVER_IP
export PROJECT_DIR
bash "$PROJECT_DIR/deploy/post-deployment-verify.sh" || log_warn "Post-deployment verification had warnings"

# Summary
echo ""
echo "=========================================="
echo -e "${GREEN}Deployment complete!${NC}"
echo "=========================================="
echo "Project directory: $PROJECT_DIR"
echo "Environment file:  $PROJECT_DIR/.env.prod"
echo "Health check:      http://${SERVER_IP}/api/v1/health/"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status gunicorn"
echo "  sudo journalctl -u gunicorn -f"
echo "  sudo tail -f /var/log/nginx/docsai_error.log"
echo "  sudo systemctl restart gunicorn"
echo ""
