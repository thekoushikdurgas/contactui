# Troubleshooting Deployment Issues

## Gunicorn Service Fails to Start

### Symptoms
- Error: `Job for gunicorn.service failed because the control process exited with error code`
- Service status shows `failed` or `inactive`

### Quick Fixes

#### 1. Check Service Logs
```bash
sudo journalctl -u gunicorn.service -f
sudo journalctl -u gunicorn.service -n 50 --no-pager
```

#### 2. Run Troubleshooting Script
```bash
cd /home/ubuntu/docsai
sudo bash deploy/troubleshoot-gunicorn.sh
```

#### 3. Common Issues and Solutions

**Issue: Gunicorn config module not found**
```bash
cd /home/ubuntu/docsai
source venv/bin/activate
python -c "import config.gunicorn.production"
```
If this fails, check:
- Virtual environment is activated
- PYTHONPATH includes project directory
- Config files exist in `config/gunicorn/`

**Issue: Socket permissions**
```bash
# Check socket exists and permissions
ls -la /run/gunicorn.sock

# Restart socket service
sudo systemctl restart gunicorn.socket
sudo systemctl restart gunicorn.service
```

**Issue: Environment file not readable**
```bash
# Fix permissions
sudo chown ubuntu:ubuntu /home/ubuntu/docsai/.env.prod
sudo chmod 600 /home/ubuntu/docsai/.env.prod

# Verify ubuntu user can read it
sudo -u ubuntu test -r /home/ubuntu/docsai/.env.prod && echo "OK" || echo "FAILED"
```

**Issue: Type=notify not supported**
If Gunicorn doesn't support systemd notifications, switch to Type=simple:

```bash
cd /home/ubuntu/docsai
sudo cp deploy/systemd/gunicorn.service.simple /etc/systemd/system/gunicorn.service
sudo systemctl daemon-reload
sudo systemctl restart gunicorn.service
```

**Issue: WSGI application import fails**
```bash
cd /home/ubuntu/docsai
source venv/bin/activate
export DJANGO_ENV=production
python -c "from config.wsgi import application"
```

If this fails:
- Check `.env.prod` has correct settings
- Verify database connection
- Check Django settings are valid

#### 4. Manual Gunicorn Test

Test Gunicorn manually to see exact error:

```bash
cd /home/ubuntu/docsai
source venv/bin/activate
export DJANGO_ENV=production
export PATH="/home/ubuntu/docsai/venv/bin:$PATH"
export PYTHONPATH="/home/ubuntu/docsai"

# Test with config file
gunicorn --config config.gunicorn.production config.wsgi:application --bind unix:/run/gunicorn.sock

# Or test with command-line args
gunicorn \
  --workers 3 \
  --worker-class sync \
  --timeout 30 \
  --bind unix:/run/gunicorn.sock \
  config.wsgi:application
```

#### 5. Reset Service

If all else fails, reset the service:

```bash
sudo systemctl stop gunicorn.service
sudo systemctl stop gunicorn.socket
sudo rm -f /run/gunicorn.sock
sudo systemctl daemon-reload
sudo systemctl start gunicorn.socket
sudo systemctl start gunicorn.service
sudo systemctl status gunicorn.service
```

---

## Nginx 502 Bad Gateway

### Symptoms
- Browser shows "502 Bad Gateway"
- Nginx error log shows connection refused

### Solutions

#### 1. Check Gunicorn is Running
```bash
sudo systemctl status gunicorn
sudo journalctl -u gunicorn -f
```

#### 2. Check Socket File
```bash
ls -la /run/gunicorn.sock
```

If socket doesn't exist:
```bash
sudo systemctl restart gunicorn.socket
sudo systemctl restart gunicorn.service
```

#### 3. Check Nginx Configuration
```bash
sudo nginx -t
sudo systemctl reload nginx
```

#### 4. Check Socket Permissions
```bash
# Socket should be readable by www-data (Nginx user)
ls -la /run/gunicorn.sock
# Should show: srw-rw-rw- 1 www-data www-data

# If wrong, restart socket service
sudo systemctl restart gunicorn.socket
```

---

## Database Connection Errors

### Symptoms
- Migration fails
- Application can't connect to database
- Error: "could not connect to server"

### Solutions

#### 1. Check Database Settings in .env.prod
```bash
grep DATABASE /home/ubuntu/docsai/.env.prod
```

