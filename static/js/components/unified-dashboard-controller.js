/**
 * Unified Dashboard Controller
 * 
 * Merges functionality from dashboard-controller.js and media-manager.js
 * Manages dashboard state, pagination, filtering, view modes, and file operations
 * 
 * Features:
 * - Primary tabs: pages, endpoints, relationships, postman, graph
 * - View modes: list, files, sync (for each tab)
 * - List view: pagination, filtering, bulk operations
 * - File browser: file list, bulk sync/delete, virtual scrolling
 * - Sync status: sync summary display
 */

class UnifiedDashboardController {
    constructor(options = {}) {
        this.options = options;
        
        // Primary tab state
        this.activeTab = options.activeTab || 'pages';
        
        // View mode state (list, files, sync)
        this.viewMode = options.viewMode || 'list';
        
        // List view state
        this.currentPage = {};
        this.pageSize = {};
        this.filters = {};
        this.loading = {};
        this.data = {};
        
        // File browser state
        this.files = {};
        this.selectedFiles = new Set();
        this.fileFilters = {};
        this.fileCache = new Map();
        this.fileCacheTimestamps = new Map();
        this.CACHE_DURATION = 5 * 60 * 1000; // 5 minutes
        
        // Virtual scrolling
        this.virtualScrollEnabled = true; // Enable virtual scrolling by default
        this.visibleRange = { start: 0, end: 50 };
        this.ITEMS_PER_PAGE = 50;
        this.VIRTUAL_SCROLL_THRESHOLD = 100; // Enable virtual scrolling for 100+ items
        this.ROW_HEIGHT = 60; // Approximate row height in pixels (for file browser)
        this.CARD_HEIGHT = 180; // Approximate card height in pixels (for list views)
        this.OVERSCAN = 5; // Render 5 extra rows above and below visible area
        this.scrollContainers = {}; // Track scroll containers per tab
        this.listScrollContainers = {}; // Track list view scroll containers
        
        // DOM cache for faster element access (Task 1.2.2)
        this.domCache = {};
        this.cacheEnabled = true;
        
        // API endpoints
        this.apiEndpoints = {
            pages: options.pagesApiUrl || '/docs/api/dashboard/pages/',
            endpoints: options.endpointsApiUrl || '/docs/api/dashboard/endpoints/',
            relationships: options.relationshipsApiUrl || '/docs/api/dashboard/relationships/',
            postman: options.postmanApiUrl || '/docs/api/dashboard/postman/',
            graph: null
        };
        
        // Media API endpoints
        this.mediaEndpoints = {
            listFiles: options.mediaListFilesUrl || '/docs/api/media/files/',
            bulkSync: options.mediaBulkSyncUrl || '/docs/api/media/bulk-sync/',
            syncStatus: options.mediaSyncStatusUrl || '/docs/api/media/sync-status/',
            previewBase: options.previewBase || '/docs/media/preview/',
            viewerBase: options.viewerBase || '/docs/media/viewer/',
            formEditBase: options.formEditBase || '/docs/media/form/edit/',
            deleteBase: options.deleteBase || '/docs/media/delete/'
        };
        
        // Pagination instances
        this.paginationInstances = {};
        
        // Bulk operations instances
        this.bulkOperations = {};
        
        // Load page size preference
        this.defaultPageSize = this.loadPageSizePreference();
        
        // Initialize
        this.init();
    }
    
    /**
     * Get DOM element with caching (Task 1.2.2: Cache DOM queries)
     * @param {string} id - Element ID
     * @param {boolean} useQuerySelector - Whether to fallback to querySelector
     * @returns {HTMLElement|null}
     */
    getCachedElement(id, useQuerySelector = false) {
        if (!this.cacheEnabled) {
            return document.getElementById(id) || (useQuerySelector ? document.querySelector(`#${id}`) : null);
        }
        
        if (!this.domCache[id]) {
            this.domCache[id] = document.getElementById(id) || (useQuerySelector ? document.querySelector(`#${id}`) : null);
        }
        return this.domCache[id];
    }
    
    /**
     * Clear DOM cache (useful when DOM structure changes)
     * @param {string|null} id - Specific ID to clear, or null to clear all
     */
    clearDomCache(id = null) {
        if (id) {
            delete this.domCache[id];
        } else {
            this.domCache = {};
        }
    }
    
    /**
     * Create DocumentFragment from HTML string (Task 1.2.1: Use DocumentFragment)
     * @param {string} html - HTML string
     * @returns {DocumentFragment}
     */
    createFragmentFromHTML(html) {
        const template = document.createElement('template');
        template.innerHTML = html;
        return template.content;
    }
    
    /**
     * Initialize controller
     */
    init() {
        // Parse URL parameters
        this.parseURL();
        
        // Initialize current state
        const tabs = ['pages', 'endpoints', 'relationships', 'postman'];
        tabs.forEach(tab => {
            this.currentPage[tab] = this.currentPage[tab] || 1;
            this.pageSize[tab] = this.pageSize[tab] || this.defaultPageSize;
            // Initialize filters object if it doesn't exist
            if (!this.filters[tab]) {
                this.filters[tab] = {};
            }
            this.loading[tab] = false;
            this.fileFilters[tab] = {
                search: '',
                syncStatus: '',
                subdirectory: '',  // For relationships and postman
                sortBy: 'name',
                sortOrder: 'asc'
            };
        });
        
        // Keep navigation hrefs consistent with current state
        this.updateNavigationHrefs();

        // Load initial data for active tab and view mode
        this.loadView(this.activeTab, this.viewMode);
        
        // Attach event listeners
        this.attachEventListeners();
    }
    
    /**
     * Parse URL parameters
     */
    parseURL() {
        const urlParams = new URLSearchParams(window.location.search);
        
        // Get active tab
        const tab = urlParams.get('tab');
        if (tab && ['pages', 'endpoints', 'relationships', 'postman', 'graph'].includes(tab)) {
            this.activeTab = tab;
        }
        
        // Get view mode
        const view = urlParams.get('view');
        if (view && ['list', 'files', 'sync'].includes(view)) {
            this.viewMode = view;
        }

        // Graph tab is not a paginated list view; ignore list-specific params and normalize later in updateURL().
        if (this.activeTab === 'graph') {
            this.viewMode = 'list';
            return;
        }
        
        // Get pagination params
        const page = parseInt(urlParams.get('page')) || 1;
        const pageSize = parseInt(urlParams.get('page_size')) || this.defaultPageSize;
        
        this.currentPage[this.activeTab] = page;
        this.pageSize[this.activeTab] = pageSize;
        
        // Get filters
        const filtersParam = urlParams.get('filters');
        if (filtersParam) {
            try {
                this.filters[this.activeTab] = JSON.parse(decodeURIComponent(filtersParam));
            } catch (e) {
                console.error('Error parsing filters from URL:', e);
            }
        }
    }
    
    /**
     * Update URL with current state
     */
    updateURL() {
        const url = new URL(window.location.href);
        url.searchParams.set('tab', this.activeTab);

        // Graph: keep URL clean (no view/page/page_size/filters)
        if (this.activeTab === 'graph') {
            url.searchParams.delete('view');
            url.searchParams.delete('page');
            url.searchParams.delete('page_size');
            url.searchParams.delete('filters');
            window.history.pushState({}, '', url);
            this.updateNavigationHrefs();
            return;
        }

        // For non-graph tabs, persist "last list state" in the URL even when view != list.
        // This makes view switching and full-page reloads/restores predictable.
        url.searchParams.set('view', this.viewMode);
        url.searchParams.set('page', (this.currentPage[this.activeTab] || 1).toString());
        url.searchParams.set('page_size', (this.pageSize[this.activeTab] || this.defaultPageSize).toString());

        const filters = this.filters[this.activeTab];
        if (filters && Object.keys(filters).length > 0) {
            url.searchParams.set('filters', encodeURIComponent(JSON.stringify(filters)));
        } else {
            url.searchParams.delete('filters');
        }
        
        window.history.pushState({}, '', url);
        this.updateNavigationHrefs();
    }

    /**
     * Update hrefs for tab/view navigation so new-tab/reload preserves state.
     */
    updateNavigationHrefs() {
        const makeUrl = (tab, viewMode) => {
            const url = new URL(window.location.href);
            url.searchParams.set('tab', tab);

            if (tab === 'graph') {
                url.searchParams.delete('view');
                url.searchParams.delete('page');
                url.searchParams.delete('page_size');
                url.searchParams.delete('filters');
                return `${url.pathname}?${url.searchParams.toString()}`;
            }

            const tabView = viewMode || (tab === this.activeTab ? this.viewMode : 'list');
            url.searchParams.set('view', tabView);

            // Per-tab state (best-effort; for inactive tabs, defaults are already initialized in init()).
            const page = this.currentPage[tab] || 1;
            const pageSize = this.pageSize[tab] || this.defaultPageSize;
            url.searchParams.set('page', page.toString());
            url.searchParams.set('page_size', pageSize.toString());

            const filters = this.filters[tab];
            if (filters && Object.keys(filters).length > 0) {
                url.searchParams.set('filters', encodeURIComponent(JSON.stringify(filters)));
            } else {
                url.searchParams.delete('filters');
            }

            return `${url.pathname}?${url.searchParams.toString()}`;
        };

        // Tab buttons
        document.querySelectorAll('a.tab-button[data-tab]').forEach(btn => {
            const tab = btn.getAttribute('data-tab');
            if (!tab) return;
            btn.setAttribute('href', makeUrl(tab, tab === 'graph' ? null : (tab === this.activeTab ? this.viewMode : 'list')));
        });

        // View mode buttons (only relevant for non-graph)
        document.querySelectorAll('.view-mode-btn[data-view-mode]').forEach(btn => {
            const viewMode = btn.getAttribute('data-view-mode');
            if (!viewMode) return;
            btn.setAttribute('href', makeUrl(this.activeTab, viewMode));
        });
    }
    
    /**
     * Load view for a tab and view mode
     */
    async loadView(tabName, viewMode) {
        // Graph tab doesn't support view modes
        if (tabName === 'graph') {
            this.activeTab = tabName;
            this.viewMode = 'list';
            this.updateURL();
            return;
        }
        
        this.activeTab = tabName;
        this.viewMode = viewMode;
        
        // Show/hide view mode containers
        this.switchViewMode(viewMode);
        
        // Load data based on view mode
        if (viewMode === 'list') {
            await this.loadList(tabName);
        } else if (viewMode === 'files') {
            await this.loadFiles(tabName);
        } else if (viewMode === 'sync') {
            await this.loadSyncStatus(tabName);
        }
        
        this.updateURL();
    }
    
