# Quick Start Deployment Guide

This guide helps you deploy DocsAI on EC2 Ubuntu server using the automated deployment script.

## Prerequisites

1. **EC2 Ubuntu 22.04 LTS** instance running
2. **SSH access** to the EC2 instance
3. **Git repository** cloned to `/home/ubuntu/docsai`
4. **Root/sudo access** on the EC2 instance

## Quick Deployment (3 Steps)

### Step 1: Clone the Repository

```bash
ssh -i your-key.pem ubuntu@34.201.10.84
sudo mkdir -p /home/ubuntu/docsai
sudo chown -R ubuntu:ubuntu /home/ubuntu/docsai
cd /home/ubuntu/docsai
git clone <your-repo-url> .
```

### Step 2: Run Deployment Script

Choose one of the following options:

#### Option A: Single-Command Deploy (pre-check → full-deploy → post-verify) ⭐ Recommended

Runs pre-deployment validation, then full deployment, then post-deployment verification:

```bash
cd /home/ubuntu/docsai
sudo bash deploy/deploy-to-ec2.sh --http-only --ip 34.201.10.84
# or with SSL: sudo bash deploy/deploy-to-ec2.sh --domain docsai.example.com --email admin@example.com
# or interactive: sudo bash deploy/deploy-to-ec2.sh --interactive
```

#### Option B: HTTP-Only (No SSL, IP-based) – full-deploy only

```bash
cd /home/ubuntu/docsai
sudo bash deploy/full-deploy.sh --http-only --ip 34.201.10.84
```

#### Option C: With Domain and SSL

```bash
cd /home/ubuntu/docsai
sudo bash deploy/full-deploy.sh --domain docsai.example.com --email admin@example.com
```

#### Option D: Interactive Mode (First time)

```bash
cd /home/ubuntu/docsai
sudo bash deploy/full-deploy.sh --interactive
```

### Step 3: Verify Deployment

```bash
# Health check
curl http://34.201.10.84/api/v1/health/

# Or run post-deployment verification script
bash deploy/post-deployment-verify.sh

# Or with domain
curl https://docsai.example.com/api/v1/health/
```

## What the Scripts Do

**`deploy-to-ec2.sh`** runs in order: `pre-deployment-check.sh` → `full-deploy.sh` → `post-deployment-verify.sh`. You can also run these separately:

- **`pre-deployment-check.sh`** – Validates system, env, and required files (no changes).
- **`post-deployment-verify.sh`** – Checks Gunicorn, Nginx, health endpoint, and logs after deploy.

The **`full-deploy.sh`** script automates the following steps:

1. ✅ **System Dependencies** - Installs Python, PostgreSQL, Nginx, etc.
2. ✅ **Database Setup** - Creates PostgreSQL database and user (optional)
3. ✅ **Python Environment** - Creates virtual environment and installs dependencies
4. ✅ **Environment Configuration** - Sets up `.env.prod` with production settings
5. ✅ **Django Setup** - Runs migrations and collects static files
6. ✅ **Gunicorn Service** - Installs and starts Gunicorn systemd service
7. ✅ **Nginx Configuration** - Sets up reverse proxy
8. ✅ **SSL Certificate** - Obtains Let's Encrypt certificate (if domain provided)
9. ✅ **Log Rotation** - Configures automatic log rotation
10. ✅ **Firewall** - Configures UFW firewall rules
11. ✅ **Verification** - Tests deployment and health endpoints

## Script Options

```bash
--http-only              Deploy with HTTP only (no SSL)
--domain DOMAIN          Domain name for SSL setup
--email EMAIL            Email for SSL certificate
--ip IP                  EC2 IP address
--interactive            Interactive mode (prompts for all settings)
--skip-db-setup          Skip database setup (use existing database)
--skip-ssl               Skip SSL setup even if domain provided
-h, --help               Show help message
```

## Post-Deployment Steps

### 1. Create Superuser

```bash
cd /home/ubuntu/docsai
source venv/bin/activate
python manage.py createsuperuser
```

### 2. Configure Environment Variables

Edit `/home/ubuntu/docsai/.env.prod` and set:
- Database credentials (if using RDS or custom setup)
- AWS S3 credentials (if using S3 storage)
- API keys (OpenAI, Google Gemini, Lambda APIs, etc.)

### 3. Verify Services

```bash
# Check Gunicorn
sudo systemctl status gunicorn

# Check Nginx
sudo systemctl status nginx

# View logs
sudo journalctl -u gunicorn -f
sudo tail -f /var/log/nginx/docsai_error.log
```

## Troubleshooting

### Script Fails at Database Setup

If you're using RDS or external database:
```bash
sudo bash deploy/full-deploy.sh --http-only --skip-db-setup
```

Then manually configure database in `.env.prod`:
```env
DATABASE_ENGINE=postgresql
DATABASE_NAME=your_db_name
DATABASE_USER=your_db_user
DATABASE_PASSWORD=your_db_password
DATABASE_HOST=your-rds-endpoint.amazonaws.com
DATABASE_PORT=5432
```

### Health Check Fails

1. Check Gunicorn logs: `sudo journalctl -u gunicorn -f`
2. Check Nginx logs: `sudo tail -f /var/log/nginx/docsai_error.log`
3. Verify firewall: `sudo ufw status`
4. Check service status: `sudo systemctl status gunicorn nginx`

### SSL Certificate Issues

1. Ensure DNS points to EC2 IP
2. Check Nginx config: `sudo nginx -t`
3. Verify certbot: `sudo certbot certificates`
4. Test renewal: `sudo certbot renew --dry-run`

## Manual Deployment (Alternative)

If you prefer manual deployment, follow the step-by-step guide:
- See [DEPLOY_EC2_34.201.10.84.md](../docs/deployment/DEPLOY_EC2_34.201.10.84.md)

## Next Steps

- Configure monitoring and alerts
- Set up automated backups
- Configure CI/CD with GitHub Actions
- Review security settings
- Set up log aggregation

## Support

For issues or questions:
1. Check logs: `sudo journalctl -u gunicorn -f`
2. Review deployment documentation
3. Check GitHub Issues
