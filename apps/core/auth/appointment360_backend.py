"""Custom authentication backend for appointment360 token-based authentication."""

import logging
from typing import Optional
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.conf import settings

from apps.core.clients.appointment360_client import Appointment360Client

logger = logging.getLogger(__name__)
User = get_user_model()


class Appointment360Backend(BaseBackend):
    """Authentication backend that validates tokens via appointment360 API."""
    
    def authenticate(self, request, token: Optional[str] = None, **kwargs):
        """
        Authenticate user using appointment360 access token.
        
        Args:
            request: Django request object
            token: Access token (if provided directly)
            
        Returns:
            User object if authenticated, None otherwise
        """
        # Check if appointment360 is enabled
        if not getattr(settings, 'GRAPHQL_ENABLED', False):
            return None
        
        # Get token from request if not provided
        if not token:
            token = request.COOKIES.get('access_token') if request else None
        
        if not token:
            return None
        
        try:
            client = Appointment360Client()
            user_info = client.get_me(token)
            
            if not user_info:
                return None
            
            # Get or create Django user
            email = user_info.get('email')
            if not email:
                return None
            
            user, created = User.objects.get_or_create(
                username=email,
                defaults={
                    'email': email,
                    'first_name': user_info.get('name', '').split()[0] if user_info.get('name') else '',
                    'last_name': ' '.join(user_info.get('name', '').split()[1:]) if user_info.get('name') and len(user_info.get('name', '').split()) > 1 else '',
                }
            )
            
            if not created:
                # Update user info if exists
                if user_info.get('name'):
                    name_parts = user_info.get('name', '').split()
                    user.first_name = name_parts[0] if name_parts else ''
                    user.last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
                user.email = email
                user.save(update_fields=['first_name', 'last_name', 'email'])
            
            return user
            
        except Exception as e:
            logger.debug(f"Token authentication failed: {e}")
            return None
    
    def get_user(self, user_id):
        """Get user by ID."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
