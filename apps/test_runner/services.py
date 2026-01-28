"""Test Runner service."""
import logging
import subprocess
import os
from typing import Optional, Dict, Any, List
from django.utils import timezone
from apps.core.services.base_service import BaseService
from .models import TestSuite, TestRun

logger = logging.getLogger(__name__)


class TestRunnerService(BaseService):
    """Service for test execution."""
    
    def __init__(self):
        """Initialize test runner service."""
        super().__init__('TestRunnerService')
    
    def run_tests(
        self,
        suite_id: str,
        test_files: List[str] = None,
        user=None
    ) -> TestRun:
        """
        Run tests for a test suite.
        
        Args:
            suite_id: Test suite ID
            test_files: Optional list of specific test files to run
            user: User running the tests
            
        Returns:
            Created TestRun instance
        """
        try:
            import uuid
            suite_uuid = uuid.UUID(suite_id) if isinstance(suite_id, str) else suite_id
            suite = TestSuite.objects.get(suite_id=suite_uuid)
            
            # Create test run
            test_run = TestRun.objects.create(
                suite=suite,
                status='running',
                started_by=user,
                started_at=timezone.now()
            )
            
            # Update suite status
            suite.status = 'running'
            suite.save()
            
            # Run tests (placeholder - would execute actual test framework)
            # In production, this would use pytest, unittest, jest, etc.
            files_to_run = test_files or suite.test_files or []
            
            # Simulate test execution
            results = self._execute_tests(files_to_run)
            
            # Update test run with results
            test_run.status = 'completed' if results.get('failed', 0) == 0 else 'failed'
            test_run.results = results
            test_run.passed = results.get('passed', 0)
            test_run.failed = results.get('failed', 0)
            test_run.skipped = results.get('skipped', 0)
            test_run.total = results.get('total', 0)
            test_run.completed_at = timezone.now()
            test_run.save()
            
            # Update suite status
            suite.status = test_run.status
            suite.save()
            
            self.logger.info(f"Test run completed: {test_run.run_id}")
            return test_run
        except TestSuite.DoesNotExist:
            self.logger.error(f"Test suite not found: {suite_id}")
            raise ValueError(f"Test suite not found: {suite_id}")
        except Exception as e:
            self.logger.error(f"Error running tests: {e}", exc_info=True)
            raise
    
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
    
    def get_results(self, run_id: str) -> Optional[TestRun]:
        """
        Get test run results.
        
        Args:
            run_id: Test run ID
            
        Returns:
            TestRun instance, or None if not found
        """
        try:
            import uuid
            run_uuid = uuid.UUID(run_id) if isinstance(run_id, str) else run_id
            return TestRun.objects.get(run_id=run_uuid)
        except (TestRun.DoesNotExist, ValueError):
            return None
    
    def list_suites(
        self,
        user=None,
        limit: int = 50,
        offset: int = 0
    ) -> List[TestSuite]:
        """
        List test suites.
        
        Args:
            user: Filter by user (optional)
            limit: Maximum number of suites
            offset: Offset for pagination
            
        Returns:
            List of TestSuite instances
        """
        queryset = TestSuite.objects.all()
        if user:
            queryset = queryset.filter(created_by=user)
        
        queryset = queryset.select_related('created_by')
        queryset = queryset.order_by('-created_at')
        
        return list(queryset[offset:offset + limit])
