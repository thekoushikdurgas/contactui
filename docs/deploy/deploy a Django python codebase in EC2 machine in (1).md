<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# deploy a Django python codebase in EC2 machine in Ubuntu with best practices

Perfect! I've got comprehensive current information. Let me create a complete production-grade deployment guide for Django on EC2 with Ubuntu, tailored to your backend expertise.

## **Complete Django Deployment Guide: EC2 + Ubuntu + Nginx + Gunicorn + PostgreSQL**[^1][^2][^3]

I'll walk you through a **production-ready setup** with best practices for 2025.

***

## **Architecture Overview**

```
User Request
    ↓
HTTPS (Port 443)
    ↓
Nginx (Reverse Proxy) - Port 80/443
    ↓
Gunicorn (WSGI Server) - Port 8000
    ↓
Django Application
    ↓
PostgreSQL (RDS or EC2)
```


***

## **Phase 1: EC2 Instance Setup**[^2][^3]

### **Step 1.1: Launch EC2 Instance**

**AWS Console → EC2 → Launch Instance:**

1. **Choose AMI:** Ubuntu 22.04 LTS (Free Tier eligible)
2. **Instance Type:** `t2.micro` (free tier) or `t2.small` for better performance
3. **Storage:** 20-30 GB EBS
4. **Security Group Rules:**
    - SSH (22) - Your IP only
    - HTTP (80) - 0.0.0.0/0
    - HTTPS (443) - 0.0.0.0/0
    - Custom TCP (5432) - Only if using EC2 PostgreSQL
5. **Key Pair:** Download `.pem` file (keep it secure)

### **Step 1.2: Connect via SSH**[^2]

```bash
# Set permissions
chmod 400 your-key.pem

# Connect
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```


***

## **Phase 2: System Setup**[^3][^2]

### **Step 2.1: Update System Packages**

```bash
# Update packages
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
  supervisor \
  certbot \
  python3-certbot-nginx
```

**Why each package:**

- `python3-dev`: For packages with C extensions
- `postgresql-client`: Connect to RDS/PostgreSQL
- `supervisor`: Process management (alternative to systemd)
- `certbot`: SSL/TLS certificates via Let's Encrypt

***

## **Phase 3: Project Setup**

### **Step 3.1: Create Project Directory \& Virtual Environment**

```bash
# Create project directory
sudo mkdir -p /var/www/django_app
sudo chown -R ubuntu:ubuntu /var/www/django_app
cd /var/www/django_app

# Clone your repository
git clone https://github.com/your-username/your-django-repo.git .

# Create virtual environment
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```


### **Step 3.2: Install Python Dependencies**

```bash
# Install requirements
pip install -r requirements.txt

# Add production packages if not in requirements
pip install gunicorn psycopg2-binary python-dotenv
```


### **Step 3.3: Configure Django Settings**

Create `.env.prod` file:

```bash
# /var/www/django_app/.env.prod

DEBUG=False
SECRET_KEY=your-production-secret-key-change-this
ALLOWED_HOSTS=your-domain.com,your-ec2-ip,www.your-domain.com

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=django_db
DB_USER=django_user
DB_PASSWORD=strong_password_here
DB_HOST=localhost  # or RDS endpoint
DB_PORT=5432

# AWS (if using S3)
USE_S3=True
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

Update `settings.py`:

```python
# settings.py
import os
from pathlib import Path
from decouple import config

# Load environment variables
DEBUG = config('DEBUG', default=False, cast=bool)
SECRET_KEY = config('SECRET_KEY')
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda v: [s.strip() for s in v.split(',')])

