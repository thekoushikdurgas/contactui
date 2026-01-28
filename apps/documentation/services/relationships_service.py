"""Relationships Service with multi-strategy pattern (Local → S3 → Lambda)."""

import logging
from typing import Optional, Dict, Any, List
from apps.documentation.services.base import DocumentationServiceBase
from apps.documentation.repositories.unified_storage import UnifiedStorage
from apps.documentation.repositories.relationships_repository import RelationshipsRepository
from apps.documentation.repositories.local_json_storage import LocalJSONStorage
from apps.documentation.utils.retry import retry_on_network_error
from apps.documentation.utils.exceptions import DocumentationError

logger = logging.getLogger(__name__)


class RelationshipsService(DocumentationServiceBase):
    """Service for relationships operations with multi-strategy pattern using UnifiedStorage."""
    
    def __init__(
        self,
        unified_storage: Optional[UnifiedStorage] = None,
        repository: Optional[RelationshipsRepository] = None,
        local_storage: Optional[LocalJSONStorage] = None
    ):
        """Initialize relationships service.
        
        Args:
            unified_storage: Optional UnifiedStorage instance. If not provided, creates new one.
            repository: Optional RelationshipsRepository instance. If not provided, creates new one.
            local_storage: Optional LocalJSONStorage instance. If not provided, creates new one.
        """
        # Initialize base class with common patterns (Task 2.3.2)
        super().__init__(
            service_name="RelationshipsService",
            unified_storage=unified_storage,
            repository=repository or RelationshipsRepository(),
            resource_name="relationships"
        )
        # Local storage for fallback reads (uses 'relationships' folder)
        if local_storage is None:
            from apps.documentation.services import get_shared_local_storage
            self.local_storage = get_shared_local_storage()
        else:
            self.local_storage = local_storage
    
    def get_relationship(
        self,
        relationship_id: str,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get relationship by ID with multi-strategy:
        1. Try Local JSON files
        2. Fallback to S3
        3. Fallback to Lambda API
        
        Uses DocumentationServiceBase._get_resource() for common patterns (Task 2.3.2).
        
        Args:
            relationship_id: Relationship identifier
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Relationship data dictionary or None if not found
            
        Raises:
            DocumentationError: If retrieval fails after retries
        """
        return self._get_resource(
            resource_id=relationship_id,
            operation_name='get_relationship',
            storage_method='get_relationship',
            use_cache=use_cache
        )

    def get_relationship_by_id(
        self, relationship_id: str, use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Alias for get_relationship for Lambda API parity."""
        return self.get_relationship(relationship_id, use_cache=use_cache)

    def get_graph(self) -> Dict[str, Any]:
        """Get graph (nodes and edges) for relationships."""
        return self.unified_storage.get_relationship_graph()

    def list_relationships(
        self,
        page_id: Optional[str] = None,
        endpoint_id: Optional[str] = None,
        usage_type: Optional[str] = None,
        usage_context: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        List relationships with multi-strategy pattern:
        1. Try Local JSON files (primary)
        2. Fallback to S3 (via repository)
        3. Fallback to Lambda API (last resort)
        """
        cache_key = self._get_cache_key(
            'list_relationships',
            page_id=page_id,
            endpoint_id=endpoint_id,
            usage_type=usage_type,
            usage_context=usage_context,
            limit=limit,
            offset=offset
        )
        if use_cache:
            cached = self._get_from_cache(cache_key)
            if cached is not None:
                self.logger.debug("Cache hit for list_relationships")
                return cached

        # Try local JSON files first
        try:
            index_data = self.local_storage.get_index('relationships')
            relationships_list = index_data.get('relationships', [])
            
            if relationships_list:
                # Apply filters if provided
                filtered_relationships = relationships_list
                
                if page_id:
                    # Filter by page_id or page_path
                    filtered_relationships = [
                        rel for rel in filtered_relationships
                        if (rel.get('page_id') == page_id or 
                            rel.get('page_path') == page_id or
                            page_id in str(rel.get('page_id', '')) or
                            page_id in str(rel.get('page_path', '')))
                    ]
                
                if endpoint_id:
                    # Resolve endpoint_id to endpoint_path and method (matching Lambda API behavior)
                    endpoint_path = None
                    endpoint_method = None
                    try:
                        from apps.documentation.services import get_endpoints_service
                        endpoints_service = get_endpoints_service()
                        endpoint_data = endpoints_service.get_endpoint(endpoint_id)
                        if endpoint_data:
                            endpoint_path = endpoint_data.get('endpoint_path') or endpoint_data.get('endpoint_id')
                            endpoint_method = endpoint_data.get('method', 'GET')
                    except Exception as e:
                        self.logger.warning(f"Failed to resolve endpoint_id {endpoint_id}: {e}")
                    
                    # Filter by endpoint_id, endpoint_path, or resolved endpoint_path+method
                    if endpoint_path and endpoint_method:
                        # Use resolved endpoint_path and method (matching Lambda API)
                        filtered_relationships = [
                            rel for rel in filtered_relationships
                            if rel.get('endpoint_path') == endpoint_path and rel.get('method', 'GET').upper() == endpoint_method.upper()
                        ]
                    else:
                        # Fallback: try direct matching
                        filtered_relationships = [
                            rel for rel in filtered_relationships
                            if (rel.get('endpoint_id') == endpoint_id or
                                rel.get('endpoint_path') == endpoint_id or
                                endpoint_id in str(rel.get('endpoint_id', '')) or
                                endpoint_id in str(rel.get('endpoint_path', '')))
                        ]
                if usage_type:
                    filtered_relationships = [
                        rel for rel in filtered_relationships
                        if rel.get('usage_type') == usage_type
                    ]
                if usage_context:
                    # Flatten endpoint-centric format (endpoint_path, method, pages[]) to flat format
                    # when usage_context is requested and records have a pages array (usage_context lives per page)
                    flattened = []
                    for rel in filtered_relationships:
                        if rel.get('pages'):
                            for p in rel.get('pages', []):
                                flat = {
                                    'page_path': p.get('page_path'),
                                    'page_id': p.get('page_path'),
                                    'endpoint_path': rel.get('endpoint_path'),
                                    'method': rel.get('method'),
                                    'usage_type': p.get('usage_type', rel.get('usage_type')),
                                    'usage_context': p.get('usage_context', rel.get('usage_context')),
                                    'via_service': p.get('via_service'),
                                    'via_hook': p.get('via_hook'),
                                    'updated_at': p.get('updated_at', rel.get('updated_at')),
                                }
                                flattened.append(flat)
                        else:
                            flattened.append(rel)
                    filtered_relationships = flattened
                    # Filter by usage_context on the flat list
                    filtered_relationships = [
                        rel for rel in filtered_relationships
                        if rel.get('usage_context') == usage_context
                    ]
                
                # Apply pagination
                total = len(filtered_relationships)
                if limit is not None:
                    paginated = filtered_relationships[offset:offset + limit]
                else:
                    paginated = filtered_relationships[offset:]
                
                self.logger.info(f"Loaded {len(paginated)} relationships from local files (total: {total})")
                result = {'relationships': paginated, 'total': total, 'source': 'local'}
                if use_cache:
                    self._set_cache(cache_key, result, 120)  # 2 minutes for list operations
                return result
        except Exception as e:
            self.logger.warning(f"Failed to load relationships from local files: {e}")
        
        # Try S3 via repository (or unified_storage for usage filters)
        try:
            if usage_type or usage_context:
                result = self.unified_storage.list_relationships(
                    page_id=page_id,
                    endpoint_id=endpoint_id,
                    usage_type=usage_type,
                    usage_context=usage_context,
                    limit=limit,
                    offset=offset,
                )
                if result.get("relationships"):
                    self.logger.info(f"Loaded {len(result['relationships'])} relationships from unified_storage")
                    if use_cache:
                        self._set_cache(cache_key, result, 120)
                    return result
            relationships = self.repository.list_all(
                page_id=page_id,
                endpoint_id=endpoint_id,
                limit=limit,
                offset=offset
            )
            if usage_type or usage_context:
                relationships = [r for r in relationships if (not usage_type or r.get("usage_type") == usage_type) and (not usage_context or r.get("usage_context") == usage_context)]
            if relationships:
                self.logger.info(f"Loaded {len(relationships)} relationships from S3")
                result = {
                    'relationships': relationships,
                    'total': len(relationships),  # Note: repository doesn't return total, so we use length
                    'source': 's3'
                }
                if use_cache:
                    self._set_cache(cache_key, result, 120)  # 2 minutes for list operations
                return result
        except Exception as e:
            self.logger.warning(f"Failed to load relationships from S3: {e}")
        
        # Return empty result if all strategies failed
        self.logger.warning("All strategies failed to load relationships")
        return {
            'relationships': [],
            'total': 0,
            'source': 'none'
        }
    
    def create_relationship(self, relationship_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create relationship (use S3 direct for writes).
        
        Args:
            relationship_data: Relationship data dictionary
            
        Returns:
            Created relationship data dictionary or None if creation failed
            
        Raises:
            ValueError: If relationship data is invalid
            DocumentationError: If creation fails after retries
        """
        # Validate required fields
        required_fields = ['relationship_id', 'page_path', 'endpoint_path', 'method']
        is_valid, error_msg = self._validate_input(relationship_data, required_fields)
        if not is_valid:
            raise ValueError(error_msg)
        
        try:
            # Retry logic for external API calls
            @retry_on_network_error(max_retries=3, initial_delay=1.0)
            def _create_relationship_with_retry():
                return self.repository.create(relationship_data)
            
            result = _create_relationship_with_retry()
            
            # Invalidate cache after create
            if result:
                relationship_id = result.get('relationship_id') or relationship_data.get('relationship_id')
                # Clear specific relationship cache
                self.unified_storage.clear_cache('relationships', relationship_id)
                # Clear all list_relationships cache (pattern-based)
                self.unified_storage.clear_cache('relationships')
                self.logger.debug(f"Cleared cache for relationship {relationship_id} and all relationships lists after create")
            
            return result
            
        except Exception as e:
            error_response = self._handle_error(
                e,
                context=f"Failed to create relationship {relationship_data.get('relationship_id', 'unknown')}",
                record_monitoring=True
            )
            raise DocumentationError(
                f"Failed to create relationship: {error_response.get('error', str(e))}"
            ) from e
    
    def update_relationship(self, relationship_id: str, relationship_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update relationship (use S3 direct for writes).
        
        Args:
            relationship_id: Relationship identifier
            relationship_data: Relationship data dictionary (partial updates supported)
            
        Returns:
            Updated relationship data dictionary or None if update failed
            
        Raises:
            ValueError: If relationship not found
            DocumentationError: If update fails after retries
        """
        # Check if relationship exists
        existing = self.get_relationship(relationship_id, use_cache=False)
        if not existing:
            raise ValueError(f"Relationship not found: {relationship_id}")
        
        try:
            # Retry logic for external API calls
            @retry_on_network_error(max_retries=3, initial_delay=1.0)
            def _update_relationship_with_retry():
                return self.repository.update(relationship_id, relationship_data)
            
            result = _update_relationship_with_retry()
            
            # Invalidate cache after update
            if result:
                # Clear specific relationship cache
                self.unified_storage.clear_cache('relationships', relationship_id)
                # Clear all list_relationships cache (pattern-based)
                self.unified_storage.clear_cache('relationships')
                self.logger.debug(f"Cleared cache for relationship {relationship_id} and all relationships lists after update")
            
            return result
            
        except Exception as e:
            error_response = self._handle_error(
                e,
                context=f"Failed to update relationship {relationship_id}",
                record_monitoring=True
            )
            raise DocumentationError(
                f"Failed to update relationship {relationship_id}: {error_response.get('error', str(e))}"
            ) from e
    
    def delete_relationship(self, relationship_id: str) -> bool:
        """
        Delete relationship (use S3 direct for writes).
        
        Args:
            relationship_id: Relationship identifier
            
        Returns:
            True if deletion was successful, False otherwise
            
        Raises:
            DocumentationError: If deletion fails after retries
        """
        try:
            # Retry logic for external API calls
            @retry_on_network_error(max_retries=3, initial_delay=1.0)
            def _delete_relationship_with_retry():
                return self.repository.delete(relationship_id)
            
            success = _delete_relationship_with_retry()
            
            # Clear cache
            if success:
                self._clear_cache_for_relationship(relationship_id)
                # Invalidate cache after delete
                self.unified_storage.clear_cache('relationships', relationship_id)
                self.unified_storage.clear_cache('relationships')
                self.logger.debug(f"Cleared cache for relationship {relationship_id} and all relationships lists after delete")
            
            return success
            
        except Exception as e:
            error_response = self._handle_error(
                e,
                context=f"Failed to delete relationship {relationship_id}",
                record_monitoring=True
            )
            raise DocumentationError(
                f"Failed to delete relationship {relationship_id}: {error_response.get('error', str(e))}"
            ) from e
    
    def _clear_cache_for_relationship(self, relationship_id: str) -> None:
        """
        Clear cache entries for a specific relationship.
        
        Args:
            relationship_id: Relationship identifier
        """
        try:
            # Use UnifiedStorage's pattern-based cache clearing
            self.unified_storage.clear_cache('relationships', relationship_id)
            self.unified_storage.clear_cache('relationships')
        except Exception as e:
            self.logger.warning(f"Failed to clear cache for relationship {relationship_id}: {e}")
    
    def get_relationship_graph(self) -> Dict[str, Any]:
        """
        Get full relationship graph (nodes and edges) for visualization.
        
        Returns:
            Dictionary with 'nodes' and 'edges' or 'relationships' list
            
        Raises:
            DocumentationError: If retrieval fails after retries
        """
        try:
            # Build graph from local storage relationships
            try:
                index_data = self.local_storage.get_index('relationships')
                relationships = index_data.get('relationships', [])
                
                if relationships:
                    self.logger.info(f"Building graph from {len(relationships)} local relationships")
                    # Return relationships for client-side graph building
                    return {
                        'relationships': relationships,
                        'total': len(relationships)
                    }
            except Exception as e:
                self.logger.error(f"Local storage fallback for graph also failed: {e}")
            
            return {'nodes': [], 'edges': []}
            
        except Exception as e:
            error_response = self._handle_error(
                e,
                context="Failed to get relationship graph",
                record_monitoring=True
            )
            raise DocumentationError(
                f"Failed to get relationship graph: {error_response.get('error', str(e))}"
            ) from e
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get relationship statistics.
        
        Returns:
            Dictionary with relationship statistics
            
        Raises:
            DocumentationError: If retrieval fails after retries
        """
        try:
            # Calculate from local data
            all_rels = self.list_relationships()
            relationships = all_rels.get('relationships', [])
            
            unique_pages = set()
            unique_endpoints = set()
            by_api_version = {}
            by_usage_type = {}
            by_usage_context = {}
            
            for rel in relationships:
                if isinstance(rel, dict):
                    page_path = rel.get('page_path')
                    endpoint_path = rel.get('endpoint_path')
                    api_version = rel.get('api_version', 'unknown')
                    ut = rel.get('usage_type') or 'primary'
                    uc = rel.get('usage_context') or 'data_fetching'
                    if page_path:
                        unique_pages.add(page_path)
                    if endpoint_path:
                        unique_endpoints.add(endpoint_path)
                    by_api_version[api_version] = by_api_version.get(api_version, 0) + 1
                    by_usage_type[ut] = by_usage_type.get(ut, 0) + 1
                    by_usage_context[uc] = by_usage_context.get(uc, 0) + 1
            
            return {
                'total_relationships': len(relationships),
                'unique_pages': len(unique_pages),
                'unique_endpoints': len(unique_endpoints),
                'by_api_version': by_api_version,
                'by_usage_type': by_usage_type,
                'by_usage_context': by_usage_context,
                'total_endpoints_documented': 0,  # Would need endpoint count
                'total_pages_documented': 0,  # Would need page count
                'endpoints_with_pages': len(unique_endpoints),
                'pages_with_endpoints': len(unique_pages)
            }
            
        except Exception as e:
            error_response = self._handle_error(
                e,
                context="Failed to get relationship statistics",
                record_monitoring=True
            )
            raise DocumentationError(
                f"Failed to get relationship statistics: {error_response.get('error', str(e))}"
            ) from e
    
    def get_relationships_by_usage_type(self, usage_type: str) -> List[Dict[str, Any]]:
        """
        Get relationships by usage type.
        
        Args:
            usage_type: Usage type filter (e.g., 'QUERY', 'MUTATION')
            
        Returns:
            List of relationship dictionaries
            
        Raises:
            DocumentationError: If retrieval fails after retries
        """
        try:
            all_rels = self.list_relationships()
            relationships = all_rels.get('relationships', [])
            return [r for r in relationships if r.get('usage_type') == usage_type]
            
        except Exception as e:
            error_response = self._handle_error(
                e,
                context=f"Failed to get relationships by usage type {usage_type}",
                record_monitoring=True
            )
            raise DocumentationError(
                f"Failed to get relationships by usage type: {error_response.get('error', str(e))}"
            ) from e
    
    def get_relationships_by_usage_context(self, usage_context: str) -> List[Dict[str, Any]]:
        """
        Get relationships by usage context.
        
        Args:
            usage_context: Usage context filter
            
        Returns:
            List of relationship dictionaries
            
        Raises:
            DocumentationError: If retrieval fails after retries
        """
        try:
            # Filter from all relationships
            all_rels = self.list_relationships()
            relationships = all_rels.get('relationships', [])
            return [r for r in relationships if r.get('usage_context') == usage_context]
            
        except Exception as e:
            error_response = self._handle_error(
                e,
                context=f"Failed to get relationships by usage context {usage_context}",
                record_monitoring=True
            )
            raise DocumentationError(
                f"Failed to get relationships by usage context: {error_response.get('error', str(e))}"
            ) from e
    
    def count_relationships_by_page(self, page_id: str) -> int:
        """
        Count relationships for a page.
        
        Args:
            page_id: Page identifier
            
        Returns:
            Number of relationships for the page
        """
        try:
            relationships = self.list_relationships(page_id=page_id)
            return relationships.get('total', 0)
            
        except Exception as e:
            self.logger.warning(f"Failed to count relationships by page {page_id}: {e}")
            return 0
    
    def count_relationships_by_endpoint(self, endpoint_id: str) -> int:
        """
        Count relationships for an endpoint.
        
        Args:
            endpoint_id: Endpoint identifier
            
        Returns:
            Number of relationships for the endpoint
        """
        try:
            # Use list_relationships with endpoint_id filter
            relationships = self.list_relationships(endpoint_id=endpoint_id)
            return relationships.get('total', 0)
            
        except Exception as e:
            self.logger.warning(f"Failed to count relationships by endpoint {endpoint_id}: {e}")
            return 0
    
    def count_relationships_by_usage_type(self, usage_type: str) -> int:
        """
        Count relationships by usage type.
        
        Args:
            usage_type: Usage type filter
            
        Returns:
            Number of relationships with the specified usage type
        """
        try:
            relationships = self.get_relationships_by_usage_type(usage_type)
            return len(relationships)
        except Exception as e:
            self.logger.warning(f"Failed to count relationships by usage type {usage_type}: {e}")
            return 0
    
    def count_relationships_by_usage_context(self, usage_context: str) -> int:
        """
        Count relationships by usage context.
        
        Args:
            usage_context: Usage context filter
            
        Returns:
            Number of relationships with the specified usage context
        """
        try:
            relationships = self.get_relationships_by_usage_context(usage_context)
            return len(relationships)
        except Exception as e:
            self.logger.warning(f"Failed to count relationships by usage context {usage_context}: {e}")
            return 0
    
    def get_relationships_by_page(
        self,
        page_id: str,
        usage_type: Optional[str] = None,
        usage_context: Optional[str] = None,
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get all relationships for a specific page.
        
        Args:
            page_id: Page identifier
            usage_type: Optional usage type filter
            usage_context: Optional usage context filter
            use_cache: Whether to use cache (default: True)
            
        Returns:
            List of relationship dictionaries for the page
        """
        result = self.list_relationships(
            page_id=page_id,
            usage_type=usage_type,
            usage_context=usage_context,
            limit=None,
            offset=0,
            use_cache=use_cache,
        )
        return result.get("relationships", [])
    
    def get_relationships_by_endpoint(
        self,
        endpoint_id: str,
        usage_type: Optional[str] = None,
        usage_context: Optional[str] = None,
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get all relationships for a specific endpoint.
        
        Args:
            endpoint_id: Endpoint identifier
            usage_type: Optional usage type filter
            usage_context: Optional usage context filter
            use_cache: Whether to use cache (default: True)
            
        Returns:
            List of relationship dictionaries for the endpoint
        """
        result = self.list_relationships(
            endpoint_id=endpoint_id,
            usage_type=usage_type,
            usage_context=usage_context,
            limit=None,
            offset=0,
            use_cache=use_cache,
        )
        return result.get("relationships", [])
    
    def get_relationships_by_page_primary(
        self,
        page_id: str,
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get primary relationships for a page.
        
        Args:
            page_id: Page identifier
            use_cache: Whether to use cache (default: True)
            
        Returns:
            List of primary relationship dictionaries
        """
        return self.get_relationships_by_page(
            page_id=page_id,
            usage_type="primary",
            use_cache=use_cache,
        )
    
    def get_relationships_by_page_secondary(
        self,
        page_id: str,
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get secondary relationships for a page.
        
        Args:
            page_id: Page identifier
            use_cache: Whether to use cache (default: True)
            
        Returns:
            List of secondary relationship dictionaries
        """
        return self.get_relationships_by_page(
            page_id=page_id,
            usage_type="secondary",
            use_cache=use_cache,
        )
    
    def get_relationships_by_endpoint_pages(
        self,
        endpoint_id: str,
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get pages for an endpoint (from relationships).
        
        Args:
            endpoint_id: Endpoint identifier
            use_cache: Whether to use cache (default: True)
            
        Returns:
            List of page dictionaries that use this endpoint
        """
        relationships = self.get_relationships_by_endpoint(
            endpoint_id=endpoint_id,
            use_cache=use_cache,
        )
        
        # Extract unique pages from relationships
        page_ids = set()
        pages = []
        
        for rel in relationships:
            page_id = rel.get("page_id") or rel.get("page_path")
            if page_id and page_id not in page_ids:
                page_ids.add(page_id)
                # Get page details
                from apps.documentation.services import get_pages_service
                pages_service = get_pages_service()
                page = pages_service.get_page(page_id)
                if page:
                    pages.append(page)
        
        return pages
    
    def get_relationship_access_control(self, relationship_id: str) -> Optional[Dict[str, Any]]:
        """
        Get access_control sub-resource for a relationship.
        
        Args:
            relationship_id: Relationship identifier
            
        Returns:
            Access control dictionary or None if relationship not found
        """
        relationship = self.get_relationship(relationship_id)
        if not relationship:
            return None
        return relationship.get("access_control")
    
    def get_relationship_data_flow(self, relationship_id: str) -> Optional[Dict[str, Any]]:
        """
        Get data flow information for a relationship.
        
        Args:
            relationship_id: Relationship identifier
            
        Returns:
            Data flow dictionary or None if relationship not found
        """
        relationship = self.get_relationship(relationship_id)
        if not relationship:
            return None
        return relationship.get("data_flow")
    
    def get_relationship_performance(self, relationship_id: str) -> Optional[Dict[str, Any]]:
        """
        Get performance metrics for a relationship.
        
        Args:
            relationship_id: Relationship identifier
            
        Returns:
            Performance metrics dictionary or None if relationship not found
        """
        relationship = self.get_relationship(relationship_id)
        if not relationship:
            return None
        return relationship.get("performance")
    
    def get_relationship_dependencies(self, relationship_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get dependencies for a relationship.
        
        Args:
            relationship_id: Relationship identifier
            
        Returns:
            List of dependency dictionaries or None if relationship not found
        """
        relationship = self.get_relationship(relationship_id)
        if not relationship:
            return None
        return relationship.get("dependencies", [])
    
    def get_relationship_postman(self, relationship_id: str) -> Optional[Dict[str, Any]]:
        """
        Get Postman configuration for a relationship.
        
        Args:
            relationship_id: Relationship identifier
            
        Returns:
            Postman configuration dictionary or None if relationship not found
        """
        relationship = self.get_relationship(relationship_id)
        if not relationship:
            return None
        return relationship.get("postman_config")
    
