"""Core views for authentication and dashboard."""
import logging
from typing import Optional, Dict, Any
from urllib.parse import quote
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.cache import cache
from django.http import HttpResponse
from django.conf import settings

from apps.core.clients.appointment360_client import Appointment360Client, Appointment360AuthError
from apps.core.decorators.auth import require_super_admin
from apps.core.super_admin_debug import debug_log

logger = logging.getLogger(__name__)


def _get_client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


def _get_geolocation(request) -> Optional[Dict[str, Any]]:
    """
    Extract basic geolocation data from request.
    Returns minimal geolocation dict with IP address.
    
    Args:
        request: Django request object
        
    Returns:
        Dictionary with 'ip' key, or None if extraction fails
    """
    try:
        ip = _get_client_ip(request)
        return {'ip': ip}
    except Exception:
        return None


def _set_auth_cookies(response: HttpResponse, access_token: str, refresh_token: str, remember_me: bool = False):
    """Set httpOnly cookies for access and refresh tokens."""
    # When remember_me=False use session cookie (omit max_age/expires). Never use expires=0 - it is
    # interpreted as Unix epoch and the cookie is discarded immediately, so the next request has no cookie.
    max_age = 86400 * 7 if remember_me else None  # 7 days if remember_me, session cookie otherwise
    
    response.set_cookie(
        'access_token',
        access_token,
        max_age=max_age,
        httponly=True,
        secure=not settings.DEBUG,  # Secure in production
        samesite='Lax',
        path='/'
    )
    response.set_cookie(
        'refresh_token',
        refresh_token,
        max_age=86400 * 30,  # 30 days for refresh token
        httponly=True,
        secure=not settings.DEBUG,
        samesite='Lax',
        path='/'
    )


def _clear_auth_cookies(response: HttpResponse):
    """Clear authentication cookies."""
    response.delete_cookie('access_token', path='/')
    response.delete_cookie('refresh_token', path='/')


def login_view(request):
    """User login view using appointment360. Rate-limited by IP; supports next redirect."""
    # Check if already authenticated (via token)
    access_token = request.COOKIES.get('access_token')
    if access_token:
        debug_log(f"login_view GET has cookie access_token len={len(access_token)}")
        try:
            client = Appointment360Client(request=request)
            user_info = client.get_me(access_token)
            debug_log(f"login_view GET get_me result user_info={bool(user_info)} role={user_info.get('role') if user_info else None}")
            if user_info:
                next_url = request.GET.get('next') or request.POST.get('next')
                target = next_url if (next_url and next_url.startswith('/') and '//' not in next_url) else None
                dest = target or 'core:dashboard'
                debug_log(f"login_view GET redirect dest={dest}")
                if target:
                    return redirect(target)
                return redirect('core:dashboard')
        except Exception as e:
            debug_log(f"login_view GET get_me exception {type(e).__name__}: {e}")
            pass  # Token might be invalid, continue with login
    
    # Check if appointment360 is enabled
    if not getattr(settings, 'GRAPHQL_ENABLED', False):
        messages.error(request, 'Authentication service is not available. Please contact support.')
        return render(request, 'core/login.html', {'next': request.GET.get('next')})
    
    ip = _get_client_ip(request)
    cooldown_key = f'login_cooldown:{ip}'
    fail_key = f'login_fail:{ip}'
    if cache.get(cooldown_key):
        messages.error(request, 'Too many failed attempts. Please try again in 15 minutes.')
        return render(request, 'core/login.html', {'next': request.GET.get('next')})
    
    if request.method == 'POST':
        email = request.POST.get('username')  # Login form uses 'username' field for email
        password = request.POST.get('password')
        remember_me = bool(request.POST.get('remember_me'))
        next_url = (request.POST.get('next') or request.GET.get('next') or '').strip()
        if next_url and ('//' in next_url or not next_url.startswith('/')):
            next_url = ''
        
        try:
            client = Appointment360Client(request=request)
            geolocation = _get_geolocation(request)
            auth_result = client.login(email, password, geolocation=geolocation)
            
            access_token = auth_result.get('access_token')
            refresh_token = auth_result.get('refresh_token')
            user_info = auth_result.get('user', {})
            
            if not access_token or not refresh_token:
                raise Appointment360AuthError("Invalid response from authentication service")
            
            # Check if user is SuperAdmin (required for access)
            is_super_admin = client.is_super_admin(access_token)
            debug_log(f"login_view POST is_super_admin={is_super_admin} email={email}")
            if not is_super_admin:
                debug_log("login_view POST denied: not SuperAdmin")
                messages.error(request, 'Access denied. SuperAdmin role required.')
                return render(request, 'core/login.html', {'next': request.GET.get('next')})
            
            # Set auth cookies and redirect via 200 + client-side redirect so the browser stores
            # the cookie before navigating. Many browsers do not send cookies set on a 302 response
            # with the immediate redirect follow-up request.
            target = (next_url or '/').strip() or '/'
            if target and ('//' in target or not target.startswith('/')):
                target = '/'
            debug_log(f"login_view POST success 200+redirect to {target!r}")
            response = render(request, 'core/redirecting.html', {'redirect_url': target})
            _set_auth_cookies(response, access_token, refresh_token, remember_me)
            
            cache.delete(fail_key)
            cache.delete(cooldown_key)
            messages.success(request, f'Welcome back, {user_info.get("name") or email}!')
            return response
            
        except Appointment360AuthError as e:
            fail_count = cache.get(fail_key, 0) + 1
            cache.set(fail_key, fail_count, timeout=900)
            if fail_count >= 5:
                cache.set(cooldown_key, 1, timeout=900)
                cache.delete(fail_key)
                messages.error(request, 'Too many failed attempts. Please try again in 15 minutes.')
            else:
                error_msg = str(e)
                if 'Authentication failed' in error_msg:
                    messages.error(request, 'Invalid email or password.')
                else:
                    messages.error(request, error_msg)
        except Exception as e:
            logger.error(f"Unexpected error during login: {e}", exc_info=True)
            messages.error(request, 'An error occurred during login. Please try again.')
    
    # Force user to be anonymous for login page rendering
    # This ensures base.html renders the auth layout instead of dashboard layout
    from django.contrib.auth.models import AnonymousUser
    if hasattr(request, 'user') and request.user.is_authenticated:
        request.user = AnonymousUser()
    
    return render(request, 'core/login.html', {'next': request.GET.get('next')})