# Database
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE'),
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
    }
}

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Media files (if using local storage)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Security settings
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_SECURITY_POLICY = {
    "default-src": ("'self'",),
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/error.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

# CORS settings (if using API)
CORS_ALLOWED_ORIGINS = [
    "https://your-domain.com",
    "https://www.your-domain.com",
]
```


### **Step 3.4: Prepare Database \& Collect Static Files**

```bash
# Load environment
source venv/bin/activate
export $(cat .env.prod | xargs)

# Create log directory
sudo mkdir -p /var/log/django
sudo chown ubuntu:ubuntu /var/log/django

# Run migrations
python manage.py migrate

# Create superuser (run interactively)
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```


***

## **Phase 4: Configure Gunicorn**[^4][^3]

### **Step 4.1: Test Gunicorn Manually**

```bash
source venv/bin/activate
cd /var/www/django_app

# Test run (replace 'myproject' with your project name)
gunicorn --bind 0.0.0.0:8000 --workers 3 myproject.wsgi:application
```

Visit: `http://your-ec2-ip:8000` - You should see your Django app

### **Step 4.2: Create Gunicorn Systemd Service**[^4][^3]

Create `/etc/systemd/system/gunicorn.service`:

```bash
sudo nano /etc/systemd/system/gunicorn.service
```

Add content:

```ini
[Unit]
Description=Gunicorn daemon for Django application
After=network.target
Requires=gunicorn.socket

[Service]
Type=notify
User=ubuntu
Group=www-data
WorkingDirectory=/var/www/django_app

# Environment variables
EnvironmentFile=/var/www/django_app/.env.prod

# Gunicorn command
ExecStart=/var/www/django_app/venv/bin/gunicorn \
  --workers 3 \
  --worker-class sync \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --timeout 30 \
  --access-logfile /var/log/django/gunicorn-access.log \
  --error-logfile /var/log/django/gunicorn-error.log \
  --bind unix:/run/gunicorn.sock \
  myproject.wsgi:application

# Restart policy
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```


### **Step 4.3: Create Gunicorn Socket**

Create `/etc/systemd/system/gunicorn.socket`:

```bash
sudo nano /etc/systemd/system/gunicorn.socket
```

Add:

```ini
[Unit]
Description=Gunicorn socket
Before=gunicorn.service

[Socket]
ListenStream=/run/gunicorn.sock
SocketMode=0666

[Install]
WantedBy=sockets.target
```


### **Step 4.4: Enable \& Start Gunicorn**

```bash
# Reload systemd daemon
sudo systemctl daemon-reload

# Enable socket and service
sudo systemctl enable gunicorn.socket
sudo systemctl enable gunicorn

# Start services
sudo systemctl start gunicorn.socket
sudo systemctl start gunicorn

# Check status
sudo systemctl status gunicorn
sudo journalctl -u gunicorn -f  # View logs in real-time
```


***

## **Phase 5: Configure Nginx**[^5][^1][^3]

### **Step 5.1: Create Nginx Configuration**

Create `/etc/nginx/sites-available/django`:

```bash
sudo nano /etc/nginx/sites-available/django
```

Add:

```nginx
# Upstream Gunicorn application
upstream django_app {
    server unix:/run/gunicorn.sock fail_timeout=0;
}

# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

# HTTP redirect to HTTPS
server {
    listen 80;
    server_name your-domain.com www.your-domain.com your-ec2-ip;
    
    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    # Redirect all HTTP to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server block
server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL certificates (configure after getting certificates)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/django_access.log;
    error_log /var/log/nginx/django_error.log;

    # Client upload size
    client_max_body_size 50M;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css text/javascript application/json;
    gzip_min_length 1000;

    # Serve static files
    location /static/ {
        alias /var/www/django_app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Serve media files (if local storage)
    location /media/ {
        alias /var/www/django_app/media/;
        expires 7d;
    }

    # Favicon & robots
    location = /favicon.ico {
        alias /var/www/django_app/static/favicon.ico;
        access_log off;
        log_not_found off;
    }

    # API rate limiting (optional)
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        
        proxy_pass http://django_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Main application proxy
    location / {
        proxy_pass http://django_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```


### **Step 5.2: Enable Nginx Configuration**

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/django /etc/nginx/sites-enabled/

# Remove default config
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```


***

## **Phase 6: SSL/TLS Setup with Let's Encrypt**[^6][^3]

### **Step 6.1: Get SSL Certificate**

```bash
# First point your domain to EC2 IP (via DNS)

# Create certbot directory
sudo mkdir -p /var/www/certbot

# Get certificate
sudo certbot certonly --webroot -w /var/www/certbot -d your-domain.com -d www.your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

# Test renewal
sudo certbot renew --dry-run
```


### **Step 6.2: Update Nginx Config with SSL Paths**

```bash
# Update the paths in nginx config (already shown above)
sudo systemctl reload nginx
```


***

## **Phase 7: PostgreSQL Setup**

### **Option A: AWS RDS (Recommended for Production)**

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': 'your-rds-endpoint.amazonaws.com',  # RDS endpoint
        'PORT': '5432',
    }
}
```


### **Option B: PostgreSQL on EC2**

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Create database and user
sudo -u postgres psql <<EOF
CREATE DATABASE django_db;
CREATE USER django_user WITH PASSWORD 'strong_password';
ALTER ROLE django_user SET client_encoding TO 'utf8';
ALTER ROLE django_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE django_user SET default_transaction_deferrable TO on;
ALTER ROLE django_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE django_db TO django_user;
\q
EOF
```


***

## **Phase 8: Monitoring \& Logging**[^3]

### **Step 8.1: Check Service Status**

```bash
# Check all services
sudo systemctl status gunicorn
sudo systemctl status nginx
sudo systemctl status postgresql

# Real-time logs
sudo journalctl -u gunicorn -f
sudo tail -f /var/log/nginx/django_access.log
```


### **Step 8.2: Create Log Rotation**

Create `/etc/logrotate.d/django`:

```bash
sudo nano /etc/logrotate.d/django
```

Add:

```
/var/log/django/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 ubuntu ubuntu
    sharedscripts
    postrotate
        systemctl reload gunicorn > /dev/null 2>&1 || true
    endscript
}
```


***

## **Phase 9: Best Practices Checklist**

```bash
# Security
✅ Change SECRET_KEY (generate new one)
✅ Set DEBUG = False
✅ Configure ALLOWED_HOSTS
✅ Enable HTTPS/SSL
✅ Set secure headers (HSTS, CSP, X-Frame-Options)
✅ Configure CSRF protection
✅ Restrict SSH access to specific IPs

