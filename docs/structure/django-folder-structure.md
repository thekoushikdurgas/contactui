# Complete Django Project File Structure with Best Practices

## Production-Ready Folder Organization

```
my_project/                              # Root project directory
│
├── 📁 config/                           # Main Django configuration
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py                      # Shared settings
│   │   ├── development.py               # Dev-specific (DEBUG=True)
│   │   ├── production.py                # Production (SSL, security)
│   │   ├── testing.py                   # Testing configuration
│   │   └── local.py                     # Local overrides (gitignored)
│   ├── urls.py                          # Main URL router
│   ├── wsgi.py                          # WSGI entry point (Gunicorn/uWSGI)
│   ├── asgi.py                          # ASGI entry point (Channels/Daphne)
│   ├── celery.py                        # Celery configuration
│   └── middleware.py                    # Custom middleware classes
│
├── 📁 apps/                             # All Django applications folder
│   ├── __init__.py
│   │
│   ├── 📁 core/                         # Reusable utilities & base components
│   │   ├── migrations/
│   │   │   ├── __init__.py
│   │   │   └── 0001_initial.py
│   │   ├── management/
│   │   │   ├── __init__.py
│   │   │   └── commands/
│   │   │       ├── __init__.py
│   │   │       ├── seed_db.py           # Database seeding
│   │   │       ├── cleanup_expired.py   # Token/cache cleanup
│   │   │       └── generate_report.py   # Report generation
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   ├── test_models.py
│   │   │   ├── test_utils.py
│   │   │   ├── test_managers.py
│   │   │   └── conftest.py              # Pytest fixtures
│   │   ├── __init__.py
│   │   ├── models.py                    # Abstract base models
│   │   ├── admin.py                     # Admin site registration
│   │   ├── apps.py                      # App configuration
│   │   ├── managers.py                  # Custom QuerySet managers
│   │   ├── serializers.py               # Base serializers
│   │   ├── signals.py                   # Django signals
│   │   ├── middleware.py                # Custom middleware
│   │   ├── decorators.py                # Reusable decorators
│   │   ├── permissions.py               # DRF permission classes
│   │   ├── pagination.py                # Pagination classes
│   │   ├── throttles.py                 # Rate throttling classes
│   │   ├── filters.py                   # Base filter classes
│   │   ├── authentication.py            # Custom authentication
│   │   ├── validators.py                # Field validators
│   │   ├── exceptions.py                # Custom exceptions
│   │   ├── constants.py                 # App-wide constants
│   │   ├── utils.py                     # Helper utilities
│   │   ├── tasks.py                     # Celery tasks (cleanup, etc.)
│   │   └── logging_config.py            # Logging configuration
│   │
│   ├── 📁 users/                        # User management app
│   │   ├── migrations/
│   │   │   ├── __init__.py
│   │   │   ├── 0001_initial.py
│   │   │   ├── 0002_add_profile.py
│   │   │   └── 0003_add_verification.py
│   │   ├── management/
│   │   │   ├── __init__.py
│   │   │   └── commands/
│   │   │       ├── __init__.py
│   │   │       └── create_admin_user.py
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   ├── test_models.py           # Model tests
│   │   │   ├── test_views.py            # View/ViewSet tests
│   │   │   ├── test_serializers.py      # Serializer tests
│   │   │   ├── test_services.py         # Service layer tests
│   │   │   ├── test_tasks.py            # Celery task tests
│   │   │   └── factories.py             # Model factories for tests
│   │   ├── __init__.py
│   │   ├── models.py                    # User & Profile models
│   │   ├── admin.py                     # Admin customization
│   │   ├── apps.py                      # App config
│   │   ├── serializers.py               # DRF serializers
│   │   ├── views.py                     # Function-based views
│   │   ├── viewsets.py                  # DRF ViewSets (CRUD)
│   │   ├── urls.py                      # App URL routing
│   │   ├── services.py                  # Business logic layer
│   │   ├── tasks.py                     # Async email/celery tasks
│   │   ├── signals.py                   # Post-save/delete signals
│   │   ├── permissions.py               # Custom permissions
│   │   ├── filters.py                   # Filtering logic
│   │   ├── forms.py                     # Django forms
│   │   ├── templates/
│   │   │   └── users/
│   │   │       ├── profile.html         # User profile template
│   │   │       ├── edit_profile.html    # Edit profile page
│   │   │       ├── user_list.html       # User listing
│   │   │       └── registration.html    # Registration form
│   │   ├── static/
│   │   │   └── users/
│   │   │       ├── css/
│   │   │       │   ├── profile.css
│   │   │       │   └── forms.css
│   │   │       ├── js/
│   │   │       │   ├── profile.js
│   │   │       │   └── validation.js
│   │   │       └── images/
│   │   │           └── avatar-default.png
│   │   └── utils.py                     # User-specific utilities
│   │
│   ├── 📁 products/                     # Product management app
│   │   ├── migrations/
│   │   │   ├── __init__.py
│   │   │   ├── 0001_initial.py
│   │   │   └── 0002_add_inventory.py
│   │   ├── management/
│   │   │   ├── __init__.py
│   │   │   └── commands/
│   │   │       ├── __init__.py
│   │   │       └── sync_products.py     # External data sync
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   ├── test_models.py
│   │   │   ├── test_viewsets.py
│   │   │   ├── test_services.py
│   │   │   └── factories.py
│   │   ├── __init__.py
│   │   ├── models.py                    # Product, Category, Stock models
│   │   ├── admin.py                     # Admin site customization
│   │   ├── apps.py
│   │   ├── serializers.py               # Product serializers
│   │   ├── viewsets.py                  # Product ViewSets
│   │   ├── urls.py
│   │   ├── services.py                  # Business logic (pricing, inventory)
│   │   ├── tasks.py                     # Stock sync, price updates
│   │   ├── signals.py                   # Inventory alerts
│   │   ├── filters.py                   # Product filtering (price, rating)
│   │   ├── permissions.py               # IsAdmin, IsVendor permissions
│   │   ├── forms.py
│   │   ├── templates/
│   │   │   └── products/
│   │   │       ├── product_list.html
│   │   │       ├── product_detail.html
│   │   │       ├── category_list.html
│   │   │       └── search_results.html
│   │   ├── static/
│   │   │   └── products/
│   │   │       ├── css/
│   │   │       │   ├── listing.css
│   │   │       │   └── filters.css
│   │   │       ├── js/
│   │   │       │   ├── filtering.js
│   │   │       │   └── cart.js
│   │   │       └── images/
│   │   │           └── placeholder.png
│   │   └── utils.py
│   │
│   ├── 📁 orders/                       # Orders & transactions
│   │   ├── migrations/
│   │   ├── management/
│   │   ├── tests/
│   │   ├── __init__.py
│   │   ├── models.py                    # Order, OrderItem, Payment
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── serializers.py
│   │   ├── viewsets.py
│   │   ├── urls.py
│   │   ├── services.py                  # Order processing logic
│   │   ├── tasks.py                     # Send order confirmation email
│   │   ├── signals.py                   # Update inventory on order
│   │   ├── permissions.py
│   │   ├── filters.py
│   │   ├── forms.py
│   │   ├── templates/
│   │   │   └── orders/
│   │   │       ├── order_list.html
│   │   │       ├── order_detail.html
│   │   │       └── checkout.html
│   │   ├── static/
│   │   │   └── orders/
│   │   │       ├── css/
│   │   │       └── js/
│   │   └── utils.py
│   │
│   ├── 📁 notifications/                # Real-time notifications
│   │   ├── migrations/
│   │   │   ├── __init__.py
│   │   │   └── 0001_initial.py
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   ├── test_consumers.py
│   │   │   └── test_services.py
│   │   ├── __init__.py
│   │   ├── models.py                    # Notification model
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── serializers.py
│   │   ├── consumers.py                 # WebSocket consumers
│   │   ├── routing.py                   # WebSocket URL routing
│   │   ├── services.py                  # Notification service
│   │   ├── tasks.py                     # Send notifications
│   │   ├── signals.py
│   │   ├── views.py                     # HTTP endpoints
│   │   ├── urls.py
│   │   └── utils.py
│   │
│   └── 📁 api/                          # Centralized API configuration
│       ├── __init__.py
│       ├── urls.py                      # All API routes
│       ├── serializers.py               # Shared API serializers
│       ├── views.py                     # Shared API views
│       ├── viewsets.py                  # Shared ViewSets
│       ├── permissions.py               # API-wide permissions
│       ├── throttles.py                 # API throttling
│       ├── pagination.py                # API pagination
│       ├── filters.py                   # API filters
│       ├── authentication.py            # Custom auth backends
│       └── schema.py                    # OpenAPI/Swagger schema
│
├── 📁 templates/                        # Project-level templates
│   ├── base.html                        # Master template
│   ├── layout.html                      # Layout wrapper
│   ├── home.html                        # Homepage
│   ├── errors/
│   │   ├── 400.html
│   │   ├── 403.html
│   │   ├── 404.html
│   │   ├── 500.html
│   │   └── 503.html
│   ├── includes/
│   │   ├── navbar.html                  # Navigation component
│   │   ├── footer.html                  # Footer component
│   │   ├── sidebar.html                 # Sidebar
│   │   ├── pagination.html              # Pagination template
│   │   ├── messages.html                # Flash messages
│   │   ├── breadcrumb.html              # Breadcrumbs
│   │   └── modal.html                   # Modal template
│   └── layouts/
│       ├── admin_layout.html
│       ├── public_layout.html
│       └── dashboard_layout.html
│
├── 📁 static/                           # Project-level static files
│   ├── css/
│   │   ├── base.css                     # Base styles
│   │   ├── styles.css                   # Main styles
│   │   ├── responsive.css               # Mobile responsive
│   │   ├── variables.css                # CSS variables
│   │   ├── animations.css               # Animations
│   │   ├── bootstrap-override.css       # Custom Bootstrap
│   │   └── themes/
│   │       ├── dark.css
│   │       └── light.css
│   ├── js/
│   │   ├── base.js                      # Base JavaScript
│   │   ├── utils.js                     # Utility functions
│   │   ├── api-client.js                # API client wrapper
│   │   ├── websocket-client.js          # WebSocket client
│   │   ├── form-validation.js           # Form validation
│   │   ├── modal.js                     # Modal handler
│   │   └── plugins/
│   │       ├── jquery-custom.js
│   │       └── bootstrap-custom.js
│   ├── images/
│   │   ├── logo.png
│   │   ├── favicon.ico
│   │   ├── icons/
│   │   │   ├── user.svg
│   │   │   ├── settings.svg
│   │   │   └── logout.svg
│   │   └── backgrounds/
│   │       └── hero.jpg
│   ├── fonts/
│   │   ├── roboto.woff2
│   │   └── inter.woff2
│   └── lib/
│       ├── bootstrap.min.css
│       ├── bootstrap.min.js
│       ├── axios.min.js
│       └── moment.min.js
│
├── 📁 media/                            # User uploaded files
│   ├── uploads/
│   │   ├── avatars/
│   │   │   └── user_123/
│   │   ├── products/
│   │   │   └── product_images/
│   │   └── documents/
│   │       └── invoices/
│   └── temp/
│       └── processing/
│
├── 📁 tests/                            # Integration & E2E tests
│   ├── __init__.py
│   ├── conftest.py                      # Pytest global configuration
│   ├── factories.py                     # Model factories (Factory Boy)
│   ├── fixtures.py                      # Reusable fixtures
│   ├── test_api.py                      # API endpoint tests
│   ├── test_integration.py              # Integration tests
│   ├── test_e2e.py                      # End-to-end tests
│   ├── test_performance.py              # Performance tests
│   └── test_security.py                 # Security tests
│
├── 📁 logs/                             # Application logs
│   ├── .gitkeep
│   ├── django.log                       # Django debug logs
│   ├── error.log                        # Error logs
│   ├── celery.log                       # Celery task logs
│   ├── access.log                       # HTTP access logs
│   └── archive/
│       └── 2025-01-*/
│
├── 📁 scripts/                          # Utility scripts
│   ├── entrypoint.sh                    # Docker entrypoint
│   ├── migrate.sh                       # Database migration script
│   ├── seed_db.sh                       # Database seeding
│   ├── backup.sh                        # Database backup
│   ├── deploy.sh                        # Deployment script
│   ├── health_check.py                  # System health check
│   └── fixtures/
│       ├── initial_data.json            # Initial fixtures
│       └── test_data.json
│
├── 📁 docs/                             # Project documentation
│   ├── README.md                        # Project overview
│   ├── SETUP.md                         # Installation guide
│   ├── API.md                           # API documentation
│   ├── DEPLOYMENT.md                    # Deployment guide
│   ├── ARCHITECTURE.md                  # Architecture overview
│   ├── CONTRIBUTING.md                  # Contribution guide
│   ├── DATABASE.md                      # Database schema
│   ├── SECURITY.md                      # Security guidelines
│   ├── TESTING.md                       # Testing guide
│   ├── TROUBLESHOOTING.md               # Troubleshooting
│   └── images/
│       ├── architecture.png
│       └── database-schema.png
│
├── 📁 staticfiles/                      # Collected static files (production)
│   └── (auto-generated by collectstatic)
│
├── 📄 manage.py                         # Django management command
├── 📄 .gitignore                        # Git ignore rules
├── 📄 .env.example                      # Environment template
├── 📄 .dockerignore                     # Docker ignore rules
├── 📄 .flake8                           # Flake8 linting config
├── 📄 .pylintrc                         # Pylint config
├── 📄 .pre-commit-config.yaml           # Pre-commit hooks
├── 📄 pyproject.toml                    # Python project metadata
├── 📄 setup.cfg                         # Setup configuration
├── 📄 pytest.ini                        # Pytest configuration
├── 📄 requirements.txt                  # Production dependencies
├── 📄 requirements-dev.txt              # Development dependencies
├── 📄 requirements-test.txt             # Testing dependencies
├── 📄 docker-compose.yml                # Docker Compose services
├── 📄 Dockerfile                        # Docker image build
├── 📄 docker-compose.prod.yml           # Production Docker Compose
├── 📄 Dockerfile.prod                   # Production Dockerfile
├── 📄 Makefile                          # Build automation
├── 📄 nginx.conf                        # Nginx configuration
├── 📄 gunicorn.conf.py                  # Gunicorn configuration
├── 📄 supervisord.conf                  # Supervisor configuration
└── 📄 LICENSE                           # Project license

```

