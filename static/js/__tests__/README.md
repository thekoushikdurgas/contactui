# Frontend Unit Tests

## Overview

Unit tests for JavaScript components, focusing on `UnifiedDashboardController` and related functionality.

## Setup

Install dependencies:

```bash
npm install
```

## Running Tests

Run all tests:
```bash
npm test
```

Run tests in watch mode:
```bash
npm run test:watch
```

Run tests with coverage:
```bash
npm run test:coverage
```

## Test Structure

- `setup.js` - Jest configuration and global mocks
- `unified-dashboard-controller.test.js` - Tests for UnifiedDashboardController

## Test Coverage

### UnifiedDashboardController Tests

- **URL Parsing** - Tab, view, page, page_size, filters extraction
- **Filter Chips** - Rendering, removal, empty state handling
- **Pagination** - Page navigation, page size changes, item count calculation
- **File Browser Filters** - Subdirectory extraction, filtering logic
- **Virtual Scrolling** - Visible range calculation, spacer heights
- **Page Size Preference** - localStorage save/load
- **URL State Management** - URL parameter updates
- **Card Actions** - URL generation for relationships and Postman
- **Grid Layout** - Responsive column calculation

## Writing New Tests

1. Create test file in `__tests__/` directory
2. Follow naming convention: `*.test.js` or `*.spec.js`
3. Use Jest's `describe` and `test` functions
4. Mock DOM APIs and fetch in `setup.js` if needed

## Mocking

- `window.location` - Mocked in setup.js
- `window.history` - Mocked in setup.js
- `localStorage` - Mocked in setup.js
- `fetch` - Mocked in setup.js
- `requestAnimationFrame` - Mocked in setup.js

## Notes

- Tests run in jsdom environment (browser-like)
- DOM is reset before each test
- Mocks are cleared before each test
