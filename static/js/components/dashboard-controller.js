/**
 * Dashboard Controller
 * 
 * Manages dashboard state, pagination, filtering, and data loading for all 4 tabs:
 * - Pages
 * - Endpoints
 * - Relationships
 * - Postman
 */

class DashboardController {
    constructor(options = {}) {
        // Store options for later use
        this.options = options;
        
        this.activeTab = options.activeTab || 'pages';
        this.currentPage = {};
        this.pageSize = {};
        this.filters = {};
        this.loading = {};
        this.data = {};
        
        // API endpoints (graph tab doesn't need API endpoint - uses dedicated viewer)
        this.apiEndpoints = {
            pages: options.pagesApiUrl || '/docs/api/dashboard/pages/',
            endpoints: options.endpointsApiUrl || '/docs/api/dashboard/endpoints/',
            relationships: options.relationshipsApiUrl || '/docs/api/dashboard/relationships/',
            postman: options.postmanApiUrl || '/docs/api/dashboard/postman/',
            graph: null  // Graph tab uses dedicated RelationshipGraphViewer
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
            this.filters[tab] = this.filters[tab] || {};
            this.loading[tab] = false;
        });
        
        // Load initial data for active tab
        this.loadTab(this.activeTab);
        
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
        
        // Get pagination params
        const page = parseInt(urlParams.get('page')) || 1;
        const pageSize = parseInt(urlParams.get('page_size')) || this.defaultPageSize;
        
        this.currentPage[this.activeTab] = page;
        this.pageSize[this.activeTab] = pageSize;
        
        // Get filters (stored as JSON in URL)
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
        url.searchParams.set('page', this.currentPage[this.activeTab].toString());
        url.searchParams.set('page_size', this.pageSize[this.activeTab].toString());
        
        // Store filters as JSON
        const filters = this.filters[this.activeTab];
        if (filters && Object.keys(filters).length > 0) {
            url.searchParams.set('filters', encodeURIComponent(JSON.stringify(filters)));
        } else {
            url.searchParams.delete('filters');
        }
        
