# Django DocsAI - Complete Deployment Guide
## EC2/Ubuntu Production Deployment

**Last Updated**: January 27, 2026  
**Target Environment**: Ubuntu 22.04 LTS on AWS EC2

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [EC2 Instance Setup](#ec2-instance-setup)
3. [System Dependencies](#system-dependencies)
4. [Project Deployment](#project-deployment)
5. [Gunicorn Configuration](#gunicorn-configuration)
6. [Nginx Configuration](#nginx-configuration)
7. [SSL/TLS Setup](#ssltls-setup)
8. [Database Setup](#database-setup)
9. [Static & Media Files](#static--media-files)
10. [Monitoring & Logging](#monitoring--logging)
11. [Post-Deployment](#post-deployment)
12. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### AWS Resources
- EC2 instance (Ubuntu 22.04 LTS)
- Security group configured (SSH, HTTP, HTTPS)
- Elastic IP (optional, recommended)
- Domain name (optional, for SSL)

### Local Machine
- SSH access to EC2 instance
- Git access to repository
- AWS credentials (for S3 operations)

---

## EC2 Instance Setup

### Step 1: Launch EC2 Instance

1. **AWS Console → EC2 → Launch Instance**
2. **AMI**: Ubuntu 22.04 LTS (Free Tier eligible)
3. **Instance Type**: `t2.micro` (free tier) or `t2.small` (recommended)
4. **Storage**: 20-30 GB EBS
5. **Security Group**:
   - SSH (22) - Your IP only
   - HTTP (80) - 0.0.0.0/0
   - HTTPS (443) - 0.0.0.0/0
   - Custom TCP (5432) - Only if using EC2 PostgreSQL
6. **Key Pair**: Download `.pem` file

### Step 2: Connect via SSH

```bash
# Set permissions
chmod 400 your-key.pem

# Connect
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

---

## System Dependencies

### Install System Packages

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y \
  python3-pip \
  python3-venv \
  python3-dev \
  postgresql-client \
  nginx \
  git \
  curl \
  wget \
  build-essential \
  libpq-dev \
  certbot \
  python3-certbot-nginx
```

---

## Project Deployment

### Step 1: Create Project Directory

```bash
# Create project directory
sudo mkdir -p /var/www/docsai
sudo chown -R ubuntu:ubuntu /var/www/docsai
cd /var/www/docsai
```

### Step 2: Clone Repository

```bash
# Clone your repository
git clone https://github.com/your-username/your-repo.git .

# Or if repository is private, use SSH
git clone git@github.com:your-username/your-repo.git .
```

### Step 3: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### Step 4: Install Python Dependencies

```bash
# Install requirements
pip install -r requirements.txt

# Verify Gunicorn is installed
pip list | grep gunicorn
```

### Step 5: Configure Environment Variables

```bash
# Copy environment template
cp .env.example .env.prod

# Edit environment file
nano .env.prod
```

**Required Variables:**
```env
DJANGO_ENV=production
DEBUG=False
SECRET_KEY=your-production-secret-key-here
ALLOWED_HOSTS=your-domain.com,your-ec2-ip,www.your-domain.com

# Database
DATABASE_ENGINE=postgresql
DATABASE_NAME=docsai
DATABASE_USER=django_user
DATABASE_PASSWORD=strong_password_here
DATABASE_HOST=localhost  # or RDS endpoint
DATABASE_PORT=5432

# AWS S3
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
S3_BUCKET_NAME=contact360docs

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

---

## Gunicorn Configuration

### Step 1: Create Log Directory

```bash
sudo mkdir -p /var/log/django
sudo chown ubuntu:ubuntu /var/log/django
```

### Step 2: Install Systemd Services

```bash
cd /var/www/docsai

# Make scripts executable
chmod +x deploy/systemd/install-systemd.sh
chmod +x deploy/nginx/install-nginx.sh
chmod +x deploy/ssl/setup-ssl.sh
chmod +x deploy/logrotate/install-logrotate.sh

# Install systemd services
sudo bash deploy/systemd/install-systemd.sh
```

### Step 3: Verify Gunicorn Service

```bash
# Check status
sudo systemctl status gunicorn

# View logs
sudo journalctl -u gunicorn -f
```

---

## Nginx Configuration

### Step 1: Install Nginx Configuration

```bash
cd /var/www/docsai
sudo bash deploy/nginx/install-nginx.sh
```

### Step 2: Update Configuration

Edit `/etc/nginx/sites-available/docsai.conf`:

```bash
sudo nano /etc/nginx/sites-available/docsai.conf
```

Update `server_name` with your domain:
```nginx
server_name your-domain.com www.your-domain.com;
```

### Step 3: Test and Reload

```bash
# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

## SSL/TLS Setup

### Step 1: Setup SSL Certificate

```bash
cd /var/www/docsai

# Run SSL setup script
sudo bash deploy/ssl/setup-ssl.sh your-domain.com admin@your-domain.com
```

This will:
- Install Certbot
- Obtain SSL certificate
- Update Nginx configuration
- Enable auto-renewal

### Step 2: Verify SSL

```bash
# Test certificate renewal
sudo certbot renew --dry-run

# Check certificate status
sudo certbot certificates
```

---

## Database Setup

### Option A: PostgreSQL on EC2

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Create database and user
sudo -u postgres psql <<EOF
CREATE DATABASE docsai;
CREATE USER django_user WITH PASSWORD 'strong_password';
ALTER ROLE django_user SET client_encoding TO 'utf8';
ALTER ROLE django_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE django_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE docsai TO django_user;
\q
EOF
```

### Option B: AWS RDS (Recommended)

1. **Create RDS Instance**:
   - Engine: PostgreSQL 15+
   - Instance class: db.t3.micro (free tier) or db.t3.small
   - Storage: 20 GB
   - Security group: Allow EC2 security group

2. **Update `.env.prod`**:
   ```env
   DATABASE_HOST=your-rds-endpoint.amazonaws.com
   ```

### Step 2: Run Migrations

```bash
cd /var/www/docsai
source venv/bin/activate

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

---

## Static & Media Files

### Option A: S3 Storage (Recommended)

1. **Setup S3 Bucket**:
   ```bash
   cd /var/www/docsai
   bash deploy/setup-s3.sh
   ```

2. **Configure in `.env.prod`**:
   ```env
   AWS_ACCESS_KEY_ID=your_key
   AWS_SECRET_ACCESS_KEY=your_secret
   S3_BUCKET_NAME=contact360docs
   ```

3. **Collect Static Files**:
   ```bash
   python manage.py collectstatic --noinput
   ```

### Option B: Local Storage with WhiteNoise

If S3 is not configured, static files will be served via WhiteNoise automatically.

---

## Monitoring & Logging

### Step 1: Install Log Rotation

```bash
cd /var/www/docsai
sudo bash deploy/logrotate/install-logrotate.sh
```

### Step 2: View Logs

```bash
# Gunicorn logs
sudo journalctl -u gunicorn -f

# Nginx logs
sudo tail -f /var/log/nginx/docsai_error.log
sudo tail -f /var/log/nginx/docsai_access.log

# Django logs
tail -f /var/www/docsai/logs/django.log
tail -f /var/www/docsai/logs/django-error.log
```

### Step 3: Health Checks

```bash
# Check application health
curl https://your-domain.com/api/v1/health/

# Check database
curl https://your-domain.com/api/v1/health/database/

# Check storage
curl https://your-domain.com/api/v1/health/storage/
```

---

## Post-Deployment

### Step 1: Verify Services

```bash
# Check all services
sudo systemctl status gunicorn
sudo systemctl status nginx
sudo systemctl status postgresql  # If using EC2 PostgreSQL
```

### Step 2: Test Application

```bash
# Test homepage
curl https://your-domain.com/

# Test API
curl https://your-domain.com/api/v1/

# Test health endpoint
curl https://your-domain.com/api/v1/health/
```

### Step 3: Create Superuser

```bash
cd /var/www/docsai
source venv/bin/activate
python manage.py createsuperuser
```

---

## Troubleshooting

### Gunicorn Not Starting

```bash
# Check logs
sudo journalctl -u gunicorn -n 50

# Check socket
ls -la /run/gunicorn.sock

# Restart service
sudo systemctl restart gunicorn
```

### Nginx 502 Bad Gateway

1. **Check Gunicorn**:
   ```bash
   sudo systemctl status gunicorn
   ```

2. **Check Socket Permissions**:
   ```bash
   ls -la /run/gunicorn.sock
   # Should be 666
   ```

3. **Check Nginx Error Log**:
   ```bash
   sudo tail -f /var/log/nginx/docsai_error.log
   ```

### Static Files Not Loading

1. **Check Static Files Collected**:
   ```bash
   ls -la /var/www/docsai/staticfiles/
   ```

2. **Re-collect Static Files**:
   ```bash
   python manage.py collectstatic --noinput --clear
   ```

3. **Check Nginx Configuration**:
   ```bash
   sudo nginx -t
   ```

### Database Connection Issues

1. **Test Connection**:
   ```bash
   python manage.py dbshell
   ```

2. **Check PostgreSQL**:
   ```bash
   sudo systemctl status postgresql
   ```

3. **Check Firewall**:
   ```bash
   sudo ufw status
   ```

### SSL Certificate Issues

1. **Check Certificate**:
   ```bash
   sudo certbot certificates
   ```

2. **Renew Certificate**:
   ```bash
   sudo certbot renew
   ```

3. **Check Nginx SSL Config**:
   ```bash
   sudo nginx -t
   ```

---

## Quick Reference Commands

### Service Management

```bash
# Restart Gunicorn
sudo systemctl restart gunicorn

# Restart Nginx
sudo systemctl restart nginx

# View Gunicorn logs
sudo journalctl -u gunicorn -f

# View Nginx logs
sudo tail -f /var/log/nginx/docsai_error.log
```

### Application Management

```bash
# Activate virtual environment
source /var/www/docsai/venv/bin/activate

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser
python manage.py createsuperuser
```

### Database Backup

```bash
# Backup database
pg_dump -U django_user docsai > backup_$(date +%Y%m%d).sql

# Restore database
psql -U django_user docsai < backup_20260127.sql
```

---

## Security Checklist

- [ ] `DEBUG=False` in production
- [ ] `SECRET_KEY` changed from default
- [ ] `ALLOWED_HOSTS` configured
- [ ] SSL certificate installed and auto-renewing
- [ ] Security headers configured
- [ ] Database credentials secure
- [ ] AWS credentials secure
- [ ] SSH key permissions set (400)
- [ ] Firewall configured (UFW)
- [ ] Regular backups scheduled

---

## Maintenance

### Daily
- Monitor logs for errors
- Check disk space: `df -h`
- Check service status: `sudo systemctl status gunicorn nginx`

### Weekly
- Review error logs
- Check SSL certificate expiration
- Verify backups

### Monthly
- Update system packages: `sudo apt update && sudo apt upgrade`
- Review security updates
- Check application performance metrics

---

**Document Version**: 1.0  
**Last Updated**: January 27, 2026
