"""
Relationships API v1 - Lambda-parity GET endpoints (38 routes).
"""

from __future__ import annotations

import logging
from django.views.decorators.http import require_http_methods
from django.http import HttpRequest, JsonResponse

from apps.documentation.services import get_relationships_service
from apps.documentation.utils.format_examples import relationship_examples, analysis_examples
from apps.documentation.utils.cache_decorator import cache_documentation_get
from django.conf import settings
from apps.documentation.utils.list_projectors import should_expand_full, to_relationship_list_item

logger = logging.getLogger(__name__)
DATA_PREFIX = getattr(settings, "S3_DATA_PREFIX", "data/")


def _rel_list(request: HttpRequest, usage_type=None, usage_context=None, page_id=None, endpoint_id=None):
    s = get_relationships_service()
    r = s.list_relationships(usage_type=usage_type, usage_context=usage_context, page_id=page_id, endpoint_id=endpoint_id, limit=None, offset=0)
    relationships = r.get("relationships", [])
    if not should_expand_full(request.GET):
        relationships = [to_relationship_list_item(rel) for rel in relationships]
    return JsonResponse({"relationships": relationships, "total": r.get("total", 0)})


@require_http_methods(["GET"])
@cache_documentation_get(timeout=300)
def relationships_list(request: HttpRequest) -> JsonResponse:
    try:
        return _rel_list(request)
    except Exception as e:
        logger.exception("relationships list failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
@cache_documentation_get(timeout=3600)
def relationships_format(request: HttpRequest) -> JsonResponse:
    examples = relationship_examples(DATA_PREFIX)
    return JsonResponse({
        "resource": "relationships",
        "s3_data_prefix": DATA_PREFIX,
        "examples": examples,
        "analyse_payload_example": analysis_examples().get("relationships_analysis"),
    })


@require_http_methods(["GET"])
@cache_documentation_get(timeout=300)
def relationships_graph(request: HttpRequest) -> JsonResponse:
    try:
        s = get_relationships_service()
        g = s.get_graph()
        return JsonResponse(g)
    except Exception as e:
        logger.exception("relationships graph failed")
        return JsonResponse({"nodes": [], "edges": []})


@require_http_methods(["GET"])
@cache_documentation_get(timeout=300)
def relationships_statistics(request: HttpRequest) -> JsonResponse:
    try:
        s = get_relationships_service()
        st = s.get_statistics()
        return JsonResponse(st)
    except Exception as e:
        logger.exception("relationships statistics failed")
        return JsonResponse({"total_relationships": 0, "unique_pages": 0, "unique_endpoints": 0})


@require_http_methods(["GET"])
def relationships_usage_types(request: HttpRequest) -> JsonResponse:
    try:
        s = get_relationships_service()
        st = s.get_statistics()
        by_ut = st.get("by_usage_type", {})
        types_data = [{"usage_type": k, "count": v} for k, v in by_ut.items()]
        return JsonResponse({"usage_types": types_data, "total": sum(v for v in by_ut.values())})
    except Exception as e:
        return JsonResponse({"usage_types": [], "total": 0})


@require_http_methods(["GET"])
def relationships_usage_contexts(request: HttpRequest) -> JsonResponse:
    try:
        s = get_relationships_service()
        st = s.get_statistics()
        by_uc = st.get("by_usage_context", {})
        ctx_data = [{"usage_context": k, "count": v} for k, v in by_uc.items()]
        return JsonResponse({"usage_contexts": ctx_data, "total": sum(v for v in by_uc.values())})
    except Exception as e:
        return JsonResponse({"usage_contexts": [], "total": 0})


# by-page, by-endpoint, by-usage-type, by-usage-context
@require_http_methods(["GET"])
def relationships_by_page(request: HttpRequest, page_id: str) -> JsonResponse:
    try:
        return _rel_list(page_id=page_id)
    except Exception as e:
        logger.exception("relationships by-page failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def relationships_by_page_count(request: HttpRequest, page_id: str) -> JsonResponse:
    try:
        s = get_relationships_service()
        r = s.list_relationships(page_id=page_id, limit=None, offset=0)
        return JsonResponse({"page_id": page_id, "count": r.get("total", 0)})
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def relationships_by_page_primary(request: HttpRequest, page_id: str) -> JsonResponse:
    try:
        return _rel_list(page_id=page_id, usage_type="primary")
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def relationships_by_page_secondary(request: HttpRequest, page_id: str) -> JsonResponse:
    try:
        return _rel_list(page_id=page_id, usage_type="secondary")
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def relationships_by_page_by_usage_type(request: HttpRequest, page_id: str, usage_type: str) -> JsonResponse:
    try:
        return _rel_list(page_id=page_id, usage_type=usage_type)
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def relationships_by_endpoint(request: HttpRequest, endpoint_id: str) -> JsonResponse:
    try:
        return _rel_list(endpoint_id=endpoint_id)
    except Exception as e:
        logger.exception("relationships by-endpoint failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def relationships_by_endpoint_count(request: HttpRequest, endpoint_id: str) -> JsonResponse:
    try:
        s = get_relationships_service()
        r = s.list_relationships(endpoint_id=endpoint_id, limit=None, offset=0)
        return JsonResponse({"endpoint_id": endpoint_id, "count": r.get("total", 0)})
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def relationships_by_endpoint_pages(request: HttpRequest, endpoint_id: str) -> JsonResponse:
    try:
        s = get_relationships_service()
        r = s.list_relationships(endpoint_id=endpoint_id, limit=None, offset=0)
        rels = r.get("relationships", [])
        pages = []
        for rel in rels:
            if rel.get("page_path"):
                pages.append({"page_path": rel.get("page_path"), "page_title": rel.get("page_title", "")})
        return JsonResponse({"endpoint_id": endpoint_id, "pages": pages, "count": len(pages)})
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def relationships_by_endpoint_by_usage_context(request: HttpRequest, endpoint_id: str, usage_context: str) -> JsonResponse:
    """GET /api/v1/relationships/by-endpoint/{endpoint_id}/by-usage-context/{usage_context}/
    Matches Lambda API shape: endpoint_id, usage_context, relationships, count."""
    try:
        s = get_relationships_service()
        r = s.list_relationships(endpoint_id=endpoint_id, usage_context=usage_context, limit=None, offset=0)
        rels = r.get("relationships", [])
        return JsonResponse({
            "endpoint_id": endpoint_id,
            "usage_context": usage_context,
            "relationships": rels,
            "count": len(rels),
        })
    except Exception as e:
        logger.exception("relationships by-endpoint by-usage-context failed")
        return JsonResponse({"detail": str(e)}, status=500)


# by-usage-type static
@require_http_methods(["GET"])
def relationships_by_usage_type_primary(request: HttpRequest) -> JsonResponse:
    try:
        return _rel_list(usage_type="primary")
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def relationships_by_usage_type_secondary(request: HttpRequest) -> JsonResponse:
    try:
        return _rel_list(usage_type="secondary")
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def relationships_by_usage_type_conditional(request: HttpRequest) -> JsonResponse:
    try:
        return _rel_list(usage_type="conditional")
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def relationships_by_usage_type_count(request: HttpRequest, usage_type: str) -> JsonResponse:
    try:
        s = get_relationships_service()
        r = s.list_relationships(usage_type=usage_type, limit=None, offset=0)
        return JsonResponse({"usage_type": usage_type, "count": r.get("total", 0)})
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def relationships_by_usage_type_by_usage_context(request: HttpRequest, usage_type: str, usage_context: str) -> JsonResponse:
    try:
        return _rel_list(usage_type=usage_type, usage_context=usage_context)
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


# by-usage-context static
@require_http_methods(["GET"])
def relationships_by_usage_context_data_fetching(request: HttpRequest) -> JsonResponse:
    try:
        return _rel_list(usage_context="data_fetching")
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def relationships_by_usage_context_data_mutation(request: HttpRequest) -> JsonResponse:
    try:
        return _rel_list(usage_context="data_mutation")
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def relationships_by_usage_context_authentication(request: HttpRequest) -> JsonResponse:
    try:
        return _rel_list(usage_context="authentication")
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def relationships_by_usage_context_analytics(request: HttpRequest) -> JsonResponse:
    try:
        return _rel_list(usage_context="analytics")
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def relationships_by_usage_context_count(request: HttpRequest, usage_context: str) -> JsonResponse:
    try:
        s = get_relationships_service()
        r = s.list_relationships(usage_context=usage_context, limit=None, offset=0)
        return JsonResponse({"usage_context": usage_context, "count": r.get("total", 0)})
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


# by-state
@require_http_methods(["GET"])
def relationships_by_state_list(request: HttpRequest, state: str) -> JsonResponse:
    try:
        s = get_relationships_service()
        r = s.list_relationships(limit=None, offset=0)
        rels = [x for x in (r.get("relationships") or []) if (x.get("state") or x.get("relationship_state")) == state]
        return JsonResponse({"relationships": rels, "total": len(rels)})
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def relationships_by_state_count(request: HttpRequest, state: str) -> JsonResponse:
    try:
        s = get_relationships_service()
        r = s.list_relationships(limit=None, offset=0)
        rels = [x for x in (r.get("relationships") or []) if (x.get("state") or x.get("relationship_state")) == state]
        return JsonResponse({"state": state, "count": len(rels)})
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


# by-lambda, by-invocation-pattern, by-postman-config (stub filter)
@require_http_methods(["GET"])
def relationships_by_lambda(request: HttpRequest, service_name: str) -> JsonResponse:
    try:
        s = get_relationships_service()
        r = s.list_relationships(limit=None, offset=0)
        rels = [x for x in (r.get("relationships") or []) if (x.get("lambda_service") or x.get("via_service")) == service_name]
        return JsonResponse({"relationships": rels, "total": len(rels)})
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def relationships_by_invocation_pattern(request: HttpRequest, pattern: str) -> JsonResponse:
    try:
        s = get_relationships_service()
        r = s.list_relationships(limit=None, offset=0)
        rels = [x for x in (r.get("relationships") or []) if pattern in str(x.get("via_hook", "")) or pattern in str(x.get("via_service", ""))]
        return JsonResponse({"relationships": rels, "total": len(rels)})
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def relationships_by_postman_config(request: HttpRequest, config_id: str) -> JsonResponse:
    try:
        s = get_relationships_service()
        r = s.list_relationships(limit=None, offset=0)
        rels = [x for x in (r.get("relationships") or []) if x.get("postman_config_id") == config_id]
        return JsonResponse({"relationships": rels, "total": len(rels)})
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def relationships_performance_slow(request: HttpRequest) -> JsonResponse:
    try:
        s = get_relationships_service()
        r = s.list_relationships(limit=None, offset=0)
        rels = [x for x in (r.get("relationships") or []) if (x.get("performance") or {}).get("slow")]
        return JsonResponse({"relationships": rels, "total": len(rels)})
    except Exception as e:
        return JsonResponse({"relationships": [], "total": 0})


@require_http_methods(["GET"])
def relationships_performance_errors(request: HttpRequest) -> JsonResponse:
    try:
        s = get_relationships_service()
        r = s.list_relationships(limit=None, offset=0)
        rels = [x for x in (r.get("relationships") or []) if (x.get("performance") or {}).get("errors")]
        return JsonResponse({"relationships": rels, "total": len(rels)})
    except Exception as e:
        return JsonResponse({"relationships": [], "total": 0})


# detail and sub-resources
@require_http_methods(["GET"])
@cache_documentation_get(timeout=600)
def relationships_detail(request: HttpRequest, relationship_id: str) -> JsonResponse:
    try:
        s = get_relationships_service()
        rel = s.get_relationship(relationship_id)
        if not rel:
            return JsonResponse({"detail": f"Relationship '{relationship_id}' not found"}, status=404)
        return JsonResponse(rel)
    except Exception as e:
        logger.exception("relationships detail failed")
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def relationships_detail_access_control(request: HttpRequest, relationship_id: str) -> JsonResponse:
    try:
        s = get_relationships_service()
        rel = s.get_relationship(relationship_id)
        if not rel:
            return JsonResponse({"detail": f"Relationship '{relationship_id}' not found"}, status=404)
        return JsonResponse({"relationship_id": relationship_id, "access_control": rel.get("access_control")})
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def relationships_detail_data_flow(request: HttpRequest, relationship_id: str) -> JsonResponse:
    try:
        s = get_relationships_service()
        rel = s.get_relationship(relationship_id)
        if not rel:
            return JsonResponse({"detail": f"Relationship '{relationship_id}' not found"}, status=404)
        return JsonResponse({"relationship_id": relationship_id, "data_flow": rel.get("data_flow")})
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def relationships_detail_performance(request: HttpRequest, relationship_id: str) -> JsonResponse:
    try:
        s = get_relationships_service()
        rel = s.get_relationship(relationship_id)
        if not rel:
            return JsonResponse({"detail": f"Relationship '{relationship_id}' not found"}, status=404)
        return JsonResponse({"relationship_id": relationship_id, "performance": rel.get("performance")})
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def relationships_detail_dependencies(request: HttpRequest, relationship_id: str) -> JsonResponse:
    try:
        s = get_relationships_service()
        rel = s.get_relationship(relationship_id)
        if not rel:
            return JsonResponse({"detail": f"Relationship '{relationship_id}' not found"}, status=404)
        return JsonResponse({"relationship_id": relationship_id, "dependencies": rel.get("dependencies", [])})
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@require_http_methods(["GET"])
def relationships_detail_postman(request: HttpRequest, relationship_id: str) -> JsonResponse:
    try:
        s = get_relationships_service()
        rel = s.get_relationship(relationship_id)
        if not rel:
            return JsonResponse({"detail": f"Relationship '{relationship_id}' not found"}, status=404)
        return JsonResponse({"relationship_id": relationship_id, "postman": rel.get("postman")})
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)
