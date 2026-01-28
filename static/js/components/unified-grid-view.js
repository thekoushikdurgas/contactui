/**
 * Unified Grid View Controller
 * 
 * A specialized grid view controller that extends UnifiedListView
 * with grid-specific features:
 * - Responsive columns
 * - Card rendering
 * - Hover effects
 */

class UnifiedGridView extends UnifiedListView {
    constructor(containerId, options = {}) {
        // Force grid mode
        options.viewMode = 'grid';
        
        super(containerId, options);
        
        this.options = {
            ...this.options,
            columns: options.columns || { sm: 1, md: 2, lg: 3, xl: 4 },
            cardVariant: options.cardVariant || 'default', // default, elevated, outlined, flat
            ...options
        };
    }
    
    /**
     * Render the grid view
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
        
        // Build responsive grid classes
        const gridClasses = this.buildGridClasses();
        
        let html = `<div class="${gridClasses}" role="list" aria-label="Items grid">`;
        
        this.options.items.forEach((item, index) => {
            html += this.renderCard(item, index);
        });
        
        html += '</div>';
        
        this.container.innerHTML = html;
        
        // Attach item event listeners
        this.attachItemListeners();
    }
    
    /**
     * Build responsive grid classes
     */
    buildGridClasses() {
        const cols = this.options.columns;
        return `grid grid-cols-${cols.sm || 1} md:grid-cols-${cols.md || 2} lg:grid-cols-${cols.lg || 3} xl:grid-cols-${cols.xl || 4} gap-4`;
    }
    
    /**
     * Render a card item
     */
    renderCard(item, index) {
        if (this.options.renderItem) {
            return this.options.renderItem(item, index, 'grid');
        }
        
        // Default card rendering
        const itemId = item.id || item._id || index;
        const isSelected = this.selectedItems.has(itemId);
        
        const variantClasses = {
            default: 'shadow-md',
            elevated: 'shadow-lg',
            outlined: 'shadow-none border-2',
            flat: 'shadow-none border-0'
        };
        
        const baseClass = `p-6 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 
                          ${variantClasses[this.options.cardVariant] || variantClasses.default}
                          hover:shadow-xl hover:-translate-y-1 transition-all duration-200 cursor-pointer`;
        
        const selectedClass = isSelected ? 'ring-2 ring-blue-500' : '';
        
        let html = `<div class="${baseClass} ${selectedClass}" 
                          data-item-id="${itemId}" 
                          role="listitem"
                          tabindex="0"
                          aria-selected="${isSelected}">`;
        
        if (this.options.selectable) {
            html += `<div class="flex justify-end mb-2">
                        <input type="checkbox" 
                               class="rounded" 
                               data-item-id="${itemId}"
                               ${isSelected ? 'checked' : ''}
                               aria-label="Select item">
                     </div>`;
        }
        
        // Card content
        html += `<div class="space-y-3">
                    <h4 class="text-lg font-semibold text-gray-900 dark:text-gray-100">${item.title || item.name || item.id || 'Item'}</h4>`;
        
        if (item.description) {
            html += `<p class="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">${item.description}</p>`;
        }
        
        // Metadata badges
        if (item.badges && Array.isArray(item.badges)) {
            html += '<div class="flex flex-wrap gap-2 mt-3">';
            item.badges.forEach(badge => {
                html += `<span class="px-2 py-1 text-xs font-medium rounded-full ${badge.class || 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}">${badge.text}</span>`;
            });
            html += '</div>';
        }
        
        html += '</div></div>';
        
        return html;
    }
    
    /**
     * Render loading state with grid skeleton
     */
    renderLoading() {
        const skeletonCount = (this.options.columns.lg || 3) * 2; // 2 rows
        const gridClasses = this.buildGridClasses();
        
        let html = `<div class="${gridClasses}">`;
        
        for (let i = 0; i < skeletonCount; i++) {
            html += `<div class="animate-pulse p-6 bg-gray-200 dark:bg-gray-700 rounded-xl">
                        <div class="h-6 bg-gray-300 dark:bg-gray-600 rounded w-3/4 mb-3"></div>
                        <div class="h-4 bg-gray-300 dark:bg-gray-600 rounded w-full mb-2"></div>
                        <div class="h-4 bg-gray-300 dark:bg-gray-600 rounded w-2/3"></div>
                     </div>`;
        }
        
        html += '</div>';
        this.container.innerHTML = html;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UnifiedGridView;
}
