"""
Logs API Client - HTTP client for Lambda logs.api REST endpoints.

Uses X-API-Key authentication. When LOGS_API_URL and LOGS_API_KEY are configured,
admin logs page fetches from Lambda logs.api instead of GraphQL.
"""
import logging
from typing import Any, Dict, List, Optional

import httpx
from django.conf import settings

from apps.core.exceptions import LambdaAPIError

logger = logging.getLogger(__name__)


class LogsApiClient:
    """Client for Lambda logs.api REST endpoints."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self.base_url = (base_url or getattr(settings, "LOGS_API_URL", "") or "").rstrip(
            "/"
        )
        self.api_key = api_key or getattr(settings, "LOGS_API_KEY", "") or ""
        self.timeout = timeout or getattr(settings, "LOGS_API_TIMEOUT", 30)

    def _headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-Key": self.api_key,
        }

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        with httpx.Client(timeout=self.timeout) as client:
            try:
                resp = client.request(
                    method=method,
                    url=url,
                    headers=self._headers(),
                    params=params,
                    json=json_data,
                )
                resp.raise_for_status()
                data = resp.json()
                if not isinstance(data, dict):
                    raise LambdaAPIError(
                        "Invalid response format",
                        endpoint=path,
                        status_code=resp.status_code,
                    )
                if not data.get("success", True):
                    raise LambdaAPIError(
                        data.get("detail", "Request failed"),
                        endpoint=path,
                        status_code=resp.status_code,
                    )
                return data
            except httpx.HTTPStatusError as e:
                detail = "Unknown error"
                try:
                    err_body = e.response.json()
                    if isinstance(err_body, dict) and "detail" in err_body:
                        detail = (
                            err_body["detail"]
                            if isinstance(err_body["detail"], str)
                            else str(err_body["detail"])
                        )
                except Exception:
                    detail = e.response.text or str(e)
                raise LambdaAPIError(
                    detail,
                    endpoint=path,
                    status_code=e.response.status_code,
                ) from e
            except httpx.RequestError as e:
                raise LambdaAPIError(
                    str(e),
                    endpoint=path,
                ) from e

    def get_statistics(
        self,
        time_range: str = "24h",
        period: str = "hourly",
    ) -> Dict[str, Any]:
        """Get aggregated log statistics.

        Args:
            time_range: '1h', '24h', '7d', or '30d'
            period: 'hourly', 'daily', or 'weekly'

        Returns:
            Dict with total_logs, error_rate, avg_response_time_ms, slow_queries_count,
            by_level, time_range
        """
        data = self._request(
            "GET",
            "/logs/statistics",
            params={"time_range": time_range, "period": period},
        )
        d = data.get("data") or {}
        return {
            "total_logs": d.get("total_logs", 0),
            "error_rate": d.get("error_rate", 0),
            "avg_response_time_ms": d.get("avg_response_time_ms", 0),
            "slow_queries_count": d.get("slow_queries_count", 0),
            "by_level": d.get("by_level") or {},
            "time_range": d.get("time_range", time_range),
        }

    def _normalize_log(self, log: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize log item to admin format (snake_case, consistent keys)."""
        return {
            "id": log.get("id", ""),
            "timestamp": log.get("timestamp"),
            "level": log.get("level", ""),
            "logger": log.get("logger", ""),
            "message": log.get("message", ""),
            "context": log.get("context"),
            "performance": log.get("performance"),
            "error": log.get("error"),
            "user_id": log.get("user_id"),
            "request_id": log.get("request_id"),
        }

    def query_logs(
        self,
        level: Optional[str] = None,
        logger_filter: Optional[str] = None,
        user_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> Dict[str, Any]:
        """Query logs with filters.

        Args:
            level: Log level filter
            logger_filter: Logger name filter
            user_id: User ID filter
            start_time: Start time (ISO)
            end_time: End time (ISO)
            limit: Max results
            skip: Offset for pagination

        Returns:
            Dict with items (list of logs) and total
        """
        params: Dict[str, Any] = {"limit": limit, "skip": skip}
        if level:
            params["level"] = level
        if logger_filter:
            params["logger"] = logger_filter
        if user_id:
            params["user_id"] = user_id
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time

        data = self._request("GET", "/logs/", params=params)
        d = data.get("data") or {}
        items = d.get("items") or []
        total = d.get("total", 0)
        return {
            "items": [self._normalize_log(x) for x in items],
            "total": total,
        }

    def search_logs(
        self,
        query: str,
        level: Optional[str] = None,
        logger_filter: Optional[str] = None,
        user_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> Dict[str, Any]:
        """Full-text search logs.

        Args:
            query: Search query (required)
            level: Log level filter
            logger_filter: Logger name filter
            user_id: User ID filter
            start_time: Start time (ISO)
            end_time: End time (ISO)
            limit: Max results
            skip: Offset for pagination

        Returns:
            Dict with items (list of logs), total, query
        """
        params: Dict[str, Any] = {"query": query, "limit": limit, "skip": skip}
        if level:
            params["level"] = level
        if logger_filter:
            params["logger"] = logger_filter
        if user_id:
            params["user_id"] = user_id
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time

        data = self._request("GET", "/logs/search", params=params)
        d = data.get("data") or {}
        items = d.get("items") or []
        total = d.get("total", 0)
        return {
            "items": [self._normalize_log(x) for x in items],
            "total": total,
        }
