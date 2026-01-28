# Deployment Architecture Documentation

## Overview

This document explains the complete deployment architecture for DocsAI on EC2 Ubuntu, including how all components work together.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Internet / Users                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    EC2 Ubuntu Server                         │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Nginx (Port 80/443)                      │  │
│  │  - Reverse Proxy                                      │  │
│  │  - SSL Termination                                    │  │
│  │  - Static File Serving                                │  │
│  │  - Rate Limiting                                      │  │
│  └──────────────┬───────────────────────────────────────┘  │
│                 │                                          │
│                 │ Unix Socket                              │
│                 ▼                                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Gunicorn (WSGI Server)                        │  │
│  │  - Multiple Workers                                  │  │
│  │  - Process Management                                │  │
│  │  - Managed by systemd                                │  │
│  └──────────────┬───────────────────────────────────────┘  │
│                 │                                          │
│                 ▼                                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Django Application                            │  │
│  │  - /home/ubuntu/docsai/                              │  │
│  │  - Python Virtual Environment                         │  │
│  │  - Environment: .env.prod                            │  │
│  └──────────────┬───────────────────────────────────────┘  │
│                 │                                          │
│        ┌────────┴────────┐                                │
│        │                 │                                │
│        ▼                 ▼                                │
│  ┌──────────┐    ┌──────────────┐                       │
│  │PostgreSQL│    │  S3 Storage   │                       │
│  │ (Local   │    │  (Optional)   │                       │
│  │  or RDS) │    │               │                       │
│  └──────────┘    └───────────────┘                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. Nginx (Reverse Proxy)

**Purpose**: 
- Receives HTTP/HTTPS requests from clients
- Routes requests to Gunicorn via Unix socket
- Serves static files directly (CSS, JS, images)
- Handles SSL/TLS termination
- Implements rate limiting

**Configuration**:
- Location: `/etc/nginx/sites-available/docsai.conf`
- Upstream: `unix:/run/gunicorn.sock`
- Static files: `/home/ubuntu/docsai/staticfiles/`
- Media files: `/home/ubuntu/docsai/media/`

**Key Features**:
- Gzip compression
- Security headers (XSS, CSRF protection)
- Rate limiting (API: 10 req/s, General: 30 req/s)
- Client upload size limit: 50MB

**Files**:
- `deploy/nginx/docsai.conf` - SSL configuration
- `deploy/nginx/docsai-http-only.conf` - HTTP-only configuration
- `deploy/nginx/install-nginx.sh` - Installation script

---

### 2. Gunicorn (WSGI Server)

**Purpose**:
- Runs Django application
- Manages multiple worker processes
- Handles request/response cycle
- Communicates with Nginx via Unix socket

**Configuration**:
- Location: `config/gunicorn/production.py`
- Socket: `unix:/run/gunicorn.sock`
- Workers: `CPU_COUNT * 2 + 1`
- Worker class: `sync`
- Timeout: 30 seconds

**Process Management**:
- Managed by systemd
- Auto-restart on failure
- Logs to: `/var/log/django/gunicorn-*.log`

**Files**:
- `deploy/systemd/gunicorn.service` - systemd service file
- `deploy/systemd/gunicorn.socket` - systemd socket file
- `deploy/systemd/install-systemd.sh` - Installation script

---

### 3. Django Application

**Purpose**:
- Core application logic
- Handles business logic
- Database interactions
- API endpoints

**Structure**:
```
/home/ubuntu/docsai/
├── apps/              # Django applications
├── config/            # Configuration
│   ├── settings/      # Environment-based settings
│   └── gunicorn/      # Gunicorn configs
├── deploy/            # Deployment scripts
├── staticfiles/       # Collected static files
├── media/             # User uploads
├── logs/              # Application logs
├── venv/              # Python virtual environment
├── .env.prod          # Production environment variables
└── manage.py          # Django management script
```

**Environment Configuration**:
- File: `.env.prod`
- Settings: `config.settings.production`
- WSGI: `config.wsgi:application`

**Key Settings**:
- `DEBUG=False`
- `DJANGO_ENV=production`
- `ALLOWED_HOSTS` - EC2 IP and/or domain
- Database configuration
- Static/media file storage (S3 or local)

---

