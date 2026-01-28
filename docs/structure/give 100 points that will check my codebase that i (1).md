<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# give 100 points that will check my codebase that it check django best practices and full power of django and python

Django best practices checklists cover security (Django's `check --deploy`), performance (N+1 avoidance), code quality (type hints, linting), structure (modular apps), testing (>90% coverage), and deployment (Docker, monitoring).[^1][^2][^3]

## Security (25 Points)

1. Run `python manage.py check --deploy` - fix all warnings.[^3][^1]
2. `DEBUG=False` in production.[^1]
3. `ALLOWED_HOSTS` set to production domains only.[^1]
4. `SECURE_SSL_REDIRECT=True` enforces HTTPS.[^2][^1]
5. `SECURE_HSTS_SECONDS=31536000; SECURE_HSTS_INCLUDE_SUBDOMAINS=True`.[^4][^1]
6. `SECURE_CONTENT_TYPE_NOSNIFF=True` prevents MIME sniffing.[^1]
7. `SECURE_BROWSER_XSS_FILTER=True` enables XSS filter.[^1]
8. `X_FRAME_OPTIONS='DENY'` blocks clickjacking.[^1]
9. `CSRF_COOKIE_SECURE=True; CSRF_COOKIE_HTTPONLY=True`.[^1]
10. `SESSION_COOKIE_SECURE=True; SESSION_COOKIE_HTTPONLY=True`.[^1]
11. Custom `User` model extends `AbstractUser` or `AbstractBaseUser`.[^2]
12. Password validation: `django.contrib.auth.password_validation` enabled.[^1]
13. Rate limiting on login/forms via `django-ratelimit` or DRF throttling.[^5]
14. CSP headers via `django-csp`: `CSP_DEFAULT_SRC=('self',)`.[^4]
15. `ServerTokens Prod; ServerSignature Off` in Nginx/Apache.[^4]
16. Dependencies pinned, scanned: `pip-audit`, `safety check`.[^4]
17. Static/media served securely (not via Django in prod).[^1]
18. SQL injection safe: Use ORM, never raw SQL without params.[^5]
19. XSS safe: Auto-escaping in templates, `|safe` only when needed.[^4]
20. CSRF tokens in all POST forms (`{% csrf_token %}`).[^5]
21. Permission classes in DRF: `IsAuthenticated`, custom perms.[^5]
22. Secrets in `.env`: Never hardcode keys.[^1]
23. Logging: No sensitive data (`LOGGING['disable_existing_loggers']=False`).[^6]
24. `data-upload-max-memory-size` limits in production.[^1]
25. MFA via `django-otp` for admin/superusers.[^2]

## Project Structure (15 Points)

26. Modular apps in `apps/` (single responsibility).[^7]
27. Settings split: `base.py`, `dev.py`, `prod.py`.[^7]
28. `requirements/{base,dev,prod}.txt` pinned versions.[^7]
29. `.pre-commit-config.yaml` with black/ruff/mypy.[^8]
30. `docker-compose.yml` for local/prod stacks.[^7]
31. `pyproject.toml` for Poetry/uv, linting config.[^8]
32. `Makefile` for lint/test/deploy commands.[^8]
33. `README.md`, `CONTRIBUTING.md`, `.env.example`.[^8]
34. Apps have `tests/`, `migrations/`, `templatetags/`, `management/commands/`.[^7]
35. Global `templates/`, `static/` for overrides.[^7]
36. `locale/` for i18n, `{% trans %}` in templates.[^7]
37. `docs/` with Sphinx for API docs.[^7]
38. `py.typed` in packages for mypy.[^7]
39. No fat models: Use managers, querysets.py.[^2]
40. Services layer for business logic (not in views).[^9]

## Code Quality/Python Power (20 Points)

41. Type hints everywhere: `def foo(user: User) -> QuerySet[Post]:`.[^8]
42. Black-formatted: `line-length=88`, single quotes.[^8]
43. Ruff/isort: Zero violations via pre-commit.[^8]
44. Docstrings: Google/numpy style, every public func/class.[^8]
45. `@dataclass` for configs, `@property` for computed fields.[^2]
46. Context managers for resources (DB, files).[^8]
47. Walrus operator `:=` for assignments in comprehensions.[^8]
48. `match/case` for state machines over if-elif chains.[^8]
49. Async views/tasks where I/O bound (ASGI, Celery).[^7]
50. Generators/yield for large querysets (`.iterator()`).[^10]
51. Enum for choices: `class Status(Enum): PENDING = 'pending'`.[^2]
52. Datetime timezone-aware: `django.utils.timezone.now()`.[^2]
53. No global state; dependency injection via factories.[^8]
54. Single responsibility: <50 LOC per func.[^8]
55. Avoid magic numbers: Named constants.[^2]
56. Logging over print(): `logger.info("User %s logged in", user.id)`.
57. Validators in serializers/forms: `validate_foo(self, value)`.
58. Custom exceptions: `class ValidationError(APIException):`.[^8]
59. `final` typing for non-overridable methods.
60. Protocol for duck typing interfaces.

## Models/ORM/Database (15 Points)

61. Proper fields: `CharField(max_length=255)`, not `TextField`.[^2]
62. Indexes: `db_index=True` on filters, `unique_together`.[^10]
63. Relationships: `ForeignKey(on_delete=CASCADE)`, `prefetch_related`.[^2]
64. Soft delete: Custom manager `filter(deleted_at__isnull=True)`.[^7]
65. `choices` tuple or `TextChoices` for status fields.[^2]
66. JSONField for unstructured data (PostgreSQL).[^10]
67. Managers: `Post.objects.published()`.[^7]
68. `select_related`/`prefetch_related` for N+1 avoidance.[^10]
69. Raw SQL only with `connection.cursor()` params.[^5]
70. Migrations squashed, no data-loss ops in prod.[^1]
71. Constraints: `CheckConstraint`, `validators`.[^2]
72. Full-text search: PostgreSQL `tsvector` or `django.contrib.postgres.search`.
73. Timezones: `USE_TZ=True`, `django-extensions` hack around.
74. Pagination: `LimitOffsetPagination` or cursor-based.[^7]
75. Database routers for sharding/read replicas.

## Views/Serialization/API (10 Points)

76. CBV with mixins: `LoginRequiredMixin`.[^10]
77. DRF ViewSets/Routers for REST APIs.[^7]
78. Permissions per action: `permission_classes_by_action`.[^5]
79. Filters: `django-filters`, `search_fields`.[^7]
80. Serializers: Nested, `read_only_fields`, `extra_kwargs`.[^7]
81. Throttling: `AnonRateThrottle`, scopes.[^5]
82. Pagination class customized.[^7]
83. Exception handlers: Custom 404/500 JSON.[^7]
84. API versioning: `api/v1/`, `DefaultVersioning`.[^7]
85. Browsable API disabled in prod (`DEFAULT_RENDERER_CLASSES`).

## Testing/Performance (10 Points)

86. >90% coverage: `pytest --cov=apps/ --cov-report=html`.[^8]
87. pytest-django, factory-boy fixtures.[^7]
88. Mock external calls: `responses`, `pytest-mock`.[^8]
89. Load testing: `locust`, `pytest-benchmark`.[^10]
90. Cache: `@cache_page`, Redis backend, `CACHEOPS`.[^10]
91. Database: Connection pooling, `CONN_MAX_AGE`.[^10]
92. Static CDN, compression middleware.[^10]
93. Celery for tasks, `django-celery-results`.[^7]
94. Channels for WebSockets if real-time.[^7]
95. `django-debug-toolbar` in dev only.

## Deployment/Monitoring (5 Points)

96. Gunicorn + Nginx/ ASGI proxy.[^1]
97. Zero-downtime: Blue-green or rolling deploys.[^1]
98. Sentry/New Relic for errors/performance.[^4]
99. Health checks: `/health/`, database connectivity.[^7]
100. CI/CD: GitHub Actions runs tests/lint/security scans.[^8]

Run Django's checklist first, then audit with these 100 points for production excellence.[^3][^2][^1]
<span style="display:none">[^11][^12][^13][^14][^15][^16][^17][^18][^19][^20][^21][^22][^23][^24][^25]</span>

<div align="center">⁂</div>

[^1]: https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

[^2]: https://codingandclimbing.in/starting-a-django-project-best-practices-code-snippets/

[^3]: https://www.freecodecamp.org/news/how-to-secure-your-django-app/

[^4]: https://www.capitalnumbers.com/blog/django-security-checklist/

[^5]: https://www.planeks.net/django-security-challenges/

[^6]: https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

[^7]: https://www.revsys.com/tidbits/recommended-django-project-layout/

[^8]: https://www.codeant.ai/blogs/source-code-audit-checklist-best-practices-for-secure-code

[^9]: https://forum.djangoproject.com/t/structuring-large-complex-django-projects-and-using-a-services-layer-in-django-projects/1487

[^10]: https://www.hostinger.com/in/tutorials/django-best-practices

[^11]: http://arxiv.org/pdf/2203.13871.pdf

[^12]: https://joss.theoj.org/papers/10.21105/joss.01584.pdf

[^13]: https://arxiv.org/pdf/2503.09089.pdf

[^14]: https://arxiv.org/pdf/2109.03550.pdf

[^15]: http://arxiv.org/pdf/2211.11501.pdf

[^16]: https://www.mdpi.com/2078-2489/12/8/319/pdf

[^17]: http://arxiv.org/pdf/2405.10891.pdf

[^18]: https://arxiv.org/pdf/2210.03991.pdf

[^19]: https://www.moontechnolabs.com/blog/django-best-practices/

[^20]: https://learndjango.com/tutorials/django-best-practices-security

[^21]: https://www.geeksforgeeks.org/python/best-practices-for-professional-developer-django-framework/

[^22]: https://dev.to/topunix/building-a-fort-django-security-best-practices-4fa4

[^23]: https://www.coursera.org/resources/django-learning-roadmap

[^24]: https://www.hostinger.com/tutorials/django-best-practices

[^25]: https://github.com/vintasoftware/django-production-launch-checklist

