"""Appointment360 GraphQL authentication client."""

import logging
from typing import Optional, Dict, Any
from django.conf import settings
from apps.core.services.graphql_client import GraphQLClient, GraphQLError

logger = logging.getLogger(__name__)


class Appointment360AuthError(Exception):
    """Exception for appointment360 authentication errors."""
    pass


class Appointment360Client:
    """Client for appointment360 GraphQL authentication API."""
    
    def __init__(self, graphql_client: Optional[GraphQLClient] = None, request=None):
        """
        Initialize appointment360 client.
        
        Args:
            graphql_client: Optional GraphQLClient instance. If not provided, creates new one.
            request: Django request object to extract access token from (optional)
        """
        self.graphql_client = graphql_client or GraphQLClient(request=request)
        self.enabled = getattr(settings, 'GRAPHQL_ENABLED', False)
        
        if not self.enabled:
            logger.warning("Appointment360 GraphQL is not enabled (GRAPHQL_ENABLED=False or APPOINTMENT360_GRAPHQL_URL not configured)")
    
    def login(self, email: str, password: str, geolocation: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Authenticate user with email and password.
        
        Args:
            email: User email
            password: User password
            geolocation: Optional geolocation data dictionary (ip, country, city, etc.)
            
        Returns:
            Dictionary with 'access_token', 'refresh_token', and 'user' (uuid, email, name)
            
        Raises:
            Appointment360AuthError: If authentication fails
        """
        if not self.enabled:
            raise Appointment360AuthError("Appointment360 GraphQL is not enabled")
        
        mutation = """
        mutation Login($input: LoginInput!) {
            auth {
                login(input: $input) {
                    accessToken
                    refreshToken
                    user {
                        uuid
                        email
                        name
                    }
                }
            }
        }
        """
        
        variables = {
            'input': {
                'email': email,
                'password': password,
            }
        }
        
        # Add geolocation if provided
        if geolocation:
            variables['input']['geolocation'] = geolocation
        
        try:
            result = self.graphql_client.execute_mutation(mutation, variables)
            if not result or 'auth' not in result or 'login' not in result['auth']:
                raise Appointment360AuthError("Invalid response from appointment360 API")
            
            login_data = result['auth']['login']
            
            # Normalize field names (GraphQL returns camelCase, we use snake_case)
            return {
                'access_token': login_data.get('accessToken'),
                'refresh_token': login_data.get('refreshToken'),
                'user': {
                    'uuid': login_data.get('user', {}).get('uuid'),
                    'email': login_data.get('user', {}).get('email'),
                    'name': login_data.get('user', {}).get('name'),
                }
            }
        except GraphQLError as e:
            logger.error(f"GraphQL error during login: {e}")
            raise Appointment360AuthError(f"Authentication failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during login: {e}", exc_info=True)
            raise Appointment360AuthError(f"Authentication failed: {str(e)}")
    
    def register(self, name: str, email: str, password: str, geolocation: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Register a new user.
        
        Args:
            name: User name
            email: User email
            password: User password
            geolocation: Optional geolocation data dictionary (ip, country, city, etc.)
            
        Returns:
            Dictionary with 'access_token', 'refresh_token', and 'user' (uuid, email, name)
            
        Raises:
            Appointment360AuthError: If registration fails
        """
        if not self.enabled:
            raise Appointment360AuthError("Appointment360 GraphQL is not enabled")
        
        mutation = """
        mutation Register($input: RegisterInput!) {
            auth {
                register(input: $input) {
                    accessToken
                    refreshToken
                    user {
                        uuid
                        email
                        name
                    }
                }
            }
        }
        """
        
        variables = {
            'input': {
                'name': name,
                'email': email,
                'password': password,
            }
        }
        
        # Add geolocation if provided
        if geolocation:
            variables['input']['geolocation'] = geolocation
        
        try:
            result = self.graphql_client.execute_mutation(mutation, variables)
            if not result or 'auth' not in result or 'register' not in result['auth']:
                raise Appointment360AuthError("Invalid response from appointment360 API")
            
            register_data = result['auth']['register']
            
            # Normalize field names
            return {
                'access_token': register_data.get('accessToken'),
                'refresh_token': register_data.get('refreshToken'),
                'user': {
                    'uuid': register_data.get('user', {}).get('uuid'),
                    'email': register_data.get('user', {}).get('email'),
                    'name': register_data.get('user', {}).get('name'),
                }
            }
        except GraphQLError as e:
            logger.error(f"GraphQL error during register: {e}")
            raise Appointment360AuthError(f"Registration failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during register: {e}", exc_info=True)
            raise Appointment360AuthError(f"Registration failed: {str(e)}")
    
    def logout(self, access_token: str) -> bool:
        """
        Logout user by blacklisting the access token.
        
        Args:
            access_token: Access token to blacklist
            
        Returns:
            True if successful
            
        Raises:
            Appointment360AuthError: If logout fails
        """
        if not self.enabled:
            raise Appointment360AuthError("Appointment360 GraphQL is not enabled")
        
        mutation = """
        mutation Logout {
            auth {
                logout
            }
        }
        """
        
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        try:
            result = self.graphql_client.execute_mutation(mutation, headers=headers)
            if not result or 'auth' not in result or 'logout' not in result['auth']:
                raise Appointment360AuthError("Invalid response from appointment360 API")
            
            return result['auth']['logout'] is True
        except GraphQLError as e:
            logger.error(f"GraphQL error during logout: {e}")
            raise Appointment360AuthError(f"Logout failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during logout: {e}", exc_info=True)
            raise Appointment360AuthError(f"Logout failed: {str(e)}")
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            Dictionary with 'access_token', 'refresh_token', and 'user' (uuid, email, name)
            
        Raises:
            Appointment360AuthError: If token refresh fails
        """
        if not self.enabled:
            raise Appointment360AuthError("Appointment360 GraphQL is not enabled")
        
        mutation = """
        mutation RefreshToken($input: RefreshTokenInput!) {
            auth {
                refreshToken(input: $input) {
                    accessToken
                    refreshToken
                    user {
                        uuid
                        email
                        name
                    }
                }
            }
        }
        """
        
        variables = {
            'input': {
                'refreshToken': refresh_token,
            }
        }
        
        try:
            result = self.graphql_client.execute_mutation(mutation, variables)
            if not result or 'auth' not in result or 'refreshToken' not in result['auth']:
                raise Appointment360AuthError("Invalid response from appointment360 API")
            
            refresh_data = result['auth']['refreshToken']
            
            # Normalize field names
            return {
                'access_token': refresh_data.get('accessToken'),
                'refresh_token': refresh_data.get('refreshToken'),
                'user': {
                    'uuid': refresh_data.get('user', {}).get('uuid'),
                    'email': refresh_data.get('user', {}).get('email'),
                    'name': refresh_data.get('user', {}).get('name'),
                }
            }
        except GraphQLError as e:
            logger.error(f"GraphQL error during token refresh: {e}")
            raise Appointment360AuthError(f"Token refresh failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {e}", exc_info=True)
            raise Appointment360AuthError(f"Token refresh failed: {str(e)}")
    
    def get_me(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get current authenticated user info with role.
        
        Args:
            access_token: Access token
            
        Returns:
            Dictionary with user info (uuid, email, name, role) or None if not authenticated
        """
        if not self.enabled:
            return None
        
        query = """
        query Me {
            auth {
                me {
                    uuid
                    email
                    name
                    profile {
                        role
                    }
                }
            }
        }
        """
        
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        try:
            result = self.graphql_client.execute_query(query, headers=headers, use_cache=False)
            if not result or 'auth' not in result:
                return None
            
            me_data = result['auth'].get('me')
            if not me_data:
                return None
            
            profile = me_data.get('profile', {})
            
            return {
                'uuid': me_data.get('uuid'),
                'email': me_data.get('email'),
                'name': me_data.get('name'),
                'role': profile.get('role') if profile else None,
            }
        except GraphQLError as e:
            logger.debug(f"GraphQL error getting user info (may not be authenticated): {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error getting user info: {e}")
            return None
    
    def get_me_with_profile(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get current authenticated user info with full profile details.
        
        Args:
            access_token: Access token
            
        Returns:
            Dictionary with full user info including profile (uuid, email, name, role, credits, etc.) 
            or None if not authenticated
        """
        if not self.enabled:
            return None
        
        query = """
        query Me {
            auth {
                me {
                    uuid
                    email
                    name
                    profile {
                        userId
                        jobTitle
                        bio
                        timezone
                        role
                        credits
                        subscriptionPlan
                        subscriptionPeriod
                        subscriptionStatus
                        subscriptionStartedAt
                        subscriptionEndsAt
                        createdAt
                        updatedAt
                    }
                }
            }
        }
        """
        
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        try:
            result = self.graphql_client.execute_query(query, headers=headers, use_cache=False)
            if not result or 'auth' not in result:
                return None
            
            me_data = result['auth'].get('me')
            if not me_data:
                return None
            
            profile = me_data.get('profile', {})
            
            return {
                'uuid': me_data.get('uuid'),
                'email': me_data.get('email'),
                'name': me_data.get('name'),
                'profile': {
                    'user_id': profile.get('userId'),
                    'job_title': profile.get('jobTitle'),
                    'bio': profile.get('bio'),
                    'timezone': profile.get('timezone'),
                    'role': profile.get('role'),
                    'credits': profile.get('credits', 0),
                    'subscription_plan': profile.get('subscriptionPlan'),
                    'subscription_period': profile.get('subscriptionPeriod'),
                    'subscription_status': profile.get('subscriptionStatus'),
                    'subscription_started_at': profile.get('subscriptionStartedAt'),
                    'subscription_ends_at': profile.get('subscriptionEndsAt'),
                    'created_at': profile.get('createdAt'),
                    'updated_at': profile.get('updatedAt'),
                } if profile else None,
            }
        except GraphQLError as e:
            logger.debug(f"GraphQL error getting user profile (may not be authenticated): {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error getting user profile: {e}")
            return None
    
    def get_user_role(self, access_token: str) -> Optional[str]:
        """
        Get user role from access token.
        
        Args:
            access_token: Access token
            
        Returns:
            User role string (e.g., 'SuperAdmin', 'Admin', 'FreeUser', 'ProUser') or None
        """
        user_info = self.get_me(access_token)
        if not user_info:
            return None
        return user_info.get('role')
    
    def is_super_admin(self, access_token: str) -> bool:
        """
        Check if user is SuperAdmin.
        
        Args:
            access_token: Access token
            
        Returns:
            True if user is SuperAdmin, False otherwise
        """
        role = self.get_user_role(access_token)
        return role == 'SuperAdmin'
    
    def is_admin_or_super_admin(self, access_token: str) -> bool:
        """
        Check if user is Admin or SuperAdmin.
        
        Args:
            access_token: Access token
            
        Returns:
            True if user is Admin or SuperAdmin, False otherwise
        """
        role = self.get_user_role(access_token)
        return role in ['Admin', 'SuperAdmin']
    
    def get_session(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get current session information.
        
        Args:
            access_token: Access token
            
        Returns:
            Dictionary with session info (user_uuid, email, is_authenticated, last_sign_in_at) or None
        """
        if not self.enabled:
            return None
        
        query = """
        query Session {
            auth {
                session {
                    userUuid
                    email
                    isAuthenticated
                    lastSignInAt
                }
            }
        }
        """
        
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        try:
            result = self.graphql_client.execute_query(query, headers=headers, use_cache=False)
            if not result or 'auth' not in result or 'session' not in result['auth']:
                return None
            
            session_data = result['auth']['session']
            
            return {
                'user_uuid': session_data.get('userUuid'),
                'email': session_data.get('email'),
                'is_authenticated': session_data.get('isAuthenticated', False),
                'last_sign_in_at': session_data.get('lastSignInAt'),
            }
        except GraphQLError as e:
            logger.debug(f"GraphQL error getting session (may not be authenticated): {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error getting session: {e}")
            return None