---

## Complete File Structure Organization by Category

### **Configuration Files (Root)**
- `manage.py` - Django CLI
- `.env.example` - Environment template
- `pyproject.toml` - Modern Python packaging
- `setup.cfg` - Alternative setup
- `pytest.ini` - Testing configuration
- `.flake8` - Code linting
- `.pylintrc` - Linting rules
- `.pre-commit-config.yaml` - Git hooks
- `Makefile` - Automation

### **Docker Files**
- `Dockerfile` - Development image
- `Dockerfile.prod` - Production image
- `docker-compose.yml` - Local services (db, redis, web)
- `docker-compose.prod.yml` - Production stack
- `.dockerignore` - Files to exclude

### **Server Configuration**
- `gunicorn.conf.py` - WSGI server config
- `nginx.conf` - Web server config
- `supervisord.conf` - Process management

### **Config Folder Structure**
```
config/
├── settings/
│   ├── base.py          # Shared
│   ├── development.py   # DEBUG=True, test email
│   ├── production.py    # SSL, security
│   ├── testing.py       # SQLite, in-memory
│   └── local.py         # Personal overrides
├── urls.py              # URL routing
├── wsgi.py              # Gunicorn entry
├── asgi.py              # Daphne/Channels entry
├── celery.py            # Celery config
└── middleware.py        # Custom middleware
```

