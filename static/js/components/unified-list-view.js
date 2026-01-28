/**
 * Unified List View Controller
 * 
 * A reusable list view controller that handles:
 * - List/grid view toggle
 * - Item rendering
 * - Selection handling
 * - Empty state
 * - Loading state
 */

class UnifiedListView {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`List view container not found: ${containerId}`);
            return;
        }
        
        this.options = {
            viewMode: options.viewMode || 'list', // 'list' or 'grid'
            items: options.items || [],
            renderItem: options.renderItem || null, // Function to render each item
            onItemClick: options.onItemClick || null,
            onItemSelect: options.onItemSelect || null,
            selectable: options.selectable || false,
            emptyStateMessage: options.emptyStateMessage || 'No items found',
            emptyStateAction: options.emptyStateAction || null,
            loading: options.loading || false,
            ...options
        };
        
        this.selectedItems = new Set();
        this.init();
    }
    
    /**
     * Initialize the list view
     */
    init() {
        // Load view mode preference from localStorage
        const savedViewMode = localStorage.getItem(`listViewMode_${this.container.id}`);
        if (savedViewMode && ['list', 'grid'].includes(savedViewMode)) {
            this.options.viewMode = savedViewMode;
        }
        
        this.render();
        this.attachEventListeners();
    }
    
    /**
     * Render the list view
     */
    render() {
        if (this.options.loading) {
            this.renderLoading();
            return;
        }
        
        if (this.options.items.length === 0) {
            this.renderEmpty();
            return;
        }
        
        const containerClass = this.options.viewMode === 'grid' 
            ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'
            : 'space-y-4';
        
        let html = `<div class="${containerClass}" role="list" aria-label="Items list">`;
        
        this.options.items.forEach((item, index) => {
            html += this.renderItem(item, index);
        });
        
        html += '</div>';
        
        this.container.innerHTML = html;
        
        // Attach item event listeners
        this.attachItemListeners();
    }
    
    /**
     * Render a single item
     */
    renderItem(item, index) {
        if (this.options.renderItem) {
            return this.options.renderItem(item, index, this.options.viewMode);
        }
        
        // Default item rendering
        const itemId = item.id || item._id || index;
        const isSelected = this.selectedItems.has(itemId);
        
        const baseClass = this.options.viewMode === 'grid'
            ? 'p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow cursor-pointer'
            : 'p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow cursor-pointer flex items-center justify-between';
        
        const selectedClass = isSelected ? 'ring-2 ring-blue-500' : '';
        
        let html = `<div class="${baseClass} ${selectedClass}" 
                          data-item-id="${itemId}" 
                          role="listitem"
                          tabindex="0"
                          aria-selected="${isSelected}">`;
        
        if (this.options.selectable) {
            html += `<input type="checkbox" 
                           class="mr-3" 
                           data-item-id="${itemId}"
                           ${isSelected ? 'checked' : ''}
                           aria-label="Select item">`;
        }
        
        html += `<div class="flex-1">
                    <h4 class="font-semibold text-gray-900 dark:text-gray-100">${item.title || item.name || item.id || 'Item'}</h4>
                    ${item.description ? `<p class="text-sm text-gray-600 dark:text-gray-400 mt-1">${item.description}</p>` : ''}
                 </div>`;
        
        html += '</div>';
        
        return html;
    }
    
    /**
     * Render loading state
     */
    renderLoading() {
        const skeletonCount = this.options.viewMode === 'grid' ? 6 : 5;
        let html = '<div class="space-y-4">';
        
        for (let i = 0; i < skeletonCount; i++) {
            html += `<div class="animate-pulse p-4 bg-gray-200 dark:bg-gray-700 rounded-lg">
                        <div class="h-4 bg-gray-300 dark:bg-gray-600 rounded w-3/4 mb-2"></div>
                        <div class="h-4 bg-gray-300 dark:bg-gray-600 rounded w-1/2"></div>
                     </div>`;
        }
        
        html += '</div>';
        this.container.innerHTML = html;
    }
    
    /**
     * Render empty state
     */
    renderEmpty() {
        let html = `<div class="flex flex-col items-center justify-center py-12 text-center">
                        <svg class="w-16 h-16 text-gray-400 dark:text-gray-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                        </svg>
                        <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">${this.options.emptyStateMessage}</h3>`;
        
        if (this.options.emptyStateAction) {
            html += `<a href="${this.options.emptyStateAction.url}" 
                        class="mt-4 inline-flex items-center px-4 py-2 bg-blue-600 dark:bg-blue-500 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-600 transition-colors">
                        ${this.options.emptyStateAction.icon ? `<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><use href="#icon-${this.options.emptyStateAction.icon}"></use></svg>` : ''}
                        ${this.options.emptyStateAction.text || 'Create New'}
                     </a>`;
        }
        
        html += '</div>';
        this.container.innerHTML = html;
    }
    
    /**
     * Toggle view mode
     */
    toggleViewMode() {
        this.options.viewMode = this.options.viewMode === 'list' ? 'grid' : 'list';
        localStorage.setItem(`listViewMode_${this.container.id}`, this.options.viewMode);
        this.render();
        
        // Dispatch custom event
        this.container.dispatchEvent(new CustomEvent('viewModeChanged', {
            detail: { viewMode: this.options.viewMode }
        }));
    }
    
    /**
     * Set view mode
     */
    setViewMode(mode) {
        if (['list', 'grid'].includes(mode)) {
            this.options.viewMode = mode;
            localStorage.setItem(`listViewMode_${this.container.id}`, mode);
            this.render();
        }
    }
    
    /**
     * Update items
     */
    updateItems(items) {
        this.options.items = items;
        this.render();
    }
    
    /**
     * Set loading state
     */
    setLoading(loading) {
        this.options.loading = loading;
        this.render();
    }
    
    /**
     * Get selected items
     */
    getSelectedItems() {
        return Array.from(this.selectedItems).map(id => {
            return this.options.items.find(item => (item.id || item._id) === id);
        }).filter(Boolean);
    }
    
    /**
     * Clear selection
     */
    clearSelection() {
        this.selectedItems.clear();
        this.render();
    }
    
    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Item click handlers are attached in attachItemListeners
    }
    
    /**
     * Attach item event listeners
     */
    attachItemListeners() {
        const items = this.container.querySelectorAll('[data-item-id]');
        
        items.forEach(item => {
            const itemId = item.getAttribute('data-item-id');
            const itemData = this.options.items.find(i => (i.id || i._id) === itemId);
            
            // Click handler
            item.addEventListener('click', (e) => {
                // Don't trigger if clicking checkbox
                if (e.target.type === 'checkbox') {
                    return;
                }
                
                if (this.options.onItemClick) {
                    this.options.onItemClick(itemData, itemId);
                }
            });
            
            // Checkbox handler
            if (this.options.selectable) {
                const checkbox = item.querySelector('input[type="checkbox"]');
                if (checkbox) {
                    checkbox.addEventListener('change', (e) => {
                        if (e.target.checked) {
                            this.selectedItems.add(itemId);
                        } else {
                            this.selectedItems.delete(itemId);
                        }
                        
                        item.setAttribute('aria-selected', e.target.checked);
                        item.classList.toggle('ring-2', e.target.checked);
                        item.classList.toggle('ring-blue-500', e.target.checked);
                        
                        if (this.options.onItemSelect) {
                            this.options.onItemSelect(this.getSelectedItems());
                        }
                    });
                }
            }
            
            // Keyboard navigation
            item.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    item.click();
                }
            });
        });
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UnifiedListView;
}
