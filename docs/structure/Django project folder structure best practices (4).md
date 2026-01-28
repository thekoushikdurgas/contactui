<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Django project folder structure best practices

Great! I found current Django best practices. Let me create a comprehensive guide with a production-ready project structure.

## Django Project Folder Structure: Best Practices[^1][^2][^3]

Here's a comprehensive guide to organizing a scalable Django project structure:

### **Recommended Production-Ready Structure**

```
my_project/                          # Project root
├── manage.py                        # Django management script
├── README.md                        # Project documentation
├── requirements.txt                 # Python dependencies
├── .gitignore                      # Git ignore rules
├── .env                            # Environment variables (DO NOT COMMIT)
├── .env.example                    # Example env file
│
├── config/                         # Project configuration (renamed from 'my_project')
│   ├── __init__.py
│   ├── settings/                   # Split settings by environment
│   │   ├── __init__.py
│   │   ├── base.py                # Shared settings
│   │   ├── development.py         # Dev-specific
│   │   ├── production.py          # Production-specific
│   │   ├── testing.py             # Test-specific
│   │   └── local.py               # Local overrides (ignored)
│   ├── urls.py                     # Main URL configuration
│   ├── wsgi.py                     # WSGI entry point
│   └── asgi.py                     # ASGI entry point (async)
│
├── apps/                           # All Django applications
│   ├── __init__.py
│   ├── core/                       # Reusable utilities & base models
│   │   ├── __init__.py
│   │   ├── models.py               # Abstract base models
│   │   ├── utils.py                # Helper functions
│   │   ├── exceptions.py           # Custom exceptions
│   │   ├── constants.py            # App-wide constants
│   │   ├── serializers.py          # Base serializers (DRF)
│   │   └── management/
│   │       └── commands/           # Custom management commands
│   │
│   ├── users/                      # Authentication & User management
│   │   ├── migrations/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── forms.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── permissions.py
│   │   ├── services.py             # Business logic
│   │   ├── tests.py
│   │   ├── templates/
│   │   │   └── users/
│   │   └── static/
│   │       └── users/
│   │
│   ├── products/                   # Product management (example)
│   │   ├── migrations/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── services.py
│   │   ├── tests.py
│   │   ├── templates/
│   │   │   └── products/
│   │   └── static/
│   │       └── products/
│   │
│   └── api/                        # REST API configuration (optional)
│       ├── __init__.py
│       ├── urls.py                 # Central API URL routing
│       └── serializers.py          # Shared serializers
│
├── templates/                      # Project-level templates
│   ├── base.html                   # Base template
│   ├── layout.html
│   ├── errors/                     # Error pages
│   │   ├── 404.html
│   │   └── 500.html
│   └── includes/                   # Reusable snippets
│       ├── navbar.html
│       └── footer.html
│
├── static/                         # Project-level static files
│   ├── css/
│   │   ├── base.css
│   │   └── styles.css
│   ├── js/
│   │   ├── base.js
│   │   └── utils.js
│   └── images/
│       └── logo.png
│
├── media/                          # User-uploaded files
│   └── uploads/
│
├── tests/                          # Integration and end-to-end tests
│   ├── __init__.py
│   ├── conftest.py                 # Pytest configuration
│   ├── test_api.py
│   └── test_integration.py
│
├── logs/                           # Application logs
│   └── .gitkeep
│
├── scripts/                        # Utility scripts
│   ├── seed_db.py                  # Database seeding
│   ├── backup.sh                   # Backup scripts
│   └── deploy.sh                   # Deployment scripts
│
├── docs/                           # Project documentation
│   ├── API.md
│   ├── SETUP.md
│   └── DEPLOYMENT.md
│
├── docker-compose.yml              # Docker Compose for local dev
├── Dockerfile                      # Docker image
└── pyproject.toml                  # Python project metadata (modern)
```


***

### **Key Configuration Best Practices**

#### **1. Split Settings by Environment**[^2]

**config/settings/base.py:**

```python
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = False
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party
    'rest_framework',
    'corsheaders',
    'django_filter',
    
    # Project apps
    'apps.core',
    'apps.users',
    'apps.products',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', 5432),
    }
}

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

**config/settings/development.py:**

```python
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*.local']

# Development logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}

# Optional: Enable Django Debug Toolbar
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']
```

**config/settings/production.py:**

```python
from .base import *

DEBUG = False
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True

# Logging for production
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
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}
```


***

#### **2. App Structure Best Practices**[^3]

Each app should follow consistent internal organization:

```
users/
├── migrations/
│   ├── __init__.py
│   ├── 0001_initial.py
│   └── 0002_add_fields.py
├── management/
│   ├── __init__.py
│   └── commands/
│       ├── __init__.py
│       └── create_admin_user.py
├── __init__.py
├── admin.py            # Django admin customization
├── apps.py             # App configuration
├── models.py           # Database models
├── forms.py            # Django forms
├── serializers.py      # DRF serializers
├── views.py            # Views (CBV recommended)
├── viewsets.py         # DRF viewsets (optional)
├── urls.py             # App-specific URLs
├── permissions.py      # DRF permissions
├── services.py         # Business logic layer
├── tests.py            # Unit tests
├── templates/
│   └── users/
│       ├── user_list.html
│       └── user_detail.html
└── static/
    └── users/
        ├── css/
        └── js/
```


***

#### **3. Use Abstract Base Models**[^3]

**apps/core/models.py:**

```python
from django.db import models

class BaseModel(models.Model):
    """Abstract base model with common fields"""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']
```

**apps/users/models.py:**

```python
from apps.core.models import BaseModel

class User(BaseModel):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    
    class Meta:
        ordering = ['-created_at']
