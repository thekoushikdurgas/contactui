# E2E Tests

End-to-end tests for the Documentation AI application using Playwright and pytest.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
playwright install chromium
```

## Running Tests

### Run all E2E tests:
```bash
pytest e2e/ --browser chromium
```

### Run specific test file:
```bash
pytest e2e/test_dashboard_navigation.py --browser chromium
```

### Run in headed mode (see browser):
```bash
pytest e2e/ --browser chromium --headed
```

### Run with debug output:
```bash
pytest e2e/ --browser chromium -v -s
```

## Test Structure

- `conftest.py`: Pytest fixtures and configuration
- `test_dashboard_navigation.py`: Dashboard navigation flow tests
- `test_page_creation_flow.py`: Page creation workflow tests

## Writing New Tests

1. Create test file in `e2e/` directory
2. Use `authenticated_page` fixture for authenticated tests
3. Use `live_server_url` fixture to get the test server URL
4. Mark tests with `@pytest.mark.django_db` if database access is needed
5. Mark tests with `@pytest.mark.e2e` to categorize as E2E tests

Example:
```python
import pytest
from playwright.sync_api import Page, expect

@pytest.mark.django_db
@pytest.mark.e2e
def test_example(authenticated_page: Page, live_server_url: str):
    page = authenticated_page
    page.goto(f"{live_server_url}/docs/")
    expect(page.locator('body')).to_contain_text('dashboard')
```

## Notes

- Tests use Django's test database
- Authentication is handled via fixtures
- Tests run against a live Django test server
- Adjust selectors based on actual HTML structure
