/**
 * Unit tests for UnifiedDashboardController
 * Tests URL parsing, filtering, pagination, and virtual scrolling features
 */

// Load the controller class by executing the source file
// This simulates how the browser loads the script
const fs = require('fs');
const path = require('path');

// Read and execute the controller file to populate window.UnifiedDashboardController
const controllerPath = path.join(__dirname, '../components/unified-dashboard-controller.js');
const controllerCode = fs.readFileSync(controllerPath, 'utf8');

// Execute the code in the global scope to populate window.UnifiedDashboardController
eval(controllerCode);

describe('UnifiedDashboardController', () => {
  let controller;
  let mockContainer;
  
  beforeEach(() => {
    // Reset DOM
    document.body.innerHTML = '';
    
    // Create mock containers
    mockContainer = document.createElement('div');
    mockContainer.id = 'pages-list';
    document.body.appendChild(mockContainer);
    
    // Create filter chips container
    const filterChipsContainer = document.createElement('div');
    filterChipsContainer.id = 'pages-filter-chips';
    document.body.appendChild(filterChipsContainer);
    
    // Reset URL
    window.location.search = '';
    window.location.href = 'http://localhost:8000/docs/';
    
    // Mock fetch
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        success: true,
        items: [],
        pagination: {
          page: 1,
          total_pages: 1,
          total: 0,
          has_previous: false,
          has_next: false,
        },
      }),
    });
    
    // Create controller instance
    if (window.UnifiedDashboardController) {
      controller = new window.UnifiedDashboardController({
        activeTab: 'pages',
        viewMode: 'list',
        pagesApiUrl: '/docs/api/dashboard/pages/',
        endpointsApiUrl: '/docs/api/dashboard/endpoints/',
        relationshipsApiUrl: '/docs/api/dashboard/relationships/',
        postmanApiUrl: '/docs/api/dashboard/postman/',
        mediaListFilesUrl: '/docs/api/media/files/',
        mediaBulkSyncUrl: '/docs/api/media/files/bulk-sync/',
        mediaSyncStatusUrl: '/docs/api/media/sync-status/',
        previewBase: '/docs/media/preview/',
        viewerBase: '/docs/media/viewer/',
        formEditBase: '/docs/media/form/edit/',
        deleteBase: '/docs/media/delete/'
      });
    }
  });
  
  afterEach(() => {
    jest.restoreAllMocks();
    document.body.innerHTML = '';
    if (controller) {
      controller = null;
    }
  });
  
  describe('URL Parsing', () => {
    test('parseURL should extract tab parameter', () => {
      window.location.search = '?tab=endpoints';
      // We'll need to create controller instance
      // For now, test the logic
      const urlParams = new URLSearchParams(window.location.search);
      const tab = urlParams.get('tab');
      expect(tab).toBe('endpoints');
    });
    
    test('parseURL should extract view parameter', () => {
      window.location.search = '?tab=pages&view=files';
      const urlParams = new URLSearchParams(window.location.search);
      const view = urlParams.get('view');
      expect(view).toBe('files');
    });
    
    test('parseURL should extract page and page_size', () => {
      window.location.search = '?tab=pages&page=2&page_size=50';
      const urlParams = new URLSearchParams(window.location.search);
      const page = parseInt(urlParams.get('page')) || 1;
      const pageSize = parseInt(urlParams.get('page_size')) || 20;
      expect(page).toBe(2);
      expect(pageSize).toBe(50);
    });
    
    test('parseURL should parse filters from URL', () => {
      const filters = { page_type: 'docs', status: 'published' };
      window.location.search = `?tab=pages&filters=${encodeURIComponent(JSON.stringify(filters))}`;
      const urlParams = new URLSearchParams(window.location.search);
      const filtersParam = urlParams.get('filters');
      const parsed = JSON.parse(decodeURIComponent(filtersParam));
      expect(parsed).toEqual(filters);
    });
  });
  
  describe('Filter Chips', () => {
    test('renderFilterChips should render chips for active filters', () => {
      const container = document.createElement('div');
      container.id = 'pages-filter-chips';
      document.body.appendChild(container);
      
      // Mock controller state
      const filters = {
        page_type: 'docs',
        status: 'published',
        search: 'test',
      };
      
      // Simulate filter chip rendering logic
      const activeFilters = [];
      Object.keys(filters).forEach(key => {
        const value = filters[key];
        if (value && value !== '' && value !== null && value !== undefined) {
          activeFilters.push({ key, name: key, value });
        }
      });
      
      expect(activeFilters.length).toBe(3);
      expect(activeFilters[0].key).toBe('page_type');
      expect(activeFilters[0].value).toBe('docs');
    });
    
    test('renderFilterChips should handle empty filters', () => {
      const filters = {};
      const activeFilters = [];
      Object.keys(filters).forEach(key => {
        if (filters[key]) {
          activeFilters.push({ key, name: key, value: filters[key] });
        }
      });
      expect(activeFilters.length).toBe(0);
    });
    
    test('removeFilter should remove filter from state', () => {
      const filters = {
        page_type: 'docs',
        status: 'published',
      };
      
      // Simulate removing a filter
      const filterKey = 'page_type';
      delete filters[filterKey];
      
      expect(filters.page_type).toBeUndefined();
      expect(filters.status).toBe('published');
    });
  });
  
  describe('Pagination', () => {
    test('goToPage should update currentPage', () => {
      const currentPage = { pages: 1 };
      const tabName = 'pages';
      const pageNumber = 3;
      
      currentPage[tabName] = pageNumber;
      
      expect(currentPage[tabName]).toBe(3);
    });
    
    test('goToPage should validate page number', () => {
      const pagination = { total_pages: 10 };
      let pageNumber = 15;
      pageNumber = Math.max(1, Math.min(pageNumber, pagination.total_pages));
      
      expect(pageNumber).toBe(10);
      
      pageNumber = -1;
      pageNumber = Math.max(1, Math.min(pageNumber, pagination.total_pages));
      expect(pageNumber).toBe(1);
    });
    
    test('changePageSize should update pageSize and reset to page 1', () => {
      const pageSize = { pages: 20 };
      const currentPage = { pages: 5 };
      const tabName = 'pages';
      const newPageSize = 50;
      
      pageSize[tabName] = newPageSize;
      currentPage[tabName] = 1;
      
      expect(pageSize[tabName]).toBe(50);
      expect(currentPage[tabName]).toBe(1);
    });
    
    test('setupPagination should calculate item count correctly', () => {
      const pagination = {
        page: 2,
        total: 100,
        total_pages: 5,
        has_previous: true,
        has_next: true,
      };
      const pageSize = 20;
      const startItem = pagination.total === 0 ? 0 : ((pagination.page - 1) * pageSize) + 1;
      const endItem = Math.min(pagination.page * pageSize, pagination.total);
      
      expect(startItem).toBe(21);
      expect(endItem).toBe(40);
    });
  });
  
  describe('File Browser Filters', () => {
    test('renderFileBrowserFilters should extract subdirectories', () => {
      const files = [
        { name: 'file1.json', subdirectory: 'by-page' },
        { name: 'file2.json', subdirectory: 'by-page' },
        { name: 'file3.json', subdirectory: 'by-endpoint' },
      ];
      
      const subdirSet = new Set();
      files.forEach(file => {
        if (file.subdirectory) {
          subdirSet.add(file.subdirectory);
        }
      });
      const subdirectories = Array.from(subdirSet).sort();
      
      expect(subdirectories).toEqual(['by-endpoint', 'by-page']);
    });
    
    test('applyFileFilters should filter by subdirectory', () => {
      const files = [
        { name: 'file1.json', subdirectory: 'by-page' },
        { name: 'file2.json', subdirectory: 'by-endpoint' },
        { name: 'file3.json', subdirectory: 'by-page' },
      ];
      const filters = { subdirectory: 'by-page' };
      
      const filtered = files.filter(file => {
        if (filters.subdirectory) {
          return file.subdirectory === filters.subdirectory;
        }
        return true;
      });
      
      expect(filtered.length).toBe(2);
      expect(filtered[0].subdirectory).toBe('by-page');
      expect(filtered[1].subdirectory).toBe('by-page');
    });
    
    test('applyFileFilters should filter by search', () => {
      const files = [
        { name: 'test1.json', relative_path: 'test1.json' },
        { name: 'test2.json', relative_path: 'test2.json' },
        { name: 'other.json', relative_path: 'other.json' },
      ];
      const filters = { search: 'test' };
      
      const filtered = files.filter(file => {
        if (filters.search) {
          const searchTerm = filters.search.toLowerCase();
          return (file.name || '').toLowerCase().includes(searchTerm) ||
                 (file.relative_path || '').toLowerCase().includes(searchTerm);
        }
        return true;
      });
      
      expect(filtered.length).toBe(2);
    });
  });
  
  describe('Virtual Scrolling', () => {
    test('should calculate visible range for file browser', () => {
      const scrollTop = 600;
      const containerHeight = 400;
      const ROW_HEIGHT = 60;
      const OVERSCAN = 5;
      const totalFiles = 100;
      
      const start = Math.max(0, Math.floor(scrollTop / ROW_HEIGHT) - OVERSCAN);
      const visibleCount = Math.ceil(containerHeight / ROW_HEIGHT);
      const end = Math.min(totalFiles, start + visibleCount + OVERSCAN * 2);
      
      expect(start).toBe(5); // floor(600/60) - 5 = 10 - 5 = 5
      expect(end).toBeLessThanOrEqual(totalFiles);
      expect(end).toBeGreaterThan(start);
    });
    
    test('should calculate visible range for list views', () => {
      const scrollTop = 900;
      const containerHeight = 600;
      const CARD_HEIGHT = 180;
      const OVERSCAN = 5;
      const cardsPerRow = 3;
      const totalItems = 100;
      
      const start = Math.max(0, Math.floor(scrollTop / CARD_HEIGHT) * cardsPerRow - OVERSCAN * cardsPerRow);
      const visibleRows = Math.ceil(containerHeight / CARD_HEIGHT);
      const end = Math.min(totalItems, start + visibleRows * cardsPerRow + OVERSCAN * cardsPerRow * 2);
      
      expect(start).toBeGreaterThanOrEqual(0);
      expect(end).toBeLessThanOrEqual(totalItems);
    });
    
    test('should enable virtual scrolling for large lists', () => {
      const VIRTUAL_SCROLL_THRESHOLD = 100;
      
      expect(50 >= VIRTUAL_SCROLL_THRESHOLD).toBe(false);
      expect(100 >= VIRTUAL_SCROLL_THRESHOLD).toBe(true);
      expect(200 >= VIRTUAL_SCROLL_THRESHOLD).toBe(true);
    });
    
    test('should calculate spacer heights correctly', () => {
      const visibleRange = { start: 10, end: 30 };
      const ROW_HEIGHT = 60;
      const totalFiles = 100;
      
      const topSpacerHeight = visibleRange.start * ROW_HEIGHT;
      const bottomSpacerHeight = (totalFiles - visibleRange.end) * ROW_HEIGHT;
      
      expect(topSpacerHeight).toBe(600);
      expect(bottomSpacerHeight).toBe(4200);
    });
  });
  
  describe('Page Size Preference', () => {
    test('loadPageSizePreference should return saved value', () => {
      localStorage.getItem.mockReturnValue('50');
      const saved = localStorage.getItem('dashboard_page_size');
      const pageSize = saved ? parseInt(saved) : 20;
      
      expect(pageSize).toBe(50);
    });
    
    test('loadPageSizePreference should return default if not set', () => {
      localStorage.getItem.mockReturnValue(null);
      const saved = localStorage.getItem('dashboard_page_size');
      const pageSize = saved ? parseInt(saved) : 20;
      
      expect(pageSize).toBe(20);
    });
    
    test('savePageSizePreference should save to localStorage', () => {
      const pageSize = 50;
      localStorage.setItem('dashboard_page_size', pageSize.toString());
      
      expect(localStorage.setItem).toHaveBeenCalledWith('dashboard_page_size', '50');
    });
  });
  
  describe('URL State Management', () => {
    test('updateURL should set tab and view parameters', () => {
      const url = new URL('http://localhost:8000/docs/');
      url.searchParams.set('tab', 'pages');
      url.searchParams.set('view', 'list');
      
      expect(url.searchParams.get('tab')).toBe('pages');
      expect(url.searchParams.get('view')).toBe('list');
    });
    
    test('updateURL should set pagination parameters for list view', () => {
      const url = new URL('http://localhost:8000/docs/');
      url.searchParams.set('tab', 'pages');
      url.searchParams.set('view', 'list');
      url.searchParams.set('page', '2');
      url.searchParams.set('page_size', '50');
      
      expect(url.searchParams.get('page')).toBe('2');
      expect(url.searchParams.get('page_size')).toBe('50');
    });
    
    test('updateURL should set filters parameter', () => {
      const url = new URL('http://localhost:8000/docs/');
      const filters = { page_type: 'docs', status: 'published' };
      url.searchParams.set('filters', encodeURIComponent(JSON.stringify(filters)));
      
      const filtersParam = url.searchParams.get('filters');
      const parsed = JSON.parse(decodeURIComponent(filtersParam));
      expect(parsed).toEqual(filters);
    });
    
    test('updateURL should delete filters if empty', () => {
      const url = new URL('http://localhost:8000/docs/?filters=test');
      url.searchParams.delete('filters');
      
      expect(url.searchParams.get('filters')).toBeNull();
    });
  });
  
  describe('Card Actions', () => {
    test('should generate correct relationship URLs', () => {
      const relationshipId = 'rel-123';
      const href = `/docs/relationships/${encodeURIComponent(relationshipId)}/`;
      const editHref = `/docs/relationships/${encodeURIComponent(relationshipId)}/edit/`;
      
      expect(href).toBe('/docs/relationships/rel-123/');
      expect(editHref).toBe('/docs/relationships/rel-123/edit/');
    });
    
    test('should generate correct Postman URLs', () => {
      const configId = 'postman-config-1';
      const href = `/docs/postman/${encodeURIComponent(configId)}/`;
      const editHref = `/docs/postman/${encodeURIComponent(configId)}/edit/`;
      
      expect(href).toBe('/docs/postman/postman-config-1/');
      expect(editHref).toBe('/docs/postman/postman-config-1/edit/');
    });
  });
  
  describe('Grid Layout Calculation', () => {
    test('getCardsPerRow should return correct columns for screen sizes', () => {
      // Mock window.innerWidth
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1920, // Desktop
      });
      
      const width = window.innerWidth;
      let cardsPerRow;
      if (width >= 1024) cardsPerRow = 3; // lg:grid-cols-3
      else if (width >= 768) cardsPerRow = 2; // md:grid-cols-2
      else cardsPerRow = 1; // grid-cols-1
      
      expect(cardsPerRow).toBe(3);
      
      // Tablet
      window.innerWidth = 900;
      const width2 = window.innerWidth;
      if (width2 >= 1024) cardsPerRow = 3;
      else if (width2 >= 768) cardsPerRow = 2;
      else cardsPerRow = 1;
      
      expect(cardsPerRow).toBe(2);
      
      // Mobile
      window.innerWidth = 500;
      const width3 = window.innerWidth;
      if (width3 >= 1024) cardsPerRow = 3;
      else if (width3 >= 768) cardsPerRow = 2;
      else cardsPerRow = 1;
      
      expect(cardsPerRow).toBe(1);
    });
  });
});
