"""GraphQL Documentation Service - Wrapper for appointment360 GraphQL API."""

from __future__ import annotations

import logging
import time
from typing import Optional, Dict, Any, List
from django.conf import settings
from django.core.cache import cache
from apps.core.services.graphql_client import GraphQLClient, GraphQLError

logger = logging.getLogger(__name__)

# Default cache timeouts (in seconds)
DEFAULT_CACHE_TIMEOUT = 300  # 5 minutes for queries
LIST_CACHE_TIMEOUT = 60  # 1 minute for list queries
DETAIL_CACHE_TIMEOUT = 300  # 5 minutes for detail queries


class GraphQLDocumentationService:
    """Service wrapper for documentation GraphQL queries and mutations with enhanced caching and logging."""
    
    def __init__(self):
        """Initialize GraphQL documentation service with enhanced configuration."""
        endpoint_url = getattr(
            settings,
            "APPOINTMENT360_GRAPHQL_URL",
            "http://localhost:8000/graphql",
        )
        api_key = getattr(settings, "APPOINTMENT360_GRAPHQL_API_KEY", None)
        
        self.client = GraphQLClient(endpoint_url=endpoint_url, api_key=api_key)
        
        # Metrics
        self.query_count = 0
        self.mutation_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.error_count = 0
        self.total_query_time = 0.0
        
        logger.info(
            "GraphQLDocumentationService initialized: endpoint=%s, api_key_configured=%s",
            endpoint_url,
            bool(api_key),
        )
    
    def _get_cache_key(self, operation: str, **kwargs: Any) -> str:
        """Generate cache key for operation with parameters."""
        key_parts = [f"graphql_docs:{operation}"]
        for key, value in sorted(kwargs.items()):
            if value is not None:
                key_parts.append(f"{key}:{value}")
        return ":".join(key_parts)
    
    def _invalidate_cache(self, operation: str, **kwargs: Any) -> None:
        """
        Invalidate cache for a specific operation.
        
        Note: Django cache doesn't support pattern deletion easily.
        This method attempts to delete the specific cache key.
        For production, consider using cache versioning.
        
        Args:
            operation: Operation name
            **kwargs: Operation parameters
        """
        try:
            cache_key = self._get_cache_key(operation, **kwargs)
            cache.delete(cache_key)
            logger.debug("Cache invalidated for key: %s", cache_key)
        except Exception as e:
            logger.warning("Failed to invalidate cache for %s: %s", operation, e)
    
    def _log_operation(
        self,
        operation: str,
        operation_type: str,
        duration: Optional[float] = None,
        success: bool = True,
        error: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Enhanced logging for GraphQL operations."""
        log_data: Dict[str, Any] = {
            "operation": operation,
            "operation_type": operation_type,
            "success": success,
        }
        
        if duration is not None:
            log_data["duration_ms"] = round(duration * 1000, 2)
        
        if error:
            log_data["error"] = error
        
        log_data.update(kwargs)
        
        if success:
            logger.info("GraphQL operation completed: %s", log_data, extra=log_data)
        else:
            logger.error("GraphQL operation failed: %s", log_data, extra=log_data)
    
    def get_page(self, page_id: str, page_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get a single documentation page by page_id."""
        query = """
        query GetDocumentationPage($pageId: String!, $pageType: String) {
            documentation {
                documentationPage(pageId: $pageId, pageType: $pageType) {
                    pageId
                    title
                    description
                    category
                    contentUrl
                    lastUpdated
                    version
                    id
                }
            }
        }
        """
        
        variables = {'pageId': page_id}
        if page_type:
            variables['pageType'] = page_type
        
        try:
            result = self.client.execute_query(query, variables, use_cache=True, cache_timeout=300)
            if result and 'documentation' in result:
                page = result['documentation'].get('documentationPage')
                if page:
                    return {
                        'page_id': page.get('pageId'),
                        'title': page.get('title'),
                        'description': page.get('description'),
                        'category': page.get('category'),
                        'content_url': page.get('contentUrl'),
                        'last_updated': page.get('lastUpdated'),
                        'version': page.get('version'),
                        '_id': page.get('id'),
                        'metadata': {
                            'title': page.get('title'),
                            'description': page.get('description'),
                            'category': page.get('category'),
                            'last_updated': page.get('lastUpdated'),
                            'version': page.get('version'),
                        }
                    }
            return None
        except GraphQLError as e:
            logger.error(f"GraphQL error getting page {page_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error getting page {page_id}: {str(e)}", exc_info=True)
            return None
    
    def list_pages(
        self,
        page_type: Optional[str] = None,
        include_drafts: bool = True,
        include_deleted: bool = False,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        List documentation pages with enhanced caching and logging.
        
        Args:
            page_type: Optional page type filter
            include_drafts: Include draft pages
            include_deleted: Include deleted pages
            status: Optional status filter
            limit: Optional limit for pagination
            offset: Offset for pagination
            use_cache: Whether to use query caching
            
        Returns:
            Dictionary with 'pages' list and 'total' count
        """
        start_time = time.time()
        self.query_count += 1
        
        # Check cache first
        cache_key = self._get_cache_key(
            "list_pages",
            page_type=page_type,
            include_drafts=include_drafts,
            include_deleted=include_deleted,
            status=status,
            limit=limit,
            offset=offset,
        )
        if use_cache:
            try:
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    self.cache_hits += 1
                    duration = time.time() - start_time
                    self._log_operation(
                        "list_pages",
                        "query",
                        duration,
                        True,
                        page_type=page_type,
                        total=len(cached_result.get("pages", [])),
                    )
                    return cached_result
            except Exception as e:
                logger.warning("Cache get failed for list_pages: %s", e)
        
        self.cache_misses += 1
        
        query = """
        query ListDocumentationPages(
            $pageType: String,
            $includeDrafts: Boolean,
            $includeDeleted: Boolean,
            $status: String
        ) {
            documentation {
                documentationPages(
                    pageType: $pageType,
                    includeDrafts: $includeDrafts,
                    includeDeleted: $includeDeleted,
                    status: $status
                ) {
                    pages {
                        pageId
                        title
                        description
                        category
                        contentUrl
                        lastUpdated
                        version
                        id
                    }
                    total
                }
            }
        }
        """
        
        variables: Dict[str, Any] = {
            "includeDrafts": include_drafts,
            "includeDeleted": include_deleted,
        }
        
        if page_type:
            variables["pageType"] = page_type
        if status:
            variables["status"] = status
        
        try:
            result = self.client.execute_query(
                query, variables, use_cache=use_cache, cache_timeout=LIST_CACHE_TIMEOUT
            )
            duration = time.time() - start_time
            self.total_query_time += duration
            
            if result and "documentation" in result:
                page_list = result["documentation"].get("documentationPages", {})
                pages = page_list.get("pages", [])
                total = page_list.get("total", 0)
                
                transformed_pages: List[Dict[str, Any]] = []
                for page in pages:
                    transformed_pages.append({
                        "page_id": page.get("pageId"),
                        "title": page.get("title"),
                        "description": page.get("description"),
                        "category": page.get("category"),
                        "content_url": page.get("contentUrl"),
                        "last_updated": page.get("lastUpdated"),
                        "version": page.get("version"),
                        "_id": page.get("id"),
                        "metadata": {
                            "title": page.get("title"),
                            "description": page.get("description"),
                            "category": page.get("category"),
                            "last_updated": page.get("lastUpdated"),
                            "version": page.get("version"),
                        },
                    })
                
                if limit is not None:
                    transformed_pages = transformed_pages[offset : offset + limit]
                elif offset > 0:
                    transformed_pages = transformed_pages[offset:]
                
                result_data = {"pages": transformed_pages, "total": total}
                
                # Cache successful result
                if use_cache:
                    try:
                        cache.set(cache_key, result_data, LIST_CACHE_TIMEOUT)
                    except Exception as e:
                        logger.warning("Cache set failed for list_pages: %s", e)
                
                self._log_operation(
                    "list_pages",
                    "query",
                    duration,
                    True,
                    page_type=page_type,
                    total=total,
                    returned=len(transformed_pages),
                )
                return result_data
            
            self._log_operation("list_pages", "query", duration, True, total=0)
            return {"pages": [], "total": 0}
        except GraphQLError as e:
            duration = time.time() - start_time
            self.error_count += 1
            self._log_operation("list_pages", "query", duration, False, str(e), page_type=page_type)
            return {"pages": [], "total": 0}
        except Exception as e:
            duration = time.time() - start_time
            self.error_count += 1
            logger.error("Error listing pages: %s", e, exc_info=True)
            self._log_operation("list_pages", "query", duration, False, str(e), page_type=page_type)
            return {"pages": [], "total": 0}
    
    def create_page(self, page_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new documentation page."""
        mutation = """
        mutation CreateDocumentationPage($input: CreateDocumentationPageInput!) {
            documentation {
                createDocumentationPage(input: $input) {
                    pageId
                    title
                    description
                    category
                    contentUrl
                    lastUpdated
                    version
                    id
                }
            }
        }
        """
        
        input_data = {
            'pageId': page_data.get('page_id'),
            'title': page_data.get('metadata', {}).get('title') or page_data.get('title', ''),
            'description': page_data.get('metadata', {}).get('description') or page_data.get('description'),
            'category': page_data.get('metadata', {}).get('category') or page_data.get('category'),
            'content': page_data.get('content', ''),
            'pageType': page_data.get('page_type', 'docs'),
        }
        
        variables = {'input': input_data}
        
        try:
            result = self.client.execute_mutation(mutation, variables)
            if result and 'documentation' in result:
                created_page = result['documentation'].get('createDocumentationPage')
                self.client.clear_cache()
                return created_page
            return None
        except GraphQLError as e:
            logger.error(f"GraphQL error creating page: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error creating page: {str(e)}", exc_info=True)
            return None
    
    def update_page(self, page_id: str, page_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing documentation page with cache invalidation.
        
        Args:
            page_id: Page identifier
            page_data: Updated page data
            
        Returns:
            Updated page data or None if error
        """
        start_time = time.time()
        self.mutation_count += 1
        
        mutation = """
        mutation UpdateDocumentationPage($pageId: String!, $input: UpdateDocumentationPageInput!) {
            documentation {
                updateDocumentationPage(pageId: $pageId, input: $input) {
                    pageId
                    title
                    description
                    category
                    contentUrl
                    lastUpdated
                    version
                    id
                }
            }
        }
        """
        
        input_data: Dict[str, Any] = {}
        metadata = page_data.get("metadata", {})
        
        if "title" in metadata or "title" in page_data:
            input_data["title"] = metadata.get("title") or page_data.get("title")
        if "description" in metadata or "description" in page_data:
            input_data["description"] = metadata.get("description") or page_data.get("description")
        if "category" in metadata or "category" in page_data:
            input_data["category"] = metadata.get("category") or page_data.get("category")
        if "content" in page_data:
            input_data["content"] = page_data["content"]
        if "status" in metadata:
            input_data["status"] = metadata["status"]
        
        variables = {"pageId": page_id, "input": input_data}
        
        try:
            result = self.client.execute_mutation(mutation, variables)
            duration = time.time() - start_time
            
            if result and "documentation" in result:
                updated_page = result["documentation"].get("updateDocumentationPage")
                
                # Invalidate cache
                self._invalidate_cache("list_pages")
                self._invalidate_cache("get_page", page_id=page_id)
                
                self._log_operation("update_page", "mutation", duration, True, page_id=page_id)
                return updated_page
            
            self._log_operation("update_page", "mutation", duration, False, "No result", page_id=page_id)
            return None
        except GraphQLError as e:
            duration = time.time() - start_time
            self.error_count += 1
            self._log_operation("update_page", "mutation", duration, False, str(e), page_id=page_id)
            return None
        except Exception as e:
            duration = time.time() - start_time
            self.error_count += 1
            logger.error("Error updating page %s: %s", page_id, e, exc_info=True)
            self._log_operation("update_page", "mutation", duration, False, str(e), page_id=page_id)
            return None
    
    def delete_page(self, page_id: str) -> bool:
        """
        Delete a documentation page with cache invalidation.
        
        Args:
            page_id: Page identifier
            
        Returns:
            True if deleted successfully, False otherwise
        """
        start_time = time.time()
        self.mutation_count += 1
        
        mutation = """
        mutation DeleteDocumentationPage($pageId: String!) {
            documentation {
                deleteDocumentationPage(pageId: $pageId) {
                    pageId
                }
            }
        }
        """
        
        variables = {"pageId": page_id}
        
        try:
            result = self.client.execute_mutation(mutation, variables)
            duration = time.time() - start_time
            
            if result and "documentation" in result:
                deleted = result["documentation"].get("deleteDocumentationPage")
                
                # Invalidate cache
                self._invalidate_cache("list_pages")
                self._invalidate_cache("get_page", page_id=page_id)
                
                success = deleted is not None
                self._log_operation("delete_page", "mutation", duration, success, page_id=page_id)
                return success
            
            self._log_operation("delete_page", "mutation", duration, False, "No result", page_id=page_id)
            return False
        except GraphQLError as e:
            duration = time.time() - start_time
            self.error_count += 1
            self._log_operation("delete_page", "mutation", duration, False, str(e), page_id=page_id)
            return False
        except Exception as e:
            duration = time.time() - start_time
            self.error_count += 1
            logger.error("Error deleting page %s: %s", page_id, e, exc_info=True)
            self._log_operation("delete_page", "mutation", duration, False, str(e), page_id=page_id)
            return False
