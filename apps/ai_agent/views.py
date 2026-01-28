"""AI Agent views."""
import json
import logging
import uuid
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils import timezone

from apps.core.decorators.auth import require_super_admin
from apps.ai_agent.services.ai_service import AIService
from apps.ai_agent.services.session_storage_service import AISessionStorageService

logger = logging.getLogger(__name__)


@require_super_admin
def chat_view(request):
    """AI chat interface."""
    session_id = request.GET.get('session_id')
    session = None
    initial_messages = []
    
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    storage = AISessionStorageService()
    
    # Get session from S3 storage if session_id provided
    if session_id:
        session = storage.get_session(session_id)
        if session:
            # Check ownership
            if session.get('created_by') != user_uuid:
                messages.error(request, 'Session not found or unauthorized.')
                return redirect('ai_agent:chat')
            
            # Get messages for this session
            db_messages = storage.get_messages(session_id)
            
            initial_messages = [
                {
                    'role': msg.get('role'),
                    'content': msg.get('content'),
                    'groundingSources': msg.get('metadata', {}).get('groundingSources', []),
                    'timestamp': msg.get('created_at')
                }
                for msg in db_messages
            ]
        else:
            messages.error(request, 'Session not found or unauthorized.')
            return redirect('ai_agent:chat')
    
    context = {
        'session_id': session_id,
        'session': session,
        'initial_messages': initial_messages
    }
    return render(request, 'ai_agent/chat.html', context)


@require_super_admin
@require_http_methods(["POST"])
@csrf_exempt
def chat_completion_api(request):
    """API endpoint for chat completion."""
    try:
        data = json.loads(request.body)
        message = data.get('message', '')
        session_id = data.get('session_id')
        context = data.get('context', [])
        
        if not message:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        # Get user UUID from token
        user_uuid = None
        if hasattr(request, 'appointment360_user'):
            user_uuid = request.appointment360_user.get('uuid')
        
        ai_service = AIService()
        storage = AISessionStorageService()
        
        # Retrieve context from local JSON files if not provided
        if not context:
            context = ai_service.retrieve_context(message, limit=5)
        
        # Get or create session
        if session_id:
            session = storage.get_session(session_id)
            if not session or session.get('created_by') != user_uuid:
                return JsonResponse({'error': 'Session not found'}, status=404)
        else:
            # Create new session
            session = storage.create_session(
                session_name=f'Chat {timezone.now().strftime("%Y-%m-%d %H:%M")}',
                created_by=user_uuid,
                patterns_learned={}
            )
            session_id = session.get('session_id')
            storage.update_session(session_id, status='running', started_at=timezone.now().isoformat())
        
        # Build messages for chat from storage
        messages_list = []
        db_messages = storage.get_messages(session_id)
        
        # Get last 20 messages for context
        for msg in db_messages[-20:]:
            messages_list.append({
                'role': msg.get('role'),
                'content': msg.get('content')
            })
        
        messages_list.append({
            'role': 'user',
            'content': message
        })
        
        # Get AI response
        response = ai_service.chat_completion(messages_list, context=context)
        
        if response:
            # Extract grounding sources from response
            grounding_sources = response.get('groundingSources', [])
            
            # Save user message
            storage.add_message(
                session_id,
                role='user',
                content=message,
                created_by=user_uuid
            )
            
            # Save assistant message
            storage.add_message(
                session_id,
                role='assistant',
                content=response.get('content', ''),
                created_by=user_uuid,
                metadata={
                    'groundingSources': grounding_sources,
                    **response.get('metadata', {})
                }
            )
            
            # Update session
            storage.update_session(session_id, updated_at=timezone.now().isoformat())
            
            return JsonResponse({
                'success': True,
                'content': response.get('content', ''),
                'groundingSources': grounding_sources,
                'metadata': response.get('metadata', {}),
                'session_id': session_id
            })
        else:
            return JsonResponse({'error': 'Failed to get AI response'}, status=500)
            
    except Exception as e:
        logger.error(f"Error in chat completion: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


@require_super_admin
def list_sessions_view(request):
    """List all AI sessions."""
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    storage = AISessionStorageService()
    
    # Get sessions filtered by user
    all_sessions = storage.list(filters={'created_by': user_uuid}, limit=50, offset=0, order_by='created_at', reverse=True)
    
    sessions_list = []
    for session in all_sessions.get('items', []):
        message_count = len(session.get('messages', []))
        sessions_list.append({
            'session': session,
            'message_count': message_count
        })
    
    context = {
        'sessions': sessions_list,
        'empty_state_chat_url': reverse('ai_agent:chat'),
    }
    return render(request, 'ai_agent/sessions.html', context)


@require_super_admin
def session_detail_view(request, session_id):
    """AI session detail view."""
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    storage = AISessionStorageService()
    
    session = storage.get_session(session_id)
    
    if not session or session.get('created_by') != user_uuid:
        messages.error(request, 'Session not found or unauthorized.')
        return redirect('ai_agent:sessions')
    
    # Get messages for this session
    messages_list = storage.get_messages(session_id)
    
    # Convert to format expected by template
    formatted_messages = [
        {
            'role': msg.get('role'),
            'content': msg.get('content'),
            'groundingSources': msg.get('metadata', {}).get('groundingSources', []),
            'timestamp': msg.get('created_at')
        }
        for msg in messages_list
    ]
    
    context = {
        'session_id': session_id,
        'session': session,
        'messages': formatted_messages
    }
    return render(request, 'ai_agent/session_detail.html', context)