```


***

#### **4. Service Layer Pattern**

**apps/users/services.py:**

```python
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class UserService:
    """Business logic for user operations"""
    
    @staticmethod
    def create_user(email, password, first_name, last_name):
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already exists")
        
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        return user
    
    @staticmethod
    def update_user_profile(user, **kwargs):
        for field, value in kwargs.items():
            if hasattr(user, field):
                setattr(user, field, value)
        user.save()
        return user
```

**apps/users/views.py:**

```python
from rest_framework import viewsets
from rest_framework.decorators import action
from .models import User
from .serializers import UserSerializer
from .services import UserService

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    @action(detail=False, methods=['post'])
    def create_user(self, request):
        user = UserService.create_user(**request.data)
        return Response(UserSerializer(user).data)
```


***

#### **5. Environment Variables Management**

**.env.example:**

```bash
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=my_project_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# AWS/Cloud
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
```

**.gitignore:**

```
.env
.env.local
*.pyc
__pycache__/
*.egg-info/
.Python
venv/
.vscode/
.idea/
*.log
staticfiles/
media/
.DS_Store
```


***

### **Key Organization Principles**[^3]

| Principle | Benefit |
| :-- | :-- |
| **Separate `config` from apps** | Clean namespace, easy to identify project config |
| **Apps folder** | Keeps apps organized, prevents root clutter |
| **Split settings** | Different environments without code changes |
| **Service layer** | Business logic separate from views |
| **Abstract models** | Reduce duplication (timestamps, is_active, etc.) |
| **Tests alongside app** | Easy to maintain and run tests per app |
| **Centralized templates** | Base templates in root for inheritance |
| **Environment variables** | Security-first, no hardcoded credentials |
| **Consistent naming** | Models (models.py), views (views.py), etc. |
| **Docker support** | Modern deployment-first approach |


***

### **Why This Structure Works**

✅ **Scalable** - Add new apps without root clutter
✅ **Maintainable** - Clear separation of concerns
✅ **Testable** - Isolated app tests run independently
✅ **Deployable** - Environment-specific configs built-in
✅ **Production-ready** - Security, logging, static files handled
✅ **Team-friendly** - Developers own their app domains

***

### **Common Commands**

```bash
# Create new Django app
python manage.py startapp --template=path/to/template apps/new_app

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Run development server
DJANGO_SETTINGS_MODULE=config.settings.development python manage.py runserver

# Run tests
python manage.py test

# Collect static files (production)
python manage.py collectstatic --noinput
```

This structure aligns with modern Django practices and scales well from small projects to large team-based applications. For your backend development background, it provides the same separation of concerns and modularity you'd want in a production system.
<span style="display:none">[^10][^11][^12][^13][^14][^15][^16][^17][^18][^19][^20][^21][^22][^23][^24][^25][^26][^27][^28][^29][^30][^31][^32][^33][^4][^5][^6][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://www.geeksforgeeks.org/python/best-practice-for-django-project-working-directory-structure/

[^2]: https://simpleisbetterthancomplex.com/tutorial/2021/06/27/how-to-start-a-production-ready-django-project.html

[^3]: https://www.bluetickconsultants.com/building-a-scalable-and-maintainable-architecture-for-large-scale-django-projects/

[^4]: https://www.cureus.com/articles/413676-improving-adherence-to-national-laparoscopic-appendicectomy-documentation-guidelines-a-quality-improvement-project

[^5]: https://link.springer.com/10.1007/s43683-025-00203-8

[^6]: http://medrxiv.org/lookup/doi/10.1101/2025.09.16.25335847

[^7]: https://ieeexplore.ieee.org/document/11332518/

[^8]: https://invergejournals.com/index.php/ijss/article/view/176

[^9]: https://invergejournals.com/index.php/ijss/article/view/167

[^10]: https://ashpublications.org/blood/article/146/Supplement 1/8120/549717/Quality-initiative-in-first-line-multiple-myeloma

[^11]: https://www.researchprotocols.org/2026/1/e80301

[^12]: https://iopn.library.illinois.edu/journals/aliseacp/article/view/2001

[^13]: https://biss.pensoft.net/article/183171/

[^14]: https://linkinghub.elsevier.com/retrieve/pii/S2215016125000627

[^15]: http://arxiv.org/pdf/2410.10513.pdf

[^16]: http://arxiv.org/pdf/2203.13871.pdf

[^17]: http://arxiv.org/pdf/2410.12114.pdf

[^18]: https://joss.theoj.org/papers/10.21105/joss.01584.pdf

[^19]: https://dx.plos.org/10.1371/journal.pcbi.1009809

[^20]: https://arxiv.org/pdf/2305.15675.pdf

[^21]: http://arxiv.org/pdf/2502.10341.pdf

[^22]: https://forum.djangoproject.com/t/best-practices-for-structuring-django-projects/39835

[^23]: https://www.reddit.com/r/django/comments/1gsuhmj/what_is_the_industry_standard_for_django_project/

[^24]: https://www.hostinger.com/in/tutorials/django-best-practices

[^25]: https://stackoverflow.com/questions/22841764/best-practice-for-django-project-working-directory-structure

[^26]: https://dev.to/buddhiraz/most-used-django-architecture-patterns-8m

[^27]: https://studygyaan.com/django/best-practice-to-structure-django-project-directories-and-files

[^28]: https://forum.djangoproject.com/t/project-naming-conventions/339

[^29]: https://oneteamsolutions.in/django-file-structure-best-practices/

[^30]: https://docs.djangoproject.com/en/6.0/intro/tutorial01/

[^31]: https://itnext.io/how-to-scale-a-monolithic-django-project-6a8394c23fe8

[^32]: https://getcyber.me/posts/anatomy-of-a-django-project-a-comprehensive-guide-to-files-and-structure/

[^33]: https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Server-side/Django/Deployment

