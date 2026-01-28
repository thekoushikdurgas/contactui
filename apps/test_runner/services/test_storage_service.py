"""Test storage service using S3 JSON storage."""

import logging
import uuid as uuid_lib
from typing import Optional, Dict, Any, List
from datetime import datetime

from apps.core.services.s3_model_storage import S3ModelStorage

logger = logging.getLogger(__name__)


class TestSuiteStorageService(S3ModelStorage):
    """Storage service for test suites using S3 JSON storage."""
    
    def __init__(self):
        """Initialize test suite storage service."""
        super().__init__(model_name='test_suites')
    
    def _extract_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata fields for test suite index."""
        return {
            'uuid': data.get('uuid') or data.get('suite_id'),
            'suite_id': data.get('suite_id') or data.get('uuid'),
            'name': data.get('name', ''),
            'status': data.get('status', 'pending'),
            'created_by': data.get('created_by'),  # UUID string
            'created_at': data.get('created_at', ''),
            'updated_at': data.get('updated_at', ''),
        }
    
    def create_suite(
        self,
        name: str,
        description: str = '',
        test_files: Optional[List[str]] = None,
        created_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new test suite."""
        suite_id = str(uuid_lib.uuid4())
        now = datetime.utcnow().isoformat()
        
        suite_data = {
            'suite_id': suite_id,
            'name': name,
            'description': description,
            'test_files': test_files or [],
            'status': 'pending',
            'created_by': created_by,
            'created_at': now,
            'updated_at': now,
            'runs': [],  # Test runs stored as nested list
        }
        
        return self.create(suite_data, item_uuid=suite_id)
    
    def get_suite(self, suite_id: str) -> Optional[Dict[str, Any]]:
        """Get test suite by ID."""
        return self.get(suite_id)
    
    def update_suite(self, suite_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Update a test suite."""
        return self.update(suite_id, kwargs)
    
    def delete_suite(self, suite_id: str) -> bool:
        """Delete a test suite."""
        return self.delete(suite_id)
    
    def create_run(
        self,
        suite_id: str,
        started_by: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a new test run for a suite."""
        suite = self.get_suite(suite_id)
        if not suite:
            return None
        
        run_id = str(uuid_lib.uuid4())
        now = datetime.utcnow().isoformat()
        
        run_data = {
            'run_id': run_id,
            'status': 'pending',
            'results': {},
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'total': 0,
            'started_by': started_by,
            'started_at': None,
            'completed_at': None,
            'created_at': now,
        }
        
        # Add run to suite's runs list
        runs = suite.get('runs', [])
        runs.append(run_data)
        
        # Update suite status
        updated_suite = self.update_suite(suite_id, {
            'runs': runs,
            'status': 'running' if suite.get('status') == 'pending' else suite.get('status')
        })
        
        return run_data if updated_suite else None
    
    def update_run(
        self,
        suite_id: str,
        run_id: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Update a test run."""
        suite = self.get_suite(suite_id)
        if not suite:
            return None
        
        runs = suite.get('runs', [])
        run_found = False
        
        for i, run in enumerate(runs):
            if run.get('run_id') == run_id:
                # Handle status timestamp updates
                if 'status' in kwargs:
                    if kwargs['status'] == 'running' and not run.get('started_at'):
                        kwargs['started_at'] = datetime.utcnow().isoformat()
                    elif kwargs['status'] in ['completed', 'failed', 'cancelled'] and not run.get('completed_at'):
                        kwargs['completed_at'] = datetime.utcnow().isoformat()
                
                runs[i] = {**run, **kwargs}
                run_found = True
                break
        
        if not run_found:
            return None
        
        # Update suite status based on latest run
        latest_run = runs[-1] if runs else None
        suite_status = suite.get('status', 'pending')
        if latest_run:
            run_status = latest_run.get('status', 'pending')
            if run_status in ['completed', 'failed']:
                suite_status = run_status
        
        return self.update_suite(suite_id, {
            'runs': runs,
            'status': suite_status
        })
    
    def get_runs(self, suite_id: str) -> List[Dict[str, Any]]:
        """Get all runs for a test suite."""
        suite = self.get_suite(suite_id)
        if not suite:
            return []
        return suite.get('runs', [])