### **Apps Folder - Modular Design**
Each app is self-contained:
```
apps/[app_name]/
├── migrations/          # Database migrations
├── management/          # Custom commands
├── tests/               # App tests
├── templates/           # HTML templates
├── static/              # CSS, JS, images
├── models.py            # Database models
├── serializers.py       # DRF serializers
├── viewsets.py          # API ViewSets
├── views.py             # Traditional views
├── urls.py              # App routing
├── services.py          # Business logic
├── tasks.py             # Celery tasks
├── signals.py           # Event handlers
├── permissions.py       # Custom permissions
├── filters.py           # Filtering logic
├── forms.py             # Django forms
└── admin.py             # Admin config
```

### **Templates Hierarchy**
```
templates/
├── base.html            # Master template
├── layout.html          # Page layout
├── home.html
├── errors/              # Error pages
│   ├── 404.html
│   ├── 500.html
│   └── 503.html
├── includes/            # Reusable components
│   ├── navbar.html
│   ├── footer.html
│   ├── pagination.html
│   └── messages.html
└── layouts/             # Layout variants
    ├── admin_layout.html
    ├── public_layout.html
    └── dashboard_layout.html
```

### **Static Files Organization**
```
static/
├── css/
│   ├── base.css         # Reset & defaults
│   ├── styles.css       # Main styles
│   ├── responsive.css   # Mobile styles
│   ├── variables.css    # CSS variables
│   ├── animations.css
│   └── themes/
│       ├── dark.css
│       └── light.css
├── js/
│   ├── base.js          # Global JS
│   ├── utils.js         # Helpers
│   ├── api-client.js    # API wrapper
│   ├── websocket-client.js
│   ├── form-validation.js
│   └── plugins/
├── images/
│   ├── logo.png
│   ├── favicon.ico
│   ├── icons/           # SVG icons
│   └── backgrounds/
├── fonts/               # Web fonts
└── lib/                 # Third-party libs
```

