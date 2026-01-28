"""
Centralized API throttling configuration.

This module provides common throttling classes for all APIs.
"""

from apps.core.throttles import (
    BurstRateThrottle,
    SustainedRateThrottle,
    AnonBurstRateThrottle,
    AnonSustainedRateThrottle,
)

__all__ = [
    'BurstRateThrottle',
    'SustainedRateThrottle',
    'AnonBurstRateThrottle',
    'AnonSustainedRateThrottle',
]
