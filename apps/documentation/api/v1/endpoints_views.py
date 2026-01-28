"""
Endpoints API v1 - Lambda-parity GET endpoints (28 routes).

Static routes before parameterized {endpoint_id}, {api_version}, {method}, {state}, {service_name}.
"""

from __future__ import annotations

import logging
from collections import Counter
from django.views.decorators.http import require_http_methods
from django.http import HttpRequest, JsonResponse

from apps.documentation.services import get_endpoints_service
from apps.documentation.utils.format_examples import endpoint_examples, analysis_examples
from apps.documentation.utils.cache_decorator import cache_documentation_get
from django.conf import settings
from apps.documentation.utils.list_projectors import should_expand_full, to_endpoint_list_item

logger = logging.getLogger(__name__)
DATA_PREFIX = getattr(settings, "S3_DATA_PREFIX", "data/")


@require_http_methods(["GET"])
@cache_documentation_get(timeout=300)
def endpoints_list(request: HttpRequest) -> JsonResponse:
    """GET /api/v1/endpoints/"""
    try:
        service = get_endpoints_service()
        result = service.list_endpoints(
            api_version=request.GET.get("api_version"),
            method=request.GET.get("method"),
            endpoint_state=request.GET.get("endpoint_state"),
            limit=int(request.GET.get("limit") or 0) or None,
            offset=int(request.GET.get("offset", 0)),
        )
        endpoints = result.get("endpoints", [])
        if not should_expand_full(request.GET):
            endpoints = [to_endpoint_list_item(ep) for ep in endpoints]
        return JsonResponse({"endpoints": endpoints, "total": result.get("total", 0)})
    except Exception as e:
        logger.exception("endpoints list failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
@cache_documentation_get(timeout=3600)
def endpoints_format(request: HttpRequest) -> JsonResponse:
    """GET /api/v1/endpoints/format/"""
    examples = endpoint_examples(DATA_PREFIX)
    return JsonResponse({
        "resource": "endpoints",
        "s3_data_prefix": DATA_PREFIX,
        "examples": examples,
        "analyse_payload_example": analysis_examples().get("endpoints_analysis"),
    })


@require_http_methods(["GET"])
def endpoints_api_versions(request: HttpRequest) -> JsonResponse:
    """GET /api/v1/endpoints/api-versions/"""
    try:
        service = get_endpoints_service()
        stats = service.get_api_version_statistics()
        return JsonResponse(stats)
    except Exception as e:
        logger.exception("endpoints api-versions failed")
        return JsonResponse({"versions": [], "total": 0})


@require_http_methods(["GET"])
@cache_documentation_get(timeout=300)
def endpoints_methods(request: HttpRequest) -> JsonResponse:
    """GET /api/v1/endpoints/methods/"""
    try:
        service = get_endpoints_service()
        stats = service.get_method_statistics()
        return JsonResponse(stats)
    except Exception as e:
        logger.exception("endpoints methods failed")
        return JsonResponse({"methods": [], "total": 0})


def _by_api_version_list(api_version: str) -> JsonResponse:
    try:
        service = get_endpoints_service()
        endpoints = service.get_endpoints_by_api_version(api_version)
        return JsonResponse({"endpoints": endpoints, "total": len(endpoints)})
    except Exception as e:
        logger.exception(f"endpoints by-api-version {api_version} failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
@cache_documentation_get(timeout=300)
def endpoints_by_api_version_v1(request: HttpRequest) -> JsonResponse:
    return _by_api_version_list("v1")


@require_http_methods(["GET"])
@cache_documentation_get(timeout=300)
def endpoints_by_api_version_v4(request: HttpRequest) -> JsonResponse:
    return _by_api_version_list("v4")


@require_http_methods(["GET"])
@cache_documentation_get(timeout=300)
def endpoints_by_api_version_graphql(request: HttpRequest) -> JsonResponse:
    return _by_api_version_list("graphql")


@require_http_methods(["GET"])
def endpoints_by_api_version_count(request: HttpRequest, api_version: str) -> JsonResponse:
    """GET /api/v1/endpoints/by-api-version/{api_version}/count/"""
    try:
        service = get_endpoints_service()
        count = service.count_endpoints_by_api_version(api_version)
        return JsonResponse({"api_version": api_version, "count": count})
    except Exception as e:
        logger.exception("endpoints by-api-version count failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def endpoints_by_api_version_stats(request: HttpRequest, api_version: str) -> JsonResponse:
    """GET /api/v1/endpoints/by-api-version/{api_version}/stats/"""
    try:
        service = get_endpoints_service()
        endpoints = service.get_endpoints_by_api_version(api_version)
        by_method = Counter(ep.get("method", "GET") for ep in endpoints)
        return JsonResponse({
            "api_version": api_version,
            "total": len(endpoints),
            "by_method": dict(by_method),
        })
    except Exception as e:
        logger.exception("endpoints by-api-version stats failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def endpoints_by_api_version_by_method(request: HttpRequest, api_version: str, method: str) -> JsonResponse:
    """GET /api/v1/endpoints/by-api-version/{api_version}/by-method/{method}/"""
    try:
        service = get_endpoints_service()
        endpoints = service.get_endpoints_by_version_and_method(api_version, method)
        return JsonResponse({"endpoints": endpoints, "total": len(endpoints)})
    except Exception as e:
        logger.exception("endpoints by-api-version by-method failed")
        return JsonResponse({"detail": str(e)}, status=500)


def _by_method_list(method: str) -> JsonResponse:
    try:
        service = get_endpoints_service()
        endpoints = service.get_endpoints_by_method(method)
        return JsonResponse({"endpoints": endpoints, "total": len(endpoints)})
    except Exception as e:
        logger.exception(f"endpoints by-method {method} failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
@cache_documentation_get(timeout=300)
def endpoints_by_method_get(request: HttpRequest) -> JsonResponse:
    return _by_method_list("GET")


@require_http_methods(["GET"])
@cache_documentation_get(timeout=300)
def endpoints_by_method_post(request: HttpRequest) -> JsonResponse:
    return _by_method_list("POST")


@require_http_methods(["GET"])
@cache_documentation_get(timeout=300)
def endpoints_by_method_query(request: HttpRequest) -> JsonResponse:
    return _by_method_list("QUERY")


@require_http_methods(["GET"])
@cache_documentation_get(timeout=300)
def endpoints_by_method_mutation(request: HttpRequest) -> JsonResponse:
    return _by_method_list("MUTATION")


@require_http_methods(["GET"])
def endpoints_by_method_count(request: HttpRequest, method: str) -> JsonResponse:
    """GET /api/v1/endpoints/by-method/{method}/count/"""
    try:
        service = get_endpoints_service()
        count = service.count_endpoints_by_method(method)
        return JsonResponse({"method": method, "count": count})
    except Exception as e:
        logger.exception("endpoints by-method count failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def endpoints_by_method_stats(request: HttpRequest, method: str) -> JsonResponse:
    """GET /api/v1/endpoints/by-method/{method}/stats/"""
    try:
        service = get_endpoints_service()
        endpoints = service.get_endpoints_by_method(method)
        by_version = Counter(ep.get("api_version", "v1") for ep in endpoints)
        return JsonResponse({
            "method": method,
            "total": len(endpoints),
            "by_api_version": dict(by_version),
        })
    except Exception as e:
        logger.exception("endpoints by-method stats failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
@cache_documentation_get(timeout=300)
def endpoints_by_state_list(request: HttpRequest, state: str) -> JsonResponse:
    """GET /api/v1/endpoints/by-state/{state}/"""
    try:
        service = get_endpoints_service()
        result = service.list_endpoints(endpoint_state=state, limit=None, offset=0)
        return JsonResponse({"endpoints": result.get("endpoints", []), "total": result.get("total", 0)})
    except Exception as e:
        logger.exception("endpoints by-state failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def endpoints_by_state_count(request: HttpRequest, state: str) -> JsonResponse:
    """GET /api/v1/endpoints/by-state/{state}/count/"""
    try:
        service = get_endpoints_service()
        result = service.list_endpoints(endpoint_state=state, limit=None, offset=0)
        return JsonResponse({"state": state, "count": result.get("total", 0)})
    except Exception as e:
        logger.exception("endpoints by-state count failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def endpoints_by_lambda_list(request: HttpRequest, service_name: str) -> JsonResponse:
    """GET /api/v1/endpoints/by-lambda/{service_name}/ - filter by lambda service name."""
    try:
        service = get_endpoints_service()
        result = service.list_endpoints(limit=None, offset=0)
        endpoints = result.get("endpoints", [])
        filtered = []
        for ep in endpoints:
            ls = ep.get("lambda_services") or {}
            primary = ls.get("primary") or {}
            if primary.get("service_name") == service_name:
                filtered.append(ep)
            for dep in (ls.get("dependencies") or []):
                if dep.get("service_name") == service_name:
                    filtered.append(ep)
                    break
        return JsonResponse({"endpoints": filtered, "total": len(filtered)})
    except Exception as e:
        logger.exception("endpoints by-lambda failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def endpoints_by_lambda_count(request: HttpRequest, service_name: str) -> JsonResponse:
    """GET /api/v1/endpoints/by-lambda/{service_name}/count/"""
    try:
        service = get_endpoints_service()
        result = service.list_endpoints(limit=None, offset=0)
        endpoints = result.get("endpoints", [])
        count = 0
        for ep in endpoints:
            ls = ep.get("lambda_services") or {}
            primary = ls.get("primary") or {}
            if primary.get("service_name") == service_name:
                count += 1
                continue
            for dep in (ls.get("dependencies") or []):
                if dep.get("service_name") == service_name:
                    count += 1
                    break
        return JsonResponse({"service_name": service_name, "count": count})
    except Exception as e:
        logger.exception("endpoints by-lambda count failed")
        return JsonResponse({"detail": str(e)}, status=500)


# ----- Detail and sub-resources (after all static/param lists) -----

@require_http_methods(["GET"])
@cache_documentation_get(timeout=600)
def endpoints_detail(request: HttpRequest, endpoint_id: str) -> JsonResponse:
    """GET /api/v1/endpoints/{endpoint_id}/"""
    try:
        service = get_endpoints_service()
        ep = service.get_endpoint(endpoint_id)
        if not ep:
            return JsonResponse({"detail": f"Endpoint '{endpoint_id}' not found"}, status=404)
        return JsonResponse(ep)
    except Exception as e:
        logger.exception("endpoints detail failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def endpoints_detail_pages(request: HttpRequest, endpoint_id: str) -> JsonResponse:
    """GET /api/v1/endpoints/{endpoint_id}/pages/ - used-by-pages."""
    try:
        service = get_endpoints_service()
        ep = service.get_endpoint(endpoint_id)
        if not ep:
            return JsonResponse({"detail": f"Endpoint '{endpoint_id}' not found"}, status=404)
        pages = ep.get("used_by_pages") or []
        return JsonResponse({"endpoint_id": endpoint_id, "pages": pages, "count": len(pages)})
    except Exception as e:
        logger.exception("endpoints detail pages failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def endpoints_detail_access_control(request: HttpRequest, endpoint_id: str) -> JsonResponse:
    """GET /api/v1/endpoints/{endpoint_id}/access-control/"""
    try:
        service = get_endpoints_service()
        ep = service.get_endpoint(endpoint_id)
        if not ep:
            return JsonResponse({"detail": f"Endpoint '{endpoint_id}' not found"}, status=404)
        return JsonResponse({"endpoint_id": endpoint_id, "access_control": ep.get("access_control")})
    except Exception as e:
        logger.exception("endpoints detail access_control failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def endpoints_detail_lambda_services(request: HttpRequest, endpoint_id: str) -> JsonResponse:
    """GET /api/v1/endpoints/{endpoint_id}/lambda-services/"""
    try:
        service = get_endpoints_service()
        ep = service.get_endpoint(endpoint_id)
        if not ep:
            return JsonResponse({"detail": f"Endpoint '{endpoint_id}' not found"}, status=404)
        return JsonResponse({"endpoint_id": endpoint_id, "lambda_services": ep.get("lambda_services")})
    except Exception as e:
        logger.exception("endpoints detail lambda_services failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def endpoints_detail_files(request: HttpRequest, endpoint_id: str) -> JsonResponse:
    """GET /api/v1/endpoints/{endpoint_id}/files/ - service_file, router_file."""
    try:
        service = get_endpoints_service()
        ep = service.get_endpoint(endpoint_id)
        if not ep:
            return JsonResponse({"detail": f"Endpoint '{endpoint_id}' not found"}, status=404)
        return JsonResponse({
            "endpoint_id": endpoint_id,
            "service_file": ep.get("service_file"),
            "router_file": ep.get("router_file"),
        })
    except Exception as e:
        logger.exception("endpoints detail files failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def endpoints_detail_methods(request: HttpRequest, endpoint_id: str) -> JsonResponse:
    """GET /api/v1/endpoints/{endpoint_id}/methods/ - service_methods."""
    try:
        service = get_endpoints_service()
        ep = service.get_endpoint(endpoint_id)
        if not ep:
            return JsonResponse({"detail": f"Endpoint '{endpoint_id}' not found"}, status=404)
        methods = ep.get("service_methods") or []
        return JsonResponse({"endpoint_id": endpoint_id, "methods": methods, "count": len(methods)})
    except Exception as e:
        logger.exception("endpoints detail methods failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def endpoints_detail_used_by_pages(request: HttpRequest, endpoint_id: str) -> JsonResponse:
    """GET /api/v1/endpoints/{endpoint_id}/used-by-pages/"""
    try:
        service = get_endpoints_service()
        ep = service.get_endpoint(endpoint_id)
        if not ep:
            return JsonResponse({"detail": f"Endpoint '{endpoint_id}' not found"}, status=404)
        pages = ep.get("used_by_pages") or []
        return JsonResponse({"endpoint_id": endpoint_id, "used_by_pages": pages, "count": len(pages)})
    except Exception as e:
        logger.exception("endpoints detail used-by-pages failed")
        return JsonResponse({"detail": str(e)}, status=500)



@require_http_methods(["GET"])
def endpoints_detail_dependencies(request: HttpRequest, endpoint_id: str) -> JsonResponse:
    """GET /api/v1/endpoints/{endpoint_id}/dependencies/"""
    try:
        service = get_endpoints_service()
        ep = service.get_endpoint(endpoint_id)
        if not ep:
            return JsonResponse({"detail": f"Endpoint '{endpoint_id}' not found"}, status=404)
        deps = (ep.get("lambda_services") or {}).get("dependencies") or []
        return JsonResponse({"endpoint_id": endpoint_id, "dependencies": deps, "count": len(deps)})
    except Exception as e:
        logger.exception("endpoints detail dependencies failed")
        return JsonResponse({"detail": str(e)}, status=500)
