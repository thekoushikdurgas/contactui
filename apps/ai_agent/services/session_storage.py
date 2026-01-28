"""AI Session Storage Service."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from django.conf import settings
from apps.documentation.repositories.s3_json_storage import S3JSONStorage

logger = logging.getLogger(__name__)


class SessionStorage:
    """Service for storing and retrieving AI chat sessions."""
    
    def __init__(self, storage: Optional[S3JSONStorage] = None):
        """Initialize session storage."""
        self.storage = storage or S3JSONStorage()
        self.data_prefix = settings.S3_DATA_PREFIX
        self.sessions_prefix = f"{self.data_prefix}ai_sessions/"
    
    def _get_session_key(self, session_id: str) -> str:
        """Get S3 key for session JSON file."""
        return f"{self.sessions_prefix}{session_id}.json"
    
    def create_session(self, user_id: str, title: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new AI session.
        
        Args:
            user_id: User ID who owns the session
            title: Optional session title
            
        Returns:
            Session dictionary
        """
        session_id = str(uuid.uuid4())
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'title': title or f'Session {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")}',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'messages': []
        }
        
        session_key = self._get_session_key(session_id)
        self.storage.write_json(session_key, session_data)
        
        logger.info(f"Created AI session: {session_id}")
        return session_data
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session dictionary or None if not found
        """
        session_key = self._get_session_key(session_id)
        return self.storage.read_json(session_key)
    
    def update_session(self, session_id: str, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Add a message to a session.
        
        Args:
            session_id: Session ID
            message: Message dictionary with 'role' and 'content'
            
        Returns:
            Updated session dictionary or None if not found
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        session['messages'].append(message)
        session['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        session_key = self._get_session_key(session_id)
        self.storage.write_json(session_key, session)
        
        return session
    
    def list_sessions(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List sessions for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of sessions to return
            
        Returns:
            List of session dictionaries
        """
        try:
            # List all session files
            files = self.storage.list_json_files(self.sessions_prefix, max_keys=limit * 2)
            
            sessions = []
            for file_key in files:
                session = self.storage.read_json(file_key)
                if session and session.get('user_id') == user_id:
                    # Only include summary info
                    sessions.append({
                        'session_id': session.get('session_id'),
                        'title': session.get('title'),
                        'created_at': session.get('created_at'),
                        'updated_at': session.get('updated_at'),
                        'message_count': len(session.get('messages', []))
                    })
            
            # Sort by updated_at descending
            sessions.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
            
            return sessions[:limit]
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return []
