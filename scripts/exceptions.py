"""Custom exception hierarchy for scripts."""


class ScriptError(Exception):
    """Base exception for all script errors."""
    
    def __init__(self, message: str, context: str = "", item: str = ""):
        """
        Initialize script error.
        
        Args:
            message: Error message
            context: Additional context (e.g., "file loading", "batch processing")
            item: Item identifier (e.g., filename, batch number)
        """
        self.message = message
        self.context = context
        self.item = item
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """Format error message with context and item."""
        parts = []
        if self.context:
            parts.append(f"[{self.context}]")
        if self.item:
            parts.append(f"Item: {self.item}")
        parts.append(self.message)
        return " ".join(parts)


class ValidationError(ScriptError):
    """Exception for validation errors."""
    
    def __init__(self, message: str, field: str = "", value: any = None, context: str = "", item: str = ""):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field: Field name that failed validation
            value: Value that failed validation
            context: Additional context
            item: Item identifier
        """
        self.field = field
        self.value = value
        super().__init__(message, context, item)


class FileError(ScriptError):
    """Exception for file-related errors."""
    
    def __init__(self, message: str, file_path: str = "", context: str = ""):
        """
        Initialize file error.
        
        Args:
            message: Error message
            file_path: Path to the file
            context: Additional context
        """
        self.file_path = file_path
        super().__init__(message, context, file_path)


class UploadError(ScriptError):
    """Exception for upload errors."""
    
    def __init__(self, message: str, batch_num: int = 0, item_count: int = 0, context: str = ""):
        """
        Initialize upload error.
        
        Args:
            message: Error message
            batch_num: Batch number (if applicable)
            item_count: Number of items in batch
            context: Additional context
        """
        self.batch_num = batch_num
        self.item_count = item_count
        item = f"batch {batch_num}" if batch_num > 0 else ""
        super().__init__(message, context, item)


class ConfigurationError(ScriptError):
    """Exception for configuration errors."""
    
    def __init__(self, message: str, setting: str = "", context: str = ""):
        """
        Initialize configuration error.
        
        Args:
            message: Error message
            setting: Setting name that caused the error
            context: Additional context
        """
        self.setting = setting
        super().__init__(message, context, setting)


class APIError(ScriptError):
    """Exception for API-related errors."""
    
    def __init__(self, message: str, endpoint: str = "", status_code: int = 0, context: str = ""):
        """
        Initialize API error.
        
        Args:
            message: Error message
            endpoint: API endpoint that failed
            status_code: HTTP status code (if applicable)
            context: Additional context
        """
        self.endpoint = endpoint
        self.status_code = status_code
        item = f"{endpoint} (status: {status_code})" if status_code > 0 else endpoint
        super().__init__(message, context, item)
