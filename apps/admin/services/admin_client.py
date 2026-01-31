"""
Admin GraphQL Client - calls Appointment360 GraphQL API for admin operations.

Uses GraphQLClient with token from request cookies.
"""
import logging
from typing import Optional, Dict, Any, List

from apps.core.services.graphql_client import GraphQLClient, GraphQLError

logger = logging.getLogger(__name__)


class AdminGraphQLClient:
    """Client for admin GraphQL operations (users, stats, history, logs, health)."""

    def __init__(self, request=None):
        self.client = GraphQLClient(request=request)

    def list_users(
        self, limit: int = 10, offset: int = 0
    ) -> Dict[str, Any]:
        """
        List all users (SuperAdmin only).
        Returns: {users: [...], total: int}
        """
        query = """
        query ListUsers($filters: UserFilterInput) {
          admin {
            users(filters: $filters) {
              items {
                uuid
                email
                name
                isActive
                lastSignInAt
                createdAt
                profile {
                  role
                  credits
                  subscriptionPlan
                  subscriptionStatus
                }
              }
              pageInfo {
                total
                limit
                offset
              }
            }
          }
        }
        """
        data = self.client.execute_query(
            query,
            variables={"filters": {"limit": limit, "offset": offset}},
            use_cache=False,
        )
        if not data or "admin" not in data:
            return {"users": [], "total": 0}
        conn = data["admin"]["users"]
        items = conn.get("items", [])
        users = []
        for u in items:
            profile = u.get("profile") or {}
            users.append({
                "uuid": u.get("uuid", ""),
                "email": u.get("email", ""),
                "name": u.get("name") or "",
                "is_active": u.get("isActive", True),
                "role": profile.get("role", "FreeUser"),
                "credits": profile.get("credits", 0),
                "subscription_plan": profile.get("subscriptionPlan") or "free",
                "subscription_status": profile.get("subscriptionStatus") or "",
                "created_at": u.get("createdAt"),
                "last_sign_in_at": u.get("lastSignInAt"),
            })
        total = conn.get("pageInfo", {}).get("total", 0)
        return {"users": users, "total": total}

    def get_user_stats(self) -> Dict[str, Any]:
        """
        Get user statistics (Admin or SuperAdmin).
        Returns: {total_users, active_users, users_by_role, users_by_plan}
        """
        query = """
        query GetUserStats {
          admin {
            userStats {
              totalUsers
              activeUsers
              usersByRole
              usersByPlan
            }
          }
        }
        """
        data = self.client.execute_query(query, use_cache=True, cache_timeout=60)
        if not data or "admin" not in data:
            return {
                "total_users": 0,
                "active_users": 0,
                "users_by_role": {},
                "users_by_plan": {},
            }
        stats = data["admin"]["userStats"]
        return {
            "total_users": stats.get("totalUsers", 0),
            "active_users": stats.get("activeUsers", 0),
            "users_by_role": stats.get("usersByRole") or {},
            "users_by_plan": stats.get("usersByPlan") or {},
        }

    def get_user_history(
        self,
        event_type: Optional[str] = None,
        limit: int = 15,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Get user history (SuperAdmin only).
        Returns: {items: [...], total: int}
        """
        filters = {"limit": limit, "offset": offset}
        if event_type and event_type not in ("all", ""):
            filters["eventType"] = event_type
        query = """
        query GetUserHistory($filters: UserHistoryFilterInput) {
          admin {
            userHistory(filters: $filters) {
              items {
                id
                userId
                userEmail
                userName
                eventType
                ip
                country
                city
                createdAt
              }
              pageInfo {
                total
                limit
                offset
              }
            }
          }
        }
        """
        data = self.client.execute_query(
            query, variables={"filters": filters}, use_cache=False
        )
        if not data or "admin" not in data:
            return {"items": [], "total": 0}
        conn = data["admin"]["userHistory"]
        items = conn.get("items", [])
        history = []
        for h in items:
            history.append({
                "id": h.get("id", ""),
                "user_id": h.get("userId"),
                "user_email": h.get("userEmail"),
                "user_name": h.get("userName"),
                "event_type": h.get("eventType", ""),
                "ip": h.get("ip"),
                "country": h.get("country"),
                "city": h.get("city"),
                "created_at": h.get("createdAt"),
            })
        total = conn.get("pageInfo", {}).get("total", 0)
        return {"items": history, "total": total}

    def get_log_statistics(
        self, time_range: str = "24h"
    ) -> Dict[str, Any]:
        """
        Get log statistics (Admin or SuperAdmin).
        time_range: '1h', '24h', '7d', '30d'
        """
        query = """
        query GetLogStatistics($timeRange: String!) {
          admin {
            logStatistics(timeRange: $timeRange) {
              timeRange
              totalLogs
              byLevel
              errorRate
              avgResponseTimeMs
              slowQueriesCount
            }
          }
        }
        """
        data = self.client.execute_query(
            query, variables={"timeRange": time_range}, use_cache=True, cache_timeout=120
        )
        if not data or "admin" not in data:
            return {
                "total_logs": 0,
                "error_rate": 0,
                "avg_response_time_ms": 0,
                "slow_queries_count": 0,
                "by_level": {},
            }
        s = data["admin"]["logStatistics"]
        return {
            "total_logs": s.get("totalLogs", 0),
            "error_rate": s.get("errorRate", 0),
            "avg_response_time_ms": s.get("avgResponseTimeMs", 0),
            "slow_queries_count": s.get("slowQueriesCount", 0),
            "by_level": s.get("byLevel") or {},
            "time_range": s.get("timeRange", time_range),
        }

    def query_logs(
        self,
        level: Optional[str] = None,
        logger_filter: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> Dict[str, Any]:
        """
        Query logs with filters (Admin or SuperAdmin).
        Returns: {items: [...], total: int}
        """
        filters = {"limit": limit, "offset": skip}
        if level:
            filters["level"] = level
        if logger_filter:
            filters["logger"] = logger_filter
        if user_id:
            filters["userId"] = user_id
        query = """
        query QueryLogs($filters: LogQueryFilterInput) {
          admin {
            logs(filters: $filters) {
              items {
                id
                timestamp
                level
                logger
                message
                context
                performance
                error
                userId
                requestId
              }
              pageInfo {
                total
                limit
                offset
              }
            }
          }
        }
        """
        data = self.client.execute_query(
            query, variables={"filters": filters}, use_cache=False
        )
        if not data or "admin" not in data:
            return {"items": [], "total": 0}
        conn = data["admin"]["logs"]
        items = conn.get("items", [])
        logs = []
        for log in items:
            logs.append({
                "id": log.get("id", ""),
                "timestamp": log.get("timestamp"),
                "level": log.get("level", ""),
                "logger": log.get("logger", ""),
                "message": log.get("message", ""),
                "context": log.get("context"),
                "performance": log.get("performance"),
                "error": log.get("error"),
                "user_id": log.get("userId"),
                "request_id": log.get("requestId"),
            })
        total = conn.get("pageInfo", {}).get("total", 0)
        return {"items": logs, "total": total}

    def get_api_metadata(self) -> Optional[Dict[str, Any]]:
        """Get API metadata from health module."""
        query = """
        query GetAPIMetadata {
          health {
            apiMetadata {
              name
              version
              docs
            }
          }
        }
        """
        data = self.client.execute_query(query, use_cache=True, cache_timeout=300)
        if not data or "health" not in data:
            return None
        m = data["health"].get("apiMetadata")
        if not m:
            return None
        return {
            "name": m.get("name", ""),
            "version": m.get("version", ""),
            "docs": m.get("docs", ""),
        }

    def get_api_health(self) -> Optional[Dict[str, Any]]:
        """Get API health status."""
        query = """
        query GetHealth {
          health {
            apiHealth {
              status
              environment
            }
          }
        }
        """
        data = self.client.execute_query(query, use_cache=False)
        if not data or "health" not in data:
            return None
        h = data["health"].get("apiHealth")
        if not h:
            return None
        return {
            "status": h.get("status", "unknown"),
            "environment": h.get("environment", ""),
        }
