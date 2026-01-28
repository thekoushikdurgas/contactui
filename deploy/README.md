# Deployment Scripts

This directory contains deployment scripts for automating DocsAI deployment on EC2 Ubuntu servers.

## Scripts Overview

### 1. `full-deploy.sh` - Complete Automated Deployment ⭐ **RECOMMENDED**

**Purpose**: Complete end-to-end deployment from git clone onwards.

**Usage**:
```bash
# HTTP-only (no SSL)
sudo bash deploy/full-deploy.sh --http-only --ip 34.201.10.84

# With domain and SSL
sudo bash deploy/full-deploy.sh --domain example.com --email admin@example.com

# Interactive mode
sudo bash deploy/full-deploy.sh --interactive
```

**What it does**:
- ✅ Installs all system dependencies
- ✅ Sets up PostgreSQL database (optional)
- ✅ Creates Python virtual environment
- ✅ Installs Python dependencies
- ✅ Configures `.env.prod` file
- ✅ Runs Django migrations
- ✅ Collects static files
- ✅ Installs Gunicorn systemd service
- ✅ Configures Nginx reverse proxy
- ✅ Sets up SSL certificate (if domain provided)
- ✅ Configures log rotation
- ✅ Sets up firewall rules
- ✅ Verifies deployment

**Best for**: First-time deployments, fresh EC2 instances.

---

### 2. `deploy.sh` - Master Deploy Script

**Purpose**: Deploys after initial setup (assumes venv and `.env.prod` exist).

**Usage**:
```bash
sudo ./deploy/deploy.sh --http-only
sudo ./deploy/deploy.sh example.com admin@example.com
```

**Best for**: Re-deployments after initial setup.

---

### 3. `remote-deploy.sh` - Remote Update Script

**Purpose**: Updates existing deployment (used by GitHub Actions).

**Usage**:
```bash
cd /home/ubuntu/docsai
bash deploy/remote-deploy.sh
```

**What it does**:
- Updates Python dependencies
- Runs migrations
- Collects static files
- Restarts Gunicorn

**Best for**: CI/CD automated deployments.

---

### 4. Component Scripts

#### `systemd/install-systemd.sh`
Installs Gunicorn systemd service and socket.

#### `nginx/install-nginx.sh`
Installs Nginx configuration for reverse proxy.

#### `ssl/setup-ssl.sh`
Sets up Let's Encrypt SSL certificate.

#### `logrotate/install-logrotate.sh`
Configures log rotation for application logs.

---

## Quick Start

### First-Time Deployment

1. **Clone repository**:
   ```bash
   ssh -i your-key.pem ubuntu@34.201.10.84
   sudo mkdir -p /home/ubuntu/docsai
   sudo chown -R ubuntu:ubuntu /home/ubuntu/docsai
   cd /home/ubuntu/docsai
   git clone <your-repo-url> .
   ```

2. **Run full deployment**:
   ```bash
   sudo bash deploy/full-deploy.sh --interactive
   ```

3. **Verify**:
   ```bash
   curl http://34.201.10.84/api/v1/health/
   ```

### Subsequent Updates

**Option A**: Use GitHub Actions (automated)
- Push to `main` branch
- GitHub Actions runs `remote-deploy.sh`

**Option B**: Manual update
```bash
cd /home/ubuntu/docsai
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
```

---

## Script Comparison

| Feature | `full-deploy.sh` | `deploy.sh` | `remote-deploy.sh` |
|---------|------------------|-------------|-------------------|
| System dependencies | ✅ | ✅ | ❌ |
| Database setup | ✅ | ❌ | ❌ |
| Python venv | ✅ | ❌ | ❌ |
| Install dependencies | ✅ | ❌ | ✅ |
| Environment config | ✅ | ❌ | ❌ |
| Django migrations | ✅ | ✅ | ✅ |
| Static files | ✅ | ✅ | ✅ |
| Gunicorn setup | ✅ | ✅ | ❌ |
| Nginx setup | ✅ | ✅ | ❌ |
| SSL setup | ✅ | ✅ | ❌ |
| Log rotation | ✅ | ✅ | ❌ |
| Firewall | ✅ | ❌ | ❌ |

---

## Common Use Cases

### Use Case 1: Fresh EC2 Instance
**Script**: `full-deploy.sh --interactive`
- Complete setup from scratch
- Interactive prompts for configuration

### Use Case 2: HTTP-Only Deployment
**Script**: `full-deploy.sh --http-only --ip 34.201.10.84`
- Quick deployment without SSL
- IP-based access

### Use Case 3: Production with SSL
**Script**: `full-deploy.sh --domain example.com --email admin@example.com`
- Full production setup
- SSL certificate from Let's Encrypt

### Use Case 4: Using RDS Database
**Script**: `full-deploy.sh --http-only --skip-db-setup`
- Skip local PostgreSQL setup
- Configure RDS in `.env.prod` manually

### Use Case 5: CI/CD Updates
**Script**: `remote-deploy.sh` (via GitHub Actions)
- Automated updates on git push
- Minimal downtime

---

## Troubleshooting

### Script Fails at Database Setup

If using RDS or external database:
```bash
sudo bash deploy/full-deploy.sh --http-only --skip-db-setup
```

Then edit `.env.prod` with your database credentials.

### Permission Errors

Ensure you're running with sudo:
```bash
sudo bash deploy/full-deploy.sh --http-only
```

### Health Check Fails

1. Check Gunicorn: `sudo systemctl status gunicorn`
2. Check Nginx: `sudo systemctl status nginx`
3. View logs: `sudo journalctl -u gunicorn -f`

### SSL Certificate Issues

1. Verify DNS points to EC2 IP
2. Check Nginx config: `sudo nginx -t`
3. Review SSL setup: `sudo certbot certificates`

---

## Documentation

- **[QUICK_START.md](./QUICK_START.md)** - Quick start guide
- **[../docs/deployment/DEPLOY_EC2_34.201.10.84.md](../docs/deployment/DEPLOY_EC2_34.201.10.84.md)** - Detailed deployment guide
- **[../docs/deployment/GITHUB_ACTIONS_DEPLOY.md](../docs/deployment/GITHUB_ACTIONS_DEPLOY.md)** - CI/CD setup

---

## Script Development

When modifying scripts:

1. **Test on clean EC2 instance** first
2. **Use `set -e`** for error handling
3. **Add logging** with colored output
4. **Validate inputs** before execution
5. **Provide rollback** instructions if possible
6. **Update documentation** with changes

---

## Support

For issues:
1. Check script logs and error messages
2. Review deployment documentation
3. Check service status: `sudo systemctl status gunicorn nginx`
4. View logs: `sudo journalctl -u gunicorn -f`
