"""
List all GET routes under /api/v1/.

Use to verify the count of Lambda-parity GET endpoints (110) and prevent regressions.
Run: python manage.py runscript list_api_v1_get_routes (or run from project root with Django set up).

Alternatively run as:
  cd contact360/docsai && python -c "
  import os, django
  os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
  django.setup()
  from django.urls import get_resolver
  from django.urls.resolvers import URLPattern, URLResolver
  def list_get_patterns(urlpatterns, prefix=''):
      for p in urlpatterns:
          if isinstance(p, URLResolver):
              list_get_patterns(p.url_patterns, prefix + str(p.pattern))
          elif isinstance(p, URLPattern) and hasattr(p.callback, 'view_class') or callable(p.callback):
              pattern = prefix + str(p.pattern)
              if '/api/v1/' in pattern or pattern.startswith('api/v1') or prefix.startswith('/api/v1'):
                  print(pattern)
  r = get_resolver()
  list_get_patterns(r.url_patterns)
  "
"""

from __future__ import annotations

import os
import sys


def _collect_patterns(urlpatterns, prefix: str = ""):
    """Recursively collect (pattern_string, name) from urlpatterns."""
    from django.urls.resolvers import URLPattern, URLResolver
    out = []
    for p in urlpatterns:
        p_prefix = prefix + str(p.pattern)
        if isinstance(p, URLResolver):
            out.extend(_collect_patterns(p.url_patterns, p_prefix))
        elif isinstance(p, URLPattern):
            out.append((p_prefix, getattr(p, "name", None)))
    return out


def run():
    """List GET routes under /api/v1/ and print count."""
    import django
    from django.urls import get_resolver
    from django.conf import settings

    if not settings.configured:
        django.setup()

    root = get_resolver()
    api_v1_patterns = []
    for p in root.url_patterns:
        if str(p.pattern) == "api/v1/":
            api_v1_patterns = _collect_patterns(p.url_patterns, "/api/v1/")
            break
    if not api_v1_patterns:
        all_p = _collect_patterns(root.url_patterns, "")
        api_v1_patterns = [(pat, name) for pat, name in all_p if pat.startswith("/api/v1/") or "/api/v1/" in pat]

    # Filter to GET-only: Django doesn't attach method to path by default; all listed v1 routes are GET in our setup
    get_routes = sorted(set(pat for pat, _ in api_v1_patterns if pat))
    count = len(get_routes)
    print(f"Total GET routes under /api/v1/: {count}")
    print("Paths:")
    for path in get_routes:
        print(f"  {path}")
    # Expect 110 Lambda + 7 health + 4 dashboard = 121, or 110 + health/dashboard
    return count


if __name__ == "__main__":
    # Allow run from repo root: python contact360/docsai/scripts/list_api_v1_get_routes.py
    docsai_path = os.path.join(os.path.dirname(__file__), "..")
    if docsai_path not in sys.path:
        sys.path.insert(0, os.path.abspath(docsai_path))
    os.chdir(os.path.abspath(docsai_path))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    run()
