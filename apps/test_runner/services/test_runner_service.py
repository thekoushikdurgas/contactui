"""Test Runner service."""
import logging
import subprocess
import os
from typing import Optional, Dict, Any, List
from django.utils import timezone
from apps.core.services.base_service import BaseService
from .test_storage_service import TestSuiteStorageService

logger = logging.getLogger(__name__)


class TestRunnerService(BaseService):
    """Service for test execution using S3 storage."""
    
    def __init__(self):
        """Initialize test runner service."""
        super().__init__('TestRunnerService')
        self.storage = TestSuiteStorageService()
    
    def run_tests(
        self,
        suite_id: str,
        test_files: List[str] = None,
        user=None
    ) -> Dict[str, Any]:
        """
        Run tests for a test suite.
        
        Args:
            suite_id: Test suite ID
            test_files: Optional list of specific test files to run
            user: User UUID running the tests
            
        Returns:
            Created test run data dictionary
        """
        suite = self.storage.get_suite(suite_id)
        if not suite:
            self.logger.error(f"Test suite not found: {suite_id}")
            raise ValueError(f"Test suite not found: {suite_id}")
        
        # Convert user to UUID string if needed
        user_uuid = None
        if user:
            if hasattr(user, 'uuid'):
                user_uuid = str(user.uuid)
            elif hasattr(user, 'id'):
                user_uuid = str(user.id)
            else:
                user_uuid = str(user)
        
        # Update suite status
        self.storage.update_suite(suite_id, status='running')
        
        # Run tests (placeholder - would execute actual test framework)
        # In production, this would use pytest, unittest, jest, etc.
        files_to_run = test_files or suite.get('test_files', []) or []
        
        # Simulate test execution
        results = self._execute_tests(files_to_run)
        
        # Create test run
        test_run = self.storage.create_run(
            suite_id=suite_id,
            started_by=user_uuid,
            status='running',
            started_at=timezone.now().isoformat()
        )
        
        # Update test run with results
        run_status = 'completed' if results.get('failed', 0) == 0 else 'failed'
        test_run = self.storage.update_run(
            test_run.get('run_id'),
            status=run_status,
            results=results,
            passed=results.get('passed', 0),
            failed=results.get('failed', 0),
            skipped=results.get('skipped', 0),
            total=results.get('total', 0),
            completed_at=timezone.now().isoformat()
        )
        
        # Update suite status
        self.storage.update_suite(suite_id, status=run_status)
        
        self.logger.info(f"Test run completed: {test_run.get('run_id')}")
        return test_run
    
    def _execute_tests(self, test_files: List[str]) -> Dict[str, Any]:
        """
        Execute test files (placeholder implementation).
        
        Args:
            test_files: List of test file paths
            
        Returns:
            Test results dictionary
        """
        # Placeholder - in production would execute actual test framework
        # This is a simplified version
        results = {
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'total': 0,
            'tests': []
        }
        
        for test_file in test_files:
            if os.path.exists(test_file):
                # Simulate test execution
                results['total'] += 1
                results['passed'] += 1
                results['tests'].append({
                    'file': test_file,
                    'status': 'passed',
                    'duration': 0.5
                })
        
        return results
    
    def get_results(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Get test run results.
        
        Args:
            run_id: Test run ID
            
        Returns:
            Test run data dictionary, or None if not found
        """
        # Find test run in test suites
        suites_result = self.storage.list(filters={}, limit=None, offset=0)
        
        for suite in suites_result.get('items', []):
            runs = suite.get('runs', [])
            for run_data in runs:
                if run_data.get('run_id') == run_id or run_data.get('id') == run_id:
                    return run_data
        
        return None
    
    def list_suites(
        self,
        user=None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List test suites.
        
        Args:
            user: Filter by user UUID (optional)
            limit: Maximum number of suites
            offset: Offset for pagination
            
        Returns:
            List of test suite data dictionaries
        """
        # Convert user to UUID string if needed
        user_uuid = None
        if user:
            if hasattr(user, 'uuid'):
                user_uuid = str(user.uuid)
            elif hasattr(user, 'id'):
                user_uuid = str(user.id)
            else:
                user_uuid = str(user)
        
        filters = {}
        if user_uuid:
            filters['created_by'] = user_uuid
        
        result = self.storage.list(filters=filters, limit=limit, offset=offset, order_by='created_at', reverse=True)
        return result.get('items', [])
