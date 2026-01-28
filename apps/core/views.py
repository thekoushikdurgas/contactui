"""Core views for authentication and dashboard."""
import logging
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.cache import cache
from django.http import HttpResponse
from django.conf import settings

from apps.core.clients.appointment360_client import Appointment360Client, Appointment360AuthError

logger = logging.getLogger(__name__)
User = get_user_model()


def _get_client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


def _set_auth_cookies(response: HttpResponse, access_token: str, refresh_token: str, remember_me: bool = False):
    """Set httpOnly cookies for access and refresh tokens."""
    max_age = 86400 * 7 if remember_me else None  # 7 days if remember_me, session cookie otherwise
    expires = None if remember_me else 0
    
    response.set_cookie(
        'access_token',
        access_token,
        max_age=max_age,
        expires=expires,
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
    if request.user.is_authenticated:
        next_url = request.GET.get('next') or request.POST.get('next')
        if next_url and next_url.startswith('/') and '//' not in next_url:
            return redirect(next_url)
        return redirect('core:dashboard')
    
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
            client = Appointment360Client()
            auth_result = client.login(email, password)
            
            access_token = auth_result.get('access_token')
            refresh_token = auth_result.get('refresh_token')
            user_info = auth_result.get('user', {})
            
            if not access_token or not refresh_token:
                raise Appointment360AuthError("Invalid response from authentication service")
            
            # Create or get Django user (for compatibility with existing code)
            # We'll use email as username
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
                user.save()
            
            # Login user in Django session (for compatibility)
            login(request, user)
            if not remember_me:
                request.session.set_expiry(0)
            else:
                request.session.set_expiry(86400 * 7)
            
            # Set auth cookies
            response = redirect(next_url or 'core:dashboard')
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
    
    return render(request, 'core/login.html', {'next': request.GET.get('next')})


def register_view(request):
    """User registration view using appointment360. Rate-limited by IP (max 5 signups/hour)."""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    # Check if appointment360 is enabled
    if not getattr(settings, 'GRAPHQL_ENABLED', False):
        messages.error(request, 'Registration service is not available. Please contact support.')
        return render(request, 'core/register.html')
    
    ip = _get_client_ip(request)
    reg_key = f'register_count:{ip}'
    reg_count = cache.get(reg_key, 0)
    if reg_count >= 5:
        messages.error(request, 'Too many registration attempts from this network. Please try again later.')
        return render(request, 'core/register.html')
    
    if request.method == 'POST':
        cache.set(reg_key, reg_count + 1, timeout=3600)
        if reg_count + 1 > 5:
            messages.error(request, 'Too many registration attempts from this network. Please try again later.')
            return render(request, 'core/register.html')
        
        name = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        
        # Validation
        if not name:
            messages.error(request, 'Username is required.')
            return render(request, 'core/register.html')
        if not email:
            messages.error(request, 'Email is required.')
            return render(request, 'core/register.html')
        if not password:
            messages.error(request, 'Password is required.')
            return render(request, 'core/register.html')
        if password != password_confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'core/register.html')
        
        try:
            client = Appointment360Client()
            auth_result = client.register(name, email, password)
            
            access_token = auth_result.get('access_token')
            refresh_token = auth_result.get('refresh_token')
            user_info = auth_result.get('user', {})
            
            if not access_token or not refresh_token:
                raise Appointment360AuthError("Invalid response from registration service")
            
            # Create Django user (for compatibility with existing code)
            # Use email as username
            user, created = User.objects.get_or_create(
                username=email,
                defaults={
                    'email': email,
                    'first_name': name.split()[0] if name else '',
                    'last_name': ' '.join(name.split()[1:]) if len(name.split()) > 1 else '',
                }
            )
            if not created:
                # Update if exists
                name_parts = name.split()
                user.first_name = name_parts[0] if name_parts else ''
                user.last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
                user.email = email
                user.save()
            
            # Login user in Django session
            login(request, user)
            request.session.set_expiry(86400 * 7)  # 7 days for new registrations
            
            # Set auth cookies
            response = redirect('core:dashboard')
            _set_auth_cookies(response, access_token, refresh_token, remember_me=True)
            
            messages.success(request, 'Account created successfully!')
            return response
            
        except Appointment360AuthError as e:
            error_msg = str(e)
            # Try to extract field-specific errors from GraphQL error message
            if 'email' in error_msg.lower():
                messages.error(request, 'This email is already registered.')
            elif 'password' in error_msg.lower():
                messages.error(request, 'Password does not meet requirements.')
            else:
                messages.error(request, f'Registration failed: {error_msg}')
        except Exception as e:
            logger.error(f"Unexpected error during registration: {e}", exc_info=True)
            messages.error(request, 'An error occurred during registration. Please try again.')
    
    return render(request, 'core/register.html')


@login_required
def logout_view(request):
    """User logout view using appointment360."""
    # Get access token from cookie
    access_token = request.COOKIES.get('access_token')
    
    # Call appointment360 logout if token exists and service is enabled
    if access_token and getattr(settings, 'GRAPHQL_ENABLED', False):
        try:
            client = Appointment360Client()
            client.logout(access_token)
        except Exception as e:
            logger.warning(f"Failed to logout from appointment360: {e}")
            # Continue with local logout even if appointment360 logout fails
    
    # Logout from Django session
    logout(request)
    
    # Clear auth cookies
    response = redirect('core:login')
    _clear_auth_cookies(response)
    
    messages.info(request, 'You have been logged out.')
    return response


@login_required
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
    
    # Active sessions
    try:
        from apps.ai_agent.models import AILearningSession
        active_sessions = AILearningSession.objects.filter(
            created_by=request.user,
            status='running'
        ).count()
    except Exception:
        active_sessions = 0
    
    # Completed tasks
    try:
        completed_tasks_list = task_service.list_tasks(status='completed', limit=100)
        completed_tasks = len(completed_tasks_list)
    except Exception:
        completed_tasks = 0
    
    # Code health (placeholder - would need codebase analysis)
    code_health = '94%'
    
    # Recent tasks
    try:
        recent_tasks_list = task_service.list_tasks(limit=4, offset=0)
        recent_tasks = [
            {
                'task_id': getattr(task, 'task_id', None),
                'title': task.title,
                'created_at': task.created_at
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
