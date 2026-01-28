#!/bin/bash
# ------------------------------------------------------------------------------
# Remote deploy script — run on EC2 (e.g. via GitHub Actions SSH).
# Usage: cd /var/www/docsai && bash deploy/remote-deploy.sh
# Caller must already have run: git fetch && git reset --hard origin/<branch>
# ------------------------------------------------------------------------------
set -e

PROJECT_DIR="${PROJECT_DIR:-/var/www/docsai}"
cd "$PROJECT_DIR"

if [ ! -f "manage.py" ] || [ ! -d "venv" ]; then
    echo "Error: $PROJECT_DIR is not the app root (manage.py, venv missing)."
    exit 1
fi

echo ">>> Activating venv and installing dependencies..."
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo ">>> Running migrations..."
python manage.py migrate --noinput

echo ">>> Collecting static files..."
python manage.py collectstatic --noinput

echo ">>> Restarting Gunicorn..."
sudo systemctl restart gunicorn

echo ">>> Done. Verify: curl -s http://localhost/api/v1/health/ || curl -s http://34.201.10.84/api/v1/health/"
