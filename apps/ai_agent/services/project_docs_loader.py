"""Project documentation loader service."""

import logging
from typing import List, Dict, Any, Optional
from apps.ai_agent.services.media_loader import MediaFileLoaderService

logger = logging.getLogger(__name__)


class ProjectDocsLoader:
    """Service for loading project documentation."""
    
    def __init__(self, media_loader: MediaFileLoaderService):
        """Initialize project docs loader.
        
        Args:
            media_loader: MediaFileLoaderService instance
        """
        self.media_loader = media_loader
        logger.info("ProjectDocsLoader initialized")
    
    def load_all_docs(self) -> List[Dict[str, Any]]:
        """Load all project documentation.
        
        Returns:
            List of documentation files with content
        """
        return self.media_loader.load_project_docs()
    
    def get_architecture_overview(self) -> Optional[str]:
        """Get architecture overview from project docs.
        
        Returns:
            Architecture overview text, or None if not found
        """
        docs = self.load_all_docs()
        for doc in docs:
            file_name = doc.get('file', '')
            if 'architecture' in file_name.lower() or 'ARCHITECTURE' in file_name:
                return doc.get('content', '')
        return None
    
    def get_readme(self) -> Optional[str]:
        """Get README content.
        
        Returns:
            README content, or None if not found
        """
        docs = self.load_all_docs()
        for doc in docs:
            file_name = doc.get('file', '')
            if 'readme' in file_name.lower():
                return doc.get('content', '')
        return None