        window.history.pushState({}, '', url);
    }
    
    /**
     * Load data for a specific tab
     */
    async loadTab(tabName, page = null, pageSize = null) {
        // Graph tab uses dedicated RelationshipGraphViewer, skip standard loading
        if (tabName === 'graph') {
            this.activeTab = tabName;
            this.updateURL();
            return;
        }
        
        if (this.loading[tabName]) {
            return; // Already loading
        }
        
        // Check if target DOM container exists
        const targetContainer = document.getElementById(`${tabName}-list`);
        
        this.activeTab = tabName;
        this.currentPage[tabName] = page || this.currentPage[tabName] || 1;
        this.pageSize[tabName] = pageSize || this.pageSize[tabName] || this.defaultPageSize;
        
        this.loading[tabName] = true;
        this.showLoading(tabName);
        
        try {
            const data = await this.fetchTabData(tabName);
            this.data[tabName] = data;
            this.renderTab(tabName, data);
            this.setupPagination(tabName, data);
        } catch (error) {
            console.error(`Error loading ${tabName}:`, error);
            this.showError(tabName, error);
        } finally {
            this.loading[tabName] = false;
        }
        
        this.updateURL();
    }
    
    /**
     * Fetch data for a tab from API
     */
    async fetchTabData(tabName) {
        const url = new URL(this.apiEndpoints[tabName], window.location.origin);
        url.searchParams.set('page', this.currentPage[tabName].toString());
        url.searchParams.set('page_size', this.pageSize[tabName].toString());
        
        // Add filters
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
     * Render tab content
     */
    renderTab(tabName, data) {
        const container = document.getElementById(`${tabName}-list`);
        if (!container) return;
        
        const items = data.items || [];
        const renderFunction = this.getRenderFunction(tabName);
        
        if (items.length === 0) {
            container.innerHTML = this.getEmptyState(tabName);
            return;
        }
        
        container.innerHTML = renderFunction(items);
        
        // Initialize bulk operations if enabled
        if (this.options.enableBulkOperations !== false && typeof BulkOperations !== 'undefined') {
            this.initBulkOperations(tabName, items);
        }
    }
    
    /**
     * Initialize bulk operations for a tab
     */
    initBulkOperations(tabName, items) {
        const container = document.getElementById(`${tabName}-list`);
        if (!container) return;
        
        // Destroy existing bulk operations if any
        if (this.bulkOperations[tabName]) {
            this.bulkOperations[tabName].clearSelection();
        }
        
        // Create bulk operations instance
        this.bulkOperations[tabName] = new BulkOperations(container.id, {
            selectAllText: 'Select All',
            selectedText: 'selected',
            actions: this.getBulkActions(tabName),
            onSelectionChange: (selectedIds) => {
                this.updateSelectedItems(tabName, selectedIds);
            },
            onBulkAction: (actionId, selectedIds) => {
                this.handleBulkAction(tabName, actionId, selectedIds);
            }
        });
        
        // Register items
        const itemElements = container.querySelectorAll('[data-item-id]');
        itemElements.forEach(element => {
            const itemId = element.getAttribute('data-item-id');
            if (itemId) {
                this.bulkOperations[tabName].registerItem(itemId, element);
            }
        });
    }
    
    /**
     * Get bulk actions for a tab
     */
    getBulkActions(tabName) {
        const actions = [];
        
        if (tabName === 'pages') {
            actions.push(
                {
                    id: 'delete',
                    text: 'Delete',
                    type: 'danger',
                    icon: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>',
                    confirm: 'Are you sure you want to delete {count} page(s)?',
                    handler: (selectedIds) => {
                        this.handleBulkDelete('pages', selectedIds);
                    }
                }
            );
        } else if (tabName === 'endpoints') {
            actions.push(
                {
                    id: 'delete',
                    text: 'Delete',
                    type: 'danger',
                    icon: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>',
                    confirm: 'Are you sure you want to delete {count} endpoint(s)?',
                    handler: (selectedIds) => {
                        this.handleBulkDelete('endpoints', selectedIds);
                    }
                }
            );
        } else if (tabName === 'relationships') {
            actions.push(
                {
                    id: 'delete',
                    text: 'Delete',
                    type: 'danger',
                    icon: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>',
                    confirm: 'Are you sure you want to delete {count} relationship(s)?',
                    handler: (selectedIds) => {
                        this.handleBulkDelete('relationships', selectedIds);
                    }
                }
            );
        } else if (tabName === 'postman') {
            actions.push(
                {
                    id: 'delete',
                    text: 'Delete',
                    type: 'danger',
                    icon: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>',
                    confirm: 'Are you sure you want to delete {count} Postman configuration(s)?',
                    handler: (selectedIds) => {
                        this.handleBulkDelete('postman', selectedIds);
                    }
                }
            );
        }
        
        return actions;
    }
    
    /**
     * Update selected items styling
     */
    updateSelectedItems(tabName, selectedIds) {
        const container = document.getElementById(`${tabName}-list`);
        if (!container) return;
        
        container.querySelectorAll('[data-item-id]').forEach(element => {
            const itemId = element.getAttribute('data-item-id');
            if (selectedIds.includes(itemId)) {
                element.classList.add('bulk-item-selected');
            } else {
                element.classList.remove('bulk-item-selected');
            }
        });
    }
    
    /**
     * Handle bulk action
     */
    handleBulkAction(tabName, actionId, selectedIds) {
        if (actionId === 'delete') {
            // Confirm deletion
            const confirmed = confirm(`Are you sure you want to delete ${selectedIds.length} item(s)?`);
            if (confirmed) {
                this.handleBulkDelete(tabName, selectedIds);
            }
        } else {
            console.log(`Bulk action ${actionId} on ${selectedIds.length} items in ${tabName}`);
            // Implement other bulk actions here
        }
    }
    
    /**
     * Handle bulk delete
     */
    async handleBulkDelete(tabName, selectedIds) {
        if (selectedIds.length === 0) {
            if (window.accessibilityManager) {
                window.accessibilityManager.announceError('No items selected for deletion');
            }
            return;
        }
        
        // Map tab names to resource types
        const resourceTypeMap = {
            'pages': 'pages',
            'endpoints': 'endpoints',
            'relationships': 'relationships',
            'postman': 'postman'
        };
        
        const resourceType = resourceTypeMap[tabName];
        if (!resourceType) {
            console.error(`Unknown resource type for tab: ${tabName}`);
            return;
        }
        
        try {
            // Show loading state
            if (window.accessibilityManager) {
                window.accessibilityManager.announceLoading(`Deleting ${selectedIds.length} item(s)...`);
            }
            
            // Call bulk delete API
            const response = await fetch('/docs/api/dashboard/bulk-delete/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin',
                body: JSON.stringify({
                    resource_type: resourceType,
                    ids: selectedIds
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                // Announce success
                if (window.accessibilityManager) {
                    window.accessibilityManager.announceSuccess(
                        `Successfully deleted ${result.deleted_count} item(s)`
                    );
                }
                
                // Show errors if any
                if (result.failed_count > 0) {
                    console.warn(`Failed to delete ${result.failed_count} item(s):`, result.errors);
                    if (window.accessibilityManager) {
                        window.accessibilityManager.announceError(
                            `Failed to delete ${result.failed_count} item(s)`
                        );
                    }
                }
                
                // Clear selection and reload tab
                if (this.bulkOperations[tabName]) {
                    this.bulkOperations[tabName].clearSelection();
                }
                
                // Reload the tab to reflect changes
                this.loadTab(tabName);
            } else {
                throw new Error(result.error || 'Delete operation failed');
            }
        } catch (error) {
            console.error('Error deleting items:', error);
            if (window.accessibilityManager) {
                window.accessibilityManager.announceError(
                    `Error deleting items: ${error.message || 'Unknown error'}`
                );
            }
            
            // Show error message
            const container = document.getElementById(`${tabName}-list`);
            if (container) {
                const errorMsg = document.createElement('div');
                errorMsg.className = 'error-message error-message-error error-message-full';
                errorMsg.innerHTML = `
                    <div class="error-message-content">
                        <div class="error-message-icon">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>
                        <div class="error-message-text">
                            <h4 class="error-message-title">Error deleting items</h4>
                            <p class="error-message-description">${error.message || 'Unknown error occurred'}</p>
                        </div>
                    </div>
                `;
                container.insertBefore(errorMsg, container.firstChild);
                
                // Remove error message after 5 seconds
                setTimeout(() => {
                    errorMsg.remove();
                }, 5000);
            }
        }
    }
    
    /**
     * Get render function for tab
     */
    getRenderFunction(tabName) {
        const renderFunctions = {
            pages: this.renderPagesList.bind(this),
            endpoints: this.renderEndpointsList.bind(this),
            relationships: this.renderRelationshipsList.bind(this),
            postman: this.renderPostmanList.bind(this)
        };
        
        return renderFunctions[tabName] || (() => '');
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
                                <p class="text-xs text-gray-500 dark:text-gray-400 font-mono">${pid.replace(/</g, '&lt;')}</p>
                            </div>
                        </div>
                        <div class="flex items-center gap-2 mt-3">
                            <span class="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400">${pageType.replace(/</g, '&lt;')}</span>
                            <span class="px-2 py-0.5 rounded-full text-xs font-medium ${statusClass(status)}">${(status + '').replace(/</g, '&lt;')}</span>
                            <span class="text-xs text-gray-500 dark:text-gray-400 font-mono">${route.replace(/</g, '&lt;')}</span>
                        </div>
                    </div>
                    <div class="flex items-center gap-2 ml-4">
                        <a href="${editHref}" 
                           onclick="event.stopPropagation();"
                           class="p-2 text-gray-400 dark:text-gray-500 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-lg transition-all" 
                           title="Edit" 
                           aria-label="Edit page ${pid}">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                        </a>
                    </div>
                </div>
            </div>
            `;
        }).join('');
    }
    
    /**
     * Render endpoints list (grid view)
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
            const editHref = `/docs/endpoints/${encodeURIComponent(endpointId)}/edit/`;
            
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
                    <!-- Bulk Selection Checkbox -->
                    <div class="flex items-start justify-between">
                        <label class="flex items-center cursor-pointer">
                            <input type="checkbox" 
                                   class="bulk-select-checkbox rounded border-gray-300 dark:border-gray-600 text-purple-600 focus:ring-purple-500" 
                                   data-item-id="${endpointId.replace(/"/g, '&quot;')}"
                                   aria-label="Select ${endpointId.replace(/"/g, '&quot;')}">
                            <span class="ml-2 text-sm text-gray-500 dark:text-gray-400 sr-only">Select for bulk operation</span>
                        </label>
                    </div>
                    
                    <!-- Endpoint Info -->
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
                    
                    <!-- Badges -->
                    <div class="flex items-center gap-2 flex-wrap">
                        <span class="px-2.5 py-1 rounded text-xs font-bold ${methodClass}">${methodValue}</span>
                        ${apiVersion ? `<span class="px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400">${apiVersion.replace(/</g, '&lt;')}</span>` : ''}
                    </div>
                    
                    <!-- Description -->
                    ${description ? `<p class="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">${description.replace(/</g, '&lt;').substring(0, 100)}${description.length > 100 ? '...' : ''}</p>` : ''}
                    
                    <!-- Action Buttons -->
                    <div class="flex items-center gap-2 pt-2 border-t border-gray-200 dark:border-gray-700">
                        <a href="${href}" 
                           class="flex-1 inline-flex items-center justify-center px-3 py-1.5 text-sm font-medium text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded-lg transition-colors"
                           onclick="event.stopPropagation()">
                            <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                            View
                        </a>
                        <a href="${editHref}" 
                           class="flex-1 inline-flex items-center justify-center px-3 py-1.5 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50 rounded-lg transition-colors"
                           onclick="event.stopPropagation()">
                            <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                            Edit
                        </a>
                    </div>
                </div>
            </div>
            `;
        }).join('');
    }
    
    /**
     * Render relationships list (grid view)
     */
    renderRelationshipsList(relationships) {
        return relationships.map(rel => {
            const pagePath = rel.page_path || rel.page_id || 'Unknown';
            const endpointPath = rel.endpoint_path || rel.endpoint_id || 'Unknown';
            const usageType = rel.usage_type || 'primary';
            const usageContext = rel.usage_context || 'data_fetching';
            const method = (rel.method || 'QUERY').toUpperCase();
            const relationshipId = rel.relationship_id || rel.id || '';
            const href = relationshipId ? `/docs/relationships/${encodeURIComponent(relationshipId)}/` : '#';
            const editHref = relationshipId ? `/docs/relationships/${encodeURIComponent(relationshipId)}/edit/` : '#';
            const pageHref = rel.page_id ? `/docs/pages/${encodeURIComponent(rel.page_id)}/` : '#';
            const endpointHref = rel.endpoint_id ? `/docs/endpoints/${encodeURIComponent(rel.endpoint_id)}/` : '#';
            
            const methodColors = {
                'GET': 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
                'POST': 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
                'PUT': 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400',
                'DELETE': 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400',
                'PATCH': 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400',
                'QUERY': 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
                'MUTATION': 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400'
            };
            
            const methodClass = methodColors[method] || 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300';
            
            const usageTypeColors = {
                'primary': 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
                'secondary': 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
                'reference': 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
            };
            
            const usageTypeClass = usageTypeColors[usageType] || 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300';
            
            return `
            <div class="p-6 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-md hover:shadow-lg hover:-translate-y-1 transition-all duration-200" 
                 data-item-id="${relationshipId.replace(/"/g, '&quot;')}"
                 role="listitem">
                <div class="space-y-3">
                    <!-- Bulk Selection Checkbox -->
                    <div class="flex items-start justify-between">
                        <label class="flex items-center cursor-pointer">
                            <input type="checkbox" 
                                   class="bulk-select-checkbox rounded border-gray-300 dark:border-gray-600 text-green-600 focus:ring-green-500" 
                                   data-item-id="${relationshipId.replace(/"/g, '&quot;')}"
                                   aria-label="Select ${relationshipId.replace(/"/g, '&quot;')}">
                            <span class="ml-2 text-sm text-gray-500 dark:text-gray-400 sr-only">Select for bulk operation</span>
                        </label>
                    </div>
                    
                    <!-- Relationship Icon and Connection Visual -->
                    <div class="flex items-center justify-center py-2">
                        <div class="flex items-center gap-2 w-full">
                            <div class="flex-1 flex items-center gap-2 p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                                <svg class="w-4 h-4 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                                <a href="${pageHref}" class="text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 truncate" onclick="event.stopPropagation()" title="${pagePath.replace(/"/g, '&quot;')}">
                                    ${pagePath.replace(/</g, '&lt;')}
                                </a>
                            </div>
                            <div class="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                                <svg class="w-5 h-5 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                                </svg>
                            </div>
                            <div class="flex-1 flex items-center gap-2 p-2 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                                <svg class="w-4 h-4 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                </svg>
                                <a href="${endpointHref}" class="text-sm font-medium text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 truncate" onclick="event.stopPropagation()" title="${endpointPath.replace(/"/g, '&quot;')}">
                                    ${endpointPath.replace(/</g, '&lt;')}
                                </a>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Badges -->
                    <div class="flex items-center gap-2 flex-wrap">
                        <span class="px-2.5 py-1 rounded text-xs font-bold ${methodClass}">${method}</span>
                        <span class="px-2 py-0.5 rounded-full text-xs font-medium ${usageTypeClass}">${usageType}</span>
                        <span class="px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">${usageContext}</span>
                    </div>
                    
                    <!-- Action Buttons -->
                    <div class="flex items-center gap-2 pt-2 border-t border-gray-200 dark:border-gray-700">
                        <a href="${href}" 
                           class="flex-1 inline-flex items-center justify-center px-3 py-1.5 text-sm font-medium text-green-600 dark:text-green-400 hover:text-green-700 dark:hover:text-green-300 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg transition-colors"
                           onclick="event.stopPropagation()">
                            <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                            View
                        </a>
                        <a href="${editHref}" 
                           class="flex-1 inline-flex items-center justify-center px-3 py-1.5 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50 rounded-lg transition-colors"
                           onclick="event.stopPropagation()">
                            <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                            Edit
                        </a>
                    </div>
                </div>
            </div>
            `;
        }).join('');
    }
    
    /**
     * Render Postman list (grid view)
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
            
            return `
            <div class="p-6 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-md hover:shadow-lg hover:-translate-y-1 transition-all duration-200 cursor-pointer" 
                 data-item-id="${configId.replace(/"/g, '&quot;')}"
                 onclick="window.location.href='${href}'"
                 role="listitem">
                <div class="space-y-3">
                    <div class="flex items-start justify-between">
                        <div class="flex items-center gap-3">
                            <div class="p-2 bg-amber-100 dark:bg-amber-900/30 rounded-lg">
                                <svg class="w-5 h-5 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                                </svg>
                            </div>
                            <div>
                                <h4 class="font-semibold text-gray-900 dark:text-gray-100">${name.replace(/</g, '&lt;')}</h4>
                                <p class="text-xs text-gray-500 dark:text-gray-400 font-mono mt-1">${configId.replace(/</g, '&lt;')}</p>
                            </div>
                        </div>
                    </div>
                    <div class="flex items-center gap-2 flex-wrap">
                        <span class="px-2 py-0.5 rounded-full text-xs font-medium ${stateClass(state)}">${state.replace(/</g, '&lt;')}</span>
                    </div>
                    ${(collectionCount > 0 || environmentCount > 0) ? `
                    <div class="flex items-center gap-4 pt-2 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400">
                        ${collectionCount > 0 ? `<span class="flex items-center gap-1">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                            </svg>
                            ${collectionCount} collection${collectionCount !== 1 ? 's' : ''}
                        </span>` : ''}
                        ${environmentCount > 0 ? `<span class="flex items-center gap-1">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                            </svg>
                            ${environmentCount} environment${environmentCount !== 1 ? 's' : ''}
                        </span>` : ''}
                    </div>
                    ` : ''}
                </div>
            </div>
            `;
        }).join('');
    }
    
    /**
     * Get empty state HTML
     */
    getEmptyState(tabName) {
        const emptyStates = {
            pages: `
                <div class="text-center py-12">
                    <p class="text-gray-500 dark:text-gray-400 mb-4">No pages found</p>
                    <a href="/docs/pages/create/" class="inline-block px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium">
                        Create First Page
                    </a>
                </div>
            `,
            endpoints: `
                <div class="text-center py-12">
                    <svg class="w-16 h-16 mx-auto text-gray-400 dark:text-gray-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    <p class="text-gray-500 dark:text-gray-400 mb-2 text-lg font-medium">No endpoints found</p>
                    <p class="text-sm text-gray-400 dark:text-gray-500 mb-4">Get started by creating your first endpoint</p>
                    <a href="/docs/endpoints/create/" class="inline-flex items-center px-4 py-2 bg-purple-600 dark:bg-purple-500 text-white rounded-lg hover:bg-purple-700 dark:hover:bg-purple-600 transition-colors text-sm font-medium">
                        <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                        </svg>
                        Create Endpoint
                    </a>
                </div>
            `,
            relationships: `
                <div class="text-center py-12">
                    <svg class="w-16 h-16 mx-auto text-gray-400 dark:text-gray-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                    </svg>
                    <p class="text-gray-500 dark:text-gray-400 mb-2 text-lg font-medium">No relationships found</p>
                    <p class="text-sm text-gray-400 dark:text-gray-500 mb-4">Connect pages to endpoints to get started</p>
                    <a href="/docs/relationships/create/" class="inline-flex items-center px-4 py-2 bg-green-600 dark:bg-green-500 text-white rounded-lg hover:bg-green-700 dark:hover:bg-green-600 transition-colors text-sm font-medium">
                        <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                        </svg>
                        Create Relationship
                    </a>
                </div>
            `,
            postman: `
                <div class="text-center py-12">
                    <svg class="w-16 h-16 mx-auto text-gray-400 dark:text-gray-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                    </svg>
                    <p class="text-gray-500 dark:text-gray-400 mb-2 text-lg font-medium">No Postman configurations found</p>
                    <p class="text-sm text-gray-400 dark:text-gray-500 mb-4">Create your first Postman collection configuration</p>
                    <a href="/docs/postman/create/" class="inline-flex items-center px-4 py-2 bg-amber-600 dark:bg-amber-500 text-white rounded-lg hover:bg-amber-700 dark:hover:bg-amber-600 transition-colors text-sm font-medium">
                        <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                        </svg>
                        Create Postman Config
                    </a>
                </div>
            `
        };
        
        return emptyStates[tabName] || '<p class="text-gray-500 dark:text-gray-400 text-center py-12">No items found</p>';
    }
    
    /**
     * Setup pagination for a tab
     */
    setupPagination(tabName, data) {
        const containerId = `${tabName}-pagination`;
        let container = document.getElementById(containerId);
        
        if (!container) {
            // Create pagination container
            const listContainer = document.getElementById(`${tabName}-list`);
            if (listContainer && listContainer.parentElement) {
                container = document.createElement('div');
                container.id = containerId;
                listContainer.parentElement.appendChild(container);
            } else {
                return; // Can't find where to insert pagination
            }
        }
        
        const pagination = data.pagination || {};
        
        if (typeof DashboardPagination === 'undefined') {
            console.error('DashboardPagination not loaded');
            return;
        }
        
        // Destroy existing pagination if any
        if (this.paginationInstances[tabName]) {
            // Clean up if needed
        }
        
        // Create new pagination instance
        this.paginationInstances[tabName] = new DashboardPagination(containerId, {
            total: pagination.total || 0,
            currentPage: pagination.page || 1,
            pageSize: pagination.page_size || this.pageSize[tabName],
            updateURL: false, // We handle URL updates ourselves
            onPageChange: (page, pageSize) => {
                this.currentPage[tabName] = page;
                this.pageSize[tabName] = pageSize;
                this.loadTab(tabName, page, pageSize);
            },
            onPageSizeChange: (newPageSize, newPage) => {
                this.pageSize[tabName] = newPageSize;
                this.currentPage[tabName] = newPage;
                this.loadTab(tabName, newPage, newPageSize);
            }
        });
    }
    
    /**
     * Show loading state
     */
    showLoading(tabName) {
        const container = document.getElementById(`${tabName}-list`);
        if (container) {
            // Use skeleton loader for better UX
            const skeletonCount = this.pageSize[tabName] || 5;
            container.innerHTML = this.getSkeletonHTML(tabName, skeletonCount);
        }
        
        // Announce loading to screen readers
        if (window.accessibilityManager) {
            window.accessibilityManager.announceLoading(`Loading ${tabName}...`);
        }
    }
    
    /**
     * Get skeleton HTML for loading state
     */
    getSkeletonHTML(tabName, count = 5) {
        return Array(count).fill(0).map(() => `
            <div class="skeleton-card">
                <div class="skeleton-line skeleton-line-title"></div>
                <div class="skeleton-line skeleton-line-text"></div>
                <div class="skeleton-line skeleton-line-text skeleton-line-short"></div>
            </div>
        `).join('');
    }
    
    /**
     * Show error state
     */
    showError(tabName, error) {
        const errorMessage = error.message || 'Unknown error occurred';
        const container = document.getElementById(`${tabName}-list`);
        
        if (container) {
            container.innerHTML = `
                <div class="error-message error-message-error error-message-full" role="alert">
                    <div class="error-message-content">
                        <div class="error-message-icon">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>
                        <div class="error-message-text">
                            <h4 class="error-message-title">Error loading ${tabName}</h4>
                            <p class="error-message-description">${errorMessage}</p>
                        </div>
                    </div>
                    <div class="error-message-actions">
                        <button type="button" 
                                class="error-message-action-btn" 
                                onclick="window.dashboardController.loadTab('${tabName}')"
                                aria-label="Retry loading ${tabName}">
                            Retry
                        </button>
                    </div>
                </div>
            `;
        }
        
        // Announce error to screen readers
        if (window.accessibilityManager) {
            window.accessibilityManager.announceError(`Error loading ${tabName}: ${errorMessage}`);
        }
    }
    
    /**
     * Apply filter
     */
    applyFilter(tabName, filterKey, filterValue) {
        // #region agent log
        try {
            fetch('http://127.0.0.1:7242/ingest/adfd807a-ef66-43c3-a0f8-1f2210dc4305', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({location: 'dashboard-controller.js:992', message: 'applyFilter called', data: {tabName, filterKey, filterValue, currentFilters: this.filters[tabName]}, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run1', hypothesisId: 'G'})}).catch(()=>{});
        } catch {}
        // #endregion
        
        if (!this.filters[tabName]) {
            this.filters[tabName] = {};
        }
        
        if (filterValue) {
            this.filters[tabName][filterKey] = filterValue;
        } else {
            delete this.filters[tabName][filterKey];
        }
        
        // Reset to page 1 when filters change
        this.currentPage[tabName] = 1;
        
        // #region agent log
        try {
            fetch('http://127.0.0.1:7242/ingest/adfd807a-ef66-43c3-a0f8-1f2210dc4305', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({location: 'dashboard-controller.js:1007', message: 'Calling loadTab after filter', data: {tabName, filters: this.filters[tabName], currentPage: this.currentPage[tabName]}, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run1', hypothesisId: 'G'})}).catch(()=>{});
        } catch {}
        // #endregion
        
        // Reload tab
        this.loadTab(tabName);
    }
    
    /**
     * Clear all filters
     */
    clearFilters(tabName) {
        this.filters[tabName] = {};
        this.currentPage[tabName] = 1;
        this.loadTab(tabName);
    }
    
    /**
     * Attach event listeners
     */
    attachEventListeners() {
        const tabLinks = document.querySelectorAll('a[href*="?tab="]');
        
        // Tab switching - let links navigate normally since tab content is server-rendered
        // Only intercept if we're on the same tab (to reload data without page refresh)
        tabLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                const url = new URL(link.href);
                const targetTab = url.searchParams.get('tab');
                
                // Only prevent default if clicking the same tab (just refresh data)
                if (targetTab === this.activeTab) {
                    e.preventDefault();
                    this.loadTab(targetTab);
                }
                // Otherwise, let the link navigate naturally to the server
            });
        });
        
        // Filter dropdowns (with debouncing for better performance)
        // Pages filters
        // #region agent log
        try {
            const pageTypeFilter = document.getElementById('page-type-filter');
            const pageStateFilter = document.getElementById('page-state-filter');
            fetch('http://127.0.0.1:7242/ingest/adfd807a-ef66-43c3-a0f8-1f2210dc4305', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({location: 'dashboard-controller.js:1041', message: 'Attaching filter listeners', data: {pageTypeFilterFound: !!pageTypeFilter, pageStateFilterFound: !!pageStateFilter, pageTypeFilterVisible: pageTypeFilter ? (pageTypeFilter.offsetParent !== null) : false, pageStateFilterVisible: pageStateFilter ? (pageStateFilter.offsetParent !== null) : false}, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run1', hypothesisId: 'G'})}).catch(()=>{});
        } catch {}
        // #endregion
        this.attachFilterListener('page-type-filter', 'pages', 'page_type');
        this.attachFilterListener('page-state-filter', 'pages', 'status');
        
        // Endpoints filters
        this.attachFilterListener('endpoint-api-version-filter', 'endpoints', 'api_version');
        this.attachFilterListener('endpoint-method-filter', 'endpoints', 'method');
        
        // Relationships filters
        this.attachFilterListener('relationship-usage-type-filter', 'relationships', 'usage_type');
        this.attachFilterListener('relationship-usage-context-filter', 'relationships', 'usage_context');
        
        // Postman filters
        this.attachFilterListener('postman-state-filter', 'postman', 'state');
        
        // Search input debouncing (if search inputs exist)
        const searchInputs = document.querySelectorAll('[data-search-input]');
        searchInputs.forEach(input => {
            const tabName = input.getAttribute('data-tab');
            if (tabName && window.debounce) {
                const debouncedSearch = window.debounce((query) => {
                    this.applyFilter(tabName, 'search', query);
                }, 300);
                
                input.addEventListener('input', (e) => {
                    debouncedSearch(e.target.value);
                });
            }
        });
        
        // Browser back/forward
        window.addEventListener('popstate', () => {
            this.parseURL();
            this.loadTab(this.activeTab);
        });
    }
    
    /**
     * Attach filter listener to a select element
     */
    attachFilterListener(elementId, tabName, filterKey) {
        const element = document.getElementById(elementId);
        
        // #region agent log
        try {
            fetch('http://127.0.0.1:7242/ingest/adfd807a-ef66-43c3-a0f8-1f2210dc4305', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({location: 'dashboard-controller.js:1082', message: 'attachFilterListener called', data: {elementId, tabName, filterKey, elementFound: !!element, elementTagName: element ? element.tagName : null, elementVisible: element ? (element.offsetParent !== null) : false}, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run1', hypothesisId: 'G'})}).catch(()=>{});
        } catch {}
        // #endregion
        
        if (!element) {
            console.warn(`[DashboardController] Filter element not found: ${elementId}`);
            return;
        }
        
        const debouncedFilter = window.debounce ? 
            window.debounce((value) => {
                // #region agent log
                try {
                    fetch('http://127.0.0.1:7242/ingest/adfd807a-ef66-43c3-a0f8-1f2210dc4305', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({location: 'dashboard-controller.js:1088', message: 'Filter value changed', data: {elementId, tabName, filterKey, value}, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run1', hypothesisId: 'G'})}).catch(()=>{});
                } catch {}
                // #endregion
                this.applyFilter(tabName, filterKey, value);
            }, 300) :
            (value) => {
                // #region agent log
                try {
                    fetch('http://127.0.0.1:7242/ingest/adfd807a-ef66-43c3-a0f8-1f2210dc4305', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({location: 'dashboard-controller.js:1090', message: 'Filter value changed (no debounce)', data: {elementId, tabName, filterKey, value}, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run1', hypothesisId: 'G'})}).catch(()=>{});
                } catch {}
                // #endregion
                this.applyFilter(tabName, filterKey, value);
            };
        
        element.addEventListener('change', (e) => {
            // #region agent log
            try {
                fetch('http://127.0.0.1:7242/ingest/adfd807a-ef66-43c3-a0f8-1f2210dc4305', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({location: 'dashboard-controller.js:1092', message: 'Filter change event fired', data: {elementId, tabName, filterKey, value: e.target.value}, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run1', hypothesisId: 'G'})}).catch(()=>{});
            } catch {}
            // #endregion
            debouncedFilter(e.target.value);
        });
        
        // Restore filter value from state
        const currentFilter = this.filters[tabName]?.[filterKey];
        if (currentFilter) {
            element.value = currentFilter;
        }
    }
    
    /**
     * Load page size preference from localStorage
     */
    loadPageSizePreference() {
        if (typeof localStorage !== 'undefined') {
            const stored = localStorage.getItem('docsai_page_size');
            if (stored) {
                const size = parseInt(stored);
                if ([10, 20, 50, 100].includes(size)) {
                    return size;
                }
            }
        }
        return 20; // Default
    }
}

// Export for global use
window.DashboardController = DashboardController;
