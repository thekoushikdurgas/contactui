/**
 * Unified Filter Controller
 * 
 * A reusable filter controller that handles:
 * - Filter UI rendering
 * - Filter persistence (URL params)
 * - Filter chips display
 * - Clear filters
 */

class UnifiedFilter {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`Filter container not found: ${containerId}`);
            return;
        }
        
        this.options = {
            filters: options.filters || [], // Array of filter definitions
            activeFilters: options.activeFilters || {},
            onFilterChange: options.onFilterChange || null,
            onClearFilters: options.onClearFilters || null,
            showChips: options.showChips !== false, // Default true
            chipsContainerId: options.chipsContainerId || null,
            persistToURL: options.persistToURL !== false, // Default true
            ...options
        };
        
        this.init();
    }
    
    /**
     * Initialize the filter
     */
    init() {
        // Load filters from URL if persistToURL is enabled
        if (this.options.persistToURL) {
            this.loadFiltersFromURL();
        }
        
        this.render();
        this.attachEventListeners();
    }
    
    /**
     * Render the filter UI
     */
    render() {
        if (this.options.filters.length === 0) {
            this.container.innerHTML = '';
            return;
        }
        
        let html = '<div class="flex flex-wrap items-center gap-4">';
        
        this.options.filters.forEach(filter => {
            html += this.renderFilterControl(filter);
        });
        
        // Clear filters button
        if (Object.keys(this.options.activeFilters).length > 0) {
            html += `<button type="button" 
                            class="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                            data-filter-clear>
                        Clear All
                     </button>`;
        }
        
        html += '</div>';
        
        this.container.innerHTML = html;
        
        // Render filter chips if enabled
        if (this.options.showChips) {
            this.renderFilterChips();
        }
    }
    
    /**
     * Render a single filter control
     */
    renderFilterControl(filter) {
        const filterId = filter.id || filter.name;
        const currentValue = this.options.activeFilters[filterId] || '';
        
        switch (filter.type) {
            case 'select':
                return this.renderSelectFilter(filter, currentValue);
            case 'multiselect':
                return this.renderMultiSelectFilter(filter, currentValue);
            case 'text':
                return this.renderTextFilter(filter, currentValue);
            case 'date':
                return this.renderDateFilter(filter, currentValue);
            default:
                return '';
        }
    }
    
    /**
     * Render select filter
     */
    renderSelectFilter(filter, currentValue) {
        const filterId = filter.id || filter.name;
        
        let html = `<div class="flex flex-col">
                        <label for="filter-${filterId}" class="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                            ${filter.label || filter.name}
                        </label>
                        <select id="filter-${filterId}" 
                                class="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                data-filter-id="${filterId}"
                                data-filter-type="select">
                            <option value="">All</option>`;
        
        if (filter.options && Array.isArray(filter.options)) {
            filter.options.forEach(option => {
                const value = typeof option === 'object' ? option.value : option;
                const label = typeof option === 'object' ? option.label : option;
                html += `<option value="${value}" ${currentValue === value ? 'selected' : ''}>${label}</option>`;
            });
        }
        
        html += `</select></div>`;
        return html;
    }
    
    /**
     * Render multi-select filter
     */
    renderMultiSelectFilter(filter, currentValue) {
        // Similar to select but allows multiple selections
        // For simplicity, using checkboxes
        const filterId = filter.id || filter.name;
        const selectedValues = Array.isArray(currentValue) ? currentValue : (currentValue ? [currentValue] : []);
        
        let html = `<div class="flex flex-col">
                        <label class="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                            ${filter.label || filter.name}
                        </label>
                        <div class="flex flex-wrap gap-2">`;
        
        if (filter.options && Array.isArray(filter.options)) {
            filter.options.forEach(option => {
                const value = typeof option === 'object' ? option.value : option;
                const label = typeof option === 'object' ? option.label : option;
                const isChecked = selectedValues.includes(value);
                
                html += `<label class="flex items-center px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${isChecked ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-500' : ''}">
                            <input type="checkbox" 
                                   value="${value}"
                                   data-filter-id="${filterId}"
                                   data-filter-type="multiselect"
                                   ${isChecked ? 'checked' : ''}
                                   class="mr-2 rounded">
                            ${label}
                         </label>`;
            });
        }
        
        html += `</div></div>`;
        return html;
    }
    
    /**
     * Render text filter
     */
    renderTextFilter(filter, currentValue) {
        const filterId = filter.id || filter.name;
        
        return `<div class="flex flex-col">
                    <label for="filter-${filterId}" class="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                        ${filter.label || filter.name}
                    </label>
                    <input type="text" 
                           id="filter-${filterId}"
                           value="${currentValue}"
                           placeholder="${filter.placeholder || 'Search...'}"
                           class="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                           data-filter-id="${filterId}"
                           data-filter-type="text">
                </div>`;
    }
    
    /**
     * Render date filter
     */
    renderDateFilter(filter, currentValue) {
        const filterId = filter.id || filter.name;
        
        return `<div class="flex flex-col">
                    <label for="filter-${filterId}" class="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                        ${filter.label || filter.name}
                    </label>
                    <input type="date" 
                           id="filter-${filterId}"
                           value="${currentValue}"
                           class="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                           data-filter-id="${filterId}"
                           data-filter-type="date">
                </div>`;
    }
    
    /**
     * Render filter chips
     */
    renderFilterChips() {
        const chipsContainer = this.options.chipsContainerId 
            ? document.getElementById(this.options.chipsContainerId)
            : this.container.parentElement?.querySelector('.filter-chips');
        
        if (!chipsContainer) {
            return;
        }
        
        const activeFilters = Object.entries(this.options.activeFilters).filter(([key, value]) => {
            return value !== '' && value !== null && (Array.isArray(value) ? value.length > 0 : true);
        });
        
        if (activeFilters.length === 0) {
            chipsContainer.innerHTML = '';
            return;
        }
        
        let html = '<div class="flex flex-wrap items-center gap-2">';
        
        activeFilters.forEach(([filterId, value]) => {
            const filter = this.options.filters.find(f => (f.id || f.name) === filterId);
            const filterLabel = filter?.label || filter?.name || filterId;
            
            const displayValue = Array.isArray(value) 
                ? value.map(v => this.getFilterOptionLabel(filter, v)).join(', ')
                : this.getFilterOptionLabel(filter, value);
            
            html += `<span class="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400">
                        <span class="font-medium">${filterLabel}:</span>
                        <span class="ml-1">${displayValue}</span>
                        <button type="button" 
                                class="ml-2 hover:text-blue-900 dark:hover:text-blue-300"
                                data-filter-chip-remove="${filterId}"
                                aria-label="Remove filter">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                     </span>`;
        });
        
        html += '</div>';
        chipsContainer.innerHTML = html;
        
        // Attach chip remove listeners
        chipsContainer.querySelectorAll('[data-filter-chip-remove]').forEach(button => {
            button.addEventListener('click', () => {
                const filterId = button.getAttribute('data-filter-chip-remove');
                this.removeFilter(filterId);
            });
        });
    }
    
    /**
     * Get filter option label
     */
    getFilterOptionLabel(filter, value) {
        if (!filter.options) {
            return value;
        }
        
        const option = filter.options.find(opt => {
            const optValue = typeof opt === 'object' ? opt.value : opt;
            return optValue === value;
        });
        
        return typeof option === 'object' ? option.label : (option || value);
    }
    
    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Filter change handlers
        this.container.querySelectorAll('[data-filter-id]').forEach(element => {
            const filterId = element.getAttribute('data-filter-id');
            const filterType = element.getAttribute('data-filter-type');
            
            if (filterType === 'text') {
                // Debounce text input
                let timeout;
                element.addEventListener('input', (e) => {
                    clearTimeout(timeout);
                    timeout = setTimeout(() => {
                        this.updateFilter(filterId, e.target.value);
                    }, 300);
                });
            } else {
                element.addEventListener('change', (e) => {
                    if (filterType === 'multiselect') {
                        this.updateMultiSelectFilter(filterId);
                    } else {
                        this.updateFilter(filterId, e.target.value);
                    }
                });
            }
        });
        
        // Clear filters button
        const clearButton = this.container.querySelector('[data-filter-clear]');
        if (clearButton) {
            clearButton.addEventListener('click', () => {
                this.clearFilters();
            });
        }
    }
    
    /**
     * Update filter value
     */
    updateFilter(filterId, value) {
        if (value === '' || value === null) {
            delete this.options.activeFilters[filterId];
        } else {
            this.options.activeFilters[filterId] = value;
        }
        
        this.saveFiltersToURL();
        this.render();
        
        if (this.options.onFilterChange) {
            this.options.onFilterChange(this.options.activeFilters);
        }
    }
    
    /**
     * Update multi-select filter
     */
    updateMultiSelectFilter(filterId) {
        const checkboxes = this.container.querySelectorAll(`[data-filter-id="${filterId}"]:checked`);
        const values = Array.from(checkboxes).map(cb => cb.value);
        
        if (values.length === 0) {
            delete this.options.activeFilters[filterId];
        } else {
            this.options.activeFilters[filterId] = values;
        }
        
        this.saveFiltersToURL();
        this.render();
        
        if (this.options.onFilterChange) {
            this.options.onFilterChange(this.options.activeFilters);
        }
    }
    
    /**
     * Remove a specific filter
     */
    removeFilter(filterId) {
        delete this.options.activeFilters[filterId];
        this.saveFiltersToURL();
        this.render();
        
        if (this.options.onFilterChange) {
            this.options.onFilterChange(this.options.activeFilters);
        }
    }
    
    /**
     * Clear all filters
     */
    clearFilters() {
        this.options.activeFilters = {};
        this.saveFiltersToURL();
        this.render();
        
        if (this.options.onClearFilters) {
            this.options.onClearFilters();
        }
        
        if (this.options.onFilterChange) {
            this.options.onFilterChange(this.options.activeFilters);
        }
    }
    
    /**
     * Load filters from URL
     */
    loadFiltersFromURL() {
        const urlParams = new URLSearchParams(window.location.search);
        const filtersParam = urlParams.get('filters');
        
        if (filtersParam) {
            try {
                this.options.activeFilters = JSON.parse(decodeURIComponent(filtersParam));
            } catch (e) {
                console.error('Error parsing filters from URL:', e);
            }
        }
    }
    
    /**
     * Save filters to URL
     */
    saveFiltersToURL() {
        if (!this.options.persistToURL) {
            return;
        }
        
        const url = new URL(window.location);
        
        if (Object.keys(this.options.activeFilters).length === 0) {
            url.searchParams.delete('filters');
        } else {
            url.searchParams.set('filters', encodeURIComponent(JSON.stringify(this.options.activeFilters)));
        }
        
        window.history.replaceState({}, '', url);
    }
    
    /**
     * Get active filters
     */
    getActiveFilters() {
        return { ...this.options.activeFilters };
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UnifiedFilter;
}
