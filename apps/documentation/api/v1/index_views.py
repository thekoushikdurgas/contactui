"""
Index API v1 - 8 GET routes (read index + validate per resource type).
"""

from __future__ import annotations

import logging
from django.views.decorators.http import require_http_methods
from django.http import HttpRequest, JsonResponse

from apps.documentation.services import get_shared_s3_index_manager
from apps.documentation.utils.cache_decorator import cache_documentation_get

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
@cache_documentation_get(timeout=300)
def index_pages(request: HttpRequest) -> JsonResponse:
    try:
        m = get_shared_s3_index_manager()
        data = m.read_index("pages")
        return JsonResponse(data)
    except Exception as e:
        logger.exception("index pages failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
@cache_documentation_get(timeout=300)
def index_endpoints(request: HttpRequest) -> JsonResponse:
    try:
        m = get_shared_s3_index_manager()
        data = m.read_index("endpoints")
        return JsonResponse(data)
    except Exception as e:
        logger.exception("index endpoints failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
@cache_documentation_get(timeout=300)
def index_relationships(request: HttpRequest) -> JsonResponse:
    try:
        m = get_shared_s3_index_manager()
        data = m.read_index("relationships")
        return JsonResponse(data)
    except Exception as e:
        logger.exception("index relationships failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
@cache_documentation_get(timeout=300)
def index_postman(request: HttpRequest) -> JsonResponse:
    try:
        m = get_shared_s3_index_manager()
        data = m.read_index("postman")
        return JsonResponse(data)
    except Exception as e:
        logger.exception("index postman failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def index_pages_validate(request: HttpRequest) -> JsonResponse:
    try:
        m = get_shared_s3_index_manager()
        result = m.validate_index("pages")
        return JsonResponse(result)
    except Exception as e:
        logger.exception("index pages validate failed")
        return JsonResponse({"detail": str(e), "valid": False}, status=500)


@require_http_methods(["GET"])
def index_endpoints_validate(request: HttpRequest) -> JsonResponse:
    try:
        m = get_shared_s3_index_manager()
        result = m.validate_index("endpoints")
        return JsonResponse(result)
    except Exception as e:
        logger.exception("index endpoints validate failed")
        return JsonResponse({"detail": str(e), "valid": False}, status=500)


@require_http_methods(["GET"])
def index_relationships_validate(request: HttpRequest) -> JsonResponse:
    try:
        m = get_shared_s3_index_manager()
        result = m.validate_index("relationships")
        return JsonResponse(result)
    except Exception as e:
        logger.exception("index relationships validate failed")
        return JsonResponse({"detail": str(e), "valid": False}, status=500)


@require_http_methods(["GET"])
def index_postman_validate(request: HttpRequest) -> JsonResponse:
    try:
        m = get_shared_s3_index_manager()
        result = m.validate_index("postman")
        return JsonResponse(result)
    except Exception as e:
        logger.exception("index postman validate failed")
        return JsonResponse({"detail": str(e), "valid": False}, status=500)
