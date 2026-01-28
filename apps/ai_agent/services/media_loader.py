"""Media file loader service for loading documentation from local JSON files."""

import logging
from typing import List, Dict, Any, Optional
from apps.documentation.repositories.local_json_storage import LocalJSONStorage

logger = logging.getLogger(__name__)


class MediaFileLoaderService:
    """Service for loading documentation from local media files."""
    
    def __init__(self, local_storage: Optional[LocalJSONStorage] = None):
        """Initialize media file loader.
        
        Args:
            local_storage: Optional LocalJSONStorage instance
        """
        self.local_storage = local_storage or LocalJSONStorage()
        logger.info("MediaFileLoaderService initialized")
    
    def load_all_pages(self) -> List[Dict[str, Any]]:
        """Load all pages from local JSON files.
        
        Returns:
            List of page data dictionaries
        """
        try:
            return self.local_storage.get_all_pages()
        except Exception as e:
            logger.error(f"Error loading all pages: {e}")
            return []
    
    def load_all_endpoints(self) -> List[Dict[str, Any]]:
        """Load all endpoints from local JSON files.
        
        Returns:
            List of endpoint data dictionaries
        """
        try:
            return self.local_storage.get_all_endpoints()
        except Exception as e:
            logger.error(f"Error loading all endpoints: {e}")
            return []
    
    def load_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Load a single page.
        
        Args:
            page_id: Page ID
            
        Returns:
            Page data dictionary, or None if not found
        """
        return self.local_storage.get_page(page_id)
    
    def load_endpoint(self, endpoint_id: str) -> Optional[Dict[str, Any]]:
        """Load a single endpoint.
        
        Args:
            endpoint_id: Endpoint ID
            
        Returns:
            Endpoint data dictionary, or None if not found
        """
        return self.local_storage.get_endpoint(endpoint_id)
    
    def load_relationships_by_page(self, page_path: str) -> Optional[Dict[str, Any]]:
        """Load relationships for a page.
        
        Args:
            page_path: Page route path
            
        Returns:
            Relationships data dictionary, or None if not found
        """
        return self.local_storage.get_relationships_by_page(page_path)
    
    def load_relationships_by_endpoint(
        self,
        endpoint_path: str,
        method: str = "QUERY"
    ) -> Optional[Dict[str, Any]]:
        """Load relationships for an endpoint.
        
        Args:
            endpoint_path: Endpoint path
            method: HTTP method
            
        Returns:
            Relationships data dictionary, or None if not found
        """
        return self.local_storage.get_relationships_by_endpoint(endpoint_path, method)
    
    def load_postman_collections(self) -> List[Dict[str, Any]]:
        """Load Postman collections from local files.
        
        Returns:
            List of Postman collection data
        """
        try:
            collections = []
            collection_files = self.local_storage.list_files('postman/collection', '*.json')
            
            for file_path in collection_files:
                collection_data = self.local_storage.read_json(file_path)
                if collection_data:
                    collections.append(collection_data)
            
            return collections
        except Exception as e:
            logger.error(f"Error loading Postman collections: {e}")
            return []
    
    def load_project_docs(self) -> List[Dict[str, Any]]:
        """Load project documentation files.
        
        Returns:
            List of project documentation data
        """
        try:
            docs = []
            doc_files = self.local_storage.list_files('project', '*.md')
            
            for file_path in doc_files:
                # Read markdown files as text
                full_path = self.local_storage._get_file_path(file_path)
                if full_path.exists():
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        docs.append({
                            'file': file_path,
                            'content': content
                        })
            
            return docs
        except Exception as e:
            logger.error(f"Error loading project docs: {e}")
            return []
