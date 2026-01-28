/**
 * Jest setup file for frontend tests
 * Configures jsdom environment and global mocks
 */

// Mock window.location
Object.defineProperty(window, 'location', {
  writable: true,
  value: {
    href: 'http://localhost:8000/docs/',
    search: '',
    origin: 'http://localhost:8000',
    pathname: '/docs/',
  },
});

// Mock window.history
Object.defineProperty(window, 'history', {
  writable: true,
  value: {
    pushState: jest.fn(),
    replaceState: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
  },
});

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;

// Mock fetch
global.fetch = jest.fn();

// Mock requestAnimationFrame
global.requestAnimationFrame = jest.fn((cb) => {
  return setTimeout(cb, 0);
});

global.cancelAnimationFrame = jest.fn((id) => {
  clearTimeout(id);
});

// Reset mocks before each test
beforeEach(() => {
  jest.clearAllMocks();
  localStorageMock.getItem.mockReturnValue(null);
  fetch.mockResolvedValue({
    ok: true,
    json: async () => ({ success: true, data: [] }),
    status: 200,
    statusText: 'OK',
  });
  
  // Reset window.location
  window.location.href = 'http://localhost:8000/docs/';
  window.location.search = '';
});
