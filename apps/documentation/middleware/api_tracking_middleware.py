"""
Middleware to track GET requests to /api/v1/ and record per-endpoint hits for statistics.
"""

from __future__ import annotations

import logging
import time
from typing import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from apps.documentation.api.v1.api_docs_registry import resolve_endpoint_key
from apps.documentation.utils.api_tracking_storage import record_hit

logger = logging.getLogger(__name__)


class ApiTrackingMiddleware:
    """
    Record each GET request to /api/v1/ for the API docs statistics.
    Runs after AuthenticationMiddleware; does not affect response.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        self.enabled = getattr(settings, "API_TRACKING_ENABLED", True)
        self.prefix = getattr(settings, "API_TRACKING_PATH_PREFIX", "/api/v1/")

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not self.enabled or request.method != "GET" or not request.path.startswith(self.prefix):
            return self.get_response(request)

        start = time.perf_counter()
        response = self.get_response(request)
        duration_ms = (time.perf_counter() - start) * 1000

        endpoint_key = resolve_endpoint_key(request.path)
        if endpoint_key:
            try:
                record_hit(endpoint_key, response.status_code, duration_ms)
            except Exception as e:
                logger.warning("ApiTrackingMiddleware record_hit failed: %s", e)

        return response
