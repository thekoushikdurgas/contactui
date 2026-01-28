/**
 * Enhanced Endpoints List Manager
 *
 * Manages the endpoints list with:
 * - Search and autocomplete
 * - Bulk operations
 * - Filtering
 * - Selection management
 */

class EndpointsListEnhanced {
    constructor(options = {}) {
        this.endpoints = options.endpoints || [];
        this.total = options.total || 0;
        this.filteredEndpoints = [...this.endpoints];

        this.init();
    }

    init() {
        this.setupSearch();
        this.setupBulkOperations();
        this.setupFilters();
        this.setupCheckboxes();
    }

    setupSearch() {
        const searchContainer = document.getElementById('search-container');
        if (!searchContainer) return;

        this.searchAutocomplete = new SearchAutocomplete(searchContainer, {
            resourceType: 'endpoints',
            placeholder: 'Search endpoints...',
            onSelect: (suggestion) => {
                // Navigate to selected endpoint
                if (suggestion.endpoint_id) {
                    window.location.href = `/docs/endpoints/${suggestion.endpoint_id}/`;
                }
            }
        });

        searchContainer.addEventListener('search-change', (e) => {
            this.filterEndpoints(e.detail.query);
        });
    }

    setupBulkOperations() {
        const bulkContainer = document.getElementById('bulk-operations-container');
        if (!bulkContainer) return;

        this.bulkOperations = new BulkOperations(bulkContainer, {
            items: this.endpoints,
            itemIdField: 'endpoint_id',
            actions: ['delete'],
            onBulkAction: (action, items) => {
                this.handleBulkAction(action, items);
            }
        });

        bulkContainer.addEventListener('selection-change', (e) => {
            this.updateCheckboxes(e.detail.selectedItems);
        });
    }

    setupFilters() {
        const methodFilter = document.getElementById('method-filter');
        const apiVersionFilter = document.getElementById('api-version-filter');

        if (methodFilter) {
            methodFilter.addEventListener('change', () => {
                this.applyFilters();
            });
        }

        if (apiVersionFilter) {
            apiVersionFilter.addEventListener('change', () => {
                this.applyFilters();
            });
        }
    }

    setupCheckboxes() {
        const checkboxes = document.querySelectorAll('.endpoint-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const endpointId = e.target.getAttribute('data-endpoint-id');
                if (this.bulkOperations) {
                    if (e.target.checked) {
                        this.bulkOperations.selectItem(endpointId);
                    } else {
                        this.bulkOperations.deselectItem(endpointId);
                    }
                }
            });
        });
    }

    filterEndpoints(query) {
        if (!query || query.trim().length === 0) {
            this.filteredEndpoints = [...this.endpoints];
        } else {
            const searchLower = query.toLowerCase();
            this.filteredEndpoints = this.endpoints.filter(endpoint => {
                const endpointId = (endpoint.endpoint_id || '').toLowerCase();
                const endpointPath = (endpoint.endpoint_path || '').toLowerCase();
                const description = (endpoint.description || '').toLowerCase();

                return endpointId.includes(searchLower) ||
                       endpointPath.includes(searchLower) ||
                       description.includes(searchLower);
            });
        }
        this.renderEndpoints();
    }

    applyFilters() {
        const methodFilter = document.getElementById('method-filter');
        const apiVersionFilter = document.getElementById('api-version-filter');

        const methodValue = methodFilter ? methodFilter.value : '';
        const apiVersionValue = apiVersionFilter ? apiVersionFilter.value : '';

        this.filteredEndpoints = this.endpoints.filter(endpoint => {
            if (methodValue && endpoint.method !== methodValue) {
                return false;
            }
            if (apiVersionValue && endpoint.api_version !== apiVersionValue) {
                return false;
            }
            return true;
        });

        this.renderEndpoints();
    }

    renderEndpoints() {
        const grid = document.getElementById('endpoints-grid');
        if (!grid) return;

        if (this.filteredEndpoints.length === 0) {
            grid.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <div class="text-gray-400 dark:text-gray-500 text-lg mb-2">No endpoints found</div>
                    <p class="text-gray-500 dark:text-gray-400">Try adjusting your search or filters</p>
                </div>
            `;
            return;
        }

        grid.innerHTML = this.filteredEndpoints.map(endpoint => `
            <div class="endpoint-card bg-white dark:bg-gray-800 rounded-lg shadow-md dark:shadow-lg border border-gray-200 dark:border-gray-700 p-6 hover:border-purple-500 dark:hover:border-purple-400 transition-all" data-endpoint-id="${endpoint.endpoint_id}">
                <div class="flex items-start gap-3 mb-4">
                    <input
                        type="checkbox"
                        class="endpoint-checkbox w-4 h-4 text-purple-600 rounded border-gray-300 dark:border-gray-600 mt-1"
                        data-endpoint-id="${endpoint.endpoint_id}"
                    />
                    <div class="flex-1">
                        <div class="flex items-center gap-2 mb-2">
                            ${this.getMethodBadge(endpoint.method || 'QUERY')}
                            <h3 class="font-semibold text-gray-900 dark:text-gray-100">${endpoint.endpoint_id || 'Unknown'}</h3>
                        </div>
                        <p class="text-sm text-gray-500 dark:text-gray-400 mb-2">${endpoint.endpoint_path || ''}</p>
                        ${endpoint.description ? `<p class="text-sm text-gray-600 dark:text-gray-300">${endpoint.description.substring(0, 100)}${endpoint.description.length > 100 ? '...' : ''}</p>` : ''}
                    </div>
                </div>
                <div class="flex items-center gap-2 mt-4">
                    <a href="/docs/endpoints/${endpoint.endpoint_id}/" class="text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 text-sm font-medium">
                        View →
                    </a>
                    <a href="/docs/endpoints/${endpoint.endpoint_id}/edit/" class="text-gray-600 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 text-sm font-medium">
                        Edit
                    </a>
                </div>
            </div>
        `).join('');

        // Re-setup checkboxes for new elements
        this.setupCheckboxes();
    }

    getMethodBadge(method) {
        const methodClasses = {
            'GET': 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
            'POST': 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
            'PUT': 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400',
            'DELETE': 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400',
            'PATCH': 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400',
            'QUERY': 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-400',
            'MUTATION': 'bg-pink-100 dark:bg-pink-900/30 text-pink-700 dark:text-pink-400'
        };

        const badgeClass = methodClasses[method] || 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300';

        return `<span class="px-2 py-1 rounded-full text-xs font-medium ${badgeClass}">${method}</span>`;
    }

    updateCheckboxes(selectedItems) {
        const checkboxes = document.querySelectorAll('.endpoint-checkbox');
        checkboxes.forEach(checkbox => {
            const endpointId = checkbox.getAttribute('data-endpoint-id');
            checkbox.checked = selectedItems.includes(endpointId);
        });
    }

    handleBulkAction(action, items) {
        console.log(`Bulk ${action} for endpoints:`, items);

        // TODO: Implement bulk actions
        // This would make API calls to perform bulk operations
        alert(`Bulk ${action} not yet implemented. Selected ${items.length} endpoints.`);
    }
}