### 4. Database (PostgreSQL)

**Options**:

**Option A: Local PostgreSQL on EC2**
- Installed via `apt install postgresql`
- Database: `docsai`
- User: `docsai_user`
- Managed locally

**Option B: AWS RDS**
- External managed database
- Configured via `.env.prod`
- Better for production scalability

**Configuration**:
```env
DATABASE_ENGINE=postgresql
DATABASE_NAME=docsai
DATABASE_USER=docsai_user
DATABASE_PASSWORD=<password>
DATABASE_HOST=localhost  # or RDS endpoint
DATABASE_PORT=5432
```

---

### 5. Static and Media Files

**Static Files** (CSS, JS, images):
- Collected via: `python manage.py collectstatic`
- Location: `/home/ubuntu/docsai/staticfiles/`
- Served by: Nginx directly (or S3 if configured)

**Media Files** (User uploads):
- Location: `/home/ubuntu/docsai/media/` (or S3)
- Served by: Nginx (local) or S3 (cloud)

**S3 Storage** (Optional):
- Configured in `.env.prod`:
  ```env
  AWS_ACCESS_KEY_ID=<key>
  AWS_SECRET_ACCESS_KEY=<secret>
  S3_BUCKET_NAME=<bucket>
  AWS_REGION=us-east-1
  ```

---

## Deployment Flow

### Initial Deployment (full-deploy.sh)

```
1. Prerequisites Check
   ├── Verify project directory exists
   ├── Check manage.py exists
   └── Verify deploy scripts present

2. System Setup
   ├── Update system packages
   ├── Install Python, PostgreSQL, Nginx
   └── Install build tools and dependencies

3. Database Setup (Optional)
   ├── Install PostgreSQL (if local)
   ├── Create database and user
   └── Set permissions

4. Python Environment
   ├── Create virtual environment
   ├── Upgrade pip
   └── Install requirements.txt

5. Environment Configuration
   ├── Copy .env.prod.example to .env.prod
   ├── Generate SECRET_KEY
   ├── Set DJANGO_ENV=production
   ├── Set DEBUG=False
   └── Configure ALLOWED_HOSTS

6. Django Setup
   ├── Run migrations
   ├── Collect static files
   ├── Validate environment
   └── Create superuser (optional)

7. Gunicorn Service
   ├── Install systemd service files
   ├── Set permissions
   ├── Enable and start service
   └── Verify status

8. Nginx Configuration
   ├── Copy Nginx config
   ├── Update server_name
   ├── Test configuration
   └── Reload Nginx

9. SSL Setup (Optional)
   ├── Install Certbot
   ├── Obtain certificate
   ├── Update Nginx config
   └── Enable auto-renewal

10. Log Rotation
    ├── Install logrotate config
    └── Test configuration

11. Firewall
    ├── Allow SSH
    ├── Allow HTTP/HTTPS
    └── Enable UFW

12. Verification
    ├── Check Gunicorn status
    ├── Check Nginx status
    └── Test health endpoint
```

### Update Deployment (remote-deploy.sh)

```
1. Activate virtual environment
2. Update Python dependencies
3. Run database migrations
4. Collect static files
5. Restart Gunicorn service
```

---

## File Permissions

```
/home/ubuntu/docsai/
├── Owner: ubuntu:ubuntu
├── Permissions: 755 (directories), 644 (files)
└── .env.prod: 600 (readable only by owner)

/var/log/django/
├── Owner: ubuntu:www-data
└── Permissions: 755

/run/gunicorn.sock
├── Owner: www-data:www-data
└── Permissions: 666
```

---

## Network Flow

### HTTP Request Flow

```
Client Request
    │
    ▼
EC2 Security Group (Port 80/443)
    │
    ▼
Nginx (Port 80/443)
    │
    ├── Static Files → Direct Response
    │
    └── Application → Unix Socket → Gunicorn → Django
                                        │
                                        ▼
                                    Database/Storage
```

### Unix Socket Communication

```
Nginx ←→ /run/gunicorn.sock ←→ Gunicorn
```

**Advantages**:
- Faster than TCP/IP
- No network overhead
- More secure (local only)
- Lower latency

---

## Security Considerations

