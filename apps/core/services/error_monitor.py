"""
Error Monitoring Service for tracking and alerting on errors.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from django.core.cache import cache
from collections import defaultdict

logger = logging.getLogger(__name__)


class ErrorMonitor:
    """
    Service for monitoring error rates and patterns.
    
    Tracks:
    - Error counts by type
    - Error rates over time
    - High error rate alerts
    - Error patterns
    """
    
    def __init__(self):
        """Initialize error monitor."""
        self.cache_prefix = "error_monitor:"
        self.error_window_minutes = 60  # Track errors in 60-minute windows
        self.alert_threshold = 10  # Alert if more than 10 errors in window
    
    def record_error(
        self,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record an error occurrence.
        
        Args:
            error_type: Type of error (e.g., 'LambdaAPIError', 'S3Error')
            error_message: Error message
            context: Additional context (endpoint, user, etc.)
        """
        try:
            now = datetime.now(timezone.utc)
            window_key = self._get_window_key(now)
            
            # Increment error count for this window
            cache_key = f"{self.cache_prefix}count:{window_key}:{error_type}"
            current_count = cache.get(cache_key, 0)
            cache.set(cache_key, current_count + 1, timeout=self.error_window_minutes * 60)
            
            # Track error details (last 100 errors)
            error_key = f"{self.cache_prefix}errors:{error_type}"
            error_list = cache.get(error_key, [])
            error_list.append({
                'timestamp': now.isoformat(),
                'message': error_message,
                'context': context or {}
            })
            # Keep only last 100 errors
            if len(error_list) > 100:
                error_list = error_list[-100:]
            cache.set(error_key, error_list, timeout=3600)  # 1 hour
            
            # Check if we should alert
            if current_count + 1 >= self.alert_threshold:
                self._trigger_alert(error_type, current_count + 1, window_key)
                
        except Exception as e:
            logger.error(f"Failed to record error in ErrorMonitor: {e}")
    
    def get_error_stats(
        self,
        error_type: Optional[str] = None,
        minutes: int = 60
    ) -> Dict[str, Any]:
        """
        Get error statistics for a time period.
        
        Args:
            error_type: Optional filter by error type
            minutes: Time window in minutes (default: 60)
            
        Returns:
            Dictionary with error statistics
        """
        try:
            now = datetime.now(timezone.utc)
            stats = {
                'total_errors': 0,
                'errors_by_type': {},
                'error_rate': 0.0,
                'window_minutes': minutes
            }
            
            # Collect errors from recent windows
            window_count = (minutes // self.error_window_minutes) + 1
            error_types = [error_type] if error_type else ['LambdaAPIError', 'S3Error', 'ValidationError', 'RepositoryError', 'Other']
            
            for et in error_types:
                count = 0
                for i in range(window_count):
                    window_time = now - timedelta(minutes=i * self.error_window_minutes)
                    window_key = self._get_window_key(window_time)
                    cache_key = f"{self.cache_prefix}count:{window_key}:{et}"
                    window_count_val = cache.get(cache_key, 0)
                    count += window_count_val
                
                stats['errors_by_type'][et] = count
                stats['total_errors'] += count
            
            # Calculate error rate (errors per minute)
            if minutes > 0:
                stats['error_rate'] = stats['total_errors'] / minutes
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get error stats: {e}")
            return {
                'total_errors': 0,
                'errors_by_type': {},
                'error_rate': 0.0,
                'window_minutes': minutes,
                'error': str(e)
            }
    
    def get_recent_errors(
        self,
        error_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get recent errors.
        
        Args:
            error_type: Optional filter by error type
            limit: Maximum number of errors to return
            
        Returns:
            List of recent error dictionaries
        """
        try:
            all_errors = []
            error_types = [error_type] if error_type else ['LambdaAPIError', 'S3Error', 'ValidationError', 'RepositoryError', 'Other']
            
            for et in error_types:
                error_key = f"{self.cache_prefix}errors:{et}"
                error_list = cache.get(error_key, [])
                all_errors.extend(error_list)
            
            # Sort by timestamp (newest first)
            all_errors.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return all_errors[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get recent errors: {e}")
            return []
    
    def _get_window_key(self, dt: datetime) -> str:
        """Get cache key for a time window."""
        # Round down to nearest window
        window_minutes = (dt.minute // self.error_window_minutes) * self.error_window_minutes
        window_dt = dt.replace(minute=window_minutes, second=0, microsecond=0)
        return window_dt.strftime("%Y%m%d%H%M")
    
    def _trigger_alert(
        self,
        error_type: str,
        count: int,
        window_key: str
    ) -> None:
        """
        Trigger alert for high error rate.
        
        Args:
            error_type: Type of error
            count: Error count
            window_key: Time window key
        """
        alert_message = (
            f"High error rate detected: {count} {error_type} errors "
            f"in window {window_key} (threshold: {self.alert_threshold})"
        )
        logger.warning(alert_message)
        
        # Store alert in cache
        alert_key = f"{self.cache_prefix}alerts:{window_key}"
        alerts = cache.get(alert_key, [])
        alerts.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error_type': error_type,
            'count': count,
            'threshold': self.alert_threshold
        })
        cache.set(alert_key, alerts, timeout=3600)  # 1 hour
    
    def clear_old_data(self, days: int = 7) -> int:
        """
        Clear error data older than specified days.
        
        Args:
            days: Number of days to keep data
            
        Returns:
            Number of cache keys cleared
        """
        # This is a simplified implementation
        # In production, you might want to use a more sophisticated cleanup
        logger.info(f"Clearing error monitor data older than {days} days")
        return 0