#### 2. Test Database Connection
```bash
cd /home/ubuntu/docsai
source venv/bin/activate
export DJANGO_ENV=production
python manage.py dbshell
```

#### 3. For Local PostgreSQL
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check database exists
sudo -u postgres psql -l | grep docsai

# Test connection
sudo -u postgres psql -d docsai -c "SELECT 1;"
```

#### 4. For RDS
- Verify security group allows connections from EC2
- Check RDS endpoint is correct
- Verify credentials are correct
- Test from EC2: `psql -h <rds-endpoint> -U <user> -d <database>`

---

## Static Files 404

### Symptoms
- CSS/JS files return 404
- Page loads but no styling

### Solutions

#### 1. Collect Static Files
```bash
cd /home/ubuntu/docsai
source venv/bin/activate
export DJANGO_ENV=production
python manage.py collectstatic --noinput
```

#### 2. Check Static Files Directory
```bash
ls -la /home/ubuntu/docsai/staticfiles/
```

#### 3. Check Nginx Configuration
```bash
# Verify static files location in Nginx config
grep -A 5 "location /static" /etc/nginx/sites-available/docsai.conf

# Should point to: /home/ubuntu/docsai/staticfiles/
```

#### 4. Check Permissions
```bash
sudo chown -R ubuntu:ubuntu /home/ubuntu/docsai/staticfiles/
sudo chmod -R 755 /home/ubuntu/docsai/staticfiles/
```

---

## SSL Certificate Issues

### Symptoms
- SSL certificate not found
- Certificate expired
- HTTPS not working

### Solutions

#### 1. Check Certificate Status
```bash
sudo certbot certificates
```

#### 2. Renew Certificate
```bash
sudo certbot renew --dry-run  # Test
sudo certbot renew            # Actual renewal
sudo systemctl reload nginx
```

#### 3. Check DNS
```bash
# Verify DNS points to EC2 IP
dig your-domain.com
nslookup your-domain.com
```

#### 4. Re-run SSL Setup
```bash
cd /home/ubuntu/docsai
sudo bash deploy/ssl/setup-ssl.sh your-domain.com admin@example.com
```

---

## Environment Variable Issues

### Symptoms
- Settings not loading
- Wrong configuration values
- Application behaves unexpectedly

### Solutions

#### 1. Check .env.prod File
```bash
cat /home/ubuntu/docsai/.env.prod
```

#### 2. Validate Environment
```bash
cd /home/ubuntu/docsai
source venv/bin/activate
export DJANGO_ENV=production
python manage.py validate_env
```

#### 3. Check Service Environment
```bash
# Check what environment variables Gunicorn sees
sudo systemctl show gunicorn.service | grep Environment
```

#### 4. Reload Service After .env.prod Changes
```bash
sudo systemctl daemon-reload
sudo systemctl restart gunicorn.service
```

---

## General Debugging Steps

### 1. Check All Services
```bash
sudo systemctl status gunicorn nginx postgresql
```

### 2. Check Logs
```bash
# Gunicorn logs
sudo journalctl -u gunicorn -f

# Nginx logs
sudo tail -f /var/log/nginx/docsai_error.log
sudo tail -f /var/log/nginx/docsai_access.log

# Django logs
tail -f /home/ubuntu/docsai/logs/django.log
```

### 3. Test Health Endpoint
```bash
curl http://34.201.10.84/api/v1/health/
# or
curl https://your-domain.com/api/v1/health/
```

### 4. Verify Firewall
```bash
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

---

## Getting Help

If issues persist:

1. **Run troubleshooting script**:
   ```bash
   sudo bash deploy/troubleshoot-gunicorn.sh
   ```

2. **Collect diagnostic information**:
   ```bash
   # Service status
   sudo systemctl status gunicorn nginx --no-pager > diagnostics.txt
   
   # Recent logs
   sudo journalctl -u gunicorn -n 100 --no-pager >> diagnostics.txt
   
   # Configuration
   cat /etc/systemd/system/gunicorn.service >> diagnostics.txt
   ```

3. **Check documentation**:
   - [DEPLOY_EC2_34.201.10.84.md](../docs/deployment/DEPLOY_EC2_34.201.10.84.md)
   - [DEPLOYMENT_ARCHITECTURE.md](./DEPLOYMENT_ARCHITECTURE.md)