### **Media Files (User Uploads)**
```
media/
├── uploads/
│   ├── avatars/         # User profile pics
│   ├── products/        # Product images
│   └── documents/       # Files
└── temp/                # Processing files
```

### **Tests Structure**
```
tests/
├── conftest.py          # Pytest config & fixtures
├── factories.py         # Factory Boy models
├── fixtures.py          # Reusable test data
├── test_api.py          # API tests
├── test_integration.py  # Integration tests
├── test_e2e.py          # End-to-end tests
├── test_performance.py  # Load tests
└── test_security.py     # Security tests
```

### **Scripts Folder**
```
scripts/
├── entrypoint.sh        # Docker start
├── migrate.sh           # Run migrations
├── seed_db.sh           # Populate DB
├── backup.sh            # Database backup
├── deploy.sh            # Deployment
├── health_check.py      # Health status
└── fixtures/
    ├── initial_data.json
    └── test_data.json
```

### **Logs Folder**
```
logs/
├── django.log           # Application logs
├── error.log            # Errors
├── celery.log           # Task logs
├── access.log           # HTTP access
└── archive/             # Old logs
    └── 2025-01-*/
```

### **Docs Folder**
```
docs/
├── README.md            # Overview
├── SETUP.md             # Installation
├── API.md               # API docs
├── DEPLOYMENT.md        # Deployment
├── ARCHITECTURE.md      # System design
├── CONTRIBUTING.md      # Dev guide
├── DATABASE.md          # Schema
├── SECURITY.md          # Security
├── TESTING.md           # Testing guide
├── TROUBLESHOOTING.md   # Issues
└── images/              # Diagrams
```

