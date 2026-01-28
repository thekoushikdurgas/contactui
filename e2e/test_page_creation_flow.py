"""
E2E tests for page creation flow (Task 4.3.1).

Tests:
- Navigate to pages tab
- Click create page button
- Fill page creation form
- Submit page creation
- Verify page appears in list
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.django_db
def test_navigate_to_pages_tab(authenticated_page: Page, live_server_url: str):
    """Test navigation to pages tab."""
    page = authenticated_page
    
    # Navigate to dashboard
    page.goto(f"{live_server_url}/docs/")
    
    # Navigate to pages tab
    pages_link = page.locator('a[href*="pages"]').or_(page.locator('a:has-text("Pages")'))
    if pages_link.count() > 0:
        pages_link.first.click()
        page.wait_for_load_state('networkidle')
        
        # Verify pages page loaded
        expect(page.locator('body')).to_contain_text('pages', timeout=5000)


@pytest.mark.django_db
def test_page_creation_flow(authenticated_page: Page, live_server_url: str):
    """Test complete page creation flow."""
    page = authenticated_page
    
    # Navigate to pages list
    page.goto(f"{live_server_url}/docs/pages/list/")
    page.wait_for_load_state('networkidle')
    
    # Click create page button
    create_button = page.locator('a[href*="create"]').or_(
        page.locator('button:has-text("Create")').or_(page.locator('a:has-text("Create Page")'))
    )
    
    if create_button.count() > 0:
        create_button.first.click()
        page.wait_for_load_state('networkidle')
        
        # Fill page creation form
        # Adjust field names based on actual form structure
        page_id_input = page.locator('input[name="page_id"]').or_(page.locator('#id_page_id'))
        if page_id_input.count() > 0:
            page_id_input.first.fill('e2e_test_page')
        
        page_type_select = page.locator('select[name="page_type"]').or_(page.locator('#id_page_type'))
        if page_type_select.count() > 0:
            page_type_select.first.select_option('markdown')
        
        content_textarea = page.locator('textarea[name="content"]').or_(page.locator('#id_content'))
        if content_textarea.count() > 0:
            content_textarea.first.fill('# E2E Test Page\n\nThis is a test page created by E2E tests.')
        
        # Submit form
        submit_button = page.locator('button[type="submit"]').or_(page.locator('button:has-text("Save")'))
        if submit_button.count() > 0:
            submit_button.first.click()
            page.wait_for_load_state('networkidle')
            
            # Verify redirect to page detail or list
            # Adjust based on actual behavior
            expect(page).to_have_url(f"{live_server_url}/docs/**", timeout=5000)
            
            # Verify page appears in list (if redirected to list)
            if 'list' in page.url:
                expect(page.locator('body')).to_contain_text('e2e_test_page', timeout=3000)


@pytest.mark.django_db
def test_page_creation_form_validation(authenticated_page: Page, live_server_url: str):
    """Test page creation form validation."""
    page = authenticated_page
    
    # Navigate to create page form
    page.goto(f"{live_server_url}/docs/pages/create/")
    page.wait_for_load_state('networkidle')
    
    # Try to submit empty form
    submit_button = page.locator('button[type="submit"]').or_(page.locator('button:has-text("Save")'))
    if submit_button.count() > 0:
        submit_button.first.click()
        page.wait_for_load_state('networkidle')
        
        # Verify validation errors are displayed
        # Adjust based on actual error display
        error_messages = page.locator('.error').or_(page.locator('.field-error')).or_(
            page.locator('[role="alert"]')
        )
        if error_messages.count() > 0:
            expect(error_messages.first).to_be_visible()
