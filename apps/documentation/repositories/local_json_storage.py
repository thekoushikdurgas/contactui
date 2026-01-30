"""Local JSON file storage client for reading from media/ directory."""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)
INDEX_CACHE_TTL = 300  # 5 minutes


class LocalJSONStorage:
    """Client for reading JSON files from local media/ directory."""

    def __init__(self, media_root: Optional[Path] = None):
        """Initialize local JSON storage client.
        
        Args:
            media_root: Optional path to media directory. Defaults to BASE_DIR / 'media'.
        """
        if media_root:
            self.media_root = Path(media_root)
        else:
            # Use BASE_DIR / 'media' for local JSON files
            self.media_root = Path(settings.BASE_DIR) / 'media'
        
        # Ensure media directory exists
        self.media_root.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"LocalJSONStorage initialized with media_root: {self.media_root}")

    def _get_file_path(self, *path_parts: str) -> Path:
        """Get full file path within media directory.
        
        Args:
            *path_parts: Path components relative to media_root
            
        Returns:
            Full Path object
        """
        return self.media_root / Path(*path_parts)

    def read_json(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Read and parse JSON file from local media directory.
        
        Args:
            file_path: Relative path from media/ directory (e.g., 'pages/index.json')
            
        Returns:
            Parsed JSON data as dictionary, or None if file doesn't exist
        """
        full_path = self._get_file_path(file_path)
        
        if not full_path.exists():
            logger.debug(f"JSON file not found: {full_path}")
            return None
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from {full_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading JSON file {full_path}: {e}")
            return None

    def delete_file(self, relative_path: str) -> bool:
        """Delete a JSON file from the local media directory if it exists.

        Args:
            relative_path: Relative path from media/ (e.g., 'pages/page_id.json')

        Returns:
            True if the file was deleted or did not exist, False on error.
        """
        full_path = self._get_file_path(relative_path)
        try:
            if full_path.exists() and full_path.is_file():
                full_path.unlink()
                logger.debug(f"Deleted local file: {full_path}")
            return True
        except OSError as e:
            logger.warning(f"Failed to delete local file {full_path}: {e}")
            return False

    def list_files(self, directory: str, pattern: str = "*.json") -> List[str]:
        """List JSON files in a directory.
        
        Args:
            directory: Relative directory path from media/ (e.g., 'pages')
            pattern: File pattern to match (default: '*.json')
            
        Returns:
            List of relative file paths
        """
        dir_path = self._get_file_path(directory)
        
        if not dir_path.exists() or not dir_path.is_dir():
            logger.debug(f"Directory not found: {dir_path}")
            return []
        
        try:
            files = []
            for file_path in dir_path.glob(pattern):
                # Return relative path from media/
                relative_path = file_path.relative_to(self.media_root)
                files.append(str(relative_path).replace('\\', '/'))
            return sorted(files)
        except Exception as e:
            logger.error(f"Error listing files in {dir_path}: {e}")
            return []

    def get_index(self, resource_type: str) -> Dict[str, Any]:
        """Read index.json file for a resource type. Cached 5 min."""
        cache_key = f"local_json_storage:index:{resource_type}"
        try:
            cached = cache.get(cache_key)
            if cached is not None:
                return cached
        except Exception as e:
            logger.warning(f"Cache get failed for key {cache_key}: {e}")

        # Try primary path first
        index_path = f"{resource_type}/index.json"
        index_data = self.read_json(index_path)
        
        # If not found and resource_type is 'relationships', try 'relationship' directory (legacy naming)
        if not index_data and resource_type == 'relationships':
            index_path = "relationship/index.json"
            index_data = self.read_json(index_path)
        
        if not index_data:
            result = {
                'version': '2.0',
                'last_updated': None,
                'total': 0,
                resource_type: [],
                'indexes': {},
                'statistics': {}
            }
        else:
            result = index_data

        try:
            cache.set(cache_key, result, INDEX_CACHE_TTL)
        except Exception as e:
            logger.warning(f"Cache set failed for key {cache_key}: {e}")
        return result

    def get_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get a single page JSON file.
        
        Args:
            page_id: Page ID (e.g., 'dashboard_page')
            
        Returns:
            Page data dictionary, or None if not found
        """
        # Try with .json extension
        file_path = f"pages/{page_id}.json"
        page_data = self.read_json(file_path)
        
        if page_data:
            return page_data
        
        # Try without .json extension if page_id already includes it
        if not page_id.endswith('.json'):
            file_path = f"pages/{page_id}"
            page_data = self.read_json(file_path)
            if page_data:
                return page_data
        
        return None

    def get_endpoint(self, endpoint_id: str) -> Optional[Dict[str, Any]]:
        """Get a single endpoint JSON file.
        
        Args:
            endpoint_id: Endpoint ID (e.g., 'get_company_graphql')
            
        Returns:
            Endpoint data dictionary, or None if not found
        """
        # Try with .json extension
        file_path = f"endpoints/{endpoint_id}.json"
        endpoint_data = self.read_json(file_path)
        
        if endpoint_data:
            return endpoint_data
        
        # Try without .json extension if endpoint_id already includes it
        if not endpoint_id.endswith('.json'):
            file_path = f"endpoints/{endpoint_id}"
            return self.read_json(file_path)
        
        return None

    def get_relationship(self, relationship_id: str) -> Optional[Dict[str, Any]]:
        """Get relationship by ID.

        Args:
            relationship_id: Relationship ID

        Returns:
            Relationship data dictionary, or None if not found
        """
        # Try with .json extension
        file_path = f"relationships/{relationship_id}.json"
        relationship_data = self.read_json(file_path)

        if relationship_data:
            return relationship_data

        # Try without .json extension if relationship_id already includes it
        if not relationship_id.endswith('.json'):
            file_path = f"relationships/{relationship_id}"
            return self.read_json(file_path)

        return None

    def get_relationships_by_page(self, page_path: str) -> Optional[Dict[str, Any]]:
        """Get relationships for a specific page.
        
        Args:
            page_path: Page route path (e.g., '/dashboard' or 'dashboard')
            
        Returns:
            Relationships data dictionary, or None if not found
        """
        # Normalize page_path: remove leading slash, replace slashes with underscores
        normalized = page_path.lstrip('/').replace('/', '_')
        
        # Try with .json extension (check both 'relationships' and legacy 'relationship')
        for dir_name in ["relationships", "relationship"]:
            file_path = f"{dir_name}/by-page/{normalized}.json"
            relationships = self.read_json(file_path)
            if relationships:
                return relationships
        
        # Try without .json extension
        if not normalized.endswith('.json'):
            for dir_name in ["relationships", "relationship"]:
                file_path = f"{dir_name}/by-page/{normalized}"
                relationships = self.read_json(file_path)
                if relationships:
                    return relationships
        
        return None

    def get_relationships_by_endpoint(
        self, 
        endpoint_path: str, 
        method: str = "QUERY"
    ) -> Optional[Dict[str, Any]]:
        """Get relationships for a specific endpoint.
        
        Args:
            endpoint_path: Endpoint path (e.g., 'graphql/GetCompany')
            method: HTTP method ('QUERY' or 'MUTATION')
            
        Returns:
            Relationships data dictionary, or None if not found
        """
        # Normalize endpoint_path: replace slashes with underscores
        normalized = endpoint_path.replace('/', '_')
        filename = f"{normalized}_{method}.json"
        
        # Try with .json extension (check both 'relationships' and legacy 'relationship')
        for dir_name in ["relationships", "relationship"]:
            file_path = f"{dir_name}/by-endpoint/{filename}"
            relationships = self.read_json(file_path)
            if relationships:
                return relationships
        
        # Try without .json extension
        if not filename.endswith('.json'):
            for dir_name in ["relationships", "relationship"]:
                file_path = f"{dir_name}/by-endpoint/{filename}"
                relationships = self.read_json(file_path)
                if relationships:
                    return relationships
        
        return None

    def get_all_pages(self) -> List[Dict[str, Any]]:
        """Get all page JSON files.
        
        Optimized with parallel file reading for better performance.
        Expected improvement: 5-10x faster for multiple files.
        
        Returns:
            List of page data dictionaries
        """
        page_files = self.list_files('pages', '*.json')
        
        # Filter out index.json files
        page_files = [fp for fp in page_files if 'index.json' not in fp]
        
        if not page_files:
            return []
        
        pages = []
        
        # Use parallel processing for file reads (Task 1.3.1)
        # Batch size of 10 concurrent reads to avoid overwhelming the system
        max_workers = min(10, len(page_files))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all file read tasks
            future_to_file = {
                executor.submit(self.read_json, file_path): file_path
                for file_path in page_files
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    page_data = future.result(timeout=5)  # 5 second timeout per file
                    if page_data:
                        pages.append(page_data)
                except Exception as e:
                    logger.warning(f"Error reading page file {file_path}: {e}")
                    continue
        
        return pages

    def get_all_endpoints(self) -> List[Dict[str, Any]]:
        """Get all endpoint JSON files.
        
        Optimized with parallel file reading for better performance.
        Expected improvement: 5-10x faster for multiple files.
        
        Returns:
            List of endpoint data dictionaries
        """
        endpoint_files = self.list_files('endpoints', '*.json')
        
        # Filter out index.json files
        endpoint_files = [fp for fp in endpoint_files if 'index.json' not in fp]
        
        if not endpoint_files:
            return []
        
        endpoints = []
        
        # Use parallel processing for file reads (Task 1.3.1)
        # Batch size of 10 concurrent reads to avoid overwhelming the system
        max_workers = min(10, len(endpoint_files))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all file read tasks
            future_to_file = {
                executor.submit(self.read_json, file_path): file_path
                for file_path in endpoint_files
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    endpoint_data = future.result(timeout=5)  # 5 second timeout per file
                    if endpoint_data:
                        endpoints.append(endpoint_data)
                except Exception as e:
                    logger.warning(f"Error reading endpoint file {file_path}: {e}")
                    continue
        
        return endpoints

    def file_exists(self, file_path: str) -> bool:
        """Check if a JSON file exists.
        
        Args:
            file_path: Relative path from media/ directory
            
        Returns:
            True if file exists, False otherwise
        """
        full_path = self._get_file_path(file_path)
        return full_path.exists() and full_path.is_file()

    def write_json(
        self,
        file_path: str,
        data: Dict[str, Any],
        create_dirs: bool = True
    ) -> bool:
        """Write JSON data to local file (optional, for editing).
        
        Args:
            file_path: Relative path from media/ directory
            data: Data dictionary to write as JSON
            create_dirs: Whether to create parent directories if they don't exist
            
        Returns:
            True if successful, False otherwise
        """
        full_path = self._get_file_path(file_path)
        
        if create_dirs:
            full_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Wrote JSON to local file: {full_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to write JSON to {full_path}: {e}")
            return False
