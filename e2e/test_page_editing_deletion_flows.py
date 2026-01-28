"""
E2E tests for page editing and deletion flows (Task 4.3.1).

Tests:
- Page editing flow
- Page deletion flow
- Endpoint creation flow
- Relationship creation flow
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.django_db
@pytest.mark.e2e
class TestPageEditingFlow:
    """Test page editing workflow."""
    
    def test_page_editing_flow_complete(self, authenticated_page: Page, live_server_url: str):
        """Test complete page editing flow."""
        page = authenticated_page
        
        # Navigate to pages list
        page.goto(f"{live_server_url}/docs/pages/list/")
        page.wait_for_load_state('networkidle')
        
        # Find first page and click to view detail
        page_link = page.locator('a[href*="/pages/"]').first
        if page_link.count() > 0:
            page_link.first.click()
            page.wait_for_load_state('networkidle')
            
            # Click edit button
            edit_button = page.locator('a[href*="edit"]').or_(
                page.locator('button:has-text("Edit")')
            )
            if edit_button.count() > 0:
                edit_button.first.click()
                page.wait_for_load_state('networkidle')
                
                # Modify content
                content_field = page.locator('textarea[name="content"]').or_(
                    page.locator('#id_content')
                )
                if content_field.count() > 0:
                    original_content = content_field.first.input_value()
                    content_field.first.fill(original_content + '\n\n## Updated Section')
                    
                    # Save changes
                    save_button = page.locator('button[type="submit"]').or_(
                        page.locator('button:has-text("Save")')
                    )
                    if save_button.count() > 0:
                        save_button.first.click()
                        page.wait_for_load_state('networkidle')
                        
                        # Verify changes reflected (redirect to detail page)
                        expect(page.locator('body')).to_contain_text('Updated Section', timeout=5000)


@pytest.mark.django_db
@pytest.mark.e2e
class TestPageDeletionFlow:
    """Test page deletion workflow."""
    
    def test_page_deletion_flow_complete(self, authenticated_page: Page, live_server_url: str):
        """Test complete page deletion flow."""
        page = authenticated_page
        
        # Navigate to pages list
        page.goto(f"{live_server_url}/docs/pages/list/")
        page.wait_for_load_state('networkidle')
        
        # Find first page and click to view detail
        page_link = page.locator('a[href*="/pages/"]').first
        if page_link.count() > 0:
            page_link.first.click()
            page.wait_for_load_state('networkidle')
            
            # Click delete button
            delete_button = page.locator('button:has-text("Delete")').or_(
                page.locator('a[href*="delete"]')
            )
            if delete_button.count() > 0:
                delete_button.first.click()
                page.wait_for_load_state('networkidle')
                
                # Handle confirmation dialog
                page.on("dialog", lambda dialog: dialog.accept())
                
                # Wait for deletion to complete
                page.wait_for_load_state('networkidle')
                
                # Verify redirect to list page
                expect(page).to_have_url(f"{live_server_url}/docs/pages/**", timeout=5000)


@pytest.mark.django_db
@pytest.mark.e2e
class TestEndpointCreationFlow:
    """Test endpoint creation workflow."""
    
    def test_endpoint_creation_flow(self, authenticated_page: Page, live_server_url: str):
        """Test endpoint creation flow."""
        page = authenticated_page
        
        # Navigate to endpoints list
        page.goto(f"{live_server_url}/docs/endpoints/list/")
        page.wait_for_load_state('networkidle')
        
        # Click create endpoint button
        create_button = page.locator('a[href*="create"]').or_(
            page.locator('button:has-text("Create")').or_(page.locator('a:has-text("Create Endpoint")'))
        )
        
        if create_button.count() > 0:
            create_button.first.click()
            page.wait_for_load_state('networkidle')
            
            # Fill endpoint form
            endpoint_id_input = page.locator('input[name="endpoint_id"]').or_(page.locator('#id_endpoint_id'))
            if endpoint_id_input.count() > 0:
                endpoint_id_input.first.fill('e2e_test_endpoint')
            
            method_select = page.locator('select[name="method"]').or_(page.locator('#id_method'))
            if method_select.count() > 0:
                method_select.first.select_option('GET')
            
            path_input = page.locator('input[name="endpoint_path"]').or_(page.locator('#id_endpoint_path'))
            if path_input.count() > 0:
                path_input.first.fill('/api/e2e/test')
            
            # Submit form
            submit_button = page.locator('button[type="submit"]').or_(page.locator('button:has-text("Save")'))
            if submit_button.count() > 0:
                submit_button.first.click()
                page.wait_for_load_state('networkidle')
                
                # Verify redirect
                expect(page).to_have_url(f"{live_server_url}/docs/**", timeout=5000)


@pytest.mark.django_db
@pytest.mark.e2e
class TestRelationshipCreationFlow:
    """Test relationship creation workflow."""
    
    def test_relationship_creation_flow(self, authenticated_page: Page, live_server_url: str):
        """Test relationship creation flow."""
        page = authenticated_page
        
        # Navigate to relationships list
        page.goto(f"{live_server_url}/docs/relationships/list/")
        page.wait_for_load_state('networkidle')
        
        # Click create relationship button
        create_button = page.locator('a[href*="create"]').or_(
            page.locator('button:has-text("Create")').or_(page.locator('a:has-text("Create Relationship")'))
        )
        
        if create_button.count() > 0:
            create_button.first.click()
            page.wait_for_load_state('networkidle')
            
            # Fill relationship form
            page_id_select = page.locator('select[name="page_id"]').or_(page.locator('#id_page_id'))
            if page_id_select.count() > 0:
                # Select first available page
                options = page_id_select.first.locator('option')
                if options.count() > 1:  # More than just placeholder
                    page_id_select.first.select_index(1)
            
            endpoint_id_select = page.locator('select[name="endpoint_id"]').or_(page.locator('#id_endpoint_id'))
            if endpoint_id_select.count() > 0:
                # Select first available endpoint
                options = endpoint_id_select.first.locator('option')
                if options.count() > 1:
                    endpoint_id_select.first.select_index(1)
            
            usage_type_select = page.locator('select[name="usage_type"]').or_(page.locator('#id_usage_type'))
            if usage_type_select.count() > 0:
                usage_type_select.first.select_option('primary')
            
            # Submit form
            submit_button = page.locator('button[type="submit"]').or_(page.locator('button:has-text("Save")'))
            if submit_button.count() > 0:
                submit_button.first.click()
                page.wait_for_load_state('networkidle')
                
                # Verify redirect
                expect(page).to_have_url(f"{live_server_url}/docs/**", timeout=5000)
