"""Schema service - DEPRECATED: Schema fetching from Lambda API removed."""

import logging
from typing import Optional, Dict, Any
from django.conf import settings
from apps.documentation.utils.schema_cache import SchemaCache

logger = logging.getLogger(__name__)


class SchemaService:
    """Service for schema management.
    
    NOTE: Lambda API schema fetching has been removed.
    This service now only provides cached schema access.
    """
    
    def __init__(self):
        """Initialize schema service."""
        self.cache = SchemaCache()
        self.schema_version = getattr(settings, 'LAMBDA_SCHEMA_VERSION', None)
    
    def get_pages_schema(self, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Get pages schema from Lambda API format endpoint.
        
        Args:
            use_cache: Whether to use cached schema if available
            
        Returns:
            Schema dictionary or None if fetch fails
        """
        # Check cache first
        if use_cache:
            cached = self.cache.get_schema('pages', self.schema_version)
            if cached and not self.cache.is_schema_stale('pages'):
                logger.debug("Using cached pages schema")
                return cached.get('schema')
        
        # Lambda API removed - return cached schema only
        if use_cache:
            cached = self.cache.get_schema('pages', self.schema_version)
            if cached:
                logger.warning("Using cached pages schema (Lambda API removed)")
                return cached.get('schema')
        
        logger.warning("No cached pages schema available (Lambda API removed)")
        return None
    
    def get_endpoints_schema(self, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Get endpoints schema - returns cached schema only (Lambda API removed)."""
        if use_cache:
            cached = self.cache.get_schema('endpoints', self.schema_version)
            if cached:
                logger.warning("Using cached endpoints schema (Lambda API removed)")
                return cached.get('schema')
        
        logger.warning("No cached endpoints schema available (Lambda API removed)")
        return None
    
    def get_relationships_schema(self, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Get relationships schema - returns cached schema only (Lambda API removed)."""
        if use_cache:
            cached = self.cache.get_schema('relationships', self.schema_version)
            if cached:
                logger.warning("Using cached relationships schema (Lambda API removed)")
                return cached.get('schema')
        
        logger.warning("No cached relationships schema available (Lambda API removed)")
        return None
    
    def get_postman_schema(self, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Get Postman schema - returns cached schema only (Lambda API removed)."""
        if use_cache:
            cached = self.cache.get_schema('postman', self.schema_version)
            if cached:
                logger.warning("Using cached postman schema (Lambda API removed)")
                return cached.get('schema')
        
        logger.warning("No cached postman schema available (Lambda API removed)")
        return None
    
    def get_schema(self, resource_type: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Get schema for a resource type.
        
        Args:
            resource_type: Type of resource ('pages', 'endpoints', 'relationships', 'postman')
            use_cache: Whether to use cached schema
            
        Returns:
            Schema dictionary or None
        """
        schema_methods = {
            'pages': self.get_pages_schema,
            'endpoints': self.get_endpoints_schema,
            'relationships': self.get_relationships_schema,
            'postman': self.get_postman_schema,
            'postman_config': self.get_postman_schema,
        }
        
        method = schema_methods.get(resource_type.lower())
        if method:
            return method(use_cache=use_cache)
        
        logger.warning(f"Unknown resource type for schema: {resource_type}")
        return None
    
    def refresh_schema(self, resource_type: str) -> Optional[Dict[str, Any]]:
        """Force refresh schema from Lambda API (bypass cache)."""
        logger.info(f"Refreshing schema for {resource_type}")
        return self.get_schema(resource_type, use_cache=False)
    
    def validate_against_schema(
        self,
        data: Dict[str, Any],
        resource_type: str,
        schema: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, list[str]]:
        """Validate data against Lambda API schema.
        
        Args:
            data: Data to validate
            resource_type: Type of resource
            schema: Optional schema (if not provided, will fetch)
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        if schema is None:
            schema = self.get_schema(resource_type)
        
        if not schema:
            return False, ["Schema not available for validation"]
        
        errors = []
        
        # Basic validation - check required fields from examples
        examples = schema.get('examples', {})
        if 'create' in examples:
            create_example = examples['create']
            # Check required fields (simplified validation)
            # Full validation would require JSON Schema validation library
        
        # Use Django validation models for detailed validation
        from apps.documentation.schemas.lambda_models import (
            validate_page_data,
            validate_endpoint_data,
            validate_relationship_data
        )
        
        try:
            if resource_type == 'pages':
                validate_page_data(data)
            elif resource_type == 'endpoints':
                validate_endpoint_data(data)
            elif resource_type == 'relationships':
                validate_relationship_data(data)
            else:
                errors.append(f"Unknown resource type: {resource_type}")
                return False, errors
        except Exception as e:
            errors.append(str(e))
            return False, errors
        
        return True, []