    /**
     * Switch view mode UI
     */
    switchViewMode(viewMode) {
        // Update view mode toggle buttons
        document.querySelectorAll('.view-mode-btn').forEach(btn => {
            const btnViewMode = btn.getAttribute('data-view-mode');
            if (btnViewMode === viewMode) {
                btn.classList.add('bg-blue-600', 'text-white');
                btn.classList.remove('text-gray-700', 'dark:text-gray-300', 'hover:bg-gray-100', 'dark:hover:bg-gray-700');
            } else {
                btn.classList.remove('bg-blue-600', 'text-white');
                btn.classList.add('text-gray-700', 'dark:text-gray-300', 'hover:bg-gray-100', 'dark:hover:bg-gray-700');
            }
        });
        
        // Show/hide view mode content
        const tabContent = this.getCachedElement(`${this.activeTab}-content`);
        if (tabContent) {
            const viewContainers = tabContent.querySelectorAll('.view-mode-content');
            viewContainers.forEach(container => {
                const containerViewMode = container.id.includes('-list-view') ? 'list' :
                                         container.id.includes('-files-view') ? 'files' :
                                         container.id.includes('-sync-view') ? 'sync' : null;
                
                if (containerViewMode === viewMode) {
                    container.classList.remove('hidden');
                    container.classList.add('active');
                } else {
                    container.classList.add('hidden');
                    container.classList.remove('active');
                }
            });
        }
    }
    
    /**
     * Load list view data
     */
    async loadList(tabName) {
        if (this.loading[tabName]) {
            return;
        }
        
        // Try both naming conventions for backward compatibility
        const targetContainer = this.getCachedElement(`${tabName}-list`, true) || 
                               document.querySelector(`#${tabName}-list-view #${tabName}-list`);
        if (!targetContainer) {
            console.warn(`Container not found for ${tabName} list view`);
            return;
        }
        
        this.loading[tabName] = true;
        this.showLoading(tabName, 'list');
        
        try {
            const data = await this.fetchTabData(tabName);
            this.data[tabName] = data;
            this.renderList(tabName, data);
            this.setupPagination(tabName, data);
        } catch (error) {
            console.error(`Error loading ${tabName}:`, error);
            this.showError(tabName, error, 'list');
        } finally {
            this.loading[tabName] = false;
        }
    }
    