# Performance
✅ Configure Gunicorn workers (4 workers = 2*cpu_cores + 1)
✅ Enable Gzip compression in Nginx
✅ Cache static files (expires headers)
✅ Use PostgreSQL with proper indexing
✅ Implement database query optimization

# Monitoring
✅ Set up error logging
✅ Monitor disk space
✅ Set up automated backups for database
✅ Use CloudWatch for metrics

# Deployment
✅ Use GitHub Actions for CI/CD
✅ Implement database backups
✅ Version control all configurations
✅ Document deployment process
```


***

## **Phase 10: Deployment Automation (GitHub Actions)**

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to EC2

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Deploy to EC2
      env:
        PRIVATE_KEY: ${{ secrets.EC2_PRIVATE_KEY }}
        HOST: ${{ secrets.EC2_HOST }}
        USER: ${{ secrets.EC2_USER }}
      run: |
        mkdir -p ~/.ssh
        echo "$PRIVATE_KEY" > ~/.ssh/private_key
        chmod 600 ~/.ssh/private_key
        ssh -i ~/.ssh/private_key -o StrictHostKeyChecking=no $USER@$HOST << 'EOF'
          cd /var/www/django_app
          git pull origin main
          source venv/bin/activate
          pip install -r requirements.txt
          python manage.py migrate
          python manage.py collectstatic --noinput
          sudo systemctl restart gunicorn
          sudo systemctl restart nginx
        EOF
```


***

## **Quick Reference: Common Commands**