def register_view(request):
    """User registration view using appointment360 GraphQL API."""
    # Check if already authenticated (via token)
    access_token = request.COOKIES.get('access_token')
    if access_token:
        try:
            client = Appointment360Client(request=request)
            user_info = client.get_me(access_token)
            if user_info:
                return redirect('core:dashboard')
        except Exception:
            pass  # Token might be invalid, continue with registration
    
    # Check if appointment360 is enabled
    if not getattr(settings, 'GRAPHQL_ENABLED', False):
        messages.error(request, 'Registration service is not available. Please contact support.')
        return render(request, 'core/register.html')
    
    ip = _get_client_ip(request)
    cooldown_key = f'register_cooldown:{ip}'
    fail_key = f'register_fail:{ip}'
    
    if cache.get(cooldown_key):
        messages.error(request, 'Too many failed attempts. Please try again in 15 minutes.')
        return render(request, 'core/register.html')
    
    if request.method == 'POST':
        name = request.POST.get('name') or request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        remember_me = bool(request.POST.get('remember_me'))
        
        # Validation
        validation_errors = []
        if not name:
            validation_errors.append('Name is required.')
        if not email:
            validation_errors.append('Email is required.')
        if not password:
            validation_errors.append('Password is required.')
        elif len(password) < 8:
            validation_errors.append('Password must be at least 8 characters long.')
        if password != password_confirm:
            validation_errors.append('Passwords do not match.')
        
        if validation_errors:
            for error in validation_errors:
                messages.error(request, error)
        else:
            try:
                client = Appointment360Client(request=request)
                geolocation = _get_geolocation(request)
                auth_result = client.register(name, email, password, geolocation=geolocation)
                
                access_token = auth_result.get('access_token')
                refresh_token = auth_result.get('refresh_token')
                user_info = auth_result.get('user', {})
                
                if not access_token or not refresh_token:
                    raise Appointment360AuthError("Invalid response from registration service")
                
                # Check if user is SuperAdmin (required for access)
                is_super_admin = client.is_super_admin(access_token)
                if not is_super_admin:
                    messages.warning(
                        request, 
                        'Account created successfully, but SuperAdmin role is required for access. '
                        'Please contact an administrator to grant access.'
                    )
                    return redirect('core:login')
                
                # Set auth cookies; redirect to /login/?next=/ so browser sends cookie on next request
                target = '/'
                response = redirect('/login/?next=' + quote(target))
                _set_auth_cookies(response, access_token, refresh_token, remember_me)
                
                cache.delete(fail_key)
                cache.delete(cooldown_key)
                messages.success(request, f'Welcome, {user_info.get("name") or email}! Your account has been created.')
                return response
                
            except Appointment360AuthError as e:
                fail_count = cache.get(fail_key, 0) + 1
                cache.set(fail_key, fail_count, timeout=900)
                if fail_count >= 5:
                    cache.set(cooldown_key, 1, timeout=900)
                    cache.delete(fail_key)
                    messages.error(request, 'Too many failed attempts. Please try again in 15 minutes.')
                else:
                    error_msg = str(e)
                    if 'already exists' in error_msg.lower() or 'duplicate' in error_msg.lower():
                        messages.error(request, 'An account with this email already exists.')
                    elif 'Registration failed' in error_msg:
                        messages.error(request, 'Registration failed. Please check your information and try again.')
                    else:
                        messages.error(request, error_msg)
            except Exception as e:
                logger.error(f"Unexpected error during registration: {e}", exc_info=True)
                messages.error(request, 'An error occurred during registration. Please try again.')
    
    return render(request, 'core/register.html')


