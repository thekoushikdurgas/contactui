"""
Custom throttling classes for Django REST Framework.
"""

from rest_framework.throttling import UserRateThrottle, AnonRateThrottle, ScopedRateThrottle


class BurstRateThrottle(UserRateThrottle):
    """Throttle for burst requests (short-term rate limiting)."""
    scope = 'burst'


class SustainedRateThrottle(UserRateThrottle):
    """Throttle for sustained requests (long-term rate limiting)."""
    scope = 'sustained'


class AnonBurstRateThrottle(AnonRateThrottle):
    """Throttle for anonymous burst requests."""
    scope = 'anon_burst'


class AnonSustainedRateThrottle(AnonRateThrottle):
    """Throttle for anonymous sustained requests."""
    scope = 'anon_sustained'