```bash
# Restart services
sudo systemctl restart gunicorn
sudo systemctl restart nginx
sudo systemctl restart postgresql

# View logs
sudo journalctl -u gunicorn -n 100
sudo tail -f /var/log/nginx/django_error.log

# Database backup
pg_dump -U django_user django_db > backup.sql

# Check disk space
df -h

# Check memory/CPU
top

# SSH with port forwarding (for database)
ssh -i key.pem -L 5432:localhost:5432 ubuntu@your-ec2-ip
```


***

## **Deployment Checklist for Production**

- [ ] Domain configured with DNS pointing to EC2 IP
- [ ] Security group rules configured (SSH, HTTP, HTTPS)
- [ ] SSL certificate installed and auto-renewal enabled
- [ ] `.env.prod` file created with all secrets
- [ ] Database configured and migrations run
- [ ] Static files collected
- [ ] Gunicorn service enabled and running
- [ ] Nginx configuration tested and running
- [ ] Logs directory created with proper permissions
- [ ] Automated backups scheduled
- [ ] Monitoring/alerting configured
- [ ] GitHub Actions or GitLab CI/CD pipeline set up

***

**Your setup is production-grade and follows Django/AWS best practices for 2025!** You now have:

- ✅ Gunicorn WSGI server
- ✅ Nginx reverse proxy with SSL/TLS
- ✅ PostgreSQL database
- ✅ Automated logging
- ✅ Security hardening
- ✅ Scalable architecture

Would you like me to help with:

1. **GitHub Actions CI/CD pipeline setup**?
2. **Docker containerization** for easier deployment?
3. **AWS RDS configuration** for managed database?
4. **CloudFront + S3** for static/media files?
5. **Monitoring with CloudWatch** or **Prometheus**?
<span style="display:none">[^10][^11][^12][^13][^14][^15][^16][^17][^18][^19][^20][^21][^22][^23][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu

[^2]: https://www.youtube.com/watch?v=3yhIeWoS5cc

[^3]: http://github.com/Kartikk-26/Django-Application-Deployment-on-EC2

[^4]: https://www.linkedin.com/pulse/deploy-django-application-ec2-postgresql-s3-domain-ssl-rashid-v6dic

[^5]: https://muktar.tech/a-step-by-step-guide-to-deploying-a-django-app-on-amazon-ec2-with-nginx-999bcd7e08de

[^6]: https://testdriven.io/blog/django-docker-https-aws/

[^7]: http://arxiv.org/pdf/2309.16962.pdf

[^8]: https://arxiv.org/pdf/1904.02184.pdf

[^9]: http://arxiv.org/pdf/2503.07437.pdf

[^10]: http://arxiv.org/pdf/1508.04973.pdf

[^11]: https://arxiv.org/pdf/2210.01073.pdf

[^12]: https://joss.theoj.org/papers/10.21105/joss.01584.pdf

[^13]: https://arxiv.org/pdf/2503.09089.pdf

[^14]: https://arxiv.org/pdf/2410.12642.pdf

[^15]: https://www.youtube.com/watch?v=tryZWxTVDks

[^16]: https://www.linkedin.com/pulse/how-deploy-django-application-aws-ubuntu-ec2-nginx-uwsgi-yiqing-lan

[^17]: https://blog.devgenius.io/how-to-deploy-a-django-project-on-an-amazon-ec2-instance-with-apache-875f925d0a9a

[^18]: https://www.freecodecamp.org/news/how-to-deploy-django-project-on-ec2/

[^19]: https://www.geeksforgeeks.org/python/how-to-deploy-django-application-in-aws-ec2/

[^20]: https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/

[^21]: https://testdriven.io/blog/deploying-django-to-ec2-with-docker-and-gitlab/

[^22]: https://seenode.com/blog/deploy-a-django-app-on-aws-ec2-with-gunicorn-and-nginx

[^23]: https://www.youtube.com/watch?v=KItpu15ZmkY

