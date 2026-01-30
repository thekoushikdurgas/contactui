"""Postman Service with multi-strategy pattern (Local → S3 → Lambda)."""

import logging
from typing import Optional, Dict, Any, List
from apps.documentation.services.base import DocumentationServiceBase
from apps.documentation.repositories.unified_storage import UnifiedStorage
from apps.documentation.repositories.postman_repository import PostmanRepository
from apps.documentation.repositories.local_json_storage import LocalJSONStorage
from apps.documentation.utils.retry import retry_on_network_error
from apps.documentation.utils.exceptions import DocumentationError

logger = logging.getLogger(__name__)


class PostmanService(DocumentationServiceBase):
    """Service for Postman operations with multi-strategy pattern using UnifiedStorage."""

    def __init__(
        self,
        unified_storage: Optional[UnifiedStorage] = None,
        repository: Optional[PostmanRepository] = None,
        local_storage: Optional[LocalJSONStorage] = None
    ):
        """Initialize Postman service.

        Args:
            unified_storage: Optional UnifiedStorage instance. If not provided, creates new one.
            repository: Optional PostmanRepository instance. If not provided, creates new one.
            local_storage: Optional LocalJSONStorage instance. If not provided, creates new one.
        """
        # Initialize base class with common patterns (Task 2.3.2)
        super().__init__(
            service_name="PostmanService",
            unified_storage=unified_storage,
            repository=repository or PostmanRepository(),
            resource_name="postman"
        )
        # Local storage for fallback reads
        if local_storage is None:
            from apps.documentation.services import get_shared_local_storage
            self.local_storage = get_shared_local_storage()
        else:
            self.local_storage = local_storage
    
    def list_configurations(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        state: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        List Postman configurations with multi-strategy pattern:
        1. Try Local JSON files (primary)
        2. Fallback to S3 (via repository)
        3. Fallback to Lambda API (last resort)
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            state: Optional state filter
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Dictionary with 'configurations' list and 'total' count
            
        Raises:
            DocumentationError: If retrieval fails after retries
        """
        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(
                'list_configurations',
                limit=limit,
                offset=offset,
                state=state
            )
            cached = self._get_from_cache(cache_key)
            if cached is not None:
                self.logger.debug("Cache hit for list_configurations")
                return cached
        
        # Try local JSON files first
        try:
            index_data = self.local_storage.get_index('postman')
            configurations_list = index_data.get('configurations', [])
            
            if configurations_list:
                # Apply state filter if provided
                filtered_configurations = configurations_list
                if state:
                    filtered_configurations = [
                        config for config in filtered_configurations
                        if config.get('state') == state
                    ]
                
                # Apply pagination
                total = len(filtered_configurations)
                if limit is not None:
                    paginated = filtered_configurations[offset:offset + limit]
                else:
                    paginated = filtered_configurations[offset:]
                
                logger.info(f"Loaded {len(paginated)} configurations from local files (total: {total})")
                return {
                    'configurations': paginated,
                    'total': total,
                    'source': 'local'
                }
        except Exception as e:
            logger.warning(f"Failed to load configurations from local files: {e}")
        
        # Try S3 via repository (scan configurations directory)
        try:
            # Note: repository doesn't have list_configurations, so we'll scan S3 directly
            from django.conf import settings
            from apps.documentation.services import get_shared_s3_storage
            s3_storage = get_shared_s3_storage()
            data_prefix = settings.S3_DATA_PREFIX
            configurations_prefix = f"{data_prefix}postman/configurations/"
            
            file_keys = s3_storage.list_json_files(configurations_prefix, max_keys=10000)
            json_files = [f for f in file_keys if not f.endswith('/index.json')]
            
            configurations = []
            for file_key in json_files:
                try:
                    config_data = s3_storage.read_json(file_key)
                    if not config_data:
                        continue
                    
                    # Apply state filter if provided
                    if state and config_data.get('state') != state:
                        continue
                    
                    config_id = config_data.get('config_id') or config_data.get('id') or file_key.split('/')[-1].replace('.json', '')
                    if "_id" not in config_data:
                        config_data["_id"] = config_id
                    
                    configurations.append(config_data)
                except Exception as e:
                    logger.warning(f"Failed to read configuration file {file_key}: {e}")
                    continue
            
            # Apply pagination
            total = len(configurations)
            if limit is not None:
                configurations = configurations[offset:offset + limit]
            else:
                configurations = configurations[offset:]
            
            if configurations:
                self.logger.info(f"Loaded {len(configurations)} configurations from S3")
                result = {
                    'configurations': configurations,
                    'total': total,
                    'source': 's3'
                }
                if use_cache:
                    cache_key = self._get_cache_key(
                        'list_configurations',
                        limit=limit,
                        offset=offset,
                        state=state
                    )
                    self._set_cache(cache_key, result, timeout=120, data_type='list')  # 2 minutes for list operations (Task 2.2.2)
                return result
        except Exception as e:
            self.logger.warning(f"Failed to load configurations from S3: {e}")
        
        # Return empty result if all strategies failed
        logger.warning("All strategies failed to load configurations")
        return {
            'configurations': [],
            'total': 0,
            'source': 'none'
        }
    
    def get_configuration(
        self,
        config_id: str,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get Postman configuration by ID.
        
        Args:
            config_id: Configuration identifier
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Configuration data dictionary or None if not found
            
        Raises:
            DocumentationError: If retrieval fails after retries
        """
        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key('get_configuration', config_id)
            cached = self._get_from_cache(cache_key)
            if cached is not None:
                self.logger.debug(f"Cache hit for configuration: {config_id}")
                return cached
        
        try:
            # Try local JSON files first (same strategy as list_configurations)
            try:
                from apps.documentation.services import get_shared_local_storage
                local_storage = get_shared_local_storage()
                # Configuration files are in postman/configurations/{config_id}.json
                config_path = f"postman/configurations/{config_id}.json"
                configuration = local_storage.read_json(config_path)
                if configuration:
                    config_id_from_file = configuration.get('config_id') or configuration.get('id') or config_id
                    if "_id" not in configuration:
                        configuration["_id"] = config_id_from_file
                    if use_cache:
                        cache_key = self._get_cache_key('get_configuration', config_id)
                        self._set_cache(cache_key, configuration, self.cache_timeout)
                    return configuration
            except Exception as e:
                self.logger.warning(f"Failed to load configuration from local files: {e}")
            
            # Fallback to repository (S3)
            @retry_on_network_error(max_retries=3, initial_delay=1.0)
            def _get_configuration_repository():
                # Try configurations directory first
                from django.conf import settings
                from apps.documentation.services import get_shared_s3_storage
                s3_storage = get_shared_s3_storage()
                data_prefix = settings.S3_DATA_PREFIX
                config_key = f"{data_prefix}postman/configurations/{config_id}.json"
                config_data = s3_storage.read_json(config_key)
                if config_data:
                    config_id_from_file = config_data.get('config_id') or config_data.get('id') or config_id
                    if "_id" not in config_data:
                        config_data["_id"] = config_id_from_file
                    return config_data
                # Fallback to old method (collections directory) for backward compatibility
                return self.repository.get_collection_by_id(config_id)
            
            configuration = _get_configuration_repository()
            if configuration:
                if use_cache:
                    cache_key = self._get_cache_key('get_configuration', config_id)
                    self._set_cache(cache_key, configuration, self.cache_timeout)
                return configuration
            
            return None
            
        except Exception as e:
            error_response = self._handle_error(
                e,
                context=f"Failed to get configuration {config_id}",
                record_monitoring=True
            )
            raise DocumentationError(
                f"Failed to retrieve configuration {config_id}: {error_response.get('error', str(e))}"
            ) from e
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get Postman configuration statistics from local/S3 data.
        
        Returns:
            Dictionary with statistics data
            
        Raises:
            DocumentationError: If retrieval fails after retries
        """
        try:
            result = self.list_configurations(limit=10000)
            configs = result.get('configurations', [])
            by_state = {}
            for c in configs:
                state = c.get('state') or 'draft'
                by_state[state] = by_state.get(state, 0) + 1
            return {
                'total_configurations': len(configs),
                'by_state': by_state,
                'updated_at': result.get('last_updated'),
            }
        except Exception as e:
            error_response = self._handle_error(
                e,
                context="Failed to get Postman statistics",
                record_monitoring=True
            )
            raise DocumentationError(
                f"Failed to get Postman statistics: {error_response.get('error', str(e))}"
            ) from e
    
    def get_configuration_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive Postman configuration statistics matching /api/v1/postman/statistics/.
        This is an alias/enhancement of get_statistics() for API parity.
        
        Returns:
            Dictionary with comprehensive statistics
        """
        return self.get_statistics()
    
    def get_collection(self, config_id: str) -> Optional[Dict[str, Any]]:
        """
        Get collection from a configuration.
        
        Args:
            config_id: Configuration identifier
            
        Returns:
            Collection data dictionary or None if not found
            
        Raises:
            DocumentationError: If retrieval fails after retries
        """
        try:
            # Get configuration
            config = self.get_configuration(config_id)
            if not config:
                return None
            
            # Check if configuration has 'collection' field directly (Lambda API format)
            if 'collection' in config:
                return config.get('collection')
            
            # Fallback: Load collection from default_collection file name
            # This handles the case where config has 'collections' array and 'default_collection' file name
            default_collection_file = config.get('default_collection')
            if default_collection_file:
                try:
                    from apps.documentation.services import get_shared_local_storage
                    local_storage = get_shared_local_storage()
                    # Collection files are in postman/collection/{file_name}
                    collection_path = f"postman/collection/{default_collection_file}"
                    collection = local_storage.read_json(collection_path)
                    if collection:
                        return collection
                except Exception as e:
                    self.logger.warning(f"Failed to load collection file {default_collection_file}: {e}")
                    # Try S3 fallback
                    try:
                        from django.conf import settings
                        from apps.documentation.services import get_shared_s3_storage
                        s3_storage = get_shared_s3_storage()
                        data_prefix = settings.S3_DATA_PREFIX
                        collection_key = f"{data_prefix}postman/collection/{default_collection_file}"
                        collection = s3_storage.read_json(collection_key)
                        if collection:
                            return collection
                    except Exception as e2:
                        self.logger.warning(f"Failed to load collection from S3: {e2}")
            
            return None
            
        except Exception as e:
            error_response = self._handle_error(
                e,
                context=f"Failed to get collection for configuration {config_id}",
                record_monitoring=True
            )
            raise DocumentationError(
                f"Failed to get collection: {error_response.get('error', str(e))}"
            ) from e
    
    def get_environments(self, config_id: str) -> List[Dict[str, Any]]:
        """
        List environments for a configuration.
        
        Args:
            config_id: Configuration identifier
            
        Returns:
            List of environment dictionaries
            
        Raises:
            DocumentationError: If retrieval fails after retries
        """
        try:
            # Get environments from configuration
            config = self.get_configuration(config_id)
            if config:
                return config.get('environments', [])
            return []
            
        except Exception as e:
            error_response = self._handle_error(
                e,
                context=f"Failed to get environments for configuration {config_id}",
                record_monitoring=True
            )
            raise DocumentationError(
                f"Failed to get environments: {error_response.get('error', str(e))}"
            ) from e
    
    def get_environment(self, config_id: str, env_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific environment from configuration.
        
        Args:
            config_id: Configuration identifier
            env_name: Environment name
            
        Returns:
            Environment data dictionary or None if not found
            
        Raises:
            DocumentationError: If retrieval fails after retries
        """
        try:
            # #region agent log
            import json
            with open('d:\\code\\ayan\\contact\\.cursor\\debug.log', 'a') as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "postman_service.py:403", "message": "get_environment entry", "data": {"config_id": config_id, "env_name": env_name}, "timestamp": __import__('time').time() * 1000}) + '\n')
            # #endregion
            
            config = self.get_configuration(config_id)
            
            # #region agent log
            with open('d:\\code\\ayan\\contact\\.cursor\\debug.log', 'a') as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "postman_service.py:407", "message": "config loaded", "data": {"config_exists": config is not None, "environments_type": type(config.get('environments', [])).__name__ if config else None, "environments_sample": str(config.get('environments', [])[:2]) if config else None}, "timestamp": __import__('time').time() * 1000}) + '\n')
            # #endregion
            
            if not config:
                return None
            
            environments = config.get('environments', [])
            
            # Handle case where environments might be a string or None
            if not isinstance(environments, list):
                if isinstance(environments, str):
                    # Single environment file name as string
                    environments = [environments]
                else:
                    # Invalid format, return None
                    self.logger.warning(f"Invalid environments format for config {config_id}: {type(environments)}")
                    return None
            
            # #region agent log
            with open('d:\\code\\ayan\\contact\\.cursor\\debug.log', 'a') as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "B", "location": "postman_service.py:412", "message": "environments array check", "data": {"environments_len": len(environments), "first_item_type": type(environments[0]).__name__ if environments else None, "first_item_value": str(environments[0]) if environments else None}, "timestamp": __import__('time').time() * 1000}) + '\n')
            # #endregion
            
            # Check if environments is array of file names (strings) or objects (dicts)
            if environments and len(environments) > 0 and isinstance(environments[0], str):
                # #region agent log
                with open('d:\\code\\ayan\\contact\\.cursor\\debug.log', 'a') as f:
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "C", "location": "postman_service.py:417", "message": "environments are file names, loading files", "data": {"env_name": env_name}, "timestamp": __import__('time').time() * 1000}) + '\n')
                # #endregion
                # Environments are file names, need to load them
                for env_file_name in environments:
                    try:
                        from apps.documentation.services import get_shared_local_storage
                        local_storage = get_shared_local_storage()
                        env_path = f"postman/environment/{env_file_name}"
                        env_data = local_storage.read_json(env_path)
                        
                        # #region agent log
                        with open('d:\\code\\ayan\\contact\\.cursor\\debug.log', 'a') as f:
                            f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "C", "location": "postman_service.py:425", "message": "loaded env file", "data": {"file_name": env_file_name, "env_data_name": env_data.get('name') if env_data else None, "matches": env_data.get('name') == env_name if env_data else False}, "timestamp": __import__('time').time() * 1000}) + '\n')
                        # #endregion
                        
                        if env_data and (env_data.get('name') == env_name or env_data.get('env_name') == env_name):
                            return env_data
                    except Exception as e:
                        self.logger.warning(f"Failed to load environment file {env_file_name}: {e}")
                        # Try S3 fallback
                        try:
                            from django.conf import settings
                            from apps.documentation.services import get_shared_s3_storage
                            s3_storage = get_shared_s3_storage()
                            data_prefix = settings.S3_DATA_PREFIX
                            env_key = f"{data_prefix}postman/environment/{env_file_name}"
                            env_data = s3_storage.read_json(env_key)
                            if env_data and (env_data.get('name') == env_name or env_data.get('env_name') == env_name):
                                return env_data
                        except Exception as e2:
                            self.logger.warning(f"Failed to load environment from S3: {e2}")
                return None
            else:
                # Environments are already objects, use existing logic
                # #region agent log
                with open('d:\\code\\ayan\\contact\\.cursor\\debug.log', 'a') as f:
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "D", "location": "postman_service.py:443", "message": "environments are objects, iterating", "data": {"env_name": env_name}, "timestamp": __import__('time').time() * 1000}) + '\n')
                # #endregion
                for env in environments:
                    # #region agent log
                    with open('d:\\code\\ayan\\contact\\.cursor\\debug.log', 'a') as f:
                        f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "D", "location": "postman_service.py:447", "message": "checking env", "data": {"env_type": type(env).__name__, "env_name_field": env.get('name') if isinstance(env, dict) else None, "matches": env.get('name') == env_name if isinstance(env, dict) else False}, "timestamp": __import__('time').time() * 1000}) + '\n')
                    # #endregion
                    if isinstance(env, dict) and (env.get('name') == env_name or env.get('env_name') == env_name):
                        return env
                return None
        except Exception as e:
            error_response = self._handle_error(
                e,
                context=f"Failed to get environment {env_name} for configuration {config_id}",
                record_monitoring=True
            )
            raise DocumentationError(
                f"Failed to get environment: {error_response.get('error', str(e))}"
            ) from e
    
    def get_endpoint_mappings(self, config_id: str) -> List[Dict[str, Any]]:
        """List endpoint mappings for a configuration."""
        config = self.get_configuration(config_id)
        if config:
            return config.get('endpoint_mappings', [])
        return []
    
    def get_endpoint_mapping(self, config_id: str, mapping_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific endpoint mapping."""
        mappings = self.get_endpoint_mappings(config_id)
        for mapping in mappings:
            if mapping.get('mapping_id') == mapping_id or mapping.get('id') == mapping_id:
                return mapping
        return None
    
    def get_test_suites(self, config_id: str) -> List[Dict[str, Any]]:
        """List test suites for a configuration (from configuration data)."""
        config = self.get_configuration(config_id)
        if config:
            return config.get('test_suites', [])
        return []
    
    def get_test_suite(self, config_id: str, suite_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific test suite."""
        suites = self.get_test_suites(config_id)
        for suite in suites:
            if suite.get('suite_id') == suite_id or suite.get('id') == suite_id:
                return suite
        return None
    
    def get_access_control(self, config_id: str) -> Optional[Dict[str, Any]]:
        """Get access control for a configuration."""
        config = self.get_configuration(config_id)
        if config:
            return config.get('access_control')
        return None
    
    def list_by_state(self, state: str) -> Dict[str, Any]:
        """List configurations by state."""
        result = self.list_configurations(state=state, limit=10000)
        return {
            'configurations': result.get('configurations', []),
            'total': result.get('total', 0)
        }
    
    def count_by_state(self, state: str) -> int:
        """Get count of configurations by state."""
        result = self.list_by_state(state)
        return result.get('total', 0)

    def create_configuration(self, config_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create Postman configuration.
        
        Args:
            config_data: Configuration data dictionary
            
        Returns:
            Created configuration data dictionary or None if creation failed
            
        Raises:
            ValueError: If configuration data is invalid
            DocumentationError: If creation fails after retries
        """
        # Validate required fields
        required_fields = ['config_id']
        is_valid, error_msg = self._validate_input(config_data, required_fields)
        if not is_valid:
            raise ValueError(error_msg)
        
        try:
            # Retry logic for external API calls
            @retry_on_network_error(max_retries=3, initial_delay=1.0)
            def _create_configuration_with_retry():
                # For now, support collection creation
                if 'collection' in config_data:
                    return self.repository.create_collection(config_data)
                return None
            
            result = _create_configuration_with_retry()
            
            # Invalidate cache after create
            if result:
                config_id = result.get('config_id') or config_data.get('config_id')
                # Clear specific configuration cache
                self.unified_storage.clear_cache('postman', config_id)
                # Clear all list_configurations cache (pattern-based)
                self.unified_storage.clear_cache('postman')
                self.logger.debug(f"Cleared cache for configuration {config_id} and all postman lists after create")
            
            return result
            
        except Exception as e:
            error_response = self._handle_error(
                e,
                context=f"Failed to create configuration {config_data.get('config_id', 'unknown')}",
                record_monitoring=True
            )
            raise DocumentationError(
                f"Failed to create configuration: {error_response.get('error', str(e))}"
            ) from e

    def update_configuration(self, config_id: str, config_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update Postman configuration.
        
        Args:
            config_id: Configuration identifier
            config_data: Configuration data dictionary (partial updates supported)
            
        Returns:
            Updated configuration data dictionary or None if update failed
            
        Raises:
            ValueError: If configuration not found
            DocumentationError: If update fails after retries
        """
        # Check if configuration exists
        existing = self.get_configuration(config_id, use_cache=False)
        if not existing:
            raise ValueError(f"Configuration not found: {config_id}")
        
        try:
            # Retry logic for external API calls
            @retry_on_network_error(max_retries=3, initial_delay=1.0)
            def _update_configuration_with_retry():
                # For now, support collection updates
                if self.repository.get_collection_by_id(config_id):
                    return self.repository.update_collection(config_id, config_data)
                return None
            
            result = _update_configuration_with_retry()
            
            # Invalidate cache after update
            if result:
                # Clear specific configuration cache
                self.unified_storage.clear_cache('postman', config_id)
                # Clear all list_configurations cache (pattern-based)
                self.unified_storage.clear_cache('postman')
                self.logger.debug(f"Cleared cache for configuration {config_id} and all postman lists after update")
            
            return result
            
        except Exception as e:
            error_response = self._handle_error(
                e,
                context=f"Failed to update configuration {config_id}",
                record_monitoring=True
            )
            raise DocumentationError(
                f"Failed to update configuration {config_id}: {error_response.get('error', str(e))}"
            ) from e

    def _delete_local_postman_file(self, config_id: str) -> None:
        """Remove local Postman configuration file and invalidate local index cache so list_configurations reflects delete."""
        try:
            from apps.documentation.services import get_shared_local_storage
            from django.core.cache import cache
            local_storage = get_shared_local_storage()
            local_storage.delete_file(f"postman/configurations/{config_id}.json")
            cache.delete("local_json_storage:index:postman")
        except Exception as e:
            self.logger.warning(f"Failed to delete local Postman config file or clear index cache for {config_id}: {e}")

    def delete_configuration(self, config_id: str) -> bool:
        """
        Delete Postman configuration.
        After successful deletion, removes local configuration file and invalidates local index cache.
        
        Args:
            config_id: Configuration identifier
            
        Returns:
            True if deletion was successful, False otherwise
            
        Raises:
            DocumentationError: If deletion fails after retries
        """
        try:
            # Retry logic for external API calls
            @retry_on_network_error(max_retries=3, initial_delay=1.0)
            def _delete_configuration_with_retry():
                # For now, support collection deletion
                return self.repository.delete_collection(config_id)
            
            success = _delete_configuration_with_retry()
            
            # Invalidate cache and local file after delete
            if success:
                self.unified_storage.clear_cache('postman', config_id)
                self.unified_storage.clear_cache('postman')
                self._delete_local_postman_file(config_id)
                self.logger.debug(f"Cleared cache for configuration {config_id} and all postman lists after delete")
            
            return success
            
        except Exception as e:
            error_response = self._handle_error(
                e,
                context=f"Failed to delete configuration {config_id}",
                record_monitoring=True
            )
            raise DocumentationError(
                f"Failed to delete configuration {config_id}: {error_response.get('error', str(e))}"
            ) from e
    
    def _clear_cache_for_configuration(self, config_id: str) -> None:
        """
        Clear cache entries for a specific configuration.
        
        Args:
            config_id: Configuration identifier
        """
        try:
            # Use UnifiedStorage's pattern-based cache clearing
            self.unified_storage.clear_cache('postman', config_id)
            self.unified_storage.clear_cache('postman')
        except Exception as e:
            self.logger.warning(f"Failed to clear cache for configuration {config_id}: {e}")

    def create_environment(self, environment_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create environment.
        
        Args:
            environment_data: Environment data dictionary
            
        Returns:
            Created environment data dictionary or None if creation failed
            
        Raises:
            ValueError: If environment data is invalid
            DocumentationError: If creation fails after retries
        """
        # Validate required fields
        required_fields = ['environment_id', 'config_id']
        is_valid, error_msg = self._validate_input(environment_data, required_fields)
        if not is_valid:
            raise ValueError(error_msg)
        
        try:
            # Retry logic for external API calls
            @retry_on_network_error(max_retries=3, initial_delay=1.0)
            def _create_environment_with_retry():
                return self.repository.create_environment(environment_data)
            
            return _create_environment_with_retry()
            
        except Exception as e:
            error_response = self._handle_error(
                e,
                context=f"Failed to create environment {environment_data.get('environment_id', 'unknown')}",
                record_monitoring=True
            )
            raise DocumentationError(
                f"Failed to create environment: {error_response.get('error', str(e))}"
            ) from e

    def update_environment(self, environment_id: str, environment_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update environment.
        
        Args:
            environment_id: Environment identifier
            environment_data: Environment data dictionary (partial updates supported)
            
        Returns:
            Updated environment data dictionary or None if update failed
            
        Raises:
            DocumentationError: If update fails after retries
        """
        try:
            # Retry logic for external API calls
            @retry_on_network_error(max_retries=3, initial_delay=1.0)
            def _update_environment_with_retry():
                return self.repository.update_environment(environment_id, environment_data)
            
            return _update_environment_with_retry()
            
        except Exception as e:
            error_response = self._handle_error(
                e,
                context=f"Failed to update environment {environment_id}",
                record_monitoring=True
            )
            raise DocumentationError(
                f"Failed to update environment {environment_id}: {error_response.get('error', str(e))}"
            ) from e

    def delete_environment(self, environment_id: str) -> bool:
        """
        Delete environment.
        
        Args:
            environment_id: Environment identifier
            
        Returns:
            True if deletion was successful, False otherwise
            
        Raises:
            DocumentationError: If deletion fails after retries
        """
        try:
            # Retry logic for external API calls
            @retry_on_network_error(max_retries=3, initial_delay=1.0)
            def _delete_environment_with_retry():
                return self.repository.delete_environment(environment_id)
            
            return _delete_environment_with_retry()
            
        except Exception as e:
            error_response = self._handle_error(
                e,
                context=f"Failed to delete environment {environment_id}",
                record_monitoring=True
            )
            raise DocumentationError(
                f"Failed to delete environment {environment_id}: {error_response.get('error', str(e))}"
            ) from e

    def get_environment_by_id(self, environment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get environment by ID.
        
        Args:
            environment_id: Environment identifier
            
        Returns:
            Environment data dictionary or None if not found
            
        Raises:
            DocumentationError: If retrieval fails after retries
        """
        try:
            @retry_on_network_error(max_retries=3, initial_delay=1.0)
            def _get_environment_by_id_with_retry():
                return self.repository.get_environment_by_id(environment_id)
            
            return _get_environment_by_id_with_retry()
            
        except Exception as e:
            error_response = self._handle_error(
                e,
                context=f"Failed to get environment {environment_id}",
                record_monitoring=True
            )
            raise DocumentationError(
                f"Failed to get environment {environment_id}: {error_response.get('error', str(e))}"
            ) from e
