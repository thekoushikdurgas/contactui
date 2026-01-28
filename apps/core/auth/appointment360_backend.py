"""Custom authentication backend for appointment360 token-based authentication.

NOTE: This backend is deprecated. We no longer use Django User model.
Authentication is handled via Appointment360 GraphQL API tokens only.
This backend is kept for backward compatibility but returns None.
"""

import logging
from typing import Optional
from django.contrib.auth.backends import BaseBackend
from django.conf import settings

from apps.core.clients.appointment360_client import Appointment360Client

logger = logging.getLogger(__name__)


class Appointment360Backend(BaseBackend):
    """
    Authentication backend that validates tokens via appointment360 API.
    
    DEPRECATED: This backend no longer creates Django User objects.
    Authentication is handled via tokens only through middleware and decorators.
    """
    
    def authenticate(self, request, token: Optional[str] = None, **kwargs):
        """
        Authenticate user using appointment360 access token.
        
        DEPRECATED: Returns None. Use middleware and decorators instead.
        
        Args:
            request: Django request object
            token: Access token (if provided directly)
            
        Returns:
            None (no Django User model used)
        """
        # This backend is deprecated - authentication handled via middleware
        logger.debug("Appointment360Backend.authenticate() called but deprecated - using token-based auth only")
        return None
    
    def get_user(self, user_id):
        """Get user by ID."""
        # This backend is deprecated - no Django User model
        return None
