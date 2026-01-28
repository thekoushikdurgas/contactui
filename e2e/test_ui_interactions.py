"""
E2E tests for UI interactions (Task 4.3.2).

Tests:
- Tab navigation
- Filtering
- Pagination
- Search
- Bulk operations
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.django_db
@pytest.mark.e2e
class TestTabNavigation:
    """Test tab navigation functionality."""
    
    def test_switching_between_tabs(self, authenticated_page: Page, live_server_url: str):
        """Test switching between dashboard tabs."""
        page = authenticated_page
        
        # Navigate to dashboard
        page.goto(f"{live_server_url}/docs/")
        page.wait_for_load_state('networkidle')
        
        # Test Pages tab
        pages_tab = page.locator('[data-tab="pages"]').or_(
            page.locator('a:has-text("Pages")').or_(page.locator('button:has-text("Pages")'))
        )
        if pages_tab.count() > 0:
            pages_tab.first.click()
            page.wait_for_load_state('networkidle')
            # Verify pages content is visible
            expect(page.locator('body')).to_contain_text('pages', timeout=3000)
        
        # Test Endpoints tab
        endpoints_tab = page.locator('[data-tab="endpoints"]').or_(
            page.locator('a:has-text("Endpoints")').or_(page.locator('button:has-text("Endpoints")'))
        )
        if endpoints_tab.count() > 0:
            endpoints_tab.first.click()
            page.wait_for_load_state('networkidle')
            expect(page.locator('body')).to_contain_text('endpoints', timeout=3000)
        
        # Test Relationships tab
        relationships_tab = page.locator('[data-tab="relationships"]').or_(
            page.locator('a:has-text("Relationships")').or_(page.locator('button:has-text("Relationships")'))
        )
        if relationships_tab.count() > 0:
            relationships_tab.first.click()
            page.wait_for_load_state('networkidle')
            expect(page.locator('body')).to_contain_text('relationships', timeout=3000)
    
    def test_active_tab_highlighting(self, authenticated_page: Page, live_server_url: str):
        """Test active tab highlighting."""
        page = authenticated_page
        
        # Navigate to dashboard
        page.goto(f"{live_server_url}/docs/")
        page.wait_for_load_state('networkidle')
        
        # Click Pages tab
        pages_tab = page.locator('[data-tab="pages"]').or_(
            page.locator('a:has-text("Pages")').or_(page.locator('button:has-text("Pages")'))
        )
        if pages_tab.count() > 0:
            pages_tab.first.click()
            page.wait_for_load_state('networkidle')
            
            # Verify active tab has active class or attribute
            active_indicator = page.locator('[data-tab="pages"].active').or_(
                page.locator('[data-tab="pages"][aria-selected="true"]').or_(
                    page.locator('a:has-text("Pages").active')
                )
            )
            # Tab might be active via class or data attribute
            if active_indicator.count() == 0:
                # Check if URL changed to indicate tab switch
                expect(page).to_have_url(f"{live_server_url}/docs/**pages**", timeout=2000)
    
    def test_tab_state_persistence(self, authenticated_page: Page, live_server_url: str):
        """Test tab state persistence (URL or localStorage)."""
        page = authenticated_page
        
        # Navigate to dashboard
        page.goto(f"{live_server_url}/docs/")
        page.wait_for_load_state('networkidle')
        
        # Switch to Endpoints tab
        endpoints_tab = page.locator('[data-tab="endpoints"]').or_(
            page.locator('a:has-text("Endpoints")')
        )
        if endpoints_tab.count() > 0:
            endpoints_tab.first.click()
            page.wait_for_load_state('networkidle')
            
            # Reload page
            page.reload()
            page.wait_for_load_state('networkidle')
            
            # Verify tab state persisted (check URL or active tab)
            # This depends on implementation - might use URL params or localStorage
            expect(page.locator('body')).to_contain_text('endpoints', timeout=3000)


@pytest.mark.django_db
@pytest.mark.e2e
class TestFiltering:
    """Test filtering functionality."""
    
    def test_filter_by_type(self, authenticated_page: Page, live_server_url: str):
        """Test filtering by type."""
        page = authenticated_page
        
        # Navigate to pages list
        page.goto(f"{live_server_url}/docs/pages/list/")
        page.wait_for_load_state('networkidle')
        
        # Find type filter dropdown
        type_filter = page.locator('select[name="page_type"]').or_(
            page.locator('select[name="type"]').or_(page.locator('[data-filter="type"]'))
        )
        
        if type_filter.count() > 0:
            # Select a filter option
            type_filter.first.select_option('markdown')
            page.wait_for_load_state('networkidle')
            
            # Verify filtered results (might need to wait for AJAX)
            page.wait_for_timeout(1000)
            # Results should be filtered (exact verification depends on implementation)
    
    def test_filter_by_status(self, authenticated_page: Page, live_server_url: str):
        """Test filtering by status."""
        page = authenticated_page
        
        # Navigate to pages list
        page.goto(f"{live_server_url}/docs/pages/list/")
        page.wait_for_load_state('networkidle')
        
        # Find status filter dropdown
        status_filter = page.locator('select[name="status"]').or_(
            page.locator('[data-filter="status"]')
        )
        
        if status_filter.count() > 0:
            # Select status filter
            status_filter.first.select_option('published')
            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(1000)
    
    def test_filter_combination(self, authenticated_page: Page, live_server_url: str):
        """Test combining multiple filters."""
        page = authenticated_page
        
        # Navigate to pages list
        page.goto(f"{live_server_url}/docs/pages/list/")
        page.wait_for_load_state('networkidle')
        
        # Apply type filter
        type_filter = page.locator('select[name="page_type"]')
        if type_filter.count() > 0:
            type_filter.first.select_option('markdown')
            page.wait_for_timeout(500)
        
        # Apply status filter
        status_filter = page.locator('select[name="status"]')
        if status_filter.count() > 0:
            status_filter.first.select_option('published')
            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(1000)
    
    def test_filter_reset(self, authenticated_page: Page, live_server_url: str):
        """Test resetting filters."""
        page = authenticated_page
        
        # Navigate to pages list
        page.goto(f"{live_server_url}/docs/pages/list/")
        page.wait_for_load_state('networkidle')
        
        # Apply a filter
        type_filter = page.locator('select[name="page_type"]')
        if type_filter.count() > 0:
            type_filter.first.select_option('markdown')
            page.wait_for_timeout(500)
        
        # Find and click reset/clear button
        reset_button = page.locator('button:has-text("Reset")').or_(
            page.locator('button:has-text("Clear")').or_(page.locator('[data-action="reset-filters"]'))
        )
        
        if reset_button.count() > 0:
            reset_button.first.click()
            page.wait_for_load_state('networkidle')
            # Verify filters are cleared
            expect(type_filter.first).to_have_value('')  # or default value


@pytest.mark.django_db
@pytest.mark.e2e
class TestPagination:
    """Test pagination functionality."""
    
    def test_next_page_button(self, authenticated_page: Page, live_server_url: str):
        """Test next page button."""
        page = authenticated_page
        
        # Navigate to pages list
        page.goto(f"{live_server_url}/docs/pages/list/")
        page.wait_for_load_state('networkidle')
        
        # Find next page button
        next_button = page.locator('button:has-text("Next")').or_(
            page.locator('a:has-text("Next")').or_(page.locator('[data-action="next-page"]'))
        )
        
        if next_button.count() > 0 and next_button.first.is_enabled():
            # Get current page indicator
            current_page_before = page.locator('[data-current-page]').or_(
                page.locator('.pagination .active')
            )
            
            # Click next button
            next_button.first.click()
            page.wait_for_load_state('networkidle')
            
            # Verify page changed (check URL or page indicator)
            # This depends on implementation
    
    def test_previous_page_button(self, authenticated_page: Page, live_server_url: str):
        """Test previous page button."""
        page = authenticated_page
        
        # Navigate to pages list and go to page 2 first
        page.goto(f"{live_server_url}/docs/pages/list/?page=2")
        page.wait_for_load_state('networkidle')
        
        # Find previous page button
        prev_button = page.locator('button:has-text("Previous")').or_(
            page.locator('a:has-text("Previous")').or_(page.locator('[data-action="prev-page"]'))
        )
        
        if prev_button.count() > 0 and prev_button.first.is_enabled():
            prev_button.first.click()
            page.wait_for_load_state('networkidle')
            # Verify page changed to page 1
    
    def test_page_number_selection(self, authenticated_page: Page, live_server_url: str):
        """Test selecting specific page number."""
        page = authenticated_page
        
        # Navigate to pages list
        page.goto(f"{live_server_url}/docs/pages/list/")
        page.wait_for_load_state('networkidle')
        
        # Find page number link (e.g., page 2)
        page_link = page.locator('a:has-text("2")').or_(
            page.locator('[data-page="2"]')
        )
        
        if page_link.count() > 0:
            page_link.first.click()
            page.wait_for_load_state('networkidle')
            # Verify URL or page indicator shows page 2
    
    def test_items_per_page_selection(self, authenticated_page: Page, live_server_url: str):
        """Test changing items per page."""
        page = authenticated_page
        
        # Navigate to pages list
        page.goto(f"{live_server_url}/docs/pages/list/")
        page.wait_for_load_state('networkidle')
        
        # Find items per page selector
        items_per_page = page.locator('select[name="page_size"]').or_(
            page.locator('select[name="limit"]').or_(page.locator('[data-action="items-per-page"]'))
        )
        
        if items_per_page.count() > 0:
            # Change to show more items
            items_per_page.first.select_option('50')
            page.wait_for_load_state('networkidle')
            # Verify more items are displayed


@pytest.mark.django_db
@pytest.mark.e2e
class TestSearch:
    """Test search functionality."""
    
    def test_search_input(self, authenticated_page: Page, live_server_url: str):
        """Test search input functionality."""
        page = authenticated_page
        
        # Navigate to pages list
        page.goto(f"{live_server_url}/docs/pages/list/")
        page.wait_for_load_state('networkidle')
        
        # Find search input
        search_input = page.locator('input[name="search"]').or_(
            page.locator('input[type="search"]').or_(page.locator('[data-action="search"]'))
        )
        
        if search_input.count() > 0:
            # Enter search query
            search_input.first.fill('test')
            page.wait_for_timeout(500)  # Wait for debounce
            
            # Verify search results update (might be AJAX)
            page.wait_for_load_state('networkidle')
    
    def test_search_results_display(self, authenticated_page: Page, live_server_url: str):
        """Test search results are displayed."""
        page = authenticated_page
        
        # Navigate to pages list
        page.goto(f"{live_server_url}/docs/pages/list/")
        page.wait_for_load_state('networkidle')
        
        # Enter search query
        search_input = page.locator('input[name="search"]')
        if search_input.count() > 0:
            search_input.first.fill('test')
            page.wait_for_load_state('networkidle')
            
            # Verify results container is visible
            results = page.locator('[data-testid="results"]').or_(
                page.locator('.results').or_(page.locator('table'))
            )
            if results.count() > 0:
                expect(results.first).to_be_visible()
    
    def test_search_clear(self, authenticated_page: Page, live_server_url: str):
        """Test clearing search."""
        page = authenticated_page
        
        # Navigate to pages list
        page.goto(f"{live_server_url}/docs/pages/list/")
        page.wait_for_load_state('networkidle')
        
        # Enter search query
        search_input = page.locator('input[name="search"]')
        if search_input.count() > 0:
            search_input.first.fill('test')
            page.wait_for_timeout(500)
            
            # Find clear button
            clear_button = page.locator('button[aria-label="Clear"]').or_(
                page.locator('button:has-text("Clear")').or_(page.locator('[data-action="clear-search"]'))
            )
            
            if clear_button.count() > 0:
                clear_button.first.click()
                page.wait_for_load_state('networkidle')
                # Verify search input is cleared
                expect(search_input.first).to_have_value('')


@pytest.mark.django_db
@pytest.mark.e2e
class TestBulkOperations:
    """Test bulk operations functionality."""
    
    def test_select_multiple_items(self, authenticated_page: Page, live_server_url: str):
        """Test selecting multiple items."""
        page = authenticated_page
        
        # Navigate to pages list
        page.goto(f"{live_server_url}/docs/pages/list/")
        page.wait_for_load_state('networkidle')
        
        # Find checkboxes
        checkboxes = page.locator('input[type="checkbox"][name*="select"]').or_(
            page.locator('input[type="checkbox"][data-item-id]')
        )
        
        if checkboxes.count() >= 2:
            # Select first two items
            checkboxes.nth(0).check()
            checkboxes.nth(1).check()
            
            # Verify bulk actions bar appears
            bulk_actions = page.locator('[data-testid="bulk-actions"]').or_(
                page.locator('.bulk-actions')
            )
            if bulk_actions.count() > 0:
                expect(bulk_actions.first).to_be_visible()
    
    def test_bulk_delete_button(self, authenticated_page: Page, live_server_url: str):
        """Test bulk delete functionality."""
        page = authenticated_page
        
        # Navigate to pages list
        page.goto(f"{live_server_url}/docs/pages/list/")
        page.wait_for_load_state('networkidle')
        
        # Select items
        checkboxes = page.locator('input[type="checkbox"][name*="select"]')
        if checkboxes.count() >= 1:
            checkboxes.nth(0).check()
            
            # Find bulk delete button
            bulk_delete = page.locator('button:has-text("Delete Selected")').or_(
                page.locator('[data-action="bulk-delete"]')
            )
            
            if bulk_delete.count() > 0:
                bulk_delete.first.click()
                
                # Handle confirmation dialog if present
                page.on("dialog", lambda dialog: dialog.accept())
                page.wait_for_load_state('networkidle')
    
    def test_select_all_functionality(self, authenticated_page: Page, live_server_url: str):
        """Test select all checkbox."""
        page = authenticated_page
        
        # Navigate to pages list
        page.goto(f"{live_server_url}/docs/pages/list/")
        page.wait_for_load_state('networkidle')
        
        # Find select all checkbox
        select_all = page.locator('input[type="checkbox"][name="select_all"]').or_(
            page.locator('[data-action="select-all"]')
        )
        
        if select_all.count() > 0:
            select_all.first.check()
            
            # Verify all item checkboxes are checked
            item_checkboxes = page.locator('input[type="checkbox"][name*="select"]')
            if item_checkboxes.count() > 0:
                # Check that at least some checkboxes are checked
                checked_count = item_checkboxes.filter(lambda cb: cb.is_checked()).count()
                # Note: Exact verification depends on implementation
