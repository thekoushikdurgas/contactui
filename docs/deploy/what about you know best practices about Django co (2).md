<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# what about you know best practices about Django codebase

Great results! Let me provide you with a comprehensive overview of **Django best practices** based on current 2024-2025 standards. Given your background in backend development, I'm tailoring this toward production-grade architecture.

## Core Django Best Practices for Production Codebases

### 1. **Project Structure \& Modularity**[^1][^2]

Use a **modular app-based architecture** with clear separation of concerns:

```
myproject/
├── config/              # Core project settings
│   ├── settings/
│   │   ├── base.py     # Shared settings
│   │   ├── dev.py      # Development
│   │   ├── prod.py     # Production
│   │   └── test.py     # Testing
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/                # Modular business logic
│   ├── users/          # Authentication & profiles
│   ├── products/       # Product catalog
│   ├── orders/         # Order processing
│   └── core/           # Shared utilities & abstract models
├── templates/
├── static/
├── tests/
├── manage.py
└── requirements.txt
```

**Key principle:** Each app should be self-contained and loosely coupled. Break domain functionality into separate apps that don't directly depend on each other.[^3]

***

### 2. **Settings Configuration Management**[^4]

Split settings by environment rather than keeping everything in one file:

```python
# settings/base.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Common settings
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    # ... apps
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    # ... middleware
]

# settings/dev.py
from .base import *

DEBUG = True
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# settings/prod.py
from .base import *

DEBUG = False
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}
```

Use **environment variables** for sensitive data (API keys, credentials) via `python-decouple` or `django-environ`.[^5]

***

### 3. **Database Query Optimization**[^2][^5]

The N+1 query problem is a common performance killer. Use `select_related()` and `prefetch_related()`:

```python
# ❌ BAD - causes N+1 queries
posts = Post.objects.all()
for post in posts:
    print(post.author.name)  # One query per post!

# ✅ GOOD - single query with JOIN
posts = Post.objects.select_related('author').all()

# ✅ For reverse relationships
authors = Author.objects.prefetch_related('posts').all()
```

**Additional optimizations:**

- Use **indexing** on frequently queried fields
- Apply **database transactions** for atomic operations
- Implement **caching** with Redis/Memcached for expensive queries[^5]

```python
from django.core.cache import cache

def get_user_profile(user_id):
    cache_key = f'user_profile_{user_id}'
    data = cache.get(cache_key)
    
    if not data:
        data = User.objects.prefetch_related('profile').get(id=user_id)
        cache.set(cache_key, data, timeout=300)  # 5 minutes
    
    return data
```


***

### 4. **Model Design Best Practices**[^6][^2]

**Abstract Base Models** reduce duplication:

```python
from django.db import models

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        abstract = True

class BlogPost(BaseModel):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
```

**Model naming conventions:**

- Use **singular names**: `BlogPost` not `BlogPosts`
- Avoid reserved names and abbreviations
- Use `choices` for fixed values[^6]

```python
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
```

**Avoid redundancy** - use `@property` for computed values:

```python
from datetime import date

class Person(models.Model):
    date_of_birth = models.DateField()
    
    @property
    def age(self):
        return date.today().year - self.date_of_birth.year
```


***

### 5. **Class-Based Views (CBVs) Over Function-Based Views**[^5]

CBVs provide reusability and cleaner code:

```python
# ✅ GOOD - leveraging generic views
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import BlogPost

class BlogPostListView(ListView):
    model = BlogPost
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 10
    
    def get_queryset(self):
        return BlogPost.objects.filter(
            is_published=True
        ).select_related('author').order_by('-created_at')

class BlogPostDetailView(DetailView):
    model = BlogPost
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'

class BlogPostCreateView(LoginRequiredMixin, CreateView):
    model = BlogPost
    fields = ['title', 'content']
    template_name = 'blog/post_form.html'
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
```


***

### 6. **Custom User Model**[^5]

Always extend Django's `AbstractUser` or `AbstractBaseUser` early:

```python
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True)
    bio = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    class Meta:
        db_table = 'auth_user'  # Keep default table name
```

Add to `settings.py`:

```python
AUTH_USER_MODEL = 'users.CustomUser'
```


***

### 7. **Testing Strategy**[^2][^5]

Comprehensive test coverage ensures maintainability:

```python
from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_creation(self):
        self.assertEqual(self.user.username, 'testuser')
        self.assertTrue(self.user.check_password('testpass123'))
    
    def test_user_str_representation(self):
        self.assertEqual(str(self.user), 'testuser')

class APIIntegrationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser')
        self.client.force_authenticate(user=self.user)
    
    def test_post_list_endpoint(self):
        response = self.client.get('/api/posts/')
        self.assertEqual(response.status_code, 200)
```


***

### 8. **Custom Management Commands**[^5]

Automate repetitive tasks:

```python
# apps/posts/management/commands/cleanup_drafts.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.posts.models import BlogPost

class Command(BaseCommand):
    help = 'Delete draft posts older than 30 days'
    
    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=30)
    
    def handle(self, *args, **options):
        cutoff_date = timezone.now() - timedelta(days=options['days'])
        deleted_count, _ = BlogPost.objects.filter(
            status='draft',
            updated_at__lt=cutoff_date
        ).delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'Deleted {deleted_count} draft posts')
        )
```

Run with: `python manage.py cleanup_drafts --days=30`

***

### 9. **Signals - Use Wisely**[^5]

Signals are powerful but can cause debugging nightmares. Use only when necessary:

```python
# ✅ GOOD - post_save for creating related objects
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

# ❌ AVOID - complex business logic in signals
# Use explicit method calls or Celery tasks instead
```


***

### 10. **Caching for Performance**[^5]

