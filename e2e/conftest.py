"""
Pytest configuration for E2E tests.

Sets up fixtures and configuration for Playwright E2E tests.
"""

import pytest
from django.test import Client
from django.contrib.auth import get_user_model
from playwright.sync_api import Page, Browser, BrowserContext

User = get_user_model()


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Set up test database for E2E tests."""
    with django_db_blocker.unblock():
        # Create test user
        user = User.objects.create_user(
            username='e2e_test_user',
            email='e2e@test.com',
            password='e2e_test_password123'
        )
        yield
        # Cleanup
        User.objects.all().delete()


@pytest.fixture
def authenticated_client(django_db_setup):
    """Create authenticated Django test client."""
    client = Client()
    client.login(username='e2e_test_user', password='e2e_test_password123')
    return client


@pytest.fixture
def authenticated_page(page: Page, live_server_url: str):
    """
    Create authenticated Playwright page.
    
    Note: This assumes the app uses Django session authentication.
    You may need to adjust based on your authentication method.
    """
    # Navigate to login page
    page.goto(f"{live_server_url}/login/")
    
    # Fill login form
    page.fill('input[name="username"]', 'e2e_test_user')
    page.fill('input[name="password"]', 'e2e_test_password123')
    
    # Submit form
    page.click('button[type="submit"]')
    
    # Wait for navigation
    page.wait_for_url(f"{live_server_url}/**")
    
    return page


@pytest.fixture
def live_server_url(live_server):
    """Get live server URL."""
    return live_server.url