### 1. Firewall (UFW)
- SSH: Port 22 (restricted to specific IPs)
- HTTP: Port 80 (0.0.0.0/0)
- HTTPS: Port 443 (0.0.0.0/0)

### 2. SSL/TLS
- Let's Encrypt certificates
- Auto-renewal via Certbot
- HSTS headers
- TLS 1.2+ only

### 3. Application Security
- `DEBUG=False` in production
- `SECRET_KEY` in `.env.prod` (600 permissions)
- `ALLOWED_HOSTS` restricted
- CSRF protection enabled
- XSS protection headers

### 4. Database Security
- Strong passwords
- Restricted user permissions
- Network isolation (RDS security groups)

---

## Monitoring and Logging

### Log Locations

**Gunicorn Logs**:
- Access: `/var/log/django/gunicorn-access.log`
- Error: `/var/log/django/gunicorn-error.log`
- Systemd: `sudo journalctl -u gunicorn -f`

**Nginx Logs**:
- Access: `/var/log/nginx/docsai_access.log`
- Error: `/var/log/nginx/docsai_error.log`

**Django Logs**:
- Application: `/home/ubuntu/docsai/logs/django.log`

**Log Rotation**:
- Daily rotation
- Keep 14 days
- Compress old logs
- Configured via `/etc/logrotate.d/docsai`

---

## Service Management

### systemd Services

**Gunicorn**:
```bash
sudo systemctl status gunicorn
sudo systemctl restart gunicorn
sudo systemctl stop gunicorn
sudo systemctl start gunicorn
```

**Nginx**:
```bash
sudo systemctl status nginx
sudo systemctl restart nginx
sudo systemctl reload nginx  # Graceful reload
```

**Socket**:
```bash
sudo systemctl status gunicorn.socket
```

---

## Troubleshooting Guide

### 502 Bad Gateway
1. Check Gunicorn: `sudo systemctl status gunicorn`
2. Check socket: `ls -la /run/gunicorn.sock`
3. Check logs: `sudo journalctl -u gunicorn -f`

### Static Files 404
1. Run: `python manage.py collectstatic --noinput`
2. Check directory: `ls -la /home/ubuntu/docsai/staticfiles/`
3. Verify Nginx config: `sudo nginx -t`

### Database Connection Error
1. Check `.env.prod` database settings
2. Test connection: `python manage.py dbshell`
3. Verify PostgreSQL is running: `sudo systemctl status postgresql`

### SSL Certificate Issues
1. Check DNS: `dig example.com`
2. Verify cert: `sudo certbot certificates`
3. Test renewal: `sudo certbot renew --dry-run`

---

## Performance Optimization

### Gunicorn Workers
- Formula: `CPU_COUNT * 2 + 1`
- Example: 2 CPU = 5 workers
- Adjust based on load testing

### Nginx Caching
- Static files: 30 days cache
- Gzip compression enabled
- Connection keep-alive

### Database Connection Pooling
- `CONN_MAX_AGE=600` (10 minutes)
- Reduces connection overhead

---

## Scaling Considerations

### Vertical Scaling
- Increase EC2 instance size
- More CPU/RAM = more Gunicorn workers
- Better database performance

### Horizontal Scaling
- Multiple EC2 instances
- Load balancer (ALB/ELB)
- Shared database (RDS)
- Shared storage (S3)

### Database Scaling
- RDS with read replicas
- Connection pooling
- Query optimization

---

## Backup Strategy

### Database Backups
- RDS automated backups (if using RDS)
- Manual: `pg_dump docsai > backup.sql`
- Schedule via cron

### Application Backups
- Code: Git repository
- Media files: S3 versioning
- Environment: Secure storage (AWS Secrets Manager)

---

## CI/CD Integration

### GitHub Actions
- Workflow: `.github/workflows/deploy.yml`
- Triggers: Push to `main` or manual
- Process:
  1. SSH to EC2
  2. Git pull
  3. Run `remote-deploy.sh`
  4. Verify health endpoint

---

## Summary

The deployment architecture uses:
- **Nginx** as reverse proxy and static file server
- **Gunicorn** as WSGI application server
- **Django** as web framework
- **PostgreSQL** as database
- **systemd** for service management
- **Let's Encrypt** for SSL certificates

All components work together to provide a secure, scalable, and maintainable production deployment.
