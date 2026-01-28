"""Schema caching for Lambda API schemas."""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class SchemaCache:
    """Cache for Lambda API schemas with versioning."""
    
    CACHE_PREFIX = "lambda_schema:"
    CACHE_VERSION_KEY = "lambda_schema:version"
    DEFAULT_TTL = 3600  # 1 hour
    
    @staticmethod
    def get_cache_key(resource_type: str, version: Optional[str] = None) -> str:
        """Generate cache key for schema."""
        if version:
            return f"{SchemaCache.CACHE_PREFIX}{resource_type}:v{version}"
        return f"{SchemaCache.CACHE_PREFIX}{resource_type}:latest"
    
    @staticmethod
    def get_schema(resource_type: str, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get cached schema."""
        cache_key = SchemaCache.get_cache_key(resource_type, version)
        try:
            cached = cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for schema: {resource_type} (version: {version or 'latest'})")
                return cached
        except Exception as e:
            logger.warning(f"Cache get failed for schema {resource_type}: {e}")
        
        logger.debug(f"Cache miss for schema: {resource_type} (version: {version or 'latest'})")
        return None
    
    @staticmethod
    def set_schema(
        resource_type: str,
        schema: Dict[str, Any],
        version: Optional[str] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """Cache schema."""
        cache_key = SchemaCache.get_cache_key(resource_type, version)
        ttl = ttl or SchemaCache.DEFAULT_TTL
        
        try:
            # Add metadata
            schema_with_meta = {
                'schema': schema,
                'resource_type': resource_type,
                'version': version,
                'cached_at': datetime.now(timezone.utc).isoformat(),
                'ttl': ttl
            }
            
            cache.set(cache_key, schema_with_meta, ttl)
            logger.info(f"Cached schema: {resource_type} (version: {version or 'latest'}, TTL: {ttl}s)")
            
            # Also cache as latest if version specified
            if version:
                latest_key = SchemaCache.get_cache_key(resource_type)
                cache.set(latest_key, schema_with_meta, ttl)
            
            return True
        except Exception as e:
            logger.error(f"Failed to cache schema {resource_type}: {e}")
            return False
    
    @staticmethod
    def get_schema_version(resource_type: str) -> Optional[str]:
        """Get cached schema version."""
        cached = SchemaCache.get_schema(resource_type)
        if cached and 'version' in cached:
            return cached['version']
        return None
    
    @staticmethod
    def clear_schema(resource_type: str, version: Optional[str] = None) -> bool:
        """Clear cached schema."""
        cache_key = SchemaCache.get_cache_key(resource_type, version)
        try:
            cache.delete(cache_key)
            logger.info(f"Cleared schema cache: {resource_type} (version: {version or 'latest'})")
            return True
        except Exception as e:
            logger.warning(f"Failed to clear schema cache {resource_type}: {e}")
            return False
    
    @staticmethod
    def clear_all_schemas() -> int:
        """Clear all schema caches."""
        # Note: Django cache doesn't support pattern deletion easily
        # In production, use cache versioning or key tracking
        logger.warning("Clear all schemas not fully implemented - use cache versioning for production")
        return 0
    
    @staticmethod
    def is_schema_stale(resource_type: str, max_age_seconds: int = 3600) -> bool:
        """Check if cached schema is stale."""
        cached = SchemaCache.get_schema(resource_type)
        if not cached:
            return True
        
        if 'cached_at' not in cached:
            return True
        
        try:
            cached_at = datetime.fromisoformat(cached['cached_at'].replace('Z', '+00:00'))
            age = (datetime.now(timezone.utc) - cached_at).total_seconds()
            return age > max_age_seconds
        except Exception as e:
            logger.warning(f"Failed to check schema staleness: {e}")
            return True