Implement Redis/Memcached for frequently accessed data:

```python
from django.views.decorators.cache import cache_page
from django.core.cache import cache

# View-level caching
@cache_page(60 * 5)  # Cache for 5 minutes
def expensive_view(request):
    posts = BlogPost.objects.all()
    return render(request, 'posts.html', {'posts': posts})

# Query-level caching
def get_popular_posts():
    cache_key = 'popular_posts'
    posts = cache.get(cache_key)
    
    if posts is None:
        posts = BlogPost.objects.filter(
            likes__gte=100
        ).order_by('-likes')[:10]
        cache.set(cache_key, posts, 60 * 60)  # 1 hour
    
    return posts
```


***

### 11. **Security Best Practices**[^6]

```python
# settings.py

# CSRF Protection
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.security.XFrameOptionsMiddleware',
]

# Security Headers
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_SECURITY_POLICY = {
    "default-src": ("'self'",),
    "script-src": ("'self'", "trusted-cdn.com"),
}

# Authentication
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# HTTPS in production
SECURE_SSL_REDIRECT = True  # Production only
SESSION_COOKIE_SECURE = True  # Production only
CSRF_COOKIE_SECURE = True  # Production only
```


***

### 12. **Documentation \& Code Style**[^5]

Follow Django's official coding style with docstrings:

```python
def calculate_discount(price: float, percentage: float) -> float:
    """Calculate discounted price.
    
    Args:
        price (float): Original price
        percentage (float): Discount percentage (0-100)
    
    Returns:
        float: Discounted price
    """
    return price * (1 - percentage / 100)
```


***

## Key Takeaways for Your Backend Stack

Since you work with FastAPI and PostgreSQL, here's how Django differs:


| Aspect | Django | FastAPI |
| :-- | :-- | :-- |
| **ORM** | Built-in Django ORM | SQLAlchemy / Tortoise (external) |
| **Admin Panel** | Built-in admin interface | None (build your own) |
| **Validation** | Django Forms/Validators | Pydantic (built-in) |
| **Async** | Async support (3.1+) | Native async/await |
| **Performance** | Monolithic, requires optimization | Lightweight, async-first |
| **Deployment** | WSGI (Gunicorn) | ASGI (Uvicorn) |

Django excels at **rapid development** with batteries included, while FastAPI excels at **performance and async operations**.

***

Would you like me to dive deeper into any specific area? I can cover:

- Django REST Framework best practices
- Celery task queuing integration
- Docker/deployment patterns
- Horizontal scaling strategies
- Testing with pytest

Let me know!
<span style="display:none">[^10][^11][^12][^13][^14][^15][^16][^17][^18][^19][^20][^21][^22][^23][^24][^25][^26][^27][^28][^29][^30][^31][^32][^33][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://django-best-practices.readthedocs.io

[^2]: https://www.bluetickconsultants.com/building-a-scalable-and-maintainable-architecture-for-large-scale-django-projects/

[^3]: https://itnext.io/how-to-scale-a-monolithic-django-project-6a8394c23fe8

[^4]: https://djangostars.com/blog/configuring-django-settings-best-practices/

[^5]: https://python.plainenglish.io/top-10-django-tips-to-improve-your-codebase-in-2024-2025-98db3069a54d

[^6]: https://codingandclimbing.in/starting-a-django-project-best-practices-code-snippets/

[^7]: https://www.randwickresearch.com/index.php/rielsj/article/view/1176

[^8]: https://ascopubs.org/doi/10.1200/JCO.2025.43.16_suppl.e22020

[^9]: https://ejournals.eu/en/journal/financial-law-review/article/the-eu-instant-payments-regulation-and-payment-packages-interpretation-and-best-practices

[^10]: https://www.cambridge.org/core/product/identifier/S2056472425106601/type/journal_article

[^11]: https://vestnik.ku.edu.kz/jour/article/view/2287

[^12]: https://journal.aldinhe.ac.uk/index.php/jldhe/article/view/1766

[^13]: https://revues.cirad.fr/index.php/BFT/article/view/37727

[^14]: https://www.semanticscholar.org/paper/f502f21019927b6ab9a83b528eb8ecdf3909eafa

[^15]: https://dl.acm.org/doi/10.1145/3708035.3736079

[^16]: https://aacrjournals.org/clincancerres/article/31/13_Supplement/B021/763253/Abstract-B021-Current-oncological-large-language

[^17]: http://arxiv.org/pdf/2203.13871.pdf

[^18]: https://arxiv.org/pdf/2503.09089.pdf

[^19]: http://arxiv.org/pdf/2307.08220.pdf

[^20]: http://arxiv.org/pdf/2104.00378.pdf

[^21]: https://dl.acm.org/doi/pdf/10.1145/3637528.3671452

[^22]: http://arxiv.org/pdf/2402.01079.pdf

[^23]: https://joss.theoj.org/papers/10.21105/joss.01584.pdf

[^24]: http://arxiv.org/pdf/2501.16050.pdf

[^25]: https://dev.to/codereviewdoctor/what-django-best-practices-is-django-breaking-4e2p

[^26]: https://www.reddit.com/r/django/comments/1f022pa/what_are_django_best_practices/

[^27]: https://www.insnapsys.com/blog/build-a-robust-application-with-django-web-development-best-practices-and-tips/

[^28]: https://dev.to/buddhiraz/most-used-django-architecture-patterns-8m

[^29]: https://dmwebsoft.com/building-scalable-web-applications-with-python-frameworks-like-django

[^30]: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

[^31]: https://data-flair.training/blogs/django-architecture/

[^32]: https://learndjango.com/tutorials/django-best-practices-models

[^33]: https://www.geeksforgeeks.org/python/django-project-mvt-structure/

