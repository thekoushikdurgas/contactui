<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Django project folder structure best practices

A solid Django project structure makes it easy to scale, test, and onboard others. Here’s a practical layout and the key best practices around it.[^1][^2][^3]

## Recommended high‑level layout

A common, maintainable layout for medium–large projects:

```text
myproject/
├── manage.py
├── README.md
├── requirements.txt
├── .env
├── myproject/            # Project config package
│   ├── __init__.py
│   ├── settings/         # Split settings
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── dev.py
│   │   ├── prod.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
├── apps/                 # All local apps
│   ├── users/
│   ├── billing/
│   └── ...
├── templates/            # Project‑wide templates
├── static/               # Project‑wide static
├── media/                # Uploaded files (often ignored in VCS)
└── scripts/              # Management/ops scripts (optional)
```

This pattern (project package + apps + global `templates`/`static` + split settings) is widely recommended for scalable Django projects.[^1][^2][^3][^4]

## Inside each Django app

Each app should be focused on one domain (users, orders, blog, etc.) and internally consistent:[^3]

```text
apps/
  users/
    __init__.py
    apps.py
    models.py
    views.py
    urls.py
    forms.py
    admin.py
    services.py      # business logic (optional)
    selectors.py     # read/query layer (optional)
    templates/
      users/
        profile.html
    static/
      users/
        users.css
    tests/
      __init__.py
      test_models.py
      test_views.py
```

Best practices here:[^3][^5]

- One **responsibility** per app (auth, payments, blog), not one giant “core” app.
- Keep templates and static files either app‑scoped (`app_name/...`) or in a shared top‑level folder with clear naming.[^1][^3][^6]
- Add a `tests` package per app with model/view/service tests to keep things local and readable.[^5][^3]


## Settings and environment management

Avoid a single `settings.py` for serious projects; use a settings package:[^1][^2][^3][^4]

- `base.py`: common settings (installed apps, middleware, templates, base DATABASES, REST framework, etc.).
- `dev.py`: debug on, local DB, console email backend, extra toolbars.
- `prod.py`: `DEBUG=False`, secure cookies, real database, cache, logging, allowed hosts, etc.

Load secrets and environment‑specific values (DB URLs, API keys) via environment variables or something like `python-dotenv`/`django-environ`, never hard‑code them.[^1][^3]

## Templates and static best practices

For templates:[^1][^3][^6]

- Use a global `templates/` with app‑namespaced folders or app‑local templates with the same convention, e.g. `templates/users/profile.html`.
- Have a base layout (`templates/base.html`) and extend it in app templates to avoid duplication.
- Set `DIRS` in `TEMPLATES` to include your global `templates/` folder.

For static files:[^1][^3][^4]

- Use `static/` at project root for shared assets, and `static/app_name/` inside apps for app‑specific assets.
- Configure `STATIC_ROOT` for collectstatic and keep `media/` separate with its own root and URL.


## Architectural best practices around structure

To keep the folder structure from turning into a ball of mud: [^1][^2][^3][^7]

- **Modular apps, not monolith app**: split by business domain, not by technical layer only.
- Consider a light “service layer”: `services.py`/`use_cases.py` for write operations, `selectors.py`/`queries.py` for read logic, so views stay thin.
- Keep third‑party config (e.g. DRF, Celery) in dedicated modules like `myproject/api/`, `myproject/celery.py`, and wire them via settings.
- Put deployment/ops scripts in `scripts/` or `infra/` rather than mixing them into apps.

If you share your target use case (e.g., “SaaS dashboard with REST API + admin”), I can propose a concrete tree adapted to that, including suggested apps (`accounts`, `organizations`, `billing`, etc.) and where to place DRF, Celery, and front‑end code.
<span style="display:none">[^10][^11][^12][^13][^14][^15][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://www.hostinger.com/in/tutorials/django-best-practices

[^2]: https://www.bluetickconsultants.com/building-a-scalable-and-maintainable-architecture-for-large-scale-django-projects/

[^3]: https://www.geeksforgeeks.org/python/best-practice-for-django-project-working-directory-structure/

[^4]: https://stackoverflow.com/questions/22841764/best-practice-for-django-project-working-directory-structure

[^5]: https://www.revsys.com/tidbits/recommended-django-project-layout/

[^6]: https://learndjango.com/tutorials/template-structure

[^7]: https://django-best-practices.readthedocs.io

[^8]: https://forum.djangoproject.com/t/best-practices-for-structuring-django-projects/39835

[^9]: https://www.hostinger.com/tutorials/django-best-practices

[^10]: https://www.reddit.com/r/django/comments/1gsuhmj/what_is_the_industry_standard_for_django_project/

[^11]: https://timmyomahony.com/blog/updated-django-project-structure-or-folder-layout/

[^12]: https://noumenal.es/notes/django/single-folder-layout/

[^13]: https://github.com/saqibur/django-project-structure

[^14]: https://codingandclimbing.in/starting-a-django-project-best-practices-code-snippets/

[^15]: https://forum.djangoproject.com/t/django-folder-file-structure/32287

