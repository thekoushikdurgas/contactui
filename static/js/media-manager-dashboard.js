/**
 * Media Manager Dashboard Controller
 * 
 * Manages Media Manager Dashboard state, pagination, filtering, and data loading
 * Uses direct service calls via AJAX API endpoints
 * 
 * Features:
 * - Tabs: pages, endpoints, relationships, postman
 * - View modes: list, grid
 * - Filtering: resource-specific filters
 * - Search: real-time search
 * - Pagination: client-side pagination
 */

class MediaManagerDashboardController {
    constructor(options = {}) {
        this.options = options;
        
        // Primary tab state
        this.activeTab = options.activeTab || 'pages';
        
        // View mode state (list, grid)
        this.viewMode = options.viewMode || 'list';
        
        // State management
        this.currentPage = {};
        this.pageSize = {};
        this.filters = {};
        this.loading = {};
        this.data = {};
        this.searchQuery = {};
        
        // API endpoints (updated to use unified routes)
        this.apiEndpoints = {
            pages: options.pagesApiUrl || '/docs/api/media-manager/pages/',  // Keep API endpoints as-is for now
            endpoints: options.endpointsApiUrl || '/docs/api/media-manager/endpoints/',
            relationships: options.relationshipsApiUrl || '/docs/api/media-manager/relationships/',
            postman: options.postmanApiUrl || '/docs/api/media-manager/postman/',
            statistics: options.statisticsApiUrl || '/docs/api/media-manager/statistics/',
            health: options.healthApiUrl || '/docs/api/media-manager/health/'
        };
        
        // Pagination instances
        this.paginationInstances = {};
        
        // Default page size
        this.defaultPageSize = 20;
        
        // Debounce timer for search
        this.searchDebounceTimer = null;
        this.SEARCH_DEBOUNCE_MS = 300;
        
        // Initialize
        this.init();
    }
    
    /**
     * Initialize controller
     */
    init() {
        // Parse URL parameters
        this.parseURL();
        
        // Initialize state for all tabs
        const tabs = ['pages', 'endpoints', 'relationships', 'postman'];
        tabs.forEach(tab => {
            this.currentPage[tab] = this.currentPage[tab] || 1;
            this.pageSize[tab] = this.pageSize[tab] || this.defaultPageSize;
            this.filters[tab] = this.filters[tab] || {};
            this.loading[tab] = false;
            this.data[tab] = { items: [], total: 0 };
            this.searchQuery[tab] = '';
        });
        
        // Load initial data for active tab
        this.loadTabData(this.activeTab);
        
        // Attach event listeners
        this.attachEventListeners();
        
        // Render initial data if available
        if (window.initialData) {
            this.renderInitialData();
        }
    }
    
    /**
     * Parse URL parameters
     */
    parseURL() {
        const urlParams = new URLSearchParams(window.location.search);
        
        // Get active tab
        const tab = urlParams.get('tab');
        if (tab && ['pages', 'endpoints', 'relationships', 'postman'].includes(tab)) {
            this.activeTab = tab;
        }
        
        // Get view mode
        const view = urlParams.get('view');
        if (view && ['list', 'grid'].includes(view)) {
            this.viewMode = view;
        }
        
        // Get pagination params
        const page = parseInt(urlParams.get('page')) || 1;
        const perPage = parseInt(urlParams.get('per_page')) || this.defaultPageSize;
        
        this.currentPage[this.activeTab] = page;
        this.pageSize[this.activeTab] = perPage;
        
        // Get search query
        const search = urlParams.get('search');
        if (search) {
            this.searchQuery[this.activeTab] = search;
        }
        
        // Get filters based on tab
        this.parseFilters();
    }
    
