"""AI Agent session storage service using S3 JSON storage."""

import logging
import uuid as uuid_lib
from typing import Optional, Dict, Any, List
from datetime import datetime

from apps.core.services.s3_model_storage import S3ModelStorage

logger = logging.getLogger(__name__)


class AISessionStorageService(S3ModelStorage):
    """Storage service for AI learning sessions using S3 JSON storage."""
    
    def __init__(self):
        """Initialize AI session storage service."""
        super().__init__(model_name='ai_sessions')
    
    def _extract_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata fields for session index."""
        return {
            'uuid': data.get('uuid') or data.get('session_id'),
            'session_id': data.get('session_id') or data.get('uuid'),
            'session_name': data.get('session_name', ''),
            'status': data.get('status', 'pending'),
            'created_by': data.get('created_by'),  # UUID string
            'created_at': data.get('created_at', ''),
            'updated_at': data.get('updated_at', ''),
        }
    
    def create_session(
        self,
        session_name: str,
        created_by: Optional[str] = None,
        patterns_learned: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create a new AI learning session."""
        session_id = str(uuid_lib.uuid4())
        now = datetime.utcnow().isoformat()
        
        session_data = {
            'session_id': session_id,
            'session_name': session_name,
            'patterns_learned': patterns_learned or {},
            'status': 'pending',
            'created_by': created_by,
            'created_at': now,
            'updated_at': now,
            'started_at': None,
            'completed_at': None,
            'messages': [],  # Chat messages stored as nested list
        }
        
        return self.create(session_data, item_uuid=session_id)
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID."""
        return self.get(session_id)
    
    def update_session(self, session_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Update a session."""
        # Handle status timestamp updates
        if 'status' in kwargs:
            session = self.get(session_id)
            if session:
                if kwargs['status'] == 'running' and not session.get('started_at'):
                    kwargs['started_at'] = datetime.utcnow().isoformat()
                elif kwargs['status'] in ['completed', 'failed'] and not session.get('completed_at'):
                    kwargs['completed_at'] = datetime.utcnow().isoformat()
        
        return self.update(session_id, kwargs)
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        created_by: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """Add a chat message to a session."""
        session = self.get(session_id)
        if not session:
            return None
        
        message_id = str(uuid_lib.uuid4())
        now = datetime.utcnow().isoformat()
        
        message = {
            'message_id': message_id,
            'role': role,
            'content': content,
            'metadata': metadata or {},
            'created_by': created_by,
            'created_at': now,
        }
        
        # Add message to session's messages list
        messages = session.get('messages', [])
        messages.append(message)
        
        return self.update(session_id, {'messages': messages})
    
    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a session."""
        session = self.get(session_id)
        if not session:
            return []
        return session.get('messages', [])
