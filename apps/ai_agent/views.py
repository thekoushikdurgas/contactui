"""AI Agent views."""
import json
import logging
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils import timezone

from apps.ai_agent.services.ai_service import AIService
from apps.ai_agent.models import AILearningSession, ChatMessage

logger = logging.getLogger(__name__)


@login_required
def chat_view(request):
    """AI chat interface."""
    session_id = request.GET.get('session_id')
    session = None
    initial_messages = []
    
    # Get session from database if session_id provided
    if session_id:
        try:
            session = AILearningSession.objects.get(
                session_id=session_id,
                created_by=request.user
            )
            # Get messages for this session
            db_messages = ChatMessage.objects.filter(
                session=session,
                created_by=request.user
            ).order_by('created_at')
            
            initial_messages = [
                {
                    'role': msg.role,
                    'content': msg.content,
                    'groundingSources': msg.metadata.get('groundingSources', []),
                    'timestamp': msg.created_at
                }
                for msg in db_messages
            ]
        except AILearningSession.DoesNotExist:
            messages.error(request, 'Session not found or unauthorized.')
            return redirect('ai_agent:chat')
    
    context = {
        'session_id': session_id,
        'session': session,
        'initial_messages': initial_messages
    }
    return render(request, 'ai_agent/chat.html', context)


@login_required
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
        
        ai_service = AIService()
        
        # Retrieve context from local JSON files if not provided
        if not context:
            context = ai_service.retrieve_context(message, limit=5)
        
        # Get or create session
        if session_id:
            try:
                session = AILearningSession.objects.get(
                    session_id=session_id,
                    created_by=request.user
                )
            except AILearningSession.DoesNotExist:
                return JsonResponse({'error': 'Session not found'}, status=404)
        else:
            # Create new session
            session = AILearningSession.objects.create(
                session_name=f'Chat {timezone.now().strftime("%Y-%m-%d %H:%M")}',
                created_by=request.user,
                status='running',
                started_at=timezone.now()
            )
        
        # Build messages for chat from database
        messages_list = []
        db_messages = ChatMessage.objects.filter(
            session=session,
            created_by=request.user
        ).order_by('created_at')[:20]  # Last 20 messages for context
        
        for msg in db_messages:
            messages_list.append({
                'role': msg.role,
                'content': msg.content
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
            ChatMessage.objects.create(
                session=session,
                role='user',
                content=message,
                created_by=request.user
            )
            
            # Save assistant message
            ChatMessage.objects.create(
                session=session,
                role='assistant',
                content=response.get('content', ''),
                metadata={
                    'groundingSources': grounding_sources,
                    **response.get('metadata', {})
                },
                created_by=request.user
            )
            
            # Update session
            session.updated_at = timezone.now()
            session.save(update_fields=['updated_at'])
            
            return JsonResponse({
                'success': True,
                'content': response.get('content', ''),
                'groundingSources': grounding_sources,
                'metadata': response.get('metadata', {}),
                'session_id': str(session.session_id)
            })
        else:
            return JsonResponse({'error': 'Failed to get AI response'}, status=500)
            
    except Exception as e:
        logger.error(f"Error in chat completion: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def list_sessions_view(request):
    """List all AI sessions (filter by request.user). Continue → /ai/chat/?session_id=..."""
    sessions_qs = AILearningSession.objects.filter(
        created_by=request.user
    ).order_by('-created_at')[:50]
    
    sessions_list = []
    for session in sessions_qs:
        message_count = ChatMessage.objects.filter(session=session).count()
        sessions_list.append({
            'session': session,
            'message_count': message_count
        })
    
    context = {
        'sessions': sessions_list,
        'empty_state_chat_url': reverse('ai_agent:chat'),
    }
    return render(request, 'ai_agent/sessions.html', context)


@login_required
def session_detail_view(request, session_id):
    """AI session detail view."""
    try:
        session = AILearningSession.objects.get(
            session_id=session_id,
            created_by=request.user
        )
    except AILearningSession.DoesNotExist:
        messages.error(request, 'Session not found or unauthorized.')
        return redirect('ai_agent:sessions')
    
    # Get messages for this session
    messages_list = ChatMessage.objects.filter(
        session=session,
        created_by=request.user
    ).select_related('session', 'created_by').order_by('created_at')
    
    # Convert to format expected by template
    formatted_messages = [
        {
            'role': msg.role,
            'content': msg.content,
            'groundingSources': msg.metadata.get('groundingSources', []),
            'timestamp': msg.created_at
        }
        for msg in messages_list
    ]
    
    context = {
        'session_id': session_id,
        'session': session,
        'messages': formatted_messages
    }
    return render(request, 'ai_agent/session_detail.html', context)
