"""Admin views - users, stats, history, logs, system status, settings."""
import logging
from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from apps.core.decorators.auth import require_super_admin, require_admin_or_super_admin
from apps.core.clients.appointment360_client import Appointment360Client
from apps.core.exceptions import LambdaAPIError
from apps.core.services.graphql_client import GraphQLError
from .services.admin_client import AdminGraphQLClient
from .services.logs_api_client import LogsApiClient
from .utils import build_logs_query_params, time_range_to_iso

logger = logging.getLogger(__name__)

LOGS_API_ENABLED = getattr(settings, "LOGS_API_ENABLED", False)
VALID_PER_PAGE = (10, 25, 50, 100)


def _get_client(request):
    return AdminGraphQLClient(request)


@login_required
@require_super_admin
def users_view(request):
    """User Management - SuperAdmin only."""
    page = int(request.GET.get("page", 1))
    per_page = 10
    offset = (page - 1) * per_page
    context = {"users": [], "total": 0, "error": None, "page": page, "per_page": per_page, "total_pages": 0}
    try:
        client = _get_client(request)
        result = client.list_users(limit=per_page, offset=offset)
        context["users"] = result.get("users", [])
        context["total"] = result.get("total", 0)
        context["total_pages"] = max(1, (context["total"] + per_page - 1) // per_page)
    except GraphQLError as e:
        logger.warning("Admin users GraphQL error: %s", e)
        context["error"] = str(e)
    except Exception as e:
        logger.exception("Admin users error")
        context["error"] = str(e)
    return render(request, "admin/users.html", context)


@login_required
@require_super_admin
def user_history_view(request):
    """User History - SuperAdmin only."""
    page = int(request.GET.get("page", 1))
    event_type = request.GET.get("event_type", "all")
    per_page = 15
    offset = (page - 1) * per_page
    context = {
        "history": [],
        "total": 0,
        "error": None,
        "page": page,
        "per_page": per_page,
        "total_pages": 0,
        "event_type": event_type,
    }
    try:
        client = _get_client(request)
        ev = event_type if event_type not in ("all", "") else None
        result = client.get_user_history(event_type=ev, limit=per_page, offset=offset)
        context["history"] = result.get("items", [])
        context["total"] = result.get("total", 0)
        context["total_pages"] = max(1, (context["total"] + per_page - 1) // per_page)
    except GraphQLError as e:
        logger.warning("Admin user history GraphQL error: %s", e)
        context["error"] = str(e)
    except Exception as e:
        logger.exception("Admin user history error")
        context["error"] = str(e)
    return render(request, "admin/user_history.html", context)


@login_required
@require_admin_or_super_admin
def statistics_view(request):
    """Statistics - Admin or SuperAdmin."""
    context = {"stats": None, "error": None}
    try:
        client = _get_client(request)
        stats = client.get_user_stats()
        plans = stats.get("users_by_plan") or {}
        stats["total_subscriptions"] = sum(plans.values())
        context["stats"] = stats
    except GraphQLError as e:
        logger.warning("Admin statistics GraphQL error: %s", e)
        context["error"] = str(e)
    except Exception as e:
        logger.exception("Admin statistics error")
        context["error"] = str(e)
    return render(request, "admin/statistics.html", context)


@login_required
@require_admin_or_super_admin
def logs_view(request):
    """System Logs - Admin or SuperAdmin. Uses Lambda logs.api when configured."""
    page = max(1, int(request.GET.get("page", 1)))
    time_range = request.GET.get("time_range", "24h")
    level = request.GET.get("level", "").strip()
    logger_filter = request.GET.get("logger", "").strip()
    user_id = request.GET.get("user_id", "").strip()
    search = request.GET.get("search", "").strip()
    raw_per_page = int(request.GET.get("per_page", 50))
    per_page = raw_per_page if raw_per_page in VALID_PER_PAGE else 50
    skip = (page - 1) * per_page

    context = {
        "log_stats": None,
        "logs": [],
        "total": 0,
        "error": None,
        "page": page,
        "per_page": per_page,
        "total_pages": 0,
        "time_range": time_range,
        "level_filter": level,
        "logger_filter": logger_filter,
        "user_id_filter": user_id,
        "search": search,
        "start_index": 0,
        "end_index": 0,
        "logs_api_enabled": LOGS_API_ENABLED,
        "prev_query_params": None,
        "next_query_params": None,
        "page_urls": [],
    }

    try:
        if LOGS_API_ENABLED:
            logs_client = LogsApiClient()
            context["log_stats"] = logs_client.get_statistics(
                time_range=time_range, period="hourly"
            )
            start_time, end_time = time_range_to_iso(time_range)
            if search:
                result = logs_client.search_logs(
                    query=search,
                    level=level or None,
                    logger_filter=logger_filter or None,
                    user_id=user_id or None,
                    start_time=start_time,
                    end_time=end_time,
                    limit=per_page,
                    skip=skip,
                )
            else:
                result = logs_client.query_logs(
                    level=level or None,
                    logger_filter=logger_filter or None,
                    user_id=user_id or None,
                    start_time=start_time,
                    end_time=end_time,
                    limit=per_page,
                    skip=skip,
                )
        else:
            client = _get_client(request)
            context["log_stats"] = client.get_log_statistics(time_range=time_range)
            result = client.query_logs(
                level=level or None,
                logger_filter=logger_filter or None,
                user_id=user_id or None,
                limit=per_page,
                skip=skip,
            )

        context["logs"] = result.get("items", [])
        context["total"] = result.get("total", 0)
        context["total_pages"] = max(1, (context["total"] + per_page - 1) // per_page)
        total = context["total"]
        context["start_index"] = (page - 1) * per_page + 1 if total else 0
        context["end_index"] = min(page * per_page, total) if total else 0
        total_pages = context["total_pages"]
        base = lambda p: build_logs_query_params(
            page=p,
            per_page=per_page,
            time_range=time_range,
            level=level,
            logger_filter=logger_filter,
            user_id=user_id,
            search=search,
        )
        context["query_params"] = base(page)
        context["prev_query_params"] = base(page - 1) if page > 1 else None
        context["next_query_params"] = base(page + 1) if page < total_pages else None
        # Page links: show current ±2
        context["page_numbers"] = [
            n for n in range(1, total_pages + 1)
            if page - 2 <= n <= page + 2
        ]
        context["page_urls"] = [(n, base(n)) for n in context["page_numbers"]]
    except (GraphQLError, LambdaAPIError) as e:
        logger.warning("Admin logs error: %s", e)
        context["error"] = str(e)
    except Exception as e:
        logger.exception("Admin logs error")
        context["error"] = str(e)
    return render(request, "admin/logs.html", context)


@login_required
@require_admin_or_super_admin
def system_status_view(request):
    """System Status - Admin or SuperAdmin."""
    context = {"metadata": None, "health": None, "error": None}
    try:
        client = _get_client(request)
        context["metadata"] = client.get_api_metadata()
        context["health"] = client.get_api_health()
    except GraphQLError as e:
        logger.warning("Admin system status GraphQL error: %s", e)
        context["error"] = str(e)
    except Exception as e:
        logger.exception("Admin system status error")
        context["error"] = str(e)
    return render(request, "admin/system_status.html", context)


@login_required
@require_admin_or_super_admin
def settings_view(request):
    """Admin Settings - Admin or SuperAdmin. Placeholder forms."""
    is_super_admin = False
    try:
        token = request.COOKIES.get("access_token") or (
            request.META.get("HTTP_AUTHORIZATION", "").replace("Bearer ", "")
        )
        if token:
            client = Appointment360Client()
            is_super_admin = client.is_super_admin(token)
    except Exception:
        pass
    context = {"is_super_admin": is_super_admin, "error": None}
    return render(request, "admin/settings.html", context)
