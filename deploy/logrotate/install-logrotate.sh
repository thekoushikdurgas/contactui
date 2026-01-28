#!/bin/bash
set -e

LOGROTATE_DIR="/etc/logrotate.d"

echo "Installing logrotate configuration..."

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root or with sudo"
    exit 1
fi

# Copy logrotate config
cp deploy/logrotate/docsai $LOGROTATE_DIR/
chmod 644 $LOGROTATE_DIR/docsai

# Test logrotate config
echo "Testing logrotate configuration..."
logrotate -d $LOGROTATE_DIR/docsai

echo "Logrotate configuration installed successfully!"
echo "Logs will be rotated daily and kept for 14 days"
