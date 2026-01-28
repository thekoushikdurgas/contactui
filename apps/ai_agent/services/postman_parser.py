"""Postman collection parser service."""

import logging
from typing import List, Dict, Any, Optional
from apps.ai_agent.services.media_loader import MediaFileLoaderService

logger = logging.getLogger(__name__)


class PostmanCollectionParser:
    """Service for parsing Postman collections."""
    
    def __init__(self, media_loader: MediaFileLoaderService):
        """Initialize Postman parser.
        
        Args:
            media_loader: MediaFileLoaderService instance
        """
        self.media_loader = media_loader
        logger.info("PostmanCollectionParser initialized")
    
    def parse_collections(self) -> List[Dict[str, Any]]:
        """Parse all Postman collections.
        
        Returns:
            List of parsed collection data
        """
        collections = self.media_loader.load_postman_collections()
        parsed = []
        
        for collection in collections:
            parsed_collection = self.parse_collection(collection)
            if parsed_collection:
                parsed.append(parsed_collection)
        
        return parsed
    
    def parse_collection(self, collection: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a single Postman collection.
        
        Args:
            collection: Postman collection JSON
            
        Returns:
            Parsed collection data, or None if invalid
        """
        try:
            info = collection.get('info', {})
            items = collection.get('item', [])
            
            parsed = {
                'name': info.get('name', 'Unknown'),
                'description': info.get('description', ''),
                'schema': info.get('schema', ''),
                'requests': []
            }
            
            # Parse items recursively
            for item in items:
                requests = self._parse_item(item)
                parsed['requests'].extend(requests)
            
            return parsed
        except Exception as e:
            logger.error(f"Error parsing Postman collection: {e}")
            return None
    
    def _parse_item(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse a Postman item (request or folder).
        
        Args:
            item: Postman item
            
        Returns:
            List of parsed requests
        """
        requests = []
        
        # Check if this is a request
        if 'request' in item:
            request_data = {
                'name': item.get('name', ''),
                'method': item.get('request', {}).get('method', 'GET'),
                'url': self._parse_url(item.get('request', {}).get('url', {})),
                'headers': item.get('request', {}).get('header', []),
                'body': item.get('request', {}).get('body', {}),
                'description': item.get('request', {}).get('description', '')
            }
            requests.append(request_data)
        
        # Check if this is a folder (has items)
        if 'item' in item:
            for sub_item in item.get('item', []):
                requests.extend(self._parse_item(sub_item))
        
        return requests
    
    def _parse_url(self, url_data: Any) -> str:
        """Parse Postman URL object.
        
        Args:
            url_data: URL data (string or object)
            
        Returns:
            URL string
        """
        if isinstance(url_data, str):
            return url_data
        
        if isinstance(url_data, dict):
            protocol = url_data.get('protocol', '')
            host = url_data.get('host', [])
            path = url_data.get('path', [])
            
            host_str = '.'.join(host) if host else ''
            path_str = '/'.join(path) if path else ''
            
            url = f"{protocol}://{host_str}/{path_str}" if protocol and host_str else path_str
            return url.lstrip('/')
        
        return str(url_data)
    
    def get_endpoint_examples(self, endpoint_path: str) -> List[Dict[str, Any]]:
        """Get Postman examples for a specific endpoint.
        
        Args:
            endpoint_path: Endpoint path to search for
            
        Returns:
            List of matching Postman requests
        """
        collections = self.media_loader.load_postman_collections()
        examples = []
        
        for collection in collections:
            items = collection.get('item', [])
            for item in items:
                requests = self._parse_item(item)
                for request in requests:
                    url = request.get('url', '')
                    if endpoint_path.lower() in url.lower():
                        examples.append(request)
        
        return examples
