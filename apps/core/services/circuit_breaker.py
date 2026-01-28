"""
Circuit Breaker Pattern Implementation for resilient service calls.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Callable, Optional, Dict, Any
from enum import Enum
from django.core.cache import cache

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, failing fast
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker implementation for resilient service calls.
    
    Prevents cascading failures by:
    - Opening circuit after failure threshold
    - Failing fast when circuit is open
    - Testing recovery with half-open state
    - Auto-closing when service recovers
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        success_threshold: int = 2
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Name of the circuit breaker (e.g., 'lambda_api', 's3_storage')
            failure_threshold: Number of failures before opening circuit
            timeout_seconds: Time to wait before trying half-open state
            success_threshold: Number of successes needed to close circuit from half-open
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.success_threshold = success_threshold
        self.cache_prefix = f"circuit_breaker:{name}:"
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception from function
        """
        state = self._get_state()
        
        if state == CircuitState.OPEN:
            # Check if timeout has passed
            if self._should_attempt_reset():
                self._set_state(CircuitState.HALF_OPEN)
                state = CircuitState.HALF_OPEN
                self.logger.info(f"Circuit breaker {self.name} entering half-open state")
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker {self.name} is OPEN. Service unavailable."
                )
        
        # Try to execute function
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise
    
    def _get_state(self) -> CircuitState:
        """Get current circuit breaker state."""
        state_key = f"{self.cache_prefix}state"
        state_str = cache.get(state_key, CircuitState.CLOSED.value)
        try:
            return CircuitState(state_str)
        except ValueError:
            return CircuitState.CLOSED
    
    def _set_state(self, state: CircuitState) -> None:
        """Set circuit breaker state."""
        state_key = f"{self.cache_prefix}state"
        cache.set(state_key, state.value, timeout=3600)  # 1 hour
    
    def _record_success(self) -> None:
        """Record a successful call."""
        current_state = self._get_state()
        
        if current_state == CircuitState.HALF_OPEN:
            # Count successes in half-open state
            success_key = f"{self.cache_prefix}half_open_successes"
            successes = cache.get(success_key, 0) + 1
            cache.set(success_key, successes, timeout=self.timeout_seconds)
            
            if successes >= self.success_threshold:
                # Close the circuit
                self._set_state(CircuitState.CLOSED)
                self._reset_counters()
                self.logger.info(f"Circuit breaker {self.name} CLOSED - service recovered")
        else:
            # Reset failure count on success
            self._reset_failure_count()
    
    def _record_failure(self) -> None:
        """Record a failed call."""
        current_state = self._get_state()
        
        if current_state == CircuitState.HALF_OPEN:
            # Failure in half-open state - open circuit again
            self._set_state(CircuitState.OPEN)
            self._set_opened_time()
            self.logger.warning(f"Circuit breaker {self.name} OPENED - service still failing")
        else:
            # Increment failure count
            failure_key = f"{self.cache_prefix}failures"
            failures = cache.get(failure_key, 0) + 1
            cache.set(failure_key, failures, timeout=self.timeout_seconds)
            
            if failures >= self.failure_threshold:
                # Open the circuit
                self._set_state(CircuitState.OPEN)
                self._set_opened_time()
                self.logger.warning(
                    f"Circuit breaker {self.name} OPENED after {failures} failures "
                    f"(threshold: {self.failure_threshold})"
                )
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        opened_time_key = f"{self.cache_prefix}opened_at"
        opened_time_str = cache.get(opened_time_key)
        
        if not opened_time_str:
            return True
        
        try:
            opened_time = datetime.fromisoformat(opened_time_str)
            elapsed = (datetime.now(timezone.utc) - opened_time).total_seconds()
            return elapsed >= self.timeout_seconds
        except Exception:
            return True
    
    def _set_opened_time(self) -> None:
        """Record when circuit was opened."""
        opened_time_key = f"{self.cache_prefix}opened_at"
        cache.set(
            opened_time_key,
            datetime.now(timezone.utc).isoformat(),
            timeout=self.timeout_seconds * 2
        )
    
    def _reset_failure_count(self) -> None:
        """Reset failure count."""
        failure_key = f"{self.cache_prefix}failures"
        cache.delete(failure_key)
    
    def _reset_counters(self) -> None:
        """Reset all counters."""
        self._reset_failure_count()
        success_key = f"{self.cache_prefix}half_open_successes"
        cache.delete(success_key)
        opened_time_key = f"{self.cache_prefix}opened_at"
        cache.delete(opened_time_key)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status."""
        state = self._get_state()
        failure_key = f"{self.cache_prefix}failures"
        failures = cache.get(failure_key, 0)
        
        status = {
            'name': self.name,
            'state': state.value,
            'failures': failures,
            'failure_threshold': self.failure_threshold,
            'timeout_seconds': self.timeout_seconds
        }
        
        if state == CircuitState.OPEN:
            opened_time_key = f"{self.cache_prefix}opened_at"
            opened_time_str = cache.get(opened_time_key)
            status['opened_at'] = opened_time_str
            if opened_time_str:
                try:
                    opened_time = datetime.fromisoformat(opened_time_str)
                    elapsed = (datetime.now(timezone.utc) - opened_time).total_seconds()
                    status['time_until_reset'] = max(0, self.timeout_seconds - elapsed)
                except Exception:
                    pass
        
        return status


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass
