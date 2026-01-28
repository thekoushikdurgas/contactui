"""
Postman API v1 - Lambda-parity GET endpoints (14 routes).
"""

from __future__ import annotations

import logging
from django.views.decorators.http import require_http_methods
from django.http import HttpRequest, JsonResponse

from apps.documentation.services import get_postman_service
from apps.documentation.utils.format_examples import postman_examples, analysis_examples
from apps.documentation.utils.cache_decorator import cache_documentation_get
from django.conf import settings
from apps.documentation.utils.list_projectors import should_expand_full, to_postman_list_item

logger = logging.getLogger(__name__)
DATA_PREFIX = getattr(settings, "S3_DATA_PREFIX", "data/")


@require_http_methods(["GET"])
@cache_documentation_get(timeout=300)
def postman_list(request: HttpRequest) -> JsonResponse:
    try:
        s = get_postman_service()
        r = s.list_configurations(limit=None, offset=0)
        configurations = r.get("configurations", [])
        if not should_expand_full(request.GET):
            configurations = [to_postman_list_item(c) for c in configurations]
        return JsonResponse({"configurations": configurations, "total": r.get("total", 0)})
    except Exception as e:
        logger.exception("postman list failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def postman_statistics(request: HttpRequest) -> JsonResponse:
    try:
        s = get_postman_service()
        st = s.get_statistics()
        return JsonResponse(st)
    except Exception as e:
        logger.exception("postman statistics failed")
        return JsonResponse({})


@require_http_methods(["GET"])
@cache_documentation_get(timeout=3600)
def postman_format(request: HttpRequest) -> JsonResponse:
    examples = postman_examples(DATA_PREFIX)
    return JsonResponse({
        "resource": "postman",
        "s3_data_prefix": DATA_PREFIX,
        "examples": examples,
    })


@require_http_methods(["GET"])
def postman_by_state_list(request: HttpRequest, state: str) -> JsonResponse:
    try:
        s = get_postman_service()
        r = s.list_by_state(state)
        if not should_expand_full(request.GET) and isinstance(r, dict) and isinstance(r.get("configurations"), list):
            r = {**r, "configurations": [to_postman_list_item(c) for c in r.get("configurations", [])]}
        return JsonResponse(r)
    except Exception as e:
        logger.exception("postman by-state failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def postman_by_state_count(request: HttpRequest, state: str) -> JsonResponse:
    try:
        s = get_postman_service()
        count = s.count_by_state(state)
        return JsonResponse({"state": state, "count": count})
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
@cache_documentation_get(timeout=600)
def postman_detail(request: HttpRequest, config_id: str) -> JsonResponse:
    try:
        s = get_postman_service()
        c = s.get_configuration(config_id)
        if not c:
            return JsonResponse({"detail": f"Configuration '{config_id}' not found"}, status=404)
        return JsonResponse(c)
    except Exception as e:
        logger.exception("postman detail failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def postman_detail_collection(request: HttpRequest, config_id: str) -> JsonResponse:
    """GET /api/v1/postman/{config_id}/collection/
    
    Returns collection from a configuration. Matches Lambda API behavior:
    - Returns 404 only if configuration not found
    - Returns collection object wrapped in {"collection": ...}
    """
    try:
        s = get_postman_service()
        collection = s.get_collection(config_id)
        if collection is None:
            return JsonResponse({"detail": f"Configuration '{config_id}' not found"}, status=404)
        # Match Lambda API format: {"collection": collection}
        return JsonResponse({"collection": collection})
    except Exception as e:
        logger.exception("postman detail collection failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def postman_detail_environments(request: HttpRequest, config_id: str) -> JsonResponse:
    try:
        s = get_postman_service()
        envs = s.get_environments(config_id)
        return JsonResponse({"config_id": config_id, "environments": envs or []})
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def postman_detail_environment(request: HttpRequest, config_id: str, env_name: str) -> JsonResponse:
    try:
        s = get_postman_service()
        env = s.get_environment(config_id, env_name)
        if env is None:
            return JsonResponse({"detail": f"Environment '{env_name}' not found"}, status=404)
        return JsonResponse(env)
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def postman_detail_mappings(request: HttpRequest, config_id: str) -> JsonResponse:
    try:
        s = get_postman_service()
        mappings = s.get_endpoint_mappings(config_id)
        return JsonResponse({"config_id": config_id, "mappings": mappings or []})
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def postman_detail_mapping(request: HttpRequest, config_id: str, mapping_id: str) -> JsonResponse:
    try:
        s = get_postman_service()
        mappings = s.get_endpoint_mappings(config_id)
        m = next((x for x in (mappings or []) if str(x.get("id")) == str(mapping_id) or x.get("mapping_id") == mapping_id), None)
        if m is None:
            return JsonResponse({"detail": "Mapping not found"}, status=404)
        return JsonResponse(m)
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def postman_detail_test_suites(request: HttpRequest, config_id: str) -> JsonResponse:
    try:
        s = get_postman_service()
        suites = s.get_test_suites(config_id)
        return JsonResponse({"config_id": config_id, "test_suites": suites or []})
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def postman_detail_test_suite(request: HttpRequest, config_id: str, suite_id: str) -> JsonResponse:
    try:
        s = get_postman_service()
        suite = s.get_test_suite(config_id, suite_id)
        if suite is None:
            return JsonResponse({"detail": "Test suite not found"}, status=404)
        return JsonResponse(suite)
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def postman_detail_access_control(request: HttpRequest, config_id: str) -> JsonResponse:
    try:
        s = get_postman_service()
        ac = s.get_access_control(config_id)
        return JsonResponse({"config_id": config_id, "access_control": ac})
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)