    /**
     * Parse filters from URL parameters
     */
    parseFilters() {
        const urlParams = new URLSearchParams(window.location.search);
        const tab = this.activeTab;
        
        if (tab === 'pages') {
            this.filters[tab] = {
                page_type: urlParams.get('page_type') || '',
                status: urlParams.get('status') || '',
                state: urlParams.get('state') || '',
                include_drafts: urlParams.get('include_drafts') !== 'false',
                include_deleted: urlParams.get('include_deleted') === 'true'
            };
        } else if (tab === 'endpoints') {
            this.filters[tab] = {
                api_version: urlParams.get('api_version') || '',
                method: urlParams.get('method') || '',
                state: urlParams.get('state') || '',
                lambda_service: urlParams.get('lambda_service') || ''
            };
        } else if (tab === 'relationships') {
            this.filters[tab] = {
                page_id: urlParams.get('page_id') || '',
                endpoint_id: urlParams.get('endpoint_id') || '',
                usage_type: urlParams.get('usage_type') || '',
                usage_context: urlParams.get('usage_context') || ''
            };
        } else if (tab === 'postman') {
            this.filters[tab] = {
                state: urlParams.get('state') || ''
            };
        }
    }
    
    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Tab switching
        document.querySelectorAll('.tab-button[data-tab]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const tab = btn.getAttribute('data-tab');
                this.switchTab(tab);
            });
        });
        
        // View mode switching
        document.querySelectorAll('.view-mode-btn[data-view-mode]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const viewMode = btn.getAttribute('data-view-mode');
                this.switchViewMode(viewMode);
            });
        });
        
        // Search inputs
        document.querySelectorAll('[data-search-input]').forEach(input => {
            input.addEventListener('input', (e) => {
                const tab = e.target.getAttribute('data-tab');
                this.handleSearch(tab, e.target.value);
            });
        });
        
        // Filter dropdowns
        this.attachFilterListeners();
    }
    
    /**
     * Attach filter listeners
     */
    attachFilterListeners() {
        // Pages filters
        const pageTypeFilter = document.getElementById('page-type-filter');
        const pageStatusFilter = document.getElementById('page-status-filter');
        const pageStateFilter = document.getElementById('page-state-filter');
        
        if (pageTypeFilter) {
            pageTypeFilter.addEventListener('change', () => {
                this.filters.pages.page_type = pageTypeFilter.value;
                this.loadTabData('pages');
            });
        }
        if (pageStatusFilter) {
            pageStatusFilter.addEventListener('change', () => {
                this.filters.pages.status = pageStatusFilter.value;
                this.loadTabData('pages');
            });
        }
        if (pageStateFilter) {
            pageStateFilter.addEventListener('change', () => {
                this.filters.pages.state = pageStateFilter.value;
                this.loadTabData('pages');
            });
        }
        
        // Endpoints filters
        const endpointApiVersionFilter = document.getElementById('endpoint-api-version-filter');
        const endpointMethodFilter = document.getElementById('endpoint-method-filter');
        const endpointStateFilter = document.getElementById('endpoint-state-filter');
        
        if (endpointApiVersionFilter) {
            endpointApiVersionFilter.addEventListener('change', () => {
                this.filters.endpoints.api_version = endpointApiVersionFilter.value;
                this.loadTabData('endpoints');
            });
        }
        if (endpointMethodFilter) {
            endpointMethodFilter.addEventListener('change', () => {
                this.filters.endpoints.method = endpointMethodFilter.value;
                this.loadTabData('endpoints');
            });
        }
        if (endpointStateFilter) {
            endpointStateFilter.addEventListener('change', () => {
                this.filters.endpoints.state = endpointStateFilter.value;
                this.loadTabData('endpoints');
            });
        }
        
        // Relationships filters
        const relationshipUsageTypeFilter = document.getElementById('relationship-usage-type-filter');
        const relationshipUsageContextFilter = document.getElementById('relationship-usage-context-filter');
        
        if (relationshipUsageTypeFilter) {
            relationshipUsageTypeFilter.addEventListener('change', () => {
                this.filters.relationships.usage_type = relationshipUsageTypeFilter.value;
                this.loadTabData('relationships');
            });
        }
        if (relationshipUsageContextFilter) {
            relationshipUsageContextFilter.addEventListener('change', () => {
                this.filters.relationships.usage_context = relationshipUsageContextFilter.value;
                this.loadTabData('relationships');
            });
        }
        
        // Postman filters
        const postmanStateFilter = document.getElementById('postman-state-filter');
        
        if (postmanStateFilter) {
            postmanStateFilter.addEventListener('change', () => {
                this.filters.postman.state = postmanStateFilter.value;
                this.loadTabData('postman');
            });
        }
    }
    
    /**
     * Switch tab
     */
    switchTab(tab) {
        if (this.activeTab === tab) return;
        
        this.activeTab = tab;
        
        // Update URL
        this.updateURL();
        
        // Update UI
        this.updateTabUI();
        
        // Load data if not already loaded
        if (!this.data[tab].items.length) {
            this.loadTabData(tab);
        } else {
            this.renderTab(tab);
        }
    }
    
    /**
     * Switch view mode
     */
    switchViewMode(viewMode) {
        if (this.viewMode === viewMode) return;
        
        this.viewMode = viewMode;
        
        // Update URL
        this.updateURL();
        
        // Update UI
        this.updateViewModeUI();
        
        // Re-render current tab
        this.renderTab(this.activeTab);
    }
    
    /**
     * Handle search input
     */
    handleSearch(tab, query) {
        this.searchQuery[tab] = query;
        
        // Debounce search
        clearTimeout(this.searchDebounceTimer);
        this.searchDebounceTimer = setTimeout(() => {
            this.loadTabData(tab);
        }, this.SEARCH_DEBOUNCE_MS);
    }
    
    /**
     * Load tab data from API
     */
    async loadTabData(tab) {
        if (this.loading[tab]) return;
        
        this.loading[tab] = true;
        this.showLoading(tab);
        
        try {
            const params = new URLSearchParams();
            
            // Add pagination
            params.append('limit', this.pageSize[tab]);
            params.append('offset', (this.currentPage[tab] - 1) * this.pageSize[tab]);
            
            // Add search
            if (this.searchQuery[tab]) {
                params.append('search', this.searchQuery[tab]);
            }
            
            // Add filters
            const filters = this.filters[tab] || {};
            Object.keys(filters).forEach(key => {
                if (filters[key]) {
                    params.append(key, filters[key]);
                }
            });
            
            // Fetch data
            const response = await fetch(`${this.apiEndpoints[tab]}?${params.toString()}`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                const data = result.data;
                
                // Store data
                if (tab === 'pages') {
                    this.data[tab] = {
                        items: data.pages || [],
                        total: data.total || 0
                    };
                } else if (tab === 'endpoints') {
                    this.data[tab] = {
                        items: data.endpoints || [],
                        total: data.total || 0
                    };
                } else if (tab === 'relationships') {
                    this.data[tab] = {
                        items: data.relationships || [],
                        total: data.total || 0
                    };
                } else if (tab === 'postman') {
                    this.data[tab] = {
                        items: data.configurations || [],
                        total: data.total || 0
                    };
                }
                
                // Render
                this.renderTab(tab);
                this.updateFilterChips(tab);
                this.setupPagination(tab);
            } else {
                throw new Error(result.message || 'Failed to load data');
            }
        } catch (error) {
            console.error(`Error loading ${tab} data:`, error);
            this.showError(tab, error.message);
        } finally {
            this.loading[tab] = false;
        }
    }
    
    /**
     * Render tab content
     */
    renderTab(tab) {
        const data = this.data[tab];
        
        if (this.viewMode === 'list') {
            this.renderListView(tab, data.items);
        } else if (this.viewMode === 'grid') {
            this.renderGridView(tab, data.items);
        }
    }
    
    /**
     * Render list view
     */
    renderListView(tab, items) {
        const container = document.getElementById(`${tab}-list`);
        if (!container) return;
        
        if (!items || items.length === 0) {
            container.innerHTML = `
                <div class="text-center py-12">
                    <p class="text-gray-500 dark:text-gray-400">No ${tab} found</p>
                </div>
            `;
            return;
        }
        
        if (tab === 'pages') {
            container.innerHTML = items.map(page => this.renderPageCard(page)).join('');
        } else if (tab === 'endpoints') {
            container.innerHTML = items.map(endpoint => this.renderEndpointCard(endpoint)).join('');
        } else if (tab === 'relationships') {
            container.innerHTML = items.map(rel => this.renderRelationshipCard(rel)).join('');
        } else if (tab === 'postman') {
            container.innerHTML = items.map(config => this.renderPostmanCard(config)).join('');
        }
    }
    
    /**
     * Render grid view
     */
    renderGridView(tab, items) {
        const container = document.getElementById(`${tab}-grid`);
        if (!container) return;
        
        if (!items || items.length === 0) {
            container.innerHTML = `
                <div class="text-center py-12">
                    <p class="text-gray-500 dark:text-gray-400">No ${tab} found</p>
                </div>
            `;
            return;
        }
        
        // Grid view uses same card rendering as list view
        this.renderListView(tab, items);
    }
    
    /**
     * Render page card
     */
    renderPageCard(page) {
        const pageId = page.page_id || 'Unknown';
        const status = (page.metadata && page.metadata.status) || 'draft';
        const pageType = page.page_type || 'docs';
        const detailUrl = `/docs/pages/${encodeURIComponent(pageId)}/detail/`;
        
        return `
            <div class="p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-blue-500 dark:hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-all">
                <div class="flex items-center justify-between">
                    <div class="flex-1">
                        <h4 class="font-semibold text-gray-900 dark:text-gray-100">${this.escapeHtml(pageId)}</h4>
                        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Type: ${this.escapeHtml(pageType)}</p>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="px-2 py-1 rounded-full text-xs font-medium ${this.getStatusClass(status)}">${this.escapeHtml(status)}</span>
                        <a href="${detailUrl}" class="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 text-sm font-medium">View</a>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * Render endpoint card
     */
    renderEndpointCard(endpoint) {
        const endpointId = endpoint.endpoint_id || 'Unknown';
        const method = (endpoint.method || 'GET').toUpperCase();
        const endpointPath = endpoint.endpoint_path || '';
        const detailUrl = `/docs/endpoints/${encodeURIComponent(endpointId)}/detail/`;
        
        return `
            <div class="p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-purple-500 dark:hover:border-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/20 transition-all">
                <div class="flex items-center justify-between">
                    <div class="flex-1">
                        <div class="flex items-center gap-2">
                            <span class="px-2 py-1 rounded text-xs font-bold ${method === 'MUTATION' ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400' : 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400'}">${method}</span>
                            <h4 class="font-semibold text-gray-900 dark:text-gray-100">${this.escapeHtml(endpointId)}</h4>
                        </div>
                        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">${this.escapeHtml(endpointPath)}</p>
                    </div>
                    <a href="${detailUrl}" class="text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 text-sm font-medium">View</a>
                </div>
            </div>
        `;
    }
    
    /**
     * Render relationship card
     */
    renderRelationshipCard(rel) {
        const pagePath = rel.page_path || rel.page_id || 'Unknown';
        const endpointPath = rel.endpoint_path || rel.endpoint_id || 'Unknown';
        const method = (rel.method || 'QUERY').toUpperCase();
        const usageType = rel.usage_type || 'primary';
        const detailUrl = `/docs/relationships/${encodeURIComponent(rel.relationship_id || '')}/detail/`;
        
        return `
            <div class="p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-green-500 dark:hover:border-green-400 hover:bg-green-50 dark:hover:bg-green-900/20 transition-all">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <div class="flex items-center gap-2 mb-2">
                            <span class="px-2 py-1 rounded text-xs font-bold ${method === 'MUTATION' ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400' : 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400'}">${method}</span>
                            <span class="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">${this.escapeHtml(usageType)}</span>
                        </div>
                        <div class="space-y-1">
                            <p class="text-sm font-medium text-gray-900 dark:text-gray-100">
                                <span class="text-gray-500 dark:text-gray-400">Page:</span> ${this.escapeHtml(pagePath)}
                            </p>
                            <p class="text-sm font-medium text-gray-900 dark:text-gray-100">
                                <span class="text-gray-500 dark:text-gray-400">Endpoint:</span> ${this.escapeHtml(endpointPath)}
                            </p>
                        </div>
                    </div>
                    <a href="${detailUrl}" class="text-green-600 dark:text-green-400 hover:text-green-700 dark:hover:text-green-300 text-sm font-medium">View</a>
                </div>
            </div>
        `;
    }
    
    /**
     * Render Postman card
     */
    renderPostmanCard(config) {
        const configId = config.config_id || config.id || 'Unknown';
        const name = config.name || configId;
        const state = config.state || 'draft';
        const detailUrl = `/docs/postman/${encodeURIComponent(configId)}/detail/`;
        
        return `
            <div class="p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-amber-500 dark:hover:border-amber-400 hover:bg-amber-50 dark:hover:bg-amber-900/20 transition-all">
                <div class="flex items-center justify-between">
                    <div class="flex-1">
                        <h4 class="font-semibold text-gray-900 dark:text-gray-100">${this.escapeHtml(name)}</h4>
                        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">${this.escapeHtml(configId)}</p>
                        <span class="mt-2 inline-block px-2 py-1 rounded-full text-xs font-medium ${this.getStatusClass(state)}">${this.escapeHtml(state)}</span>
                    </div>
                    <a href="${detailUrl}" class="text-amber-600 dark:text-amber-400 hover:text-amber-700 dark:hover:text-amber-300 text-sm font-medium">View</a>
                </div>
            </div>
        `;
    }
    
    /**
     * Render initial data from server
     */
    renderInitialData() {
        if (window.initialData) {
            const data = JSON.parse(window.initialData);
            
            if (this.activeTab === 'pages' && data.pages) {
                this.data.pages = {
                    items: data.pages,
                    total: data.total || 0
                };
                this.renderTab('pages');
            } else if (this.activeTab === 'endpoints' && data.endpoints) {
                this.data.endpoints = {
                    items: data.endpoints,
                    total: data.total || 0
                };
                this.renderTab('endpoints');
            } else if (this.activeTab === 'relationships' && data.relationships) {
                this.data.relationships = {
                    items: data.relationships,
                    total: data.total || 0
                };
                this.renderTab('relationships');
            } else if (this.activeTab === 'postman' && data.postman) {
                this.data.postman = {
                    items: data.postman,
                    total: data.total || 0
                };
                this.renderTab('postman');
            }
        }
    }
    
    /**
     * Update tab UI
     */
    updateTabUI() {
        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active');
            btn.setAttribute('aria-selected', 'false');
        });
        
        const activeBtn = document.querySelector(`.tab-button[data-tab="${this.activeTab}"]`);
        if (activeBtn) {
            activeBtn.classList.add('active');
            activeBtn.setAttribute('aria-selected', 'true');
        }
        
        // Update tab content visibility
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        
        const activeContent = document.getElementById(`${this.activeTab}-content`);
        if (activeContent) {
            activeContent.classList.add('active');
        }
    }
    
    /**
     * Update view mode UI
     */
    updateViewModeUI() {
        // Update view mode buttons
        document.querySelectorAll('.view-mode-btn').forEach(btn => {
            btn.classList.remove('bg-blue-600', 'text-white');
            btn.classList.add('text-gray-700', 'dark:text-gray-300');
        });
        
        const activeBtn = document.querySelector(`.view-mode-btn[data-view-mode="${this.viewMode}"]`);
        if (activeBtn) {
            activeBtn.classList.add('bg-blue-600', 'text-white');
            activeBtn.classList.remove('text-gray-700', 'dark:text-gray-300');
        }
        
        // Update view mode content visibility
        document.querySelectorAll('.view-mode-content').forEach(content => {
            content.classList.add('hidden');
            content.classList.remove('active');
        });
        
        const activeView = document.getElementById(`${this.activeTab}-${this.viewMode}-view`);
        if (activeView) {
            activeView.classList.remove('hidden');
            activeView.classList.add('active');
        }
    }
    
    /**
     * Update filter chips
     */
    updateFilterChips(tab) {
        const container = document.getElementById(`${tab}-filter-chips`);
        if (!container) return;
        
        const filters = this.filters[tab] || {};
        const chips = [];
        
        Object.keys(filters).forEach(key => {
            if (filters[key]) {
                chips.push(`
                    <span class="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400">
                        ${key}: ${filters[key]}
                        <button onclick="window.mediaManagerDashboardController.removeFilter('${tab}', '${key}')" class="hover:text-blue-900 dark:hover:text-blue-300">
                            ×
                        </button>
                    </span>
                `);
            }
        });
        
        if (this.searchQuery[tab]) {
            chips.push(`
                <span class="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400">
                    search: ${this.searchQuery[tab]}
                    <button onclick="window.mediaManagerDashboardController.removeSearch('${tab}')" class="hover:text-blue-900 dark:hover:text-blue-300">
                        ×
                    </button>
                </span>
            `);
        }
        
        container.innerHTML = chips.join('');
    }
    
    /**
     * Remove filter
     */
    removeFilter(tab, key) {
        if (this.filters[tab]) {
            this.filters[tab][key] = '';
            this.loadTabData(tab);
        }
    }
    
    /**
     * Remove search
     */
    removeSearch(tab) {
        this.searchQuery[tab] = '';
        const searchInput = document.querySelector(`[data-search-input][data-tab="${tab}"]`);
        if (searchInput) {
            searchInput.value = '';
        }
        this.loadTabData(tab);
    }
    
    /**
     * Setup pagination
     */
    setupPagination(tab) {
        const container = document.getElementById(`${tab}-pagination`);
        if (!container) return;
        
        const total = this.data[tab].total || 0;
        const pageSize = this.pageSize[tab];
        const currentPage = this.currentPage[tab];
        const totalPages = Math.ceil(total / pageSize);
        
        if (totalPages <= 1) {
            container.innerHTML = '';
            return;
        }
        
        const paginationHTML = this.generatePaginationHTML(tab, currentPage, totalPages);
        container.innerHTML = paginationHTML;
        
        // Attach pagination event listeners
        container.querySelectorAll('a[data-page]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = parseInt(link.getAttribute('data-page'));
                this.goToPage(tab, page);
            });
        });
    }
    
    /**
     * Generate pagination HTML
     */
    generatePaginationHTML(tab, currentPage, totalPages) {
        const pages = [];
        
        // Previous button
        if (currentPage > 1) {
            pages.push(`<a href="#" data-page="${currentPage - 1}" class="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700">Previous</a>`);
        }
        
        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
                if (i === currentPage) {
                    pages.push(`<span class="px-3 py-2 rounded-lg bg-blue-600 text-white">${i}</span>`);
                } else {
                    pages.push(`<a href="#" data-page="${i}" class="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700">${i}</a>`);
                }
            } else if (i === currentPage - 3 || i === currentPage + 3) {
                pages.push(`<span class="px-3 py-2">...</span>`);
            }
        }
        
        // Next button
        if (currentPage < totalPages) {
            pages.push(`<a href="#" data-page="${currentPage + 1}" class="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700">Next</a>`);
        }
        
        return `<div class="flex items-center justify-center gap-2">${pages.join('')}</div>`;
    }
    
    /**
     * Go to page
     */
    goToPage(tab, page) {
        this.currentPage[tab] = page;
        this.updateURL();
        this.loadTabData(tab);
    }
    
    /**
     * Update URL without reload
     */
    updateURL() {
        const params = new URLSearchParams();
        
        params.append('tab', this.activeTab);
        params.append('view', this.viewMode);
        params.append('page', this.currentPage[this.activeTab]);
        params.append('per_page', this.pageSize[this.activeTab]);
        
        // Add search
        if (this.searchQuery[this.activeTab]) {
            params.append('search', this.searchQuery[this.activeTab]);
        }
        
        // Add filters
        const filters = this.filters[this.activeTab] || {};
        Object.keys(filters).forEach(key => {
            if (filters[key]) {
                params.append(key, filters[key]);
            }
        });
        
        const newURL = `${window.location.pathname}?${params.toString()}`;
        window.history.pushState({}, '', newURL);
    }
    
    /**
     * Show loading state
     */
    showLoading(tab) {
        const container = document.getElementById(`${tab}-list`) || document.getElementById(`${tab}-grid`);
        if (container) {
            container.innerHTML = `
                <div class="text-center py-12">
                    <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    <p class="mt-4 text-gray-500 dark:text-gray-400">Loading ${tab}...</p>
                </div>
            `;
        }
    }
    
    /**
     * Show error state
     */
    showError(tab, message) {
        const container = document.getElementById(`${tab}-list`) || document.getElementById(`${tab}-grid`);
        if (container) {
            container.innerHTML = `
                <div class="text-center py-12">
                    <p class="text-red-500 dark:text-red-400">Error: ${this.escapeHtml(message)}</p>
                    <button onclick="window.mediaManagerDashboardController.loadTabData('${tab}')" class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                        Retry
                    </button>
                </div>
            `;
        }
    }
    
    /**
     * Get status class
     */
    getStatusClass(status) {
        if (!status) return 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300';
        if (['published', 'active', 'completed'].includes(status)) return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400';
        if (['draft', 'pending'].includes(status)) return 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400';
        if (['failed', 'cancelled'].includes(status)) return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400';
        return 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300';
    }
    
    /**
     * Escape HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}
