"""API views for AI Agent."""
import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from apps.core.decorators.auth import require_super_admin
from apps.ai_agent.services.ai_service import AIService
from apps.ai_agent.services.session_storage_service import AISessionStorageService

logger = logging.getLogger(__name__)
ai_service = AIService()


@require_super_admin
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
        
        # Get user UUID from token
        user_uuid = None
        if hasattr(request, 'appointment360_user'):
            user_uuid = request.appointment360_user.get('uuid')
        
        storage = AISessionStorageService()
        
        # Get or create session
        if session_id:
            session = storage.get_session(session_id)
            if not session or session.get('created_by') != user_uuid:
                return JsonResponse({'error': 'Session not found'}, status=404)
        else:
            session = storage.create_session(
                session_name=f'Chat {timezone.now().strftime("%Y-%m-%d %H:%M")}',
                created_by=user_uuid,
                patterns_learned={}
            )
            session_id = session.get('session_id')
            storage.update_session(session_id, status='running', started_at=timezone.now().isoformat())
        
        # Build messages from storage
        messages_list = []
        db_messages = storage.get_messages(session_id)
        
        for msg in db_messages[-20:]:  # Last 20 messages
            messages_list.append({
                'role': msg.get('role'),
                'content': msg.get('content')
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
            storage.add_message(
                session_id,
                role='user',
                content=prompt,
                created_by=user_uuid
            )
            
            storage.add_message(
                session_id,
                role='assistant',
                content=response.get('content', ''),
                created_by=user_uuid,
                metadata={
                    'groundingSources': response.get('groundingSources', []),
                    **response.get('metadata', {})
                }
            )
            
            storage.update_session(session_id, updated_at=timezone.now().isoformat())
            
            return JsonResponse({
                'text': response.get('content', ''),
                'groundingSources': response.get('groundingSources', []),
                'session_id': session_id,
                'metadata': response.get('metadata', {})
            })
        else:
            return JsonResponse({'error': 'Failed to get AI response'}, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Chat API error: {e}", exc_info=True)
        return JsonResponse({'error': 'Internal server error'}, status=500)


@require_super_admin
@require_http_methods(["GET"])
def sessions_api(request):
    """List AI sessions."""
    limit = int(request.GET.get('limit', 50))
    
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    storage = AISessionStorageService()
    
    sessions_result = storage.list(filters={'created_by': user_uuid}, limit=limit, offset=0, order_by='created_at', reverse=True)
    
    sessions_data = []
    for session in sessions_result.get('items', []):
        message_count = len(session.get('messages', []))
        sessions_data.append({
            'session_id': session.get('session_id'),
            'session_name': session.get('session_name'),
            'status': session.get('status'),
            'started_at': session.get('started_at'),
            'created_at': session.get('created_at'),
            'updated_at': session.get('updated_at'),
            'message_count': message_count
        })
    
    return JsonResponse({'sessions': sessions_data})


@require_super_admin
@require_http_methods(["GET"])
def session_detail_api(request, session_id):
    """Get session detail."""
    # Get user UUID from token
    user_uuid = None
    if hasattr(request, 'appointment360_user'):
        user_uuid = request.appointment360_user.get('uuid')
    
    storage = AISessionStorageService()
    
    session = storage.get_session(session_id)
    
    if not session or session.get('created_by') != user_uuid:
        return JsonResponse({'error': 'Session not found'}, status=404)
    
    messages = storage.get_messages(session_id)
    
    messages_data = [
        {
            'role': msg.get('role'),
            'content': msg.get('content'),
            'groundingSources': msg.get('metadata', {}).get('groundingSources', []),
            'timestamp': msg.get('created_at')
        }
        for msg in messages
    ]
    
    return JsonResponse({
        'session': {
            'session_id': session.get('session_id'),
            'session_name': session.get('session_name'),
            'status': session.get('status'),
            'started_at': session.get('started_at'),
            'created_at': session.get('created_at'),
            'updated_at': session.get('updated_at')
        },
        'messages': messages_data
    })
