"""
Pytest configuration and fixtures for knowledge tests.
"""

import pytest
from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def client():
    """Django test client fixture."""
    return Client()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def authenticated_client(client, user):
    """Authenticated test client fixture."""
    client.force_login(user)
    return client
