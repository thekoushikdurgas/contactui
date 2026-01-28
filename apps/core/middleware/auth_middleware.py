"""Authentication middleware for appointment360 token-based auth."""

import logging
from django.contrib.auth import get_user_model
from django.conf import settings

from apps.core.clients.appointment360_client import Appointment360Client, Appointment360AuthError

logger = logging.getLogger(__name__)
User = get_user_model()


class Appointment360AuthMiddleware:
    """
    Middleware to authenticate users via appointment360 tokens from cookies.
    
    This middleware runs after AuthenticationMiddleware and sets request.user
    based on the access_token cookie if the user is not already authenticated.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.enabled = getattr(settings, 'GRAPHQL_ENABLED', False)
        self.auth_enabled = getattr(settings, 'GRAPHQL_AUTH_ENABLED', True)
    
    def __call__(self, request):
        # Only process if appointment360 auth is enabled
        if not (self.enabled and self.auth_enabled):
            return self.get_response(request)
        
        # Skip if user is already authenticated via session
        if hasattr(request, 'user') and request.user.is_authenticated:
            return self.get_response(request)
        
        # Get access token from cookie
        access_token = request.COOKIES.get('access_token')
        if not access_token:
            return self.get_response(request)
        
        # Try to authenticate using appointment360 backend
        try:
            from apps.core.auth.appointment360_backend import Appointment360Backend
            backend = Appointment360Backend()
            user = backend.authenticate(request, token=access_token)
            
            if user:
                request.user = user
                # Also set in session for compatibility
                from django.contrib.auth import login
                login(request, user)
            else:
                # Token might be expired, try to refresh
                refresh_token = request.COOKIES.get('refresh_token')
                if refresh_token:
                    try:
                        client = Appointment360Client()
                        auth_result = client.refresh_token(refresh_token)
                        
                        new_access_token = auth_result.get('access_token')
                        new_refresh_token = auth_result.get('refresh_token')
                        
                        if new_access_token and new_refresh_token:
                            # Authenticate with new token
                            user = backend.authenticate(request, token=new_access_token)
                            if user:
                                request.user = user
                                from django.contrib.auth import login
                                login(request, user)
                                
                                # Update cookies in response
                                response = self.get_response(request)
                                # Set cookies directly to avoid circular import
                                max_age = 86400 * 7
                                response.set_cookie(
                                    'access_token',
                                    new_access_token,
                                    max_age=max_age,
                                    httponly=True,
                                    secure=not settings.DEBUG,
                                    samesite='Lax',
                                    path='/'
                                )
                                response.set_cookie(
                                    'refresh_token',
                                    new_refresh_token,
                                    max_age=86400 * 30,
                                    httponly=True,
                                    secure=not settings.DEBUG,
                                    samesite='Lax',
                                    path='/'
                                )
                                return response
                    except Appointment360AuthError:
                        # Refresh failed, tokens are invalid
                        pass
                    except Exception as e:
                        logger.warning(f"Error refreshing token: {e}")
        
        except Exception as e:
            logger.debug(f"Token authentication middleware error: {e}")
        
        return self.get_response(request)
