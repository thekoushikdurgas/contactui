"""
Playwright configuration for E2E tests.

Run with: pytest e2e/ --browser chromium
"""

import pytest
from playwright.sync_api import Playwright, Browser, BrowserContext, Page


@pytest.fixture(scope="session")
def browser_type_launch_args(playwright: Playwright):
    """Configure browser launch arguments."""
    return {
        "headless": True,
        "slow_mo": 100,  # Slow down operations for debugging
    }


@pytest.fixture(scope="session")
def browser(playwright: Playwright, browser_type_launch_args):
    """Launch browser for E2E tests."""
    browser = playwright.chromium.launch(**browser_type_launch_args)
    yield browser
    browser.close()


@pytest.fixture
def context(browser: Browser):
    """Create browser context."""
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True,
    )
    yield context
    context.close()


@pytest.fixture
def page(context: BrowserContext):
    """Create page for E2E tests."""
    page = context.new_page()
    yield page
    page.close()