    /**
     * Load file browser data
     */
    async loadFiles(tabName, forceRefresh = false) {
        // Try both naming conventions
        const container = document.getElementById(`${tabName}-file-browser`) || 
                         document.querySelector(`#${tabName}-files-view #${tabName}-file-browser`);
        if (!container) {
            console.warn(`Container not found for ${tabName} file browser`);
            return;
        }
        
        this.showLoading(tabName, 'files');
        
        const cacheKey = this.getFileCacheKey(tabName);
        
        // Check cache first
        if (!forceRefresh) {
            const cachedData = this.getFileCache(cacheKey);
            if (cachedData) {
                this.files[tabName] = cachedData;
                this.renderFiles(tabName, cachedData);
                this.hideLoading(tabName, 'files');
                return;
            }
        }
        
        try {
            const url = new URL(this.mediaEndpoints.listFiles, window.location.origin);
            url.searchParams.set('resource_type', tabName);
            
            const response = await fetch(url, {
                headers: { 'Accept': 'application/json' }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.files[tabName] = data.data || [];
                this.setFileCache(cacheKey, this.files[tabName]);
                this.renderFiles(tabName, this.files[tabName]);
            } else {
                throw new Error(data.error || 'API returned unsuccessful response');
            }
        } catch (error) {
            console.error(`Error loading files for ${tabName}:`, error);
            this.showError(tabName, error, 'files');
        } finally {
            this.hideLoading(tabName, 'files');
        }
    }
    
    /**
     * Load sync status data
     */
    async loadSyncStatus(tabName) {
        // Try both naming conventions
        const container = document.getElementById(`${tabName}-sync-status`) || 
                         document.querySelector(`#${tabName}-sync-view #${tabName}-sync-status`);
        if (!container) {
            console.warn(`Container not found for ${tabName} sync status`);
            return;
        }
        
        this.showLoading(tabName, 'sync');
        
        try {
            const url = new URL(this.mediaEndpoints.syncStatus, window.location.origin);
            const response = await fetch(url, {
                headers: { 'Accept': 'application/json' }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.renderSyncStatus(tabName, data.data);
            } else {
                throw new Error(data.error || 'API returned unsuccessful response');
            }
        } catch (error) {
            console.error(`Error loading sync status for ${tabName}:`, error);
            this.showError(tabName, error, 'sync');
        } finally {
            this.hideLoading(tabName, 'sync');
        }
    }
    
    /**
     * Fetch list view data from API
     */
    async fetchTabData(tabName) {
        const url = new URL(this.apiEndpoints[tabName], window.location.origin);
        url.searchParams.set('page', this.currentPage[tabName].toString());
        url.searchParams.set('page_size', this.pageSize[tabName].toString());
        
        const filters = this.filters[tabName] || {};
        
        Object.keys(filters).forEach(key => {
            if (filters[key]) {
                url.searchParams.set(key, filters[key]);
            }
        });

        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
    
    /**
     * Render list view
     */
    renderList(tabName, data) {
        const container = this.getCachedElement(`${tabName}-list`);
        if (!container) {
            return;
        }
        
        const items = data.items || [];
        const renderFunction = this.getRenderFunction(tabName);
        
        if (items.length === 0) {
            container.innerHTML = this.getEmptyState(tabName, 'list', data);
            this.setupPagination(tabName, data);
            this.renderFilterChips(tabName);
            return;
        }
        
        // Enable virtual scrolling for large lists
        const useVirtualScroll = items.length >= this.VIRTUAL_SCROLL_THRESHOLD;
        
        if (useVirtualScroll) {
            // Render with virtual scrolling wrapper
            this.renderListWithVirtualScroll(tabName, items, renderFunction, container);
        } else {
            // Normal rendering for small lists
            container.innerHTML = renderFunction(items);
        }
        
        // Render filter chips after rendering list
        this.renderFilterChips(tabName);
        
        // Initialize bulk operations if enabled (skip if BulkOperations is not available to avoid recursion)
        if (this.options.enableBulkOperations !== false && typeof BulkOperations !== 'undefined') {
            // Only initialize if window.dashboardController exists and is NOT the same instance
            if (window.dashboardController && window.dashboardController !== this && window.dashboardController.initBulkOperations) {
                try {
                    window.dashboardController.initBulkOperations(tabName, items);
                } catch (e) {
                    console.warn('Error initializing bulk operations:', e);
                }
            }
        }
        
        // Setup virtual scrolling if enabled
        if (useVirtualScroll) {
            this.setupListVirtualScrolling(tabName, items);
        }
    }
    
    /**
     * Render list with virtual scrolling wrapper
     */
    renderListWithVirtualScroll(tabName, items, renderFunction, container) {
        // Calculate visible range (estimate based on card height)
        const visibleItems = items.slice(this.visibleRange.start, this.visibleRange.end);
        const cardsHtml = renderFunction(visibleItems);
        
        // Calculate spacer heights
        const topSpacerHeight = this.visibleRange.start * this.CARD_HEIGHT;
        const bottomSpacerHeight = (items.length - this.visibleRange.end) * this.CARD_HEIGHT;
        
        container.innerHTML = `
            <div class="virtual-scroll-list-container" 
                 id="${tabName}-list-scroll-container"
                 style="max-height: 800px; overflow-y: auto; overflow-x: hidden;">
                <div style="height: ${topSpacerHeight}px;" class="virtual-scroll-spacer-top"></div>
                <div id="${tabName}-list-cards" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    ${cardsHtml}
                </div>
                <div style="height: ${bottomSpacerHeight}px;" class="virtual-scroll-spacer-bottom"></div>
            </div>
        `;
    }
    
    /**
     * Setup virtual scrolling for list views
     */
    setupListVirtualScrolling(tabName, allItems) {
        const container = this.getCachedElement(`${tabName}-list-scroll-container`);
        if (!container) return;
        
        // Store reference
        this.listScrollContainers[tabName] = {
            container: container,
            allItems: allItems,
            scrollTop: 0,
            renderFunction: this.getRenderFunction(tabName)
        };
        
        // Initialize visible range
        this.updateListVisibleRange(tabName);
        
        // Attach scroll listener
        const handleScroll = () => {
            const scrollTop = container.scrollTop;
            const containerHeight = container.clientHeight;
            
            // Calculate visible range (accounting for grid layout - 3 columns on large screens)
            const cardsPerRow = this.getCardsPerRow();
            const start = Math.max(0, Math.floor(scrollTop / this.CARD_HEIGHT) * cardsPerRow - this.OVERSCAN * cardsPerRow);
            const visibleRows = Math.ceil(containerHeight / this.CARD_HEIGHT);
            const end = Math.min(allItems.length, start + visibleRows * cardsPerRow + this.OVERSCAN * cardsPerRow * 2);
            
            // Update if range changed
            if (start !== this.visibleRange.start || end !== this.visibleRange.end) {
                this.visibleRange = { start, end };
                this.listScrollContainers[tabName].scrollTop = scrollTop;
                
                // Re-render visible cards
                this.renderListCards(tabName, allItems);
            }
        };
        
        // Use throttled scroll handler
        let scrollTimeout;
        container.addEventListener('scroll', () => {
            if (scrollTimeout) {
                cancelAnimationFrame(scrollTimeout);
            }
            scrollTimeout = requestAnimationFrame(handleScroll);
        }, { passive: true });
        
        // Handle resize
        const handleResize = () => {
            this.updateListVisibleRange(tabName);
            this.renderListCards(tabName, allItems);
        };
        
        window.addEventListener('resize', handleResize);
        
        // Store cleanup function
        this.listScrollContainers[tabName].cleanup = () => {
            window.removeEventListener('resize', handleResize);
        };
    }
    
    /**
     * Get number of cards per row based on screen size
     */
    getCardsPerRow() {
        // Estimate based on window width (matches Tailwind breakpoints)
        const width = window.innerWidth;
        if (width >= 1024) return 3; // lg:grid-cols-3
        if (width >= 768) return 2;  // md:grid-cols-2
        return 1; // grid-cols-1
    }
    
    /**
     * Update visible range for list views
     */
    updateListVisibleRange(tabName) {
        const scrollData = this.listScrollContainers[tabName];
        if (!scrollData) return;
        
        const container = scrollData.container;
        const scrollTop = container.scrollTop;
        const containerHeight = container.clientHeight;
        const cardsPerRow = this.getCardsPerRow();
        
        const start = Math.max(0, Math.floor(scrollTop / this.CARD_HEIGHT) * cardsPerRow - this.OVERSCAN * cardsPerRow);
        const visibleRows = Math.ceil(containerHeight / this.CARD_HEIGHT);
        const end = Math.min(scrollData.allItems.length, start + visibleRows * cardsPerRow + this.OVERSCAN * cardsPerRow * 2);
        
        this.visibleRange = { start, end };
    }
    
    /**
     * Render visible list cards
     */
    renderListCards(tabName, allItems) {
        const cardsContainer = this.getCachedElement(`${tabName}-list-cards`);
        const topSpacer = document.querySelector(`#${tabName}-list-scroll-container .virtual-scroll-spacer-top`);
        const bottomSpacer = document.querySelector(`#${tabName}-list-scroll-container .virtual-scroll-spacer-bottom`);
        
        if (!cardsContainer) return;
        
        const scrollData = this.listScrollContainers[tabName];
        if (!scrollData) return;
        
        const visibleItems = allItems.slice(this.visibleRange.start, this.visibleRange.end);
        const cardsHtml = scrollData.renderFunction(visibleItems);
        
        // Update cards using DocumentFragment for better performance (Task 1.2.1)
        if (cardsContainer) {
            const fragment = this.createFragmentFromHTML(cardsHtml);
            cardsContainer.innerHTML = ''; // Clear first
            cardsContainer.appendChild(fragment);
        }
        
        // Update spacer heights
        const topSpacerHeight = this.visibleRange.start * this.CARD_HEIGHT;
        const bottomSpacerHeight = (allItems.length - this.visibleRange.end) * this.CARD_HEIGHT;
        
        if (topSpacer) {
            topSpacer.style.height = `${topSpacerHeight}px`;
        }
        if (bottomSpacer) {
            bottomSpacer.style.height = `${bottomSpacerHeight}px`;
        }
    }
    
    /**
     * Render file browser
     */
    renderFiles(tabName, files) {
        // Try both naming conventions
        const container = document.getElementById(`${tabName}-file-browser`) || 
                         document.querySelector(`#${tabName}-files-view #${tabName}-file-browser`);
        if (!container) {
            console.warn(`Container not found for rendering ${tabName} files`);
            return;
        }
        
        if (!files || files.length === 0) {
            // Use DocumentFragment for better performance (Task 1.2.1)
            const emptyFragment = this.createFragmentFromHTML(this.getEmptyState(tabName, 'files'));
            container.innerHTML = '';
            container.appendChild(emptyFragment);
            return;
        }
        
        // Render file browser filters (search, sync status, subdirectory)
        const filtersHtml = this.renderFileBrowserFilters(tabName, files);
        
        // Apply filters
        const filteredFiles = this.applyFileFilters(tabName, files);
        
        // Render bulk actions bar if it doesn't exist
        this.ensureBulkActionsBar(tabName);
        
        // Render file cards (matching List View card design)
        const cardsHtml = this.renderFileCards(tabName, filteredFiles);
        
        // Use DocumentFragment for better performance (Task 1.2.1)
        const fragment = this.createFragmentFromHTML(filtersHtml + cardsHtml);
        container.innerHTML = '';
        container.appendChild(fragment);
        
        // Attach file browser event listeners
        this.attachFileBrowserListeners(tabName);
        this.attachFileBrowserFilterListeners(tabName);
        
        // Setup virtual scrolling if enabled
        if (this.virtualScrollEnabled && files.length >= this.VIRTUAL_SCROLL_THRESHOLD) {
            this.setupVirtualScrolling(tabName, files);
        }
    }
    
    /**
     * Setup virtual scrolling for file browser
     */
    setupVirtualScrolling(tabName, allFiles) {
        const container = this.getCachedElement(`${tabName}-file-scroll-container`);
        if (!container) return;
        
        // Store reference to container and files
        this.scrollContainers[tabName] = {
            container: container,
            allFiles: allFiles,
            scrollTop: 0
        };
        
        // Initialize visible range
        this.updateVisibleRange(tabName);
        
        // Attach scroll listener
        const handleScroll = () => {
            const scrollTop = container.scrollTop;
            const containerHeight = container.clientHeight;
            
            // Calculate visible range
            const start = Math.max(0, Math.floor(scrollTop / this.ROW_HEIGHT) - this.OVERSCAN);
            const visibleCount = Math.ceil(containerHeight / this.ROW_HEIGHT);
            const end = Math.min(allFiles.length, start + visibleCount + this.OVERSCAN * 2);
            
            // Update if range changed
            if (start !== this.visibleRange.start || end !== this.visibleRange.end) {
                this.visibleRange = { start, end };
                this.scrollContainers[tabName].scrollTop = scrollTop;
                
                // Re-render only the visible portion
                this.renderFileTableRows(tabName, allFiles);
            }
        };
        
        // Use throttled scroll handler with requestAnimationFrame for smooth performance (Task 1.2.3)
        let scrollTimeout;
        const throttledScrollHandler = () => {
            if (scrollTimeout) {
                cancelAnimationFrame(scrollTimeout);
            }
            scrollTimeout = requestAnimationFrame(handleScroll);
        };
        container.addEventListener('scroll', throttledScrollHandler, { passive: true });
        
        // Handle resize
        const handleResize = () => {
            this.updateVisibleRange(tabName);
            this.renderFileTableRows(tabName, allFiles);
        };
        
        window.addEventListener('resize', handleResize);
        
        // Store cleanup function
        this.scrollContainers[tabName].cleanup = () => {
            window.removeEventListener('resize', handleResize);
        };
    }
    
    /**
     * Update visible range based on scroll position
     */
    updateVisibleRange(tabName) {
        const scrollData = this.scrollContainers[tabName];
        if (!scrollData) return;
        
        const container = scrollData.container;
        const scrollTop = container.scrollTop;
        const containerHeight = container.clientHeight;
        
        const start = Math.max(0, Math.floor(scrollTop / this.ROW_HEIGHT) - this.OVERSCAN);
        const visibleCount = Math.ceil(containerHeight / this.ROW_HEIGHT);
        const end = Math.min(scrollData.allFiles.length, start + visibleCount + this.OVERSCAN * 2);
        
        this.visibleRange = { start, end };
    }
    
    /**
     * Render only the visible rows of the file table
     */
    renderFileTableRows(tabName, allFiles) {
        const tbody = document.getElementById(`${tabName}-file-table-body`);
        if (!tbody) return;
        
        const visibleFiles = allFiles.slice(this.visibleRange.start, this.visibleRange.end);
        
        const rows = visibleFiles.map((file, index) => {
            const rel = (file.relative_path || file.file_path || '').replace(/\\/g, '/');
            const name = file.name || rel.split('/').pop() || '—';
            const viewerUrl = `${this.mediaEndpoints.viewerBase}${this.encodePath(rel)}`;
            const editUrl = `${this.mediaEndpoints.formEditBase}${this.encodePath(rel)}`;
            const deleteUrl = `${this.mediaEndpoints.deleteBase}${this.encodePath(rel)}`;
            
            // Determine sync status badge colors (matching List View badge colors)
            let syncBadgeClass = 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300';
            if (file.sync_status === 'synced') {
                syncBadgeClass = 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400';
            } else if (file.sync_status === 'out_of_sync') {
                syncBadgeClass = 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400';
            }
            
            return `
                <tr class="bg-white dark:bg-gray-800 border-b border-gray-100 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors duration-150">
                    <td class="px-4 py-3">
                        <input type="checkbox" 
                               class="file-checkbox rounded border-gray-300 dark:border-gray-600 text-blue-600 dark:text-blue-400 focus:ring-blue-500" 
                               data-file-path="${this.escapeHtml(rel)}"
                               data-tab="${tabName}">
                    </td>
                    <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-gray-100">
                        <a href="${viewerUrl}" class="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 hover:underline transition-colors">${this.escapeHtml(name)}</a>
                    </td>
                    <td class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">${this.formatDate(file.modified)}</td>
                    <td class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">${this.formatSize(file.size)}</td>
                    <td class="px-4 py-3">
                        <span class="px-2 py-0.5 rounded-full text-xs font-medium ${syncBadgeClass}">
                            ${this.escapeHtml(file.sync_status || 'unknown')}
                        </span>
                    </td>
                    <td class="px-4 py-3">
                        <div class="flex flex-wrap gap-2 items-center">
                            <a href="${viewerUrl}" 
                               class="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 hover:underline transition-colors"
                               title="View file">
                                View
                            </a>
                            <a href="${editUrl}" 
                               onclick="event.stopPropagation();"
                               class="p-1.5 text-gray-400 dark:text-gray-500 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-lg transition-all"
                               title="Edit file"
                               aria-label="Edit file ${this.escapeHtml(name)}">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                </svg>
                            </a>
                            <a href="${deleteUrl}" 
                               class="text-sm text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 hover:underline transition-colors"
                               title="Delete file">
                                Delete
                            </a>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
        
        // Calculate spacer heights
        const topSpacerHeight = this.visibleRange.start * this.ROW_HEIGHT;
        const bottomSpacerHeight = (allFiles.length - this.visibleRange.end) * this.ROW_HEIGHT;
        
        const topSpacer = `<tr class="virtual-scroll-spacer" style="height: ${topSpacerHeight}px; display: table-row;"><td colspan="6" style="height: ${topSpacerHeight}px; padding: 0;"></td></tr>`;
        const bottomSpacer = `<tr class="virtual-scroll-spacer" style="height: ${bottomSpacerHeight}px; display: table-row;"><td colspan="6" style="height: ${bottomSpacerHeight}px; padding: 0;"></td></tr>`;
        
        // Use DocumentFragment for better performance (Task 1.2.1)
        const fragment = this.createFragmentFromHTML(topSpacer + rows + bottomSpacer);
        tbody.innerHTML = '';
        tbody.appendChild(fragment);
        
        // Re-attach event listeners for checkboxes
        this.attachFileBrowserListeners(tabName);
    }
    
    /**
     * Ensure bulk actions bar exists
     */
    ensureBulkActionsBar(tabName) {
        // Check if bulk actions bar already exists
        let bulkBar = document.getElementById('bulk-actions-bar');
        if (bulkBar) return;
        
        // Find the files view container
        const filesView = document.getElementById(`${tabName}-files-view`);
        if (!filesView) return;
        
        // Create bulk actions bar (matching List View button styling)
        bulkBar = document.createElement('div');
        bulkBar.id = 'bulk-actions-bar';
        bulkBar.className = 'hidden mb-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg shadow-sm';
        bulkBar.innerHTML = `
            <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div class="flex items-center gap-3">
                    <span class="text-sm font-medium text-gray-900 dark:text-gray-100">
                        <span id="selected-count" class="font-semibold text-blue-600 dark:text-blue-400">0</span> file(s) selected
                    </span>
                </div>
                <div class="flex items-center gap-2 flex-wrap">
                    <button id="bulk-sync-btn" 
                            class="inline-flex items-center px-4 py-2 bg-blue-600 dark:bg-blue-500 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium transition-colors shadow-sm"
                            disabled>
                        <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
                        </svg>
                        Sync Selected
                    </button>
                    <button id="bulk-delete-btn" 
                            class="inline-flex items-center px-4 py-2 bg-red-600 dark:bg-red-500 text-white rounded-lg hover:bg-red-700 dark:hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium transition-colors shadow-sm"
                            disabled>
                        <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                        Delete Selected
                    </button>
                    <button id="clear-selection-btn" 
                            class="px-3 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg text-sm font-medium transition-colors"
                            onclick="window.unifiedDashboardController.clearFileSelection()">
                        Clear
                    </button>
                </div>
            </div>
        `;
        
        // Insert before the file browser container
        const fileBrowser = document.getElementById(`${tabName}-file-browser`);
        if (fileBrowser && fileBrowser.parentNode) {
            fileBrowser.parentNode.insertBefore(bulkBar, fileBrowser);
        }
        
        // Attach event listeners to new buttons
        const bulkSyncBtn = document.getElementById('bulk-sync-btn');
        if (bulkSyncBtn && !bulkSyncBtn.hasAttribute('data-listener-attached')) {
            bulkSyncBtn.setAttribute('data-listener-attached', 'true');
            bulkSyncBtn.addEventListener('click', () => {
                this.bulkSyncFiles(tabName);
            });
        }
        
        const bulkDeleteBtn = document.getElementById('bulk-delete-btn');
        if (bulkDeleteBtn && !bulkDeleteBtn.hasAttribute('data-listener-attached')) {
            bulkDeleteBtn.setAttribute('data-listener-attached', 'true');
            bulkDeleteBtn.addEventListener('click', () => {
                this.bulkDeleteFiles(tabName);
            });
        }
    }
    
    /**
     * Clear file selection
     */
    clearFileSelection() {
        this.selectedFiles.clear();
        // Uncheck all checkboxes
        document.querySelectorAll('.file-checkbox').forEach(cb => {
            cb.checked = false;
        });
        this.updateBulkActions();
    }
    
    /**
     * Render sync status
     */
    renderSyncStatus(tabName, syncData) {
        // Try both naming conventions
        const container = document.getElementById(`${tabName}-sync-status`) || 
                         document.querySelector(`#${tabName}-sync-view #${tabName}-sync-status`);
        if (!container) {
            console.warn(`Container not found for rendering ${tabName} sync status`);
            return;
        }
        
        const byType = syncData.by_type || {};
        const tabData = byType[tabName] || {};
        
        const html = `
            <div class="space-y-4">
                <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Sync Status for ${tabName}</h3>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div class="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                            <p class="text-sm text-gray-600 dark:text-gray-400">Total Files</p>
                            <p class="text-2xl font-bold text-gray-900 dark:text-gray-100">${tabData.total || 0}</p>
                        </div>
                        <div class="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                            <p class="text-sm text-gray-600 dark:text-gray-400">Synced</p>
                            <p class="text-2xl font-bold text-gray-900 dark:text-gray-100">${tabData.synced || 0}</p>
                        </div>
                        <div class="p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                            <p class="text-sm text-gray-600 dark:text-gray-400">Out of Sync</p>
                            <p class="text-2xl font-bold text-gray-900 dark:text-gray-100">${tabData.out_of_sync || 0}</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML = html;
    }
    
    /**
     * Render file cards (matching List View card design)
     */
    renderFileCards(tabName, files) {
        if (!files || files.length === 0) {
            return `
                <div class="text-center py-12">
                    <svg class="w-12 h-12 mx-auto text-gray-400 dark:text-gray-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                    </svg>
                    <p class="text-gray-500 dark:text-gray-400 text-sm font-medium">No files found</p>
                    <p class="text-gray-400 dark:text-gray-500 text-xs mt-1">Try adjusting your filters or check back later</p>
                </div>
            `;
        }
        
        const cards = files.map(file => {
            const rel = (file.relative_path || file.file_path || '').replace(/\\/g, '/');
            const name = file.name || rel.split('/').pop() || '—';
            const viewerUrl = `${this.mediaEndpoints.viewerBase}${this.encodePath(rel)}`;
            const editUrl = `${this.mediaEndpoints.formEditBase}${this.encodePath(rel)}`;
            const deleteUrl = `${this.mediaEndpoints.deleteBase}${this.encodePath(rel)}`;
            
            // Determine sync status badge colors (matching List View badge colors)
            let syncBadgeClass = 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300';
            if (file.sync_status === 'synced') {
                syncBadgeClass = 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400';
            } else if (file.sync_status === 'out_of_sync') {
                syncBadgeClass = 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400';
            }
            
            // Determine file type/category badge
            const fileExtension = name.split('.').pop()?.toLowerCase() || 'file';
            const categoryBadge = tabName || fileExtension;
            
            return `
                <div class="p-6 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-md hover:shadow-lg hover:-translate-y-1 transition-all duration-200 cursor-pointer group"
                     data-item-id="${this.escapeHtml(rel)}"
                     data-file-path="${this.escapeHtml(rel)}"
                     onclick="window.location.href='${viewerUrl}'"
                     role="listitem">
                    <div class="flex items-start justify-between">
                        <div class="flex-1 min-w-0">
                            <div class="flex items-center gap-2 mb-2">
                                <div class="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex-shrink-0">
                                    <svg class="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                    </svg>
                                </div>
                                <div class="flex-1 min-w-0">
                                    <h4 class="font-semibold text-gray-900 dark:text-gray-100 mb-1 truncate" title="${this.escapeHtml(name)}">${this.escapeHtml(name)}</h4>
                                    <p class="text-xs text-gray-500 dark:text-gray-400 font-mono truncate" title="${this.escapeHtml(rel)}">${this.escapeHtml(rel)}</p>
                                </div>
                            </div>
                            <div class="flex items-center gap-2 mt-3 flex-wrap">
                                <span class="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400">${this.escapeHtml(categoryBadge)}</span>
                                <span class="px-2 py-0.5 rounded-full text-xs font-medium ${syncBadgeClass}">${this.escapeHtml(file.sync_status || 'unknown')}</span>
                                <span class="text-xs text-gray-500 dark:text-gray-400 font-mono truncate ml-auto" title="${this.escapeHtml(rel)}">${this.escapeHtml(rel)}</span>
                            </div>
                        </div>
                        <div class="flex items-center gap-2 ml-4 flex-shrink-0">
                            <input type="checkbox" 
                                   class="file-checkbox rounded border-gray-300 dark:border-gray-600 text-blue-600 dark:text-blue-400 focus:ring-blue-500"
                                   data-file-path="${this.escapeHtml(rel)}"
                                   data-tab="${tabName}"
                                   onclick="event.stopPropagation();">
                            <a href="${editUrl}" 
                               onclick="event.stopPropagation();"
                               class="p-2 text-gray-400 dark:text-gray-500 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-lg transition-all" 
                               title="Edit file"
                               aria-label="Edit file ${this.escapeHtml(name)}">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                </svg>
                            </a>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        return `
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
                ${cards}
            </div>
        `;
    }
    
    /**
     * Render file table (legacy method - kept for reference)
     */
    renderFileTable(tabName, files) {
        if (!files || files.length === 0) {
            return `
                <div class="text-center py-12">
                    <svg class="w-12 h-12 mx-auto text-gray-400 dark:text-gray-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                    </svg>
                    <p class="text-gray-500 dark:text-gray-400 text-sm font-medium">No files found</p>
                    <p class="text-gray-400 dark:text-gray-500 text-xs mt-1">Try adjusting your filters or check back later</p>
                </div>
            `;
        }
        
        // Determine if virtual scrolling should be enabled
        const useVirtualScroll = this.virtualScrollEnabled && files.length >= this.VIRTUAL_SCROLL_THRESHOLD;
        
        const rows = files.map(file => {
            const rel = (file.relative_path || file.file_path || '').replace(/\\/g, '/');
            const name = file.name || rel.split('/').pop() || '—';
            const viewerUrl = `${this.mediaEndpoints.viewerBase}${this.encodePath(rel)}`;
            const editUrl = `${this.mediaEndpoints.formEditBase}${this.encodePath(rel)}`;
            const deleteUrl = `${this.mediaEndpoints.deleteBase}${this.encodePath(rel)}`;
            
            return `
                <tr class="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td class="px-4 py-3">
                        <input type="checkbox" 
                               class="file-checkbox rounded border-gray-300 dark:border-gray-600 text-blue-600 dark:text-blue-400 focus:ring-blue-500" 
                               data-file-path="${this.escapeHtml(rel)}"
                               data-tab="${tabName}">
                    </td>
                    <td class="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">
                        <a href="${viewerUrl}" class="text-blue-600 dark:text-blue-400 hover:underline">${this.escapeHtml(name)}</a>
                    </td>
                    <td class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">${this.formatDate(file.modified)}</td>
                    <td class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">${this.formatSize(file.size)}</td>
                    <td class="px-4 py-3">
                        <span class="px-2 py-0.5 rounded text-xs ${file.sync_status === 'synced' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'}">
                            ${this.escapeHtml(file.sync_status || 'unknown')}
                        </span>
                    </td>
                    <td class="px-4 py-3 flex flex-wrap gap-2 items-center">
                        <a href="${viewerUrl}" class="text-sm text-blue-600 dark:text-blue-400 hover:underline">View</a>
                        <a href="${editUrl}" class="text-sm text-gray-600 dark:text-gray-400 hover:underline">Edit</a>
                        <a href="${deleteUrl}" class="text-sm text-red-600 dark:text-red-400 hover:underline">Delete</a>
                    </td>
                </tr>
            `;
        }).join('');
        
        // Calculate spacer heights for virtual scrolling
        // Initialize visibleRange if not set (for non-virtual scrolling case)
        if (!this.visibleRange) {
            this.visibleRange = { start: 0, end: files.length };
        }
        const topSpacerHeight = useVirtualScroll ? this.visibleRange.start * this.ROW_HEIGHT : 0;
        const bottomSpacerHeight = useVirtualScroll 
            ? (files.length - this.visibleRange.end) * this.ROW_HEIGHT 
            : 0;
        
        const topSpacer = useVirtualScroll 
            ? `<tr class="virtual-scroll-spacer" style="height: ${topSpacerHeight}px; display: table-row;"><td colspan="6" style="height: ${topSpacerHeight}px; padding: 0;"></td></tr>`
            : '';
        const bottomSpacer = useVirtualScroll
            ? `<tr class="virtual-scroll-spacer" style="height: ${bottomSpacerHeight}px; display: table-row;"><td colspan="6" style="height: ${bottomSpacerHeight}px; padding: 0;"></td></tr>`
            : '';
        
        return `
            <div class="overflow-x-auto ${useVirtualScroll ? 'virtual-scroll-container' : ''}" 
                 id="${tabName}-file-scroll-container"
                 style="${useVirtualScroll ? 'max-height: 600px; overflow-y: auto;' : ''}">
                <table class="w-full text-left">
                    <thead class="bg-gray-50 dark:bg-gray-900/50 sticky top-0 z-10 border-b border-gray-200 dark:border-gray-700">
                        <tr>
                            <th class="px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                <input type="checkbox" 
                                       id="select-all-files-${tabName}" 
                                       class="rounded border-gray-300 dark:border-gray-600 text-blue-600 dark:text-blue-400 focus:ring-blue-500">
                            </th>
                            <th class="px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Name</th>
                            <th class="px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Modified</th>
                            <th class="px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Size</th>
                            <th class="px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Sync</th>
                            <th class="px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                        </tr>
                    </thead>
                    <tbody id="${tabName}-file-table-body">
                        ${topSpacer}
                        ${rows}
                        ${bottomSpacer}
                    </tbody>
                </table>
            </div>
        `;
    }
    
    /**
     * Render file browser filters
     */
    renderFileBrowserFilters(tabName, files) {
        const filters = this.fileFilters[tabName] || {};
        
        // Extract unique subdirectories for relationships and postman
        let subdirectories = [];
        if (tabName === 'relationships' || tabName === 'postman') {
            const subdirSet = new Set();
            files.forEach(file => {
                if (file.subdirectory) {
                    subdirSet.add(file.subdirectory);
                }
            });
            subdirectories = Array.from(subdirSet).sort();
        }
        
        let filtersHtml = '<div class="mb-4 flex flex-wrap items-center gap-3 p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg border border-gray-200 dark:border-gray-700">';
        
        // Search input
        filtersHtml += `
            <div class="flex-1 min-w-[200px]">
                <label for="${tabName}-file-search" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Search</label>
                <input 
                    type="text" 
                    id="${tabName}-file-search" 
                    value="${this.escapeHtml(filters.search || '')}"
                    placeholder="Search files..."
                    class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500">
            </div>
        `;
        
        // Subdirectory filter (for relationships and postman)
        if (subdirectories.length > 0) {
            const subdirectoryLabels = {
                'by-page': 'By Page',
                'by-endpoint': 'By Endpoint',
                'collection': 'Collection',
                'environment': 'Environment',
                'configurations': 'Configurations'
            };
            
            filtersHtml += `
                <div class="min-w-[180px]">
                    <label for="${tabName}-file-subdirectory" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Subdirectory</label>
                    <select 
                        id="${tabName}-file-subdirectory" 
                        class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500">
                        <option value="">All Subdirectories</option>
                        ${subdirectories.map(subdir => `
                            <option value="${this.escapeHtml(subdir)}" ${filters.subdirectory === subdir ? 'selected' : ''}>
                                ${this.escapeHtml(subdirectoryLabels[subdir] || subdir)}
                            </option>
                        `).join('')}
                    </select>
                </div>
            `;
        }
        
        // Sync status filter
        filtersHtml += `
            <div class="min-w-[150px]">
                <label for="${tabName}-file-sync-status" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Sync Status</label>
                <select 
                    id="${tabName}-file-sync-status" 
                    class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option value="">All Status</option>
                    <option value="synced" ${filters.syncStatus === 'synced' ? 'selected' : ''}>Synced</option>
                    <option value="out_of_sync" ${filters.syncStatus === 'out_of_sync' ? 'selected' : ''}>Out of Sync</option>
                    <option value="unknown" ${filters.syncStatus === 'unknown' ? 'selected' : ''}>Unknown</option>
                </select>
            </div>
        `;
        
        // Sort by
        filtersHtml += `
            <div class="min-w-[120px]">
                <label for="${tabName}-file-sort-by" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Sort By</label>
                <select 
                    id="${tabName}-file-sort-by" 
                    class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option value="name" ${filters.sortBy === 'name' ? 'selected' : ''}>Name</option>
                    <option value="modified" ${filters.sortBy === 'modified' ? 'selected' : ''}>Modified</option>
                    <option value="size" ${filters.sortBy === 'size' ? 'selected' : ''}>Size</option>
                </select>
            </div>
        `;
        
        // Sort order
        filtersHtml += `
            <div class="min-w-[100px]">
                <label for="${tabName}-file-sort-order" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Order</label>
                <select 
                    id="${tabName}-file-sort-order" 
                    class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option value="asc" ${filters.sortOrder === 'asc' ? 'selected' : ''}>Ascending</option>
                    <option value="desc" ${filters.sortOrder === 'desc' ? 'selected' : ''}>Descending</option>
                </select>
            </div>
        `;
        
        filtersHtml += '</div>';
        return filtersHtml;
    }
    
    /**
     * Attach file browser filter event listeners
     */
    attachFileBrowserFilterListeners(tabName) {
        // Search input
        const searchInput = document.getElementById(`${tabName}-file-search`);
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchInput.searchTimeout);
                searchInput.searchTimeout = setTimeout(() => {
                    this.fileFilters[tabName].search = e.target.value;
                    this.renderFiles(tabName, this.files[tabName]);
                }, 300);
            });
        }
        
        // Subdirectory filter
        const subdirectorySelect = document.getElementById(`${tabName}-file-subdirectory`);
        if (subdirectorySelect) {
            subdirectorySelect.addEventListener('change', (e) => {
                this.fileFilters[tabName].subdirectory = e.target.value || '';
                this.renderFiles(tabName, this.files[tabName]);
            });
        }
        
        // Sync status filter
        const syncStatusSelect = document.getElementById(`${tabName}-file-sync-status`);
        if (syncStatusSelect) {
            syncStatusSelect.addEventListener('change', (e) => {
                this.fileFilters[tabName].syncStatus = e.target.value || '';
                this.renderFiles(tabName, this.files[tabName]);
            });
        }
        
        // Sort by
        const sortBySelect = document.getElementById(`${tabName}-file-sort-by`);
        if (sortBySelect) {
            sortBySelect.addEventListener('change', (e) => {
                this.fileFilters[tabName].sortBy = e.target.value || 'name';
                this.renderFiles(tabName, this.files[tabName]);
            });
        }
        
        // Sort order
        const sortOrderSelect = document.getElementById(`${tabName}-file-sort-order`);
        if (sortOrderSelect) {
            sortOrderSelect.addEventListener('change', (e) => {
                this.fileFilters[tabName].sortOrder = e.target.value || 'asc';
                this.renderFiles(tabName, this.files[tabName]);
            });
        }
    }
    
    /**
     * Apply file filters
     */
    applyFileFilters(tabName, files) {
        let filtered = [...files];
        const filters = this.fileFilters[tabName] || {};
        
        // Search filter
        if (filters.search) {
            const searchTerm = filters.search.toLowerCase();
            filtered = filtered.filter(file =>
                (file.name || '').toLowerCase().includes(searchTerm) ||
                (file.relative_path || '').toLowerCase().includes(searchTerm)
            );
        }
        
        // Sync status filter
        if (filters.syncStatus) {
            filtered = filtered.filter(file => file.sync_status === filters.syncStatus);
        }
        
        // Subdirectory filter (for relationships and postman)
        if (filters.subdirectory) {
            filtered = filtered.filter(file => file.subdirectory === filters.subdirectory);
        }
        
        // Sorting
        filtered.sort((a, b) => {
            let aVal, bVal;
            switch (filters.sortBy) {
                case 'modified':
                    aVal = new Date(a.modified || 0);
                    bVal = new Date(b.modified || 0);
                    break;
                case 'size':
                    aVal = a.size || 0;
                    bVal = b.size || 0;
                    break;
                default: // 'name'
                    aVal = (a.name || '').toLowerCase();
                    bVal = (b.name || '').toLowerCase();
            }
            
            if (aVal < bVal) return filters.sortOrder === 'asc' ? -1 : 1;
            if (aVal > bVal) return filters.sortOrder === 'asc' ? 1 : -1;
            return 0;
        });
        
        return filtered;
    }
    
    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Primary tab switching
        // The server renders only the active tab's content ({% if active_tab == 'pages' %}...{% elif %}...).
        // Other tab panels are not in the DOM. So we must navigate (allow default) when switching to a
        // different tab. Same-tab click: prevent default and refresh data.
        // Use a.tab-button[data-tab] so we don't attach to inputs (e.g. search has data-tab).
        document.querySelectorAll('a.tab-button[data-tab]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tab = btn.getAttribute('data-tab');
                if (!tab) return;
                if (tab !== this.activeTab) {
                    // Different tab: allow navigation so server renders that tab's content
                    return;
                }
                e.preventDefault();
                // Same tab: refresh current view
                this.loadView(tab, this.viewMode);
            });
        });
        
        // View mode switching - handle both click events and prevent default navigation
        document.querySelectorAll('.view-mode-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const viewMode = btn.getAttribute('data-view-mode');
                if (viewMode && viewMode !== this.viewMode) {
                    this.loadView(this.activeTab, viewMode);
                }
            });
        });
        
        // List view filters
        this.attachListFilters();
        
        // Attach bulk action buttons if they exist
        const bulkSyncBtn = document.getElementById('bulk-sync-btn');
        if (bulkSyncBtn && !bulkSyncBtn.hasAttribute('data-listener-attached')) {
            bulkSyncBtn.setAttribute('data-listener-attached', 'true');
            bulkSyncBtn.addEventListener('click', () => {
                this.bulkSyncFiles(this.activeTab);
            });
        }
        
        const bulkDeleteBtn = document.getElementById('bulk-delete-btn');
        if (bulkDeleteBtn && !bulkDeleteBtn.hasAttribute('data-listener-attached')) {
            bulkDeleteBtn.setAttribute('data-listener-attached', 'true');
            bulkDeleteBtn.addEventListener('click', () => {
                this.bulkDeleteFiles(this.activeTab);
            });
        }
    }
    
    /**
     * Attach list view filter listeners
     */
    attachListFilters() {
        const tabs = ['pages', 'endpoints', 'relationships', 'postman'];
        tabs.forEach(tab => {
            // Search inputs
            const searchInput = document.getElementById(`${tab}-search`);
            if (searchInput) {
                searchInput.addEventListener('input', (e) => {
                    clearTimeout(searchInput.searchTimeout);
                    searchInput.searchTimeout = setTimeout(() => {
                        this.filters[tab].search = e.target.value;
                        // Update filter chips
                        this.renderFilterChips(tab);
                        this.loadList(tab);
                    }, 300);
                });
            }
            
            // Filter selects
            const filterSelects = document.querySelectorAll(`#${tab}-filters select`);
            
            filterSelects.forEach(select => {
                // Map filter IDs to API parameter names
                const filterIdToApiKey = {
                    'page-type-filter': 'page_type',
                    'page-state-filter': 'status',
                    'endpoint-api-version-filter': 'api_version',
                    'endpoint-method-filter': 'method',
                    'relationship-usage-type-filter': 'usage_type',
                    'relationship-usage-context-filter': 'usage_context',
                    'postman-state-filter': 'state'
                };
                
                const filterName = filterIdToApiKey[select.id] || select.id.replace(`${tab}-`, '').replace('-filter', '').replace('-', '_');
                
                select.addEventListener('change', (e) => {
                    if (e.target.value) {
                        this.filters[tab][filterName] = e.target.value;
                    } else {
                        delete this.filters[tab][filterName];
                    }
                    
                    // Reset to page 1 when filters change
                    this.currentPage[tab] = 1;
                    
                    this.loadList(tab);
                });
            });
        });
    }
    
    /**
     * Render filter chips for active filters
     */
    renderFilterChips(tabName) {
        const container = document.getElementById(`${tabName}-filter-chips`);
        if (!container) {
            return;
        }
        
        const filters = this.filters[tabName] || {};
        const activeFilters = [];
        
        // Map filter keys to display names
        const filterDisplayNames = {
            'page_type': 'Page Type',
            'status': 'Status',
            'api_version': 'API Version',
            'method': 'Method',
            'usage_type': 'Usage Type',
            'usage_context': 'Usage Context',
            'state': 'State',
            'search': 'Search'
        };
        
        // Collect active filters
        Object.keys(filters).forEach(key => {
            const value = filters[key];
            if (value && value !== '' && value !== null && value !== undefined) {
                activeFilters.push({
                    key: key,
                    name: filterDisplayNames[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                    value: value
                });
            }
        });
        
        // Render chips
        if (activeFilters.length === 0) {
            container.innerHTML = '';
            return;
        }
        
        let chipsHtml = '<div class="flex flex-wrap items-center gap-2 mb-4">';
        activeFilters.forEach(filter => {
            const displayValue = filter.value.length > 30 ? filter.value.substring(0, 30) + '...' : filter.value;
            chipsHtml += `
                <span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 border border-blue-200 dark:border-blue-800">
                    <span class="text-xs text-blue-600 dark:text-blue-400">${this.escapeHtml(filter.name)}:</span>
                    <span>${this.escapeHtml(displayValue)}</span>
                    <button 
                        onclick="window.unifiedDashboardController.removeFilter('${tabName}', '${filter.key}')"
                        class="ml-1 text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-full p-0.5"
                        aria-label="Remove ${this.escapeHtml(filter.name)} filter"
                        title="Remove filter">
                        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </span>
            `;
        });
        chipsHtml += '</div>';
        
        container.innerHTML = chipsHtml;
    }
    
    /**
     * Remove a filter and reload data
     */
    removeFilter(tabName, filterKey) {
        const filters = this.filters[tabName] || {};
        
        if (filterKey === 'search') {
            // Clear search input
            const searchInput = document.getElementById(`${tabName}-search`);
            if (searchInput) {
                searchInput.value = '';
            }
        } else {
            // Clear filter select
            const filterSelects = document.querySelectorAll(`#${tabName}-filters select`);
            filterSelects.forEach(select => {
                const filterIdToApiKey = {
                    'page-type-filter': 'page_type',
                    'page-state-filter': 'status',
                    'endpoint-api-version-filter': 'api_version',
                    'endpoint-method-filter': 'method',
                    'relationship-usage-type-filter': 'usage_type',
                    'relationship-usage-context-filter': 'usage_context',
                    'postman-state-filter': 'state'
                };
                const apiKey = filterIdToApiKey[select.id] || select.id.replace(`${tabName}-`, '').replace('-filter', '').replace('-', '_');
                if (apiKey === filterKey) {
                    select.value = '';
                }
            });
        }
        
        // Remove filter from state
        delete filters[filterKey];
        this.filters[tabName] = filters;
        
        // Reset to page 1
        this.currentPage[tabName] = 1;
        
        // Update filter chips
        this.renderFilterChips(tabName);
        
        // Reload data
        this.loadList(tabName);
    }
    
    /**
     * Attach file browser event listeners
     */
    attachFileBrowserListeners(tabName) {
        // File checkboxes
        const checkboxes = document.querySelectorAll(`#${tabName}-file-browser .file-checkbox`);
        checkboxes.forEach(checkbox => {
            // Remove existing listeners to prevent duplicates
            const newCheckbox = checkbox.cloneNode(true);
            checkbox.parentNode.replaceChild(newCheckbox, checkbox);
            
            newCheckbox.addEventListener('change', (e) => {
                const filePath = newCheckbox.getAttribute('data-file-path');
                if (e.target.checked) {
                    this.selectedFiles.add(filePath);
                } else {
                    this.selectedFiles.delete(filePath);
                }
                this.updateBulkActions();
            });
        });
        
        // Select all checkbox
        const selectAll = document.getElementById(`select-all-files-${tabName}`);
        if (selectAll) {
            // Remove existing listener
            const newSelectAll = selectAll.cloneNode(true);
            selectAll.parentNode.replaceChild(newSelectAll, selectAll);
            
            newSelectAll.addEventListener('change', (e) => {
                const checkboxes = document.querySelectorAll(`#${tabName}-file-browser .file-checkbox`);
                checkboxes.forEach(cb => {
                    cb.checked = e.target.checked;
                    const filePath = cb.getAttribute('data-file-path');
                    if (e.target.checked) {
                        this.selectedFiles.add(filePath);
                    } else {
                        this.selectedFiles.delete(filePath);
                    }
                });
                this.updateBulkActions();
            });
        }
    }
    
    /**
     * Bulk sync files
     */
    async bulkSyncFiles(tabName) {
        const filePaths = Array.from(this.selectedFiles);
        if (filePaths.length === 0) return;
        
        const btn = document.getElementById('bulk-sync-btn');
        const originalText = btn ? btn.textContent : 'Sync';
        if (btn) {
            btn.disabled = true;
            btn.textContent = 'Syncing...';
        }
        
        try {
            const response = await fetch(this.mediaEndpoints.bulkSync, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    resource_type: tabName,
                    direction: 'to_lambda',
                    file_paths: filePaths
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showToast('Files synced successfully!', 'success');
                await this.loadFiles(tabName, true); // Force refresh
                this.selectedFiles.clear();
                this.updateBulkActions();
            } else {
                this.showToast('Bulk sync failed: ' + (data.error || 'Unknown error'), 'error');
            }
        } catch (error) {
            console.error('Bulk sync error:', error);
            this.showToast('Bulk sync failed. Please try again.', 'error');
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.textContent = originalText;
            }
        }
    }
    
    /**
     * Bulk delete files
     */
    async bulkDeleteFiles(tabName) {
        const filePaths = Array.from(this.selectedFiles);
        if (filePaths.length === 0) {
            this.showToast('No files selected', 'warning');
            return;
        }
        
        if (!confirm(`Are you sure you want to delete ${filePaths.length} selected file(s)? This action cannot be undone.`)) {
            return;
        }
        
        const btn = document.getElementById('bulk-delete-btn');
        const originalText = btn ? btn.innerHTML : 'Delete Selected';
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<svg class="w-4 h-4 inline mr-1.5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A9.001 9.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a9.003 9.003 0 01-15.357-2m15.357 2H15" /></svg>Deleting...';
        }
        
        try {
            const deletePromises = filePaths.map(filePath => {
                return fetch(`${this.mediaEndpoints.deleteBase}${this.encodePath(filePath)}/`, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': this.getCsrfToken()
                    }
                });
            });
            
            const responses = await Promise.all(deletePromises);
            const successCount = responses.filter(r => r.ok).length;
            
            if (successCount === filePaths.length) {
                this.showToast(`Successfully deleted ${filePaths.length} file(s)`, 'success');
            } else {
                this.showToast(`Deleted ${successCount} of ${filePaths.length} file(s). Some deletions failed.`, 'warning');
            }
            
            await this.loadFiles(tabName, true); // Force refresh
            this.selectedFiles.clear();
            this.updateBulkActions();
        } catch (error) {
            console.error('Bulk delete error:', error);
            this.showToast('Bulk delete failed. Please try again.', 'error');
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        }
    }
    
    /**
     * Show toast notification
     */
    showToast(message, type = 'info', duration = 3000) {
        // Remove existing toasts
        const existingToasts = document.querySelectorAll('.toast-notification');
        existingToasts.forEach(toast => toast.remove());
        
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast-notification fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg transform translate-x-full transition-transform duration-300`;
        
        // Set colors based on type
        const colors = {
            success: 'bg-green-100 border-green-500 text-green-800 dark:bg-green-900/30 dark:text-green-400',
            error: 'bg-red-100 border-red-500 text-red-800 dark:bg-red-900/30 dark:text-red-400',
            warning: 'bg-yellow-100 border-yellow-500 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
            info: 'bg-blue-100 border-blue-500 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400'
        };
        
        toast.classList.add(...colors[type].split(' '));
        
        // Add icon based on type
        const icons = {
            success: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
            error: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"/></svg>',
            warning: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"/></svg>',
            info: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>'
        };
        
        toast.innerHTML = `
            <div class="flex items-center gap-3">
                <div class="flex-shrink-0">
                    ${icons[type]}
                </div>
                <div class="flex-1 text-sm font-medium">
                    ${this.escapeHtml(message)}
                </div>
                <button type="button" class="flex-shrink-0 ml-2 text-current hover:opacity-75" onclick="this.parentElement.parentElement.remove()">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                </button>
            </div>
        `;
        
        // Add to page
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.classList.remove('translate-x-full');
        }, 100);
        
        // Auto remove
        setTimeout(() => {
            toast.classList.add('translate-x-full');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
    
    /**
     * Update bulk actions UI
     */
    updateBulkActions() {
        const bulkBar = document.getElementById('bulk-actions-bar');
        const selectedCount = document.getElementById('selected-count');
        const bulkSyncBtn = document.getElementById('bulk-sync-btn');
        const bulkDeleteBtn = document.getElementById('bulk-delete-btn');
        
        if (this.selectedFiles.size > 0) {
            if (bulkBar) bulkBar.classList.remove('hidden');
            if (selectedCount) selectedCount.textContent = this.selectedFiles.size;
            if (bulkSyncBtn) bulkSyncBtn.disabled = false;
            if (bulkDeleteBtn) bulkDeleteBtn.disabled = false;
        } else {
            if (bulkBar) bulkBar.classList.add('hidden');
            if (bulkSyncBtn) bulkSyncBtn.disabled = true;
            if (bulkDeleteBtn) bulkDeleteBtn.disabled = true;
        }
    }
    
    /**
     * Show loading state
     */
    showLoading(tabName, viewMode) {
        let container;
        if (viewMode === 'list') {
            container = document.getElementById(`${tabName}-list`) || 
                       document.querySelector(`#${tabName}-list-view #${tabName}-list`);
        } else if (viewMode === 'files') {
            container = document.getElementById(`${tabName}-file-browser`) || 
                       document.querySelector(`#${tabName}-files-view #${tabName}-file-browser`);
        } else {
            container = document.getElementById(`${tabName}-sync-status`) || 
                       document.querySelector(`#${tabName}-sync-view #${tabName}-sync-status`);
        }
        
        if (container) {
            container.innerHTML = '<div class="text-center py-12"><div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div><p class="mt-2 text-gray-500 dark:text-gray-400">Loading...</p></div>';
        }
    }
    
    /**
     * Hide loading state
     */
    hideLoading(tabName, viewMode) {
        // Loading is replaced by content, so nothing to hide
    }
    
    /**
     * Show error state
     */
    showError(tabName, error, viewMode) {
        let container;
        if (viewMode === 'list') {
            container = document.getElementById(`${tabName}-list`) || 
                       document.querySelector(`#${tabName}-list-view #${tabName}-list`);
        } else if (viewMode === 'files') {
            container = document.getElementById(`${tabName}-file-browser`) || 
                       document.querySelector(`#${tabName}-files-view #${tabName}-file-browser`);
        } else {
            container = document.getElementById(`${tabName}-sync-status`) || 
                       document.querySelector(`#${tabName}-sync-view #${tabName}-sync-status`);
        }
        
        if (container) {
            container.innerHTML = `
                <div class="text-center py-12">
                    <div class="text-red-600 dark:text-red-400 mb-2">
                        <svg class="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"/>
                        </svg>
                    </div>
                    <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">Error</h3>
                    <p class="text-sm text-gray-500 dark:text-gray-400">${this.escapeHtml(error.message || 'An error occurred')}</p>
                    <button onclick="window.unifiedDashboardController.loadView('${tabName}', '${viewMode}')" 
                            class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                        Retry
                    </button>
                </div>
            `;
        }
    }
    
    /**
     * Get empty state HTML
     * @param {string} tabName - Tab (pages, endpoints, etc.)
     * @param {string} viewMode - 'list' or 'files'
     * @param {object} [data] - Optional response data; used to show filter-aware message when filters are active
     */
    getEmptyState(tabName, viewMode = 'list', data) {
        if (viewMode === 'files') {
            return '<p class="text-gray-500 dark:text-gray-400 text-center py-12">No files found</p>';
        }
        const filters = this.filters[tabName] || {};
        const hasActiveFilters = Object.keys(filters).some(k => filters[k]);
        const label = tabName === 'pages' ? 'pages' : tabName === 'endpoints' ? 'endpoints' : tabName === 'relationships' ? 'relationships' : 'items';
        if (hasActiveFilters) {
            return `<p class="text-gray-500 dark:text-gray-400 text-center py-12">No ${label} match your current filters.</p><p class="text-sm text-gray-400 dark:text-gray-500 text-center">Try changing or clearing the filters above.</p>`;
        }
        return `<p class="text-gray-500 dark:text-gray-400 text-center py-12">No ${label} found</p>`;
    }
    
    /**
     * Get render function for list view
     */
    getRenderFunction(tabName) {
        // Direct render functions (use local methods to avoid recursion)
        const renderFunctions = {
            pages: this.renderPagesList.bind(this),
            endpoints: this.renderEndpointsList.bind(this),
            relationships: this.renderRelationshipsList.bind(this),
            postman: this.renderPostmanList.bind(this)
        };
        
        return renderFunctions[tabName] || ((items) => {
            return items.map(item => {
                const id = item[`${tabName.slice(0, -1)}_id`] || item.id || 'Unknown';
                return `<div class="p-4 border rounded">${id}</div>`;
            }).join('');
        });
    }
    
    /**
     * Render pages list
     */
    renderPagesList(pages) {
        const pageDetailUrlBase = window.pageDetailUrlBase || '/docs/pages/';
        
        function statusClass(s) {
            if (!s) return 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300';
            if (['published','active','completed'].includes(s)) return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400';
            if (['draft','pending'].includes(s)) return 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400';
            if (['failed','cancelled'].includes(s)) return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400';
            return 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300';
        }
        
        return pages.map(page => {
            const pid = (page.page_id || '').toString();
            const status = (page.metadata && page.metadata.status) || 'draft';
            const route = (page.metadata && page.metadata.route) || '/';
            const pageType = page.page_type || 'docs';
            const title = (page.metadata && page.metadata.content_sections && page.metadata.content_sections.title) || pid;
            const href = pageDetailUrlBase.replace('__PID__', encodeURIComponent(pid));
            const editHref = `/docs/pages/${encodeURIComponent(pid)}/edit/?return_url=${encodeURIComponent(window.location.href)}`;
            // Only show subtitle when it adds information (avoid duplicate title/subtitle when title === pid)
            const showSubtitle = title !== pid;
            const subtitleHtml = showSubtitle ? `<p class="text-xs text-gray-500 dark:text-gray-400 font-mono">${pid.replace(/</g, '&lt;')}</p>` : (route && route !== '/' ? `<p class="text-xs text-gray-500 dark:text-gray-400 font-mono">${route.replace(/</g, '&lt;')}</p>` : '');
            
            return `
            <div class="p-6 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-md hover:shadow-lg hover:-translate-y-1 transition-all duration-200 cursor-pointer" 
                 data-item-id="${pid.replace(/"/g, '&quot;')}"
                 onclick="window.location.href='${href}'"
                 role="listitem">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <div class="flex items-center gap-2 mb-2">
                            <div class="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                                <svg class="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                            </div>
                            <div class="flex-1">
                                <h4 class="font-semibold text-gray-900 dark:text-gray-100 mb-1">${(title || pid || 'Unknown').replace(/</g, '&lt;')}</h4>
                                ${subtitleHtml}
                            </div>
                        </div>
                        <div class="flex items-center gap-2 mt-3">
                            <span class="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400">${pageType.replace(/</g, '&lt;')}</span>
                            <span class="px-2 py-0.5 rounded-full text-xs font-medium ${statusClass(status)}">${(status + '').replace(/</g, '&lt;')}</span>
                            <span class="text-xs text-gray-500 dark:text-gray-400 font-mono">${route.replace(/</g, '&lt;')}</span>
                        </div>
                    </div>
                    <div class="flex items-center gap-2 ml-4">
                        <a href="${href}" 
                           onclick="event.stopPropagation();"
                           class="p-2 text-gray-400 dark:text-gray-500 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-lg transition-all" 
                           title="View" 
                           aria-label="View page ${pid.replace(/"/g, '&quot;')}">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                        </a>
                        <a href="${editHref}" 
                           onclick="event.stopPropagation();"
                           class="p-2 text-gray-400 dark:text-gray-500 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-lg transition-all" 
                           title="Edit" 
                           aria-label="Edit page ${pid.replace(/"/g, '&quot;')}">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                        </a>
                        <a href="/docs/pages/${encodeURIComponent(pid)}/delete/?return_url=${encodeURIComponent(window.location.href)}" 
                           onclick="event.stopPropagation();"
                           class="p-2 text-gray-400 dark:text-gray-500 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-all" 
                           title="Delete" 
                           aria-label="Delete page ${pid.replace(/"/g, '&quot;')}">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                        </a>
                    </div>
                </div>
            </div>
            `;
        }).join('');
    }
    
    /**
     * Render endpoints list
     */
    renderEndpointsList(endpoints) {
        const method = (m) => (m && (m + '').toUpperCase()) || 'QUERY';
        
        return endpoints.map(endpoint => {
            const endpointId = endpoint.endpoint_id || 'Unknown';
            const endpointPath = endpoint.endpoint_path || '';
            const methodValue = method(endpoint.method);
            const apiVersion = endpoint.api_version || '';
            const description = endpoint.description || endpoint.metadata?.description || '';
            const href = `/docs/endpoints/${encodeURIComponent(endpointId)}/`;
            const editHref = `/docs/endpoints/${encodeURIComponent(endpointId)}/edit/?return_url=${encodeURIComponent(window.location.href)}`;
            const deleteHref = `/docs/endpoints/${encodeURIComponent(endpointId)}/delete/?return_url=${encodeURIComponent(window.location.href)}`;
            
            const methodColors = {
                'GET': 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
                'POST': 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
                'PUT': 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400',
                'DELETE': 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400',
                'PATCH': 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400',
                'QUERY': 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
                'MUTATION': 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400'
            };
            
            const methodClass = methodColors[methodValue] || 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300';
            
            return `
            <div class="p-6 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-md hover:shadow-lg hover:-translate-y-1 transition-all duration-200" 
                 data-item-id="${endpointId.replace(/"/g, '&quot;')}"
                 role="listitem">
                <div class="space-y-3">
                    <div class="flex items-start justify-between">
                        <div class="flex items-center gap-3 flex-1">
                            <div class="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                                <svg class="w-5 h-5 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                </svg>
                            </div>
                            <div class="flex-1 min-w-0">
                                <h4 class="font-semibold text-gray-900 dark:text-gray-100 truncate" title="${endpointId.replace(/"/g, '&quot;')}">${endpointId.replace(/</g, '&lt;')}</h4>
                                ${endpointPath ? `<p class="text-xs text-gray-500 dark:text-gray-400 font-mono mt-1 truncate" title="${endpointPath.replace(/"/g, '&quot;')}">${endpointPath.replace(/</g, '&lt;')}</p>` : ''}
                            </div>
                        </div>
                    </div>
                    <div class="flex items-center gap-2 flex-wrap">
                        <span class="px-2.5 py-1 rounded text-xs font-bold ${methodClass}">${methodValue}</span>
                        ${apiVersion ? `<span class="px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400">${apiVersion.replace(/</g, '&lt;')}</span>` : ''}
                    </div>
                    ${description ? `<p class="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">${description.replace(/</g, '&lt;').substring(0, 100)}${description.length > 100 ? '...' : ''}</p>` : ''}
                    <div class="flex items-center gap-2 pt-2 border-t border-gray-200 dark:border-gray-700">
                        <a href="${href}" class="p-2 text-gray-400 dark:text-gray-500 hover:text-purple-600 dark:hover:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/30 rounded-lg transition-all" title="View" aria-label="View endpoint ${endpointId.replace(/"/g, '&quot;')}" onclick="event.stopPropagation();">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                        </a>
                        <a href="${editHref}" class="p-2 text-gray-400 dark:text-gray-500 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-lg transition-all" title="Edit" aria-label="Edit endpoint ${endpointId.replace(/"/g, '&quot;')}" onclick="event.stopPropagation();">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                        </a>
                        <a href="${deleteHref}" class="p-2 text-gray-400 dark:text-gray-500 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-all" title="Delete" aria-label="Delete endpoint ${endpointId.replace(/"/g, '&quot;')}" onclick="event.stopPropagation();">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                        </a>
                    </div>
                </div>
            </div>
            `;
        }).join('');
    }

    /**
     * Render relationships list
     */
    renderRelationshipsList(relationships) {
        return relationships.map(rel => {
            const relationshipId = rel.relationship_id || rel.id || 'Unknown';
            const pagePath = rel.page_path || rel.page_id || 'Unknown';
            const endpointPath = rel.endpoint_path || rel.endpoint_id || 'Unknown';
            const usageType = rel.usage_type || 'primary';
            const usageContext = rel.usage_context || 'data_fetching';
            const method = (rel.method || 'QUERY').toUpperCase();
            
            const href = `/docs/relationships/${encodeURIComponent(relationshipId)}/`;
            const editHref = `/docs/relationships/${encodeURIComponent(relationshipId)}/edit/?return_url=${encodeURIComponent(window.location.href)}`;
            const deleteHref = `/docs/relationships/${encodeURIComponent(relationshipId)}/delete/?return_url=${encodeURIComponent(window.location.href)}`;
            
            return `
            <div class="p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-blue-500 dark:hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-all">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <div class="flex items-center gap-2 mb-2">
                            <span class="px-2 py-1 rounded text-xs font-bold ${method === 'MUTATION' ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400' : 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400'}">${method}</span>
                            <span class="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">${usageType}</span>
                            <span class="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">${usageContext}</span>
                        </div>
                        <div class="space-y-1">
                            <p class="text-sm font-medium text-gray-900 dark:text-gray-100">
                                <span class="text-gray-500 dark:text-gray-400">Page:</span> ${pagePath.replace(/</g, '&lt;')}
                            </p>
                            <p class="text-sm font-medium text-gray-900 dark:text-gray-100">
                                <span class="text-gray-500 dark:text-gray-400">Endpoint:</span> ${endpointPath.replace(/</g, '&lt;')}
                            </p>
                        </div>
                    </div>
                    <div class="flex items-center gap-2 ml-4">
                        <a href="${href}" class="p-2 text-gray-400 dark:text-gray-500 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-lg transition-all" title="View relationship" aria-label="View relationship ${relationshipId}" onclick="event.stopPropagation();">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                        </a>
                        <a href="${editHref}" class="p-2 text-gray-400 dark:text-gray-500 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-lg transition-all" title="Edit relationship" aria-label="Edit relationship ${relationshipId}" onclick="event.stopPropagation();">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                        </a>
                        <a href="${deleteHref}" class="p-2 text-gray-400 dark:text-gray-500 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-all" title="Delete relationship" aria-label="Delete relationship ${relationshipId}" onclick="event.stopPropagation();">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                        </a>
                    </div>
                </div>
            </div>
            `;
        }).join('');
    }
    
    /**
     * Render postman list
     */
    renderPostmanList(postmanConfigs) {
        function stateClass(s) {
            if (!s) return 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300';
            if (['published', 'active'].includes(s)) return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400';
            if (['draft', 'development'].includes(s)) return 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400';
            if (['test'].includes(s)) return 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400';
            return 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300';
        }
        
        return postmanConfigs.map(config => {
            const configId = config.config_id || config.id || 'Unknown';
            const name = config.name || configId;
            const state = config.state || 'draft';
            const collectionCount = config.collection ? (config.collection.item ? config.collection.item.length : 0) : 0;
            const environmentCount = config.environments ? config.environments.length : 0;
            
            const href = `/docs/postman/${encodeURIComponent(configId)}/`;
            const editHref = `/docs/postman/${encodeURIComponent(configId)}/edit/?return_url=${encodeURIComponent(window.location.href)}`;
            const deleteHref = `/docs/postman/${encodeURIComponent(configId)}/delete/?return_url=${encodeURIComponent(window.location.href)}`;
            
            return `
            <div class="p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-blue-500 dark:hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-all">
                <div class="flex items-center justify-between">
                    <div class="flex-1">
                        <h4 class="font-semibold text-gray-900 dark:text-gray-100">${name.replace(/</g, '&lt;')}</h4>
                        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">${configId.replace(/</g, '&lt;')}</p>
                        <div class="flex items-center gap-3 mt-2">
                            <span class="px-2 py-1 rounded-full text-xs font-medium ${stateClass(state)}">${state.replace(/</g, '&lt;')}</span>
                            ${collectionCount > 0 ? `<span class="text-xs text-gray-500 dark:text-gray-400">${collectionCount} collection${collectionCount !== 1 ? 's' : ''}</span>` : ''}
                            ${environmentCount > 0 ? `<span class="text-xs text-gray-500 dark:text-gray-400">${environmentCount} environment${environmentCount !== 1 ? 's' : ''}</span>` : ''}
                        </div>
                    </div>
                    <div class="flex items-center gap-2">
                        <a href="${href}" class="p-2 text-gray-400 dark:text-gray-500 hover:text-amber-600 dark:hover:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-900/30 rounded-lg transition-all" title="View Postman configuration" aria-label="View Postman configuration ${configId}" onclick="event.stopPropagation();">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                        </a>
                        <a href="${editHref}" class="p-2 text-gray-400 dark:text-gray-500 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-lg transition-all" title="Edit Postman configuration" aria-label="Edit Postman configuration ${configId}" onclick="event.stopPropagation();">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                        </a>
                        <a href="${deleteHref}" class="p-2 text-gray-400 dark:text-gray-500 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-all" title="Delete Postman configuration" aria-label="Delete Postman configuration ${configId}" onclick="event.stopPropagation();">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                        </a>
                    </div>
                </div>
            </div>
            `;
        }).join('');
    }
    
    /**
     * Setup pagination
     */
    setupPagination(tabName, data) {
        // Use existing pagination setup if available, but avoid recursion
        if (window.dashboardController && window.dashboardController !== this && window.dashboardController.setupPagination) {
            try {
                window.dashboardController.setupPagination(tabName, data);
                return;
            } catch (e) {
                console.warn('Error setting up pagination via dashboardController:', e);
                // Fall through to local implementation
            }
        }
        
        // Enhanced pagination setup
        const paginationContainer = document.getElementById(`${tabName}-pagination`);
        if (!paginationContainer || !data.pagination) return;
        
        const { page, total_pages, has_previous, has_next, total } = data.pagination;
        const pageSize = this.pageSize[tabName] || this.defaultPageSize;
        const startItem = total === 0 ? 0 : ((page - 1) * pageSize) + 1;
        const endItem = Math.min(page * pageSize, total);
        // When total is 0, show "Page 1 of 1" instead of "Page 1 of 0" to avoid invalid state
        const displayTotalPages = total === 0 ? 1 : Math.max(1, total_pages);
        
        let paginationHtml = '<div class="flex flex-col sm:flex-row items-center justify-between gap-4 mt-6">';
        
        // Item count display
        paginationHtml += `<div class="text-sm text-gray-500 dark:text-gray-400">`;
        if (total > 0) {
            paginationHtml += `Showing <span class="font-medium text-gray-700 dark:text-gray-300">${startItem}-${endItem}</span> of <span class="font-medium text-gray-700 dark:text-gray-300">${total}</span> items`;
        } else {
            paginationHtml += 'No items found';
        }
        paginationHtml += `</div>`;
        
        // Pagination controls
        paginationHtml += '<div class="flex items-center gap-2">';
        
        // Page size selector
        paginationHtml += `
            <div class="flex items-center gap-2">
                <label for="${tabName}-page-size" class="text-sm text-gray-500 dark:text-gray-400">Per page:</label>
                <select id="${tabName}-page-size" 
                        class="px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        onchange="window.unifiedDashboardController.changePageSize('${tabName}', this.value)">
                    <option value="10" ${pageSize === 10 ? 'selected' : ''}>10</option>
                    <option value="20" ${pageSize === 20 ? 'selected' : ''}>20</option>
                    <option value="50" ${pageSize === 50 ? 'selected' : ''}>50</option>
                    <option value="100" ${pageSize === 100 ? 'selected' : ''}>100</option>
                </select>
            </div>
        `;
        
        // First page button
        paginationHtml += `
            <button 
                onclick="window.unifiedDashboardController.goToPage('${tabName}', 1)"
                ${!has_previous ? 'disabled' : ''}
                class="px-3 py-1.5 text-sm font-medium border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                title="First page">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
                </svg>
            </button>
        `;
        
        // Previous page button
        paginationHtml += `
            <button 
                onclick="window.unifiedDashboardController.goToPage('${tabName}', ${page - 1})"
                ${!has_previous ? 'disabled' : ''}
                class="px-3 py-1.5 text-sm font-medium border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed">
                Previous
            </button>
        `;
        
        // Page number input (use displayTotalPages so empty result shows "Page 1 of 1" not "of 0")
        paginationHtml += `
            <div class="flex items-center gap-1">
                <span class="text-sm text-gray-500 dark:text-gray-400">Page</span>
                <input 
                    type="number" 
                    id="${tabName}-page-input"
                    min="1" 
                    max="${displayTotalPages}" 
                    value="${total === 0 ? 1 : page}"
                    class="w-16 px-2 py-1.5 text-sm text-center border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    onchange="window.unifiedDashboardController.goToPage('${tabName}', parseInt(this.value) || 1)"
                    onkeypress="if(event.key==='Enter') { window.unifiedDashboardController.goToPage('${tabName}', parseInt(this.value) || 1); }"
                    aria-label="Page number">
                <span class="text-sm text-gray-500 dark:text-gray-400">of ${displayTotalPages}</span>
            </div>
        `;
        
        // Next page button
        paginationHtml += `
            <button 
                onclick="window.unifiedDashboardController.goToPage('${tabName}', ${page + 1})"
                ${!has_next ? 'disabled' : ''}
                class="px-3 py-1.5 text-sm font-medium border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed">
                Next
            </button>
        `;
        
        // Last page button
        paginationHtml += `
            <button 
                onclick="window.unifiedDashboardController.goToPage('${tabName}', ${total_pages})"
                ${!has_next ? 'disabled' : ''}
                class="px-3 py-1.5 text-sm font-medium border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                title="Last page">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                </svg>
            </button>
        `;
        
        paginationHtml += '</div></div>';
        paginationContainer.innerHTML = paginationHtml;
    }
    
    /**
     * Go to a specific page
     */
    goToPage(tabName, pageNumber) {
        const paginationContainer = document.getElementById(`${tabName}-pagination`);
        if (!paginationContainer) return;
        
        const pageInput = document.getElementById(`${tabName}-page-input`);
        if (pageInput) {
            const pagination = this.data[tabName]?.pagination;
            if (pagination) {
                const maxPage = pagination.total_pages || 1;
                pageNumber = Math.max(1, Math.min(pageNumber, maxPage));
            }
        }
        
        this.currentPage[tabName] = pageNumber;
        this.updateURL();
        this.loadList(tabName);
    }
    
    /**
     * Change page size
     */
    changePageSize(tabName, newPageSize) {
        const pageSize = parseInt(newPageSize) || this.defaultPageSize;
        this.pageSize[tabName] = pageSize;
        this.savePageSizePreference(pageSize);
        this.currentPage[tabName] = 1; // Reset to first page
        this.updateURL();
        this.loadList(tabName);
    }
    
    /**
     * Initialize bulk operations
     */
    initBulkOperations(tabName, items) {
        // Use existing bulk operations if available, but avoid recursion
        if (window.dashboardController && window.dashboardController !== this && window.dashboardController.initBulkOperations) {
            try {
                window.dashboardController.initBulkOperations(tabName, items);
            } catch (e) {
                console.warn('Error initializing bulk operations:', e);
            }
        }
    }
    
    /**
     * File cache helpers
     */
    getFileCacheKey(tabName) {
        return `files_${tabName}`;
    }
    
    getFileCache(key) {
        const timestamp = this.fileCacheTimestamps.get(key);
        if (!timestamp || Date.now() - timestamp > this.CACHE_DURATION) {
            return null;
        }
        return this.fileCache.get(key);
    }
    
    setFileCache(key, data) {
        this.fileCache.set(key, data);
        this.fileCacheTimestamps.set(key, Date.now());
    }
    
    /**
     * Utility functions
     */
    loadPageSizePreference() {
        try {
            const saved = localStorage.getItem('dashboard_page_size');
            return saved ? parseInt(saved) : 20;
        } catch {
            return 20;
        }
    }
    
    savePageSizePreference(pageSize) {
        try {
            localStorage.setItem('dashboard_page_size', pageSize.toString());
        } catch (e) {
            console.warn('Failed to save page size preference:', e);
        }
    }
    
    formatDate(v) {
        if (v == null) return "—";
        if (typeof v === "number") {
            const d = new Date(v * 1000);
            return isNaN(d.getTime()) ? "—" : d.toLocaleString();
        }
        const d = new Date(v);
        return isNaN(d.getTime()) ? String(v) : d.toLocaleString();
    }
    
    formatSize(n) {
        if (n == null || n === 0) return "0 B";
        const k = 1024;
        const u = ["B", "KB", "MB", "GB"];
        let i = 0;
        while (n >= k && i < u.length - 1) {
            n /= k;
            i++;
        }
        return n.toFixed(1) + " " + u[i];
    }
    
    escapeHtml(s) {
        const div = document.createElement("div");
        div.textContent = s;
        return div.innerHTML;
    }
    
    encodePath(p) {
        return p.split("/").map(s => encodeURIComponent(s)).join("/");
    }
    
    getCsrfToken() {
        const m = document.cookie.match(/csrftoken=([^;]+)/);
        return m ? m[1] : "";
    }
}

// Export for global use
window.UnifiedDashboardController = UnifiedDashboardController;
