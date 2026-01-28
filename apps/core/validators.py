"""File upload validators for Django."""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.conf import settings


def validate_file_size(file, max_size_mb: int = None):
    """
    Validate file size.
    
    Args:
        file: Django uploaded file object
        max_size_mb: Maximum file size in MB (defaults to FILE_UPLOAD_MAX_MEMORY_SIZE)
    
    Raises:
        ValidationError: If file size exceeds limit
    """
    if max_size_mb is None:
        # Use settings default (convert bytes to MB)
        max_size_bytes = getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', 10485760)  # 10MB default
        max_size_mb = max_size_bytes / (1024 * 1024)
    else:
        max_size_bytes = max_size_mb * 1024 * 1024
    
    if file.size > max_size_bytes:
        raise ValidationError(
            _('File size cannot exceed %(max_size)sMB. Current size: %(current_size)sMB.'),
            params={
                'max_size': max_size_mb,
                'current_size': round(file.size / (1024 * 1024), 2)
            }
        )


def validate_file_type(file, allowed_types: list = None):
    """
    Validate file type (MIME type).
    
    Args:
        file: Django uploaded file object
        allowed_types: List of allowed MIME types (defaults to common types)
    
    Raises:
        ValidationError: If file type is not allowed
    """
    if allowed_types is None:
        allowed_types = [
            'image/jpeg',
            'image/png',
            'image/gif',
            'image/webp',
            'application/pdf',
            'application/json',
            'text/plain',
            'text/csv',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        ]
    
    if file.content_type not in allowed_types:
        raise ValidationError(
            _('File type %(file_type)s is not allowed. Allowed types: %(allowed_types)s.'),
            params={
                'file_type': file.content_type,
                'allowed_types': ', '.join(allowed_types)
            }
        )


def validate_file_extension(file, allowed_extensions: list = None):
    """
    Validate file extension.
    
    Args:
        file: Django uploaded file object
        allowed_extensions: List of allowed extensions (e.g., ['.jpg', '.png', '.pdf'])
    
    Raises:
        ValidationError: If file extension is not allowed
    """
    if allowed_extensions is None:
        allowed_extensions = [
            '.jpg', '.jpeg', '.png', '.gif', '.webp',
            '.pdf',
            '.json',
            '.txt', '.csv',
            '.xls', '.xlsx',
        ]
    
    file_name = file.name.lower()
    file_extension = None
    
    # Extract extension
    if '.' in file_name:
        file_extension = '.' + file_name.split('.')[-1]
    
    if file_extension not in allowed_extensions:
        raise ValidationError(
            _('File extension %(extension)s is not allowed. Allowed extensions: %(allowed_extensions)s.'),
            params={
                'extension': file_extension or 'none',
                'allowed_extensions': ', '.join(allowed_extensions)
            }
        )
