<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# deploy a Django python codebase in EC2 machine in Ubuntu with best practices

Deploying a Django app on an EC2 Ubuntu instance follows production standards using Gunicorn as the WSGI server, Nginx as a reverse proxy, systemd for process management, and security hardening.[^1][^2][^3]

## Launch EC2 Instance

Launch a t2.micro (free tier eligible) Ubuntu 22.04 LTS instance in AWS EC2. Configure the security group for inbound SSH (port 22), HTTP (80), HTTPS (443). Create and download an SSH key pair (.pem), then set permissions: `chmod 400 your-key.pem`.[^2][^1]

SSH in: `ssh -i your-key.pem ubuntu@your-ec2-public-ip`.

## Server Setup

Update packages and install essentials: `sudo apt update && sudo apt upgrade -y && sudo apt install python3-pip python3-venv nginx gunicorn git postgresql postgresql-contrib libpq-dev ufw -y`. Enable UFW firewall: `sudo ufw allow OpenSSH && sudo ufw allow 'Nginx Full' && sudo ufw --force enable`.[^4][^3][^2]

Create a PostgreSQL database/user: `sudo -u postgres psql`, then `CREATE DATABASE django_db; CREATE USER django_user WITH PASSWORD 'securepass'; GRANT ALL PRIVILEGES ON DATABASE django_db TO django_user; ALTER ROLE django_user SET client_encoding TO 'utf8'; ALTER ROLE django_user SET default_transaction_isolation TO 'read committed'; ALTER ROLE django_user SET timezone TO 'UTC'; \q`.[^3]

## Project Deployment

In `/home/ubuntu/`, clone your repo: `git clone your-repo.git && cd your-project`. Create venv: `python3 -m venv venv && source venv/bin/activate`. Install deps: `pip install -r requirements.txt gunicorn psycopg2-binary`.[^2]

Update `settings.py`: `DEBUG = False`, `ALLOWED_HOSTS = ['your-ec2-ip', 'your-domain.com']`, `DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': 'django_db', 'USER': 'django_user', 'PASSWORD': 'securepass', 'HOST': 'localhost'}}`, add `STATIC_ROOT = BASE_DIR / 'static/'`. Run `python manage.py makemigrations && python manage.py migrate && python manage.py collectstatic --noinput && python manage.py createsuperuser`.[^3][^2]

Test Gunicorn: `gunicorn --bind 0.0.0.0:8000 yourproject.wsgi` (visit http://your-ec2-ip:8000).[^2]

## Gunicorn Systemd Service

Create `/etc/systemd/system/gunicorn.service`:

```
[Unit]
Description=Gunicorn for Django
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/your-project
Environment="PATH=/home/ubuntu/your-project/venv/bin"
ExecStart=/home/ubuntu/your-project/venv/bin/gunicorn --workers 3 --bind unix:/run/gunicorn.sock yourproject.wsgi:application

[Install]
WantedBy=multi-user.target
```

Enable/start: `sudo systemctl daemon-reload && sudo systemctl start gunicorn && sudo systemctl enable gunicorn`.[^4][^3][^2]

## Nginx Configuration

Create `/etc/nginx/sites-available/yourproject`:

```
server {
    listen 80;
    server_name your-ec2-ip your-domain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root /home/ubuntu/your-project;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
```

Enable: `sudo ln -s /etc/nginx/sites-available/yourproject /etc/nginx/sites-enabled && sudo nginx -t && sudo systemctl restart nginx`.[^3][^2]

## Security and HTTPS

Install Certbot: `sudo apt install certbot python3-certbot-nginx -y && sudo certbot --nginx -d your-domain.com`. Use `.env` for secrets (django-environ). Set `SECURE_SSL_REDIRECT = True` in settings.py post-SSL.[^4][^2]

Monitor: `sudo journalctl -u gunicorn -f`, `sudo tail -f /var/log/nginx/error.log`. Scale workers via `--workers=(2*CPU)+1`.[^2][^3]
<span style="display:none">[^10][^11][^12][^13][^14][^15][^16][^17][^18][^19][^20][^21][^22][^23][^24][^25][^5][^6][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://seenode.com/blog/deploy-a-django-app-on-aws-ec2-with-gunicorn-and-nginx

[^2]: https://jpit.az/uploads/article/en/2025_2/OPTIMIZATION_OF_ACCESS_TO_STATIC_DATA_IN_DISTRIBUTED_SYSTEMS_A_KUBERNETES-BASED_SOLUTION_WITH_POSTGRESQL_AND_DJANGO.pdf

[^3]: https://arxiv.org/abs/2507.03487

[^4]: http://github.com/Kartikk-26/Django-Application-Deployment-on-EC2

[^5]: https://www.mdpi.com/2076-3417/8/6/965/pdf

[^6]: https://arxiv.org/pdf/1905.07314.pdf

[^7]: https://arxiv.org/pdf/2305.13933.pdf

[^8]: https://arxiv.org/pdf/2206.00699.pdf

[^9]: https://www.mdpi.com/2079-9292/12/2/357/pdf?version=1673344794

[^10]: https://arxiv.org/pdf/1904.02184.pdf

[^11]: https://www.mdpi.com/1424-8220/23/4/2215

[^12]: http://arxiv.org/pdf/2309.16962.pdf

[^13]: https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu

[^14]: https://www.icertglobal.com/blog/deploying-django-projects-on-aws-a-step-by-step-guide-blog

[^15]: https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Server-side/Django/Deployment

[^16]: https://www.linkedin.com/pulse/how-deploy-django-application-aws-ubuntu-ec2-nginx-uwsgi-yiqing-lan

[^17]: https://www.freecodecamp.org/news/how-to-deploy-django-project-on-ec2/

[^18]: https://realpython.com/django-nginx-gunicorn/

[^19]: https://seenode.com/blog/deploy-a-django-app-on-aws-ec2-with-gunicorn-and-nginx/

[^20]: https://www.linkedin.com/pulse/deploy-django-application-ec2-postgresql-s3-domain-ssl-rashid-v6dic

[^21]: https://gist.github.com/rmiyazaki6499/92a7dc283e160333defbae97447c5a83

[^22]: https://www.youtube.com/watch?v=KItpu15ZmkY

[^23]: https://stackoverflow.com/questions/77711250/deploying-django-project-in-an-amazon-ec2-ubuntu-instance

[^24]: https://dev.to/awscommunity-asean/create-and-deploy-python-django-application-in-aws-ec2-instance-4hbm

[^25]: https://github.com/erkamesen/Django-AWS-Deploy