def logout_view(request):
    """User logout view using appointment360."""
    # Get access token from cookie
    access_token = request.COOKIES.get('access_token')
    
    # Call appointment360 logout if token exists and service is enabled
    if access_token and getattr(settings, 'GRAPHQL_ENABLED', False):
        try:
            client = Appointment360Client(request=request)
            client.logout(access_token)
        except Exception as e:
            logger.warning(f"Failed to logout from appointment360: {e}")
            # Continue with logout even if appointment360 logout fails
    
    # Clear auth cookies (no Django session to logout from)
    response = redirect('core:login')
    _clear_auth_cookies(response)
    
    messages.info(request, 'You have been logged out.')
    return response


@require_super_admin
def dashboard_view(request):
    """Main dashboard view."""
    from apps.documentation.services.pages_service import PagesService
    from apps.documentation.services.endpoints_service import EndpointsService
    from apps.tasks.services import TaskService
    
    # Aggregate statistics from services
    pages_service = PagesService()
    endpoints_service = EndpointsService()
    task_service = TaskService()
    
    try:
        # Get total pages count from local JSON files
        pages_result = pages_service.list_pages(limit=1, offset=0)
        total_pages = pages_result.get('total', 0)
    except Exception:
        total_pages = 0
    
    try:
        # Get total endpoints count
        endpoints_result = endpoints_service.list_endpoints(limit=1, offset=0)
        total_endpoints = endpoints_result.get('total', 0)
    except Exception:
        total_endpoints = 0
    
    # Active sessions - will use storage service once migrated
    active_sessions = 0
    
    # Completed tasks
    try:
        completed_tasks_list = task_service.list_tasks(status='completed', limit=100)
        completed_tasks = len(completed_tasks_list) if isinstance(completed_tasks_list, list) else 0
    except Exception:
        completed_tasks = 0
    
    # Code health (placeholder - would need codebase analysis)
    code_health = '94%'
    
    # Recent tasks
    try:
        recent_tasks_list = task_service.list_tasks(limit=4, offset=0)
        recent_tasks = [
            {
                'task_id': task.get('task_id') if isinstance(task, dict) else getattr(task, 'task_id', None),
                'title': task.get('title') if isinstance(task, dict) else getattr(task, 'title', ''),
                'created_at': task.get('created_at') if isinstance(task, dict) else getattr(task, 'created_at', None)
            }
            for task in recent_tasks_list
        ]
    except Exception:
        recent_tasks = []
    
    context = {
        'total_pages': f'{total_pages:,}' if total_pages > 0 else '0',
        'total_endpoints': f'{total_endpoints:,}' if total_endpoints > 0 else '0',
        'active_sessions': str(active_sessions),
        'completed_tasks': f'{completed_tasks:,}' if completed_tasks > 0 else '0',
        'code_health': code_health,
        'recent_tasks': recent_tasks,
    }
    return render(request, 'core/dashboard.html', context)
