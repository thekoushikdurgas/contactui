"""Centralized configuration management for scripts."""

import os
from typing import Any, Dict, Optional

from scripts.utils.context import get_settings, is_django_context, get_logger

logger = get_logger(__name__)


class ScriptConfig:
    """Centralized configuration for scripts."""
    
    def __init__(self):
        """Initialize configuration from settings."""
        self.settings = get_settings()
        self._config_cache: Dict[str, Any] = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        # Check cache first
        if key in self._config_cache:
            return self._config_cache[key]
        
        # Try to get from settings
        value = default
        if hasattr(self.settings, "get"):
            value = self.settings.get(key, default)
        elif hasattr(self.settings, key):
            value = getattr(self.settings, key, default)
        
        # Cache the value
        self._config_cache[key] = value
        return value
    
    def get_s3_bucket(self) -> str:
        """Get S3 bucket name."""
        return self.get("S3_BUCKET_NAME", os.getenv("S3_BUCKET_NAME", "contact360docs"))
    
    def get_s3_data_prefix(self) -> str:
        """Get S3 data prefix."""
        return self.get("S3_DATA_PREFIX", os.getenv("S3_DATA_PREFIX", "data/"))
    
    def get_s3_documentation_prefix(self) -> str:
        """Get S3 documentation prefix."""
        return self.get(
            "S3_DOCUMENTATION_PREFIX",
            os.getenv("S3_DOCUMENTATION_PREFIX", "documentation/"),
        )
    
    def get_aws_region(self) -> str:
        """Get AWS region."""
        return self.get("AWS_REGION", os.getenv("AWS_REGION", "us-east-1"))
    
    def get_aws_access_key_id(self) -> Optional[str]:
        """Get AWS access key ID."""
        return self.get("AWS_ACCESS_KEY_ID", os.getenv("AWS_ACCESS_KEY_ID"))
    
    def get_aws_secret_access_key(self) -> Optional[str]:
        """Get AWS secret access key."""
        return self.get("AWS_SECRET_ACCESS_KEY", os.getenv("AWS_SECRET_ACCESS_KEY"))
    
    def use_local_json_files(self) -> bool:
        """Check if local JSON files should be used."""
        value = self.get("USE_LOCAL_JSON_FILES", os.getenv("USE_LOCAL_JSON_FILES", "False"))
        if isinstance(value, bool):
            return value
        return str(value).lower() == "true"
    
    def get_batch_size(self) -> int:
        """Get default batch size for operations."""
        return int(self.get("BATCH_SIZE", os.getenv("BATCH_SIZE", "50")))
    
    def get_max_retries(self) -> int:
        """Get maximum number of retries."""
        return int(self.get("MAX_RETRIES", os.getenv("MAX_RETRIES", "3")))
    
    def get_retry_delay(self) -> float:
        """Get retry delay in seconds."""
        return float(self.get("RETRY_DELAY", os.getenv("RETRY_DELAY", "1.0")))
    
    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate configuration.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required S3 settings
        bucket = self.get_s3_bucket()
        if not bucket:
            errors.append("S3_BUCKET_NAME is required")
        
        # Check AWS credentials (optional, may use IAM role)
        access_key = self.get_aws_access_key_id()
        secret_key = self.get_aws_secret_access_key()
        
        if access_key and not secret_key:
            errors.append("AWS_SECRET_ACCESS_KEY is required when AWS_ACCESS_KEY_ID is set")
        if secret_key and not access_key:
            errors.append("AWS_ACCESS_KEY_ID is required when AWS_SECRET_ACCESS_KEY is set")
        
        return len(errors) == 0, errors


# Global config instance
_config_instance: Optional[ScriptConfig] = None


def get_config() -> ScriptConfig:
    """
    Get global configuration instance.
    
    Returns:
        ScriptConfig instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ScriptConfig()
    return _config_instance
