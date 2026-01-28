"""Accessibility scan storage service using S3 JSON storage."""

import logging
import uuid as uuid_lib
from typing import Optional, Dict, Any
from datetime import datetime

from apps.core.services.s3_model_storage import S3ModelStorage

logger = logging.getLogger(__name__)


class AccessibilityScanStorageService(S3ModelStorage):
    """Storage service for accessibility scans using S3 JSON storage."""
    
    def __init__(self):
        """Initialize accessibility scan storage service."""
        super().__init__(model_name='accessibility_scans')
    
    def _extract_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata fields for scan index."""
        return {
            'uuid': data.get('uuid') or data.get('scan_id'),
            'scan_id': data.get('scan_id') or data.get('uuid'),
            'url': data.get('url', ''),
            'score': data.get('score', 0),
            'total_issues': data.get('total_issues', 0),
            'critical_issues': data.get('critical_issues', 0),
            'scanned_by': data.get('scanned_by'),  # UUID string
            'created_at': data.get('created_at', ''),
        }
    
    def create_scan(
        self,
        url: str,
        issues: Optional[list] = None,
        score: int = 0,
        scanned_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new accessibility scan."""
        scan_id = str(uuid_lib.uuid4())
        now = datetime.utcnow().isoformat()
        
        issues = issues or []
        total_issues = len(issues)
        critical_issues = len([i for i in issues if i.get('severity') == 'critical'])
        warning_issues = len([i for i in issues if i.get('severity') in ['serious', 'moderate']])
        info_issues = len([i for i in issues if i.get('severity') == 'minor'])
        
        scan_data = {
            'scan_id': scan_id,
            'url': url,
            'issues': issues,
            'score': score,
            'total_issues': total_issues,
            'critical_issues': critical_issues,
            'warning_issues': warning_issues,
            'info_issues': info_issues,
            'scanned_by': scanned_by,
            'created_at': now,
        }
        
        return self.create(scan_data, item_uuid=scan_id)
    
    def get_scan(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Get scan by ID."""
        return self.get(scan_id)
    
    def delete_scan(self, scan_id: str) -> bool:
        """Delete a scan."""
        return self.delete(scan_id)
