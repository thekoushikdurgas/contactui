"""Semantic search service for searching across local JSON files."""

import logging
from typing import List, Dict, Any, Optional
from apps.ai_agent.services.media_loader import MediaFileLoaderService

logger = logging.getLogger(__name__)


class SemanticSearchService:
    """Service for semantic search across documentation files."""
    
    def __init__(self, media_loader: MediaFileLoaderService):
        """Initialize semantic search service.
        
        Args:
            media_loader: MediaFileLoaderService instance
        """
        self.media_loader = media_loader
        logger.info("SemanticSearchService initialized")
    
    def _simple_search(
        self,
        query: str,
        items: List[Dict[str, Any]],
        search_fields: List[str],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Simple text-based search.
        
        Args:
            query: Search query
            items: List of items to search
            search_fields: List of field names to search in
            limit: Maximum number of results
            
        Returns:
            List of matching items with relevance scores
        """
        query_lower = query.lower()
        results = []
        
        for item in items:
            score = 0
            for field in search_fields:
                field_value = item.get(field, '')
                if isinstance(field_value, str):
                    if query_lower in field_value.lower():
                        # Higher score for exact matches and matches in important fields
                        if field in ['title', 'page_id', 'endpoint_id', 'endpoint_path']:
                            score += 10
                        else:
                            score += 1
                elif isinstance(field_value, dict):
                    # Search in nested dictionaries
                    for key, value in field_value.items():
                        if isinstance(value, str) and query_lower in value.lower():
                            score += 1
            
            if score > 0:
                results.append({
                    'data': item,
                    'score': score
                })
        
        # Sort by score and return top results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
    
    def search_pages(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search pages.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching pages with scores
        """
        pages = self.media_loader.load_all_pages()
        return self._simple_search(
            query,
            pages,
            ['page_id', 'title', 'metadata.route', 'metadata.purpose', 'metadata.description'],
            limit
        )
    
    def search_endpoints(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search endpoints.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching endpoints with scores
        """
        endpoints = self.media_loader.load_all_endpoints()
        return self._simple_search(
            query,
            endpoints,
            ['endpoint_id', 'endpoint_path', 'description', 'graphql_operation'],
            limit
        )
    
    def search_relationships(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search relationships.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching relationships with scores
        """
        # Load relationships index
        try:
            relationships_index = self.media_loader.local_storage.get_index('retations')
            relationships = relationships_index.get('relationships', [])
            
            return self._simple_search(
                query,
                relationships,
                ['endpoint_path', 'page_path'],
                limit
            )
        except Exception as e:
            logger.error(f"Error searching relationships: {e}")
            return []
    
    def search_postman(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search Postman collections.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching Postman items with scores
        """
        collections = self.media_loader.load_postman_collections()
        results = []
        
        for collection in collections:
            items = collection.get('item', [])
            for item in items:
                if self._matches_query(item, query):
                    results.append({
                        'data': item,
                        'score': 1
                    })
        
        return results[:limit]
    
    def _matches_query(self, item: Dict[str, Any], query: str) -> bool:
        """Check if item matches query.
        
        Args:
            item: Postman item
            query: Search query
            
        Returns:
            True if item matches query
        """
        query_lower = query.lower()
        name = item.get('name', '').lower()
        request = item.get('request', {})
        url = str(request.get('url', '')).lower()
        
        return query_lower in name or query_lower in url
    
    def search_project_docs(self, query: str, limit: int = 5) -> List[str]:
        """Search project documentation.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching documentation excerpts
        """
        docs = self.media_loader.load_project_docs()
        query_lower = query.lower()
        results = []
        
        for doc in docs:
            content = doc.get('content', '')
            if query_lower in content.lower():
                # Extract relevant excerpt
                index = content.lower().find(query_lower)
                start = max(0, index - 100)
                end = min(len(content), index + len(query) + 100)
                excerpt = content[start:end]
                results.append(excerpt)
                if len(results) >= limit:
                    break
        
        return results
