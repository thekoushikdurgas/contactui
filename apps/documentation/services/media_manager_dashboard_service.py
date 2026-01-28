"""Media Manager Dashboard Service - Unified service wrapper for dashboard operations."""

import logging
from typing import Optional, Dict, Any, List
from apps.core.services.base_service import BaseService
from apps.documentation.services import (
    get_pages_service,
    get_endpoints_service,
    get_relationships_service,
    get_postman_service,
)
from apps.documentation.utils.health_checks import get_comprehensive_health_status

logger = logging.getLogger(__name__)


class MediaManagerDashboardService(BaseService):
    """Unified service for Media Manager Dashboard operations."""
    
    def __init__(self):
        """Initialize Media Manager Dashboard Service."""
        super().__init__("MediaManagerDashboardService")
        self.pages_service = get_pages_service()
        self.endpoints_service = get_endpoints_service()
        self.relationships_service = get_relationships_service()
        self.postman_service = get_postman_service()
        self.cache_timeout = 300  # 5 minutes default
    
    def get_dashboard_overview(self) -> Dict[str, Any]:
        """
        Get overview statistics for all resource types.
        
        Returns:
            Dictionary with overview statistics including:
            - total_pages, total_endpoints, total_relationships, total_postman
            - pages_by_type, endpoints_by_method, relationships_by_type
            - last_updated timestamps
        """
        try:
            # Get statistics from all services
            pages_stats = self.pages_service.get_pages_statistics()
            endpoints_stats = self.endpoints_service.get_api_version_statistics()
            relationships_stats = self.relationships_service.get_statistics()
            postman_stats = self.postman_service.get_statistics()
            
            return {
                "pages": {
                    "total": pages_stats.get("total", 0),
                    "by_type": pages_stats.get("statistics", {}).get("by_type", {}),
                    "by_state": pages_stats.get("statistics", {}).get("by_state", {}),
                    "last_updated": pages_stats.get("last_updated"),
                },
                "endpoints": {
                    "total": sum(v.get("count", 0) for v in endpoints_stats.get("versions", [])),
                    "by_api_version": {v.get("api_version"): v.get("count", 0) for v in endpoints_stats.get("versions", [])},
                    "by_method": self.endpoints_service.get_method_statistics().get("methods", []),
                },
                "relationships": {
                    "total": relationships_stats.get("total_relationships", 0),
                    "by_usage_type": relationships_stats.get("by_usage_type", {}),
                    "by_usage_context": relationships_stats.get("by_usage_context", {}),
                },
                "postman": {
                    "total": postman_stats.get("total_configurations", 0),
                    "by_state": postman_stats.get("by_state", {}),
                    "last_updated": postman_stats.get("updated_at"),
                },
            }
        except Exception as e:
            self.logger.error(f"Failed to get dashboard overview: {e}", exc_info=True)
            return {
                "pages": {"total": 0, "by_type": {}, "by_state": {}},
                "endpoints": {"total": 0, "by_api_version": {}, "by_method": []},
                "relationships": {"total": 0, "by_usage_type": {}, "by_usage_context": {}},
                "postman": {"total": 0, "by_state": {}},
            }
    
    def get_resource_list(
        self,
        resource_type: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Get list of resources with filters.
        
        Args:
            resource_type: Resource type ('pages', 'endpoints', 'relationships', 'postman')
            filters: Optional filters dictionary
            
        Returns:
            Dictionary with resource list and total count
        """
        filters = filters or {}
        
        try:
            if resource_type == "pages":
                return self.pages_service.list_pages(
                    page_type=filters.get("page_type"),
                    status=filters.get("status"),
                    page_state=filters.get("state"),
                    include_drafts=filters.get("include_drafts", True),
                    include_deleted=filters.get("include_deleted", False),
                    limit=filters.get("limit"),
                    offset=filters.get("offset", 0),
                )
            elif resource_type == "endpoints":
                return self.endpoints_service.list_endpoints(
                    api_version=filters.get("api_version"),
                    method=filters.get("method"),
                    endpoint_state=filters.get("state"),
                    limit=filters.get("limit"),
                    offset=filters.get("offset", 0),
                )
            elif resource_type == "relationships":
                return self.relationships_service.list_relationships(
                    page_id=filters.get("page_id"),
                    endpoint_id=filters.get("endpoint_id"),
                    usage_type=filters.get("usage_type"),
                    usage_context=filters.get("usage_context"),
                    limit=filters.get("limit"),
                    offset=filters.get("offset", 0),
                )
            elif resource_type == "postman":
                return self.postman_service.list_configurations(
                    state=filters.get("state"),
                    limit=filters.get("limit"),
                    offset=filters.get("offset", 0),
                )
            else:
                raise ValueError(f"Invalid resource_type: {resource_type}")
        except Exception as e:
            self.logger.error(f"Failed to get resource list for {resource_type}: {e}", exc_info=True)
            return {"pages": [], "endpoints": [], "relationships": [], "postman": [], "total": 0}.get(resource_type, {})
    
    def get_resource_detail(
        self,
        resource_type: str,
        resource_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed resource information.
        
        Args:
            resource_type: Resource type ('pages', 'endpoints', 'relationships', 'postman')
            resource_id: Resource identifier
            
        Returns:
            Resource data dictionary or None if not found
        """
        try:
            if resource_type == "pages":
                return self.pages_service.get_page(resource_id)
            elif resource_type == "endpoints":
                return self.endpoints_service.get_endpoint(resource_id)
            elif resource_type == "relationships":
                return self.relationships_service.get_relationship(resource_id)
            elif resource_type == "postman":
                return self.postman_service.get_configuration(resource_id)
            else:
                raise ValueError(f"Invalid resource_type: {resource_type}")
        except Exception as e:
            self.logger.error(f"Failed to get resource detail for {resource_type}/{resource_id}: {e}", exc_info=True)
            return None
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status for all components.
        
        Returns:
            Dictionary with health status for all components
        """
        try:
            return get_comprehensive_health_status()
        except Exception as e:
            self.logger.error(f"Failed to get health status: {e}", exc_info=True)
            return {
                "status": "unknown",
                "components": {
                    "application": {"status": "unknown"},
                    "database": {"status": "unknown"},
                    "cache": {"status": "unknown"},
                    "storage": {"status": "unknown"},
                    "external_api": {"status": "unknown"},
                },
            }
    
    def get_resource_counts(self) -> Dict[str, int]:
        """
        Get counts for all resource types.
        
        Returns:
            Dictionary with counts for each resource type
        """
        try:
            pages_result = self.pages_service.list_pages(limit=1, offset=0)
            endpoints_result = self.endpoints_service.list_endpoints(limit=1, offset=0)
            relationships_result = self.relationships_service.list_relationships(limit=1, offset=0)
            postman_result = self.postman_service.list_configurations(limit=1, offset=0)
            
            return {
                "pages": pages_result.get("total", 0),
                "endpoints": endpoints_result.get("total", 0),
                "relationships": relationships_result.get("total", 0),
                "postman": postman_result.get("total", 0),
            }
        except Exception as e:
            self.logger.error(f"Failed to get resource counts: {e}", exc_info=True)
            return {
                "pages": 0,
                "endpoints": 0,
                "relationships": 0,
                "postman": 0,
            }
