"""
Application-wide constants.
"""

# User roles and permissions
USER_ROLES = {
    'ADMIN': 'admin',
    'STAFF': 'staff',
    'USER': 'user',
}

# Theme preferences
THEME_PREFERENCES = {
    'LIGHT': 'light',
    'DARK': 'dark',
}

# API response status codes
API_STATUS = {
    'SUCCESS': 'success',
    'ERROR': 'error',
    'WARNING': 'warning',
}

# File upload limits (in bytes)
FILE_UPLOAD_LIMITS = {
    'AVATAR': 5 * 1024 * 1024,  # 5MB
    'DOCUMENT': 10 * 1024 * 1024,  # 10MB
    'IMAGE': 5 * 1024 * 1024,  # 5MB
}

# Pagination defaults
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Cache timeouts (in seconds)
CACHE_TIMEOUTS = {
    'SHORT': 300,  # 5 minutes
    'MEDIUM': 1800,  # 30 minutes
    'LONG': 3600,  # 1 hour
    'VERY_LONG': 86400,  # 24 hours
}