---

## Key Organization Principles

### **1. Separation of Concerns**
- Models in `models.py`
- Views/ViewSets in `views.py` / `viewsets.py`
- Business logic in `services.py`
- Serializers in `serializers.py`
- Async tasks in `tasks.py`

### **2. Modular Apps**
Each app is independent:
- Own migrations
- Own tests
- Own templates
- Own static files
- Own URL routing

### **3. Reusable Components**
- `core/` app for shared code
- Abstract models in `core/models.py`
- Base permissions in `core/permissions.py`
- Common utilities in `core/utils.py`

### **4. Environment-Based Config**
```
config/settings/
├── base.py      # All environments
├── development.py
├── production.py
├── testing.py
└── local.py (gitignored)
```

### **5. DRY Principle**
- Inheritance: Abstract models, base serializers
- Mixins: Reusable model/view logic
- Signals: Auto-execution on events
- Decorators: Cross-cutting concerns

### **6. Production-Ready**
- Docker support
- Health checks
- Logging system
- Performance monitoring
- Security headers

---

## File Count Reference

- **Models**: ~20-30 models across apps
- **Serializers**: ~25-35 serializers
- **ViewSets**: ~15-20 ViewSets
- **Tests**: ~50-100 test files
- **Templates**: ~30-50 templates
- **Static files**: ~5-10 files per app
- **Management commands**: ~10-15 commands
- **Tasks**: ~20-30 Celery tasks

---

## Quick Navigation

| Purpose | Location |
|---------|----------|
| Add new feature | `apps/[app_name]/` |
| Database model | `apps/[app_name]/models.py` |
| API endpoint | `apps/[app_name]/viewsets.py` |
| Business logic | `apps/[app_name]/services.py` |
| Background job | `apps/[app_name]/tasks.py` |
| HTML template | `templates/[app_name]/` |
| CSS/JS | `static/[app_name]/` |
| User files | `media/uploads/` |
| Write test | `tests/` or `apps/[app_name]/tests/` |
| Configuration | `config/settings/` |
| Documentation | `docs/` |
| Deployment | `scripts/`, `docker-compose.yml` |

---

## Best Practices by Folder

### ✅ **config/**
- One settings file per environment
- No hardcoded values (use .env)
- Keep middleware minimal
- Custom middleware in separate file

### ✅ **apps/[app_name]/**
- One model class per concept
- DRY: use abstract models
- Services layer for business logic
- Tests run independently per app
- Signal handlers for event-driven code

### ✅ **templates/**
- Use template inheritance (base.html)
- Reusable includes components
- Minimal logic (use context in view)
- One template per view action

### ✅ **static/**
- Organize by file type (css/, js/)
- Minimize per-app, maximize reuse
- Variables.css for centralized styling
- Themes for light/dark modes

### ✅ **tests/**
- One test file per model/view/service
- Use factories for test data
- Pytest fixtures for setup
- Mock external APIs
- Aim for 80%+ coverage

### ✅ **Media/**
- Organize by type (avatars/, products/)
- Use UUID for file naming
- Separate temp files
- Regular cleanup tasks

This structure scales from **5-person teams to 50+**. Add new apps without refactoring existing code!
