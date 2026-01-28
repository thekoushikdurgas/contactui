"""Configuration management and feature flags."""

from django.conf import settings


class Config:
    """Configuration class for feature flags and settings."""
    
    @staticmethod
    def is_openai_enabled() -> bool:
        """Check if OpenAI is enabled.
        
        Returns:
            True if OpenAI API key is configured
        """
        return bool(getattr(settings, 'OPENAI_API_KEY', ''))
    
    @staticmethod
    def is_gemini_enabled() -> bool:
        """Check if Gemini AI is enabled.
        
        Returns:
            True if Gemini API key is configured
        """
        return bool(getattr(settings, 'GEMINI_API_KEY', ''))
    
    @staticmethod
    def is_graphql_enabled() -> bool:
        """Check if GraphQL is enabled.
        
        Returns:
            True if GraphQL API key is configured
        """
        return bool(getattr(settings, 'GRAPHQL_ENABLED', False))
    
    @staticmethod
    def is_lambda_enabled() -> bool:
        """Check if Lambda API is enabled.
        
        Returns:
            True if Lambda API key is configured
        """
        return bool(getattr(settings, 'LAMBDA_DOCUMENTATION_API_KEY', ''))
    
    @staticmethod
    def use_local_json_files() -> bool:
        """Check if local JSON files should be used.
        
        Returns:
            True if local JSON files should be used as primary source
        """
        return getattr(settings, 'USE_LOCAL_JSON_FILES', True)
    
    @staticmethod
    def is_s3_enabled() -> bool:
        """Check if S3 is enabled.
        
        Returns:
            True if S3 credentials are configured
        """
        return bool(
            getattr(settings, 'AWS_ACCESS_KEY_ID', '') and
            getattr(settings, 'AWS_SECRET_ACCESS_KEY', '')
        )
    
    @staticmethod
    def get_storage_strategy() -> str:
        """Get the storage strategy being used.
        
        Returns:
            Storage strategy string ('local', 's3', 'graphql', 'lambda', or 'mixed')
        """
        if Config.use_local_json_files():
            if Config.is_s3_enabled() or Config.is_graphql_enabled() or Config.is_lambda_enabled():
                return 'mixed'
            return 'local'
        elif Config.is_graphql_enabled():
            return 'graphql'
        elif Config.is_lambda_enabled():
            return 'lambda'
        elif Config.is_s3_enabled():
            return 's3'
        else:
            return 'none'
