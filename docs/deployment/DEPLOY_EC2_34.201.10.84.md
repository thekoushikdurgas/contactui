# DocsAI EC2 Runbook: 34.201.10.84

Step-by-step deployment for **DocsAI** on **EC2 Ubuntu** at **34.201.10.84**. Use **HTTP-only** (no domain) first; add **SSL** when you have a domain.

---

## Quick reference

| Item | Value |
|------|--------|
| **EC2 IP** | 34.201.10.84 |
| **App dir** | `/var/www/docsai` (recommended) |
| **Env file** | `/var/www/docsai/.env.prod` |
| **Health** | `curl http://34.201.10.84/api/v1/health/` |
| **Logs** | `sudo journalctl -u gunicorn -f`, `tail -f /var/log/nginx/docsai_error.log` |

---

## 1. Prerequisites

- EC2 Ubuntu 22.04, reachable at 34.201.10.84
- SSH key (`.pem`), e.g. `ubuntu` user
- Git access to the DocsAI repo

---

## 2. EC2 & security group

- **AMI**: Ubuntu 22.04 LTS  
- **Instance**: `t2.micro` or `t2.small`, 20–30 GB EBS  
- **Security group**:
  - SSH (22) — your IP
  - HTTP (80) — `0.0.0.0/0`
  - HTTPS (443) — `0.0.0.0/0`
  - TCP 5432 — only if PostgreSQL runs on this EC2

```bash
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@34.201.10.84
```

---

## 3. System packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
  python3-pip python3-venv python3-dev \
  postgresql-client nginx git curl wget \
  build-essential libpq-dev
```

For **SSL later** (when you have a domain):

```bash
sudo apt install -y certbot python3-certbot-nginx
```

---

## 4. Database (PostgreSQL)

### Option A: PostgreSQL on EC2

```bash
sudo apt install -y postgresql postgresql-contrib
sudo -u postgres psql -c "CREATE DATABASE docsai;"
sudo -u postgres psql -c "CREATE USER docsai_user WITH PASSWORD 'your-secure-password';"
sudo -u postgres psql -c "ALTER ROLE docsai_user SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE docsai_user SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE docsai TO docsai_user;"
```

### Option B: RDS

Create DB and user in RDS; set `DATABASE_HOST` to the RDS endpoint in `.env.prod`.

---

## 5. Project setup

```bash
sudo mkdir -p /var/www/docsai
sudo chown -R ubuntu:ubuntu /var/www/docsai
cd /var/www/docsai
git clone <your-repo-url> .
```

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

---

## 6. Production env

```bash
cp .env.prod.example .env.prod
nano .env.prod   # or vim
```

Set at least:

- `SECRET_KEY` — from `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- `ALLOWED_HOSTS=34.201.10.84,localhost,127.0.0.1`
- `DEBUG=False`
- `DJANGO_ENV=production`
- `DATABASE_*` (name, user, password, host, port)

---

## 7. Migrate, static, superuser

If you see `bash: cd: /var/www/docsai: No such file or directory`, you deployed the code to a different path
(e.g. `/home/ubuntu/contactui`). In that case, run the commands from your actual project directory.

```bash
cd /var/www/docsai
source venv/bin/activate
export DJANGO_ENV=production
python manage.py migrate --noinput
python manage.py createsuperuser
python manage.py validate_env
python manage.py check --deploy

# If you enabled S3 static/media in production, collectstatic will upload to S3.
# NOTE: Buckets with Object Ownership = "Bucket owner enforced" do not allow ACLs.
# This repo sets AWS_DEFAULT_ACL=None; ensure your bucket policy/IAM grants access.
python manage.py collectstatic --noinput
mkdir -p logs
```

---

## 8. Systemd (Gunicorn)

```bash
cd /var/www/docsai
sudo bash deploy/systemd/install-systemd.sh
```

Check:

```bash
sudo systemctl status gunicorn
```

---

## 9. Nginx

### HTTP-only (no domain, recommended first)

```bash
cd /var/www/docsai
sudo bash deploy/nginx/install-nginx.sh --http-only
```

### With domain + SSL

1. Point DNS (e.g. `docsai.example.com`) to `34.201.10.84`
2. Install Nginx (no `--http-only`), then SSL:

```bash
sudo bash deploy/nginx/install-nginx.sh
sudo bash deploy/ssl/setup-ssl.sh docsai.example.com admin@example.com
```

---

## 10. Logrotate (optional)

```bash
cd /var/www/docsai
sudo bash deploy/logrotate/install-logrotate.sh
```

---

## 11. Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

---

## 12. Verify

```bash
# HTTP-only
curl -s http://34.201.10.84/api/v1/health/ | head -20

# With SSL
curl -s https://docsai.example.com/api/v1/health/ | head -20
```

Open `http://34.201.10.84/` (or `https://...`), log in with the superuser.

---

## 13. Using the master deploy script

**After** clone, venv, `pip install`, and `.env.prod` exist:

### HTTP-only

```bash
cd /var/www/docsai
sudo ./deploy/deploy.sh --http-only
```

### With domain + SSL

```bash
sudo ./deploy/deploy.sh example.com admin@example.com
```

The script installs deps, systemd, Nginx, optional SSL, logrotate, runs collectstatic and migrate.

---

## 14. Common commands

| Task | Command |
|------|---------|
| Restart Gunicorn | `sudo systemctl restart gunicorn` |
| Gunicorn logs | `sudo journalctl -u gunicorn -f` |
| Nginx error log | `sudo tail -f /var/log/nginx/docsai_error.log` |
| Django app log | `tail -f /var/www/docsai/logs/django.log` |
| Reload Nginx | `sudo systemctl reload nginx` |

---

## 15. GitHub Actions deployment

Deploy automatically on **push to `main`** or **manually** via workflow:

1. **Secrets** (Settings → Secrets and variables → Actions): `EC2_SSH_PRIVATE_KEY`, `EC2_HOST` (e.g. `34.201.10.84`), `EC2_USER` (e.g. `ubuntu`).
2. **Trigger**: Push to `main` or **Actions → Deploy to EC2 → Run workflow**.
3. The workflow SSHs to EC2, runs `git fetch` / `git reset`, then `deploy/remote-deploy.sh` (pip, migrate, collectstatic, restart Gunicorn).

See **[GITHUB_ACTIONS_DEPLOY.md](./GITHUB_ACTIONS_DEPLOY.md)** for details, troubleshooting, and optional CI gating.

---

## 16. Troubleshooting

- **502 Bad Gateway**: Gunicorn not running or socket wrong. Check `systemctl status gunicorn` and `ls -la /run/gunicorn.sock`.
- **Static 404**: Run `python manage.py collectstatic --noinput`; ensure `/var/www/docsai/staticfiles` exists and Nginx `alias` is correct.
- **DB connection**: Verify `DATABASE_*` in `.env.prod`, and that Postgres allows connections from the app (e.g. `pg_hba.conf`, RDS security group).

---

See also: [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md), [GITHUB_ACTIONS_DEPLOY.md](./GITHUB_ACTIONS_DEPLOY.md), [.env.prod.example](../../.env.prod.example).
