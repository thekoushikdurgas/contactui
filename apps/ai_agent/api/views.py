"""API views for AI Agent."""
import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from apps.ai_agent.services.ai_service import AIService
from apps.ai_agent.models import AILearningSession, ChatMessage

logger = logging.getLogger(__name__)
ai_service = AIService()


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def chat_api(request):
    """Handle AI chat requests."""
    try:
        data = json.loads(request.body)
        prompt = data.get('prompt', '')
        history = data.get('history', [])
        session_id = data.get('session_id')
        
        if not prompt:
            return JsonResponse({'error': 'Prompt is required'}, status=400)
        
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
            session = AILearningSession.objects.create(
                session_name=f'Chat {timezone.now().strftime("%Y-%m-%d %H:%M")}',
                created_by=request.user,
                status='running',
                started_at=timezone.now()
            )
        
        # Build messages from database
        messages_list = []
        db_messages = ChatMessage.objects.filter(
            session=session,
            created_by=request.user
        ).order_by('created_at')[:20]
        
        for msg in db_messages:
            messages_list.append({
                'role': msg.role,
                'content': msg.content
            })
        
        messages_list.append({
            'role': 'user',
            'content': prompt
        })
        
        # Get AI response
        context = data.get('context', [])
        if not context:
            context = ai_service.retrieve_context(prompt, limit=5)
        
        response = ai_service.chat_completion(messages_list, context=context)
        
        if response:
            # Save messages
            ChatMessage.objects.create(
                session=session,
                role='user',
                content=prompt,
                created_by=request.user
            )
            
            ChatMessage.objects.create(
                session=session,
                role='assistant',
                content=response.get('content', ''),
                metadata={
                    'groundingSources': response.get('groundingSources', []),
                    **response.get('metadata', {})
                },
                created_by=request.user
            )
            
            session.updated_at = timezone.now()
            session.save(update_fields=['updated_at'])
            
            return JsonResponse({
                'text': response.get('content', ''),
                'groundingSources': response.get('groundingSources', []),
                'session_id': str(session.session_id),
                'metadata': response.get('metadata', {})
            })
        else:
            return JsonResponse({'error': 'Failed to get AI response'}, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Chat API error: {e}", exc_info=True)
        return JsonResponse({'error': 'Internal server error'}, status=500)


@login_required
@require_http_methods(["GET"])
def sessions_api(request):
    """List AI sessions."""
    limit = int(request.GET.get('limit', 50))
    sessions = AILearningSession.objects.filter(
        created_by=request.user
    ).order_by('-created_at')[:limit]
    
    sessions_data = []
    for session in sessions:
        message_count = ChatMessage.objects.filter(session=session).count()
        sessions_data.append({
            'session_id': str(session.session_id),
            'session_name': session.session_name,
            'status': session.status,
            'started_at': session.started_at.isoformat() if session.started_at else None,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat(),
            'message_count': message_count
        })
    
    return JsonResponse({'sessions': sessions_data})


@login_required
@require_http_methods(["GET"])
def session_detail_api(request, session_id):
    """Get session detail."""
    try:
        session = AILearningSession.objects.get(
            session_id=session_id,
            created_by=request.user
        )
    except AILearningSession.DoesNotExist:
        return JsonResponse({'error': 'Session not found'}, status=404)
    
    messages = ChatMessage.objects.filter(
        session=session,
        created_by=request.user
    ).order_by('created_at')
    
    messages_data = [
        {
            'role': msg.role,
            'content': msg.content,
            'groundingSources': msg.metadata.get('groundingSources', []),
            'timestamp': msg.created_at.isoformat()
        }
        for msg in messages
    ]
    
    return JsonResponse({
        'session': {
            'session_id': str(session.session_id),
            'session_name': session.session_name,
            'status': session.status,
            'started_at': session.started_at.isoformat() if session.started_at else None,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat()
        },
        'messages': messages_data
    })
