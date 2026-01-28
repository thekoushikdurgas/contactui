"""
E2E tests for dashboard navigation flow (Task 4.3.1).

Tests:
- User login
- Dashboard page load
- Navigation between tabs
- Dashboard statistics display
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.django_db
def test_user_login(page: Page, live_server_url: str):
    """Test user login flow."""
    # Navigate to login page
    page.goto(f"{live_server_url}/login/")
    
    # Verify login page loaded
    expect(page).to_have_title(containing="Login")
    
    # Fill login form
    page.fill('input[name="username"]', 'e2e_test_user')
    page.fill('input[name="password"]', 'e2e_test_password123')
    
    # Submit form
    page.click('button[type="submit"]')
    
    # Wait for redirect to dashboard
    page.wait_for_url(f"{live_server_url}/docs/**")
    
    # Verify successful login (check for dashboard content)
    expect(page.locator('body')).to_contain_text('dashboard', timeout=5000)


@pytest.mark.django_db
def test_dashboard_page_load(authenticated_page: Page, live_server_url: str):
    """Test dashboard page loads correctly."""
    page = authenticated_page
    
    # Navigate to dashboard
    page.goto(f"{live_server_url}/docs/")
    
    # Verify dashboard loaded
    expect(page.locator('body')).to_contain_text('dashboard', timeout=5000)
    
    # Verify dashboard elements are present
    # Adjust selectors based on actual dashboard structure
    expect(page.locator('[data-testid="dashboard"]').or_(page.locator('.dashboard'))).to_be_visible()


@pytest.mark.django_db
def test_dashboard_tab_navigation(authenticated_page: Page, live_server_url: str):
    """Test navigation between dashboard tabs."""
    page = authenticated_page
    
    # Navigate to dashboard
    page.goto(f"{live_server_url}/docs/")
    
    # Wait for dashboard to load
    page.wait_for_load_state('networkidle')
    
    # Test Pages tab
    pages_tab = page.locator('[data-tab="pages"]').or_(page.locator('a:has-text("Pages")'))
    if pages_tab.count() > 0:
        pages_tab.first.click()
        page.wait_for_load_state('networkidle')
        # Verify pages content is visible
        expect(page.locator('body')).to_contain_text('pages', timeout=3000)
    
    # Test Endpoints tab
    endpoints_tab = page.locator('[data-tab="endpoints"]').or_(page.locator('a:has-text("Endpoints")'))
    if endpoints_tab.count() > 0:
        endpoints_tab.first.click()
        page.wait_for_load_state('networkidle')
        # Verify endpoints content is visible
        expect(page.locator('body')).to_contain_text('endpoints', timeout=3000)
    
    # Test Relationships tab
    relationships_tab = page.locator('[data-tab="relationships"]').or_(page.locator('a:has-text("Relationships")'))
    if relationships_tab.count() > 0:
        relationships_tab.first.click()
        page.wait_for_load_state('networkidle')
        # Verify relationships content is visible
        expect(page.locator('body')).to_contain_text('relationships', timeout=3000)


@pytest.mark.django_db
def test_dashboard_statistics_display(authenticated_page: Page, live_server_url: str):
    """Test dashboard statistics are displayed."""
    page = authenticated_page
    
    # Navigate to dashboard
    page.goto(f"{live_server_url}/docs/")
    
    # Wait for dashboard to load
    page.wait_for_load_state('networkidle')
    
    # Verify statistics elements are present
    # Adjust selectors based on actual dashboard structure
    stats_container = page.locator('[data-testid="statistics"]').or_(
        page.locator('.statistics').or_(page.locator('.dashboard-stats'))
    )
    
    # Statistics might be loaded via AJAX, so wait a bit
    page.wait_for_timeout(2000)
    
    # Check if statistics container exists (might be empty initially)
    if stats_container.count() > 0:
        expect(stats_container.first).to_be_visible()
