"""Core decorators package."""

from .auth import (
    require_appointment360_auth,
    require_super_admin,
    require_admin_or_super_admin,
)

__all__ = [
    'require_appointment360_auth',
    'require_super_admin',
    'require_admin_or_super_admin',
]
