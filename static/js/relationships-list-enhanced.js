/**
 * Enhanced Relationships List Manager
 *
 * Manages the relationships list with:
 * - Search and autocomplete
 * - Bulk operations
 * - Filtering
 * - Selection management
 */

class RelationshipsListEnhanced {
    constructor(options = {}) {
        this.relationships = options.relationships || [];
        this.total = options.total || 0;
        this.filteredRelationships = [...this.relationships];

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
            resourceType: 'relationships',
            placeholder: 'Search relationships...',
            onSelect: (suggestion) => {
                // Navigate to selected relationship
                if (suggestion.relationship_id) {
                    window.location.href = `/docs/relationships/${suggestion.relationship_id}/`;
                }
            }
        });

        searchContainer.addEventListener('search-change', (e) => {
            this.filterRelationships(e.detail.query);
        });
    }

    setupBulkOperations() {
        const bulkContainer = document.getElementById('bulk-operations-container');
        if (!bulkContainer) return;

        this.bulkOperations = new BulkOperations(bulkContainer, {
            items: this.relationships,
            itemIdField: 'relationship_id',
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
        const usageTypeFilter = document.getElementById('usage-type-filter');
        const usageContextFilter = document.getElementById('usage-context-filter');

        if (usageTypeFilter) {
            usageTypeFilter.addEventListener('change', () => {
                this.applyFilters();
            });
        }

        if (usageContextFilter) {
            usageContextFilter.addEventListener('change', () => {
                this.applyFilters();
            });
        }
    }

    setupCheckboxes() {
        const checkboxes = document.querySelectorAll('.relationship-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const relationshipId = e.target.getAttribute('data-relationship-id');
                if (this.bulkOperations) {
                    if (e.target.checked) {
                        this.bulkOperations.selectItem(relationshipId);
                    } else {
                        this.bulkOperations.deselectItem(relationshipId);
                    }
                }
            });
        });
    }

    filterRelationships(query) {
        if (!query || query.trim().length === 0) {
            this.filteredRelationships = [...this.relationships];
        } else {
            const searchLower = query.toLowerCase();
            this.filteredRelationships = this.relationships.filter(relationship => {
                const relationshipId = (relationship.relationship_id || '').toLowerCase();
                const endpointPath = (relationship.endpoint_path || '').toLowerCase();
                const pagePath = (relationship.page_path || '').toLowerCase();

                return relationshipId.includes(searchLower) ||
                       endpointPath.includes(searchLower) ||
                       pagePath.includes(searchLower);
            });
        }
        this.renderRelationships();
    }

    applyFilters() {
        const usageTypeFilter = document.getElementById('usage-type-filter');
        const usageContextFilter = document.getElementById('usage-context-filter');

        const usageTypeValue = usageTypeFilter ? usageTypeFilter.value : '';
        const usageContextValue = usageContextFilter ? usageContextFilter.value : '';

        this.filteredRelationships = this.relationships.filter(relationship => {
            if (usageTypeValue && relationship.usage_type !== usageTypeValue) {
                return false;
            }
            if (usageContextValue && relationship.usage_context !== usageContextValue) {
                return false;
            }
            return true;
        });

        this.renderRelationships();
    }

    renderRelationships() {
        const grid = document.getElementById('relationships-grid');
        if (!grid) return;

        if (this.filteredRelationships.length === 0) {
            grid.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <div class="text-gray-400 dark:text-gray-500 text-lg mb-2">No relationships found</div>
                    <p class="text-gray-500 dark:text-gray-400">Try adjusting your search or filters</p>
                </div>
            `;
            return;
        }

        grid.innerHTML = this.filteredRelationships.map(relationship => `
            <div class="relationship-card bg-white dark:bg-gray-800 rounded-lg shadow-md dark:shadow-lg border border-gray-200 dark:border-gray-700 p-6 hover:border-green-500 dark:hover:border-green-400 transition-all" data-relationship-id="${relationship.relationship_id}">
                <div class="flex items-start gap-3 mb-4">
                    <input
                        type="checkbox"
                        class="relationship-checkbox w-4 h-4 text-green-600 rounded border-gray-300 dark:border-gray-600 mt-1"
                        data-relationship-id="${relationship.relationship_id}"
                    />
                    <div class="flex-1">
                        <div class="flex items-center gap-2 mb-2">
                            ${relationship.endpoint_path ? `<span class="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400">${relationship.method || 'GET'}</span>` : ''}
                            <h3 class="font-semibold text-gray-900 dark:text-gray-100">${relationship.endpoint_path || relationship.relationship_id || 'Unknown'}</h3>
                        </div>
                        ${relationship.pages ? `<p class="text-sm text-gray-500 dark:text-gray-400 mb-2">Used by ${relationship.pages.length} page${relationship.pages.length !== 1 ? 's' : ''}</p>` : ''}
                        <div class="flex items-center gap-2">
                            ${relationship.usage_type ? `<span class="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">${relationship.usage_type.charAt(0).toUpperCase() + relationship.usage_type.slice(1)}</span>` : ''}
                            ${relationship.usage_context ? `<span class="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">${relationship.usage_context.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}</span>` : ''}
                        </div>
                    </div>
                </div>
                <div class="flex items-center gap-2 mt-4">
                    <a href="/docs/relationships/${relationship.relationship_id}/" class="text-green-600 dark:text-green-400 hover:text-green-700 dark:hover:text-green-300 text-sm font-medium">
                        View →
                    </a>
                    <a href="/docs/relationships/${relationship.relationship_id}/edit/" class="text-gray-600 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 text-sm font-medium">
                        Edit
                    </a>
                </div>
            </div>
        `).join('');

        // Re-setup checkboxes for new elements
        this.setupCheckboxes();
    }

    updateCheckboxes(selectedItems) {
        const checkboxes = document.querySelectorAll('.relationship-checkbox');
        checkboxes.forEach(checkbox => {
            const relationshipId = checkbox.getAttribute('data-relationship-id');
            checkbox.checked = selectedItems.includes(relationshipId);
        });
    }

    handleBulkAction(action, items) {
        console.log(`Bulk ${action} for relationships:`, items);

        // TODO: Implement bulk actions
        // This would make API calls to perform bulk operations
        alert(`Bulk ${action} not yet implemented. Selected ${items.length} relationships.`);
    }
}