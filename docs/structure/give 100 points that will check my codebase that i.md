<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# give 100 points that will check my codebase that it check django best practices and full power of django and python

Here’s a comprehensive **100-point checklist** to audit your Django codebase against best practices and full Python/Django power. Use it to score your project (✓/✗/N/A). Grouped by category for easy scanning.

## Project Structure (10 points) [^1][^2][^3]

1. Uses `apps/` folder for all first-party apps?
2. Project settings split into `config/settings/` (base.py, dev.py, prod.py)?
3. `pyproject.toml` or `requirements/` for dependency management?
4. Global `templates/` and `static/` with app‑scoped subfolders?
5. Separate `media/` folder configured correctly?
6. `docker/` or `infra/` for deployment configs?
7. `scripts/` for management/maintenance scripts?
8. `.env.example` for environment variables (no secrets committed)?
9. `.gitignore` excludes `media/`, `__pycache__`, `.env`, `.pytest_cache`?
10. Clear README.md with setup, local dev, deployment instructions?

## Code Organization \& Architecture (15 points) [^1][^4][^5]

11. Fat models, skinny views (business logic in models/services)?
12. Service layer (`services.py` or `services/`) for complex business logic?
13. Selector/query layer (`selectors.py`) for read operations?
14. One responsibility per app (domain‑driven, not one giant app)?
15. Custom managers/querysets for reusable query patterns?
16. Permissions centralized (e.g. `permissions.py` per app)?
17. Signals isolated and documented (in `signals.py`)?
18. Celery tasks in `tasks.py` per app?
19. Custom management commands in `management/commands/`?
20. Middleware in dedicated app (e.g. `core/middleware/`)?
21. API versioning (e.g. `api/v1/`, `api/v2/`)?
22. Forms/serializers centralized (not inline in views)?
23. Utils/helpers in `core/utils/` or app‑specific?
24. Enums/choices in `utils/enums.py`?
25. No spaghetti code; clear separation of concerns?

## Models \& Database (15 points) [^6][^1][^7]

26. `AUTH_USER_MODEL` customized if needed?
27. Abstract base models for timestamps/audit fields?
28. Proper field types (e.g. `CharField(max_length=...)`, `DecimalField`)?
29. Indexes on frequently queried/filtered fields (`db_index=True`)?
30. `UniqueConstraint` for multi‑column uniqueness?
31. Custom managers for common filters (e.g. `PublishedManager`)?
32. `select_related`/`prefetch_related` used to avoid N+1 queries?
33. `exists()` for existence checks, not `count()` or `get_or_none()`?
34. Database routing if using multiple DBs?
35. Migrations reviewed and squashed when appropriate?
36. Soft deletes implemented if needed (e.g. `is_active`)?
37. Model `__str__()` returns meaningful string?
38. `get_absolute_url()` defined?
39. Model validators used (`validators.RegexValidator`)?
40. Raw SQL only when ORM can't optimize?

## Views \& APIs (12 points) [^1][^4][^7]

41. Class‑based views or DRF viewsets preferred over FBVs?
42. Views thin (orchestrate services/selectors, no business logic)?
43. Proper HTTP status codes (not all 200)?
44. Pagination on list views/APIs?
45. Throttling/rate limiting on APIs?
46. Input validation via forms/serializers?
47. Exception handling centralized?
48. CSRF protection enabled and used?
49. No direct `request.user` checks in views (use permissions)?
50. API responses consistent (e.g. `Response({'data': ...})`)?
51. WebSocket support if real‑time needed (`channels`)?
52. No template logic in views (use context processors)?

## Templates \& Frontend (8 points) [^1][^8]

53. `{% extends %}` first in templates?
54. Blocks well‑defined, minimal logic (use filters/tags)?
55. Template tags/filters custom if needed?
56. No business logic in templates?
57. App‑scoped template names (e.g. `accounts/login.html`)?
58. Base template with includes for navbar/footer?
59. Static files loaded via `{% static %}`?
60. CSRF token in all POST forms?

## Security (12 points) [^9][^1][^7]

