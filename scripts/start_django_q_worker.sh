#!/bin/bash
# Django-Q Worker Startup Script (Linux/Mac)
# 
# This script starts the Django-Q worker cluster for background task processing.
# Run this in a separate terminal or as a background service.

set -e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_DIR"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Load environment variables from .env if it exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start Django-Q cluster
echo "Starting Django-Q worker cluster..."
echo "Project directory: $PROJECT_DIR"
echo "Press Ctrl+C to stop the worker"
echo ""

python manage.py qcluster
