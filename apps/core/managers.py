"""Custom managers and querysets for common query patterns."""
from django.contrib.auth.models import UserManager
from django.db import models
from django.utils import timezone
from datetime import timedelta
from typing import Optional


class BaseQuerySet(models.QuerySet):
    """Base queryset with common query methods."""
    
    def active(self):
        """Return only active objects."""
        return self.filter(is_active=True)
    
    def published(self):
        """Return only published objects (if model has published_at field)."""
        if hasattr(self.model, 'published_at'):
            return self.filter(
                published_at__lte=timezone.now(),
                is_active=True
            )
        return self.filter(is_active=True)
    
    def recent(self, days: int = 7):
        """Return objects created in the last N days."""
        cutoff = timezone.now() - timedelta(days=days)
        return self.filter(created_at__gte=cutoff)
    
    def by_created_date(self, order: str = 'desc'):
        """Order by created_at."""
        if order == 'desc':
            return self.order_by('-created_at')
        return self.order_by('created_at')
    
    def by_updated_date(self, order: str = 'desc'):
        """Order by updated_at."""
        if hasattr(self.model, 'updated_at'):
            if order == 'desc':
                return self.order_by('-updated_at')
            return self.order_by('updated_at')
        return self


class BaseManager(models.Manager):
    """Base manager using BaseQuerySet."""
    
    def get_queryset(self):
        return BaseQuerySet(self.model, using=self._db)
    
    def active(self):
        """Return only active objects."""
        return self.get_queryset().active()
    
    def published(self):
        """Return only published objects."""
        return self.get_queryset().published()
    
    def recent(self, days: int = 7):
        """Return objects created in the last N days."""
        return self.get_queryset().recent(days)
    
    def by_created_date(self, order: str = 'desc'):
        """Order by created_at."""
        return self.get_queryset().by_created_date(order)
    
    def by_updated_date(self, order: str = 'desc'):
        """Order by updated_at."""
        return self.get_queryset().by_updated_date(order)


class UserBaseManager(UserManager):
    """
    Auth-aware manager for the custom User model.

    Django's auth commands (e.g. createsuperuser) expect UserManager behavior
    including get_by_natural_key(). We also keep the common BaseQuerySet helpers.
    """

    def get_queryset(self):
        return BaseQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def published(self):
        return self.get_queryset().published()

    def recent(self, days: int = 7):
        return self.get_queryset().recent(days)

    def by_created_date(self, order: str = 'desc'):
        return self.get_queryset().by_created_date(order)

    def by_updated_date(self, order: str = 'desc'):
        return self.get_queryset().by_updated_date(order)