61. `DEBUG=False` in production?
62. `SECRET_KEY` from env vars?
63. `ALLOWED_HOSTS` explicitly set?
64. `SECURE_SSL_REDIRECT=True` in HTTPS?
65. `SECURE_HSTS_SECONDS` enabled?
66. `SECURE_CONTENT_TYPE_NOSNIFF=True`?
67. `SECURE_BROWSER_XSS_FILTER=True`?
68. Passwords hashed with `PBKDF2` or better?
69. Sensitive data encrypted (e.g. `django-cryptography`)?
70. Session cookies secure/httponly?
71. Audit logging (e.g. `django-simple-history`)?
72. CSP headers configured?

## Performance \& Optimization (10 points) [^1][^7]

73. Caching configured (Redis/Memcached)?
74. Static/media via CDN in prod?
75. Database connection pooling?
76. Gunicorn/uWSGI + Nginx setup?
77. `iterator()` for large querysets?
78. `only()`/`defer()` for partial selects?
79. Query profiling (e.g. `django-debug-toolbar` in dev)?
80. Compression middleware?
81. Lazy loading for heavy assets?
82. Celery for background tasks?

## Testing (8 points) [^1][^4]

83. Unit tests for models/services/selectors (>80% coverage)?
84. Integration tests for views/APIs?
85. E2E tests for critical flows?
86. Factories (e.g. `factory-boy`) for test data?
87. `pytest` or `pytest-django`?
88. Mocking external services?
89. Test isolation (transactions, db reset)?
90. CI runs tests on PRs?

## Deployment \& Ops (5 points) [^7][^10]

91. Dockerized with multi‑stage builds?
92. CI/CD pipeline (GitHub Actions/GitLab CI)?
93. Zero‑downtime deploys?
94. Health checks configured?
95. Monitoring (Sentry/New Relic)?

## Python/Django Power (5 points)

96. Type hints throughout (`typing`, `pydantic`)?
97. Modern Python 3.12+ features (match/case, etc.)?
98. Linting (black, isort, flake8, mypy)?
99. Pre‑commit hooks?
100. Full Django features used (signals, middleware, custom tags, channels if applicable)?

Score your project against this—aim for 80+ points. If you share weak areas (e.g., “testing is 0/8”), I can give targeted fixes or code examples. This checklist draws from official docs, community standards, and production patterns.[^1][^4][^11][^7]
<span style="display:none">[^12][^13][^14][^15][^16][^17][^18][^19][^20][^21]</span>

<div align="center">⁂</div>

[^1]: https://www.hostinger.com/in/tutorials/django-best-practices

[^2]: https://www.geeksforgeeks.org/python/best-practice-for-django-project-working-directory-structure/

[^3]: https://stackoverflow.com/questions/22841764/best-practice-for-django-project-working-directory-structure

[^4]: https://www.geeksforgeeks.org/python/best-practices-for-professional-developer-django-framework/

[^5]: https://forum.djangoproject.com/t/structuring-large-complex-django-projects-and-using-a-services-layer-in-django-projects/1487

[^6]: https://djangostars.com/blog/django-models-best-practices/

[^7]: https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

[^8]: https://learndjango.com/tutorials/template-structure

[^9]: https://djangostars.com/blog/why-we-use-django-framework/

[^10]: https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

[^11]: https://django-best-practices.readthedocs.io

[^12]: https://www.moontechnolabs.com/blog/django-best-practices/

[^13]: https://swimm.io/learn/code-reviews/ultimate-10-step-code-review-checklist

[^14]: https://pypi.org/project/django-audit-log/

[^15]: https://redwerk.com/blog/code-review-checklist/

[^16]: https://code.djangoproject.com/wiki/AuditTrail

[^17]: https://www.reddit.com/r/django/comments/ka3s94/need_review_checklist_for_the_firsttime/

[^18]: https://www.codementor.io/blog/code-review-checklist-76q7ovkaqj

[^19]: https://www.youtube.com/watch?v=6beE6G4fS10

[^20]: https://www.reddit.com/r/django/comments/1f022pa/what_are_django_best_practices/

[^21]: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

