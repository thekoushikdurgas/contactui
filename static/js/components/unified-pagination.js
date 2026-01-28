/**
 * Unified Pagination Component
 * 
 * A wrapper around DashboardPagination that provides a consistent API
 * for use across all views. This component can be used standalone or
 * as an alias to DashboardPagination.
 * 
 * Usage:
 * const pagination = new UnifiedPagination('pagination-container', {
 *   total: 100,
 *   currentPage: 1,
 *   pageSize: 20,
 *   onPageChange: (page, pageSize) => { ... }
 * });
 */

// Use DashboardPagination as the base implementation
class UnifiedPagination extends DashboardPagination {
    constructor(containerId, options = {}) {
        // Ensure consistent defaults
        const unifiedOptions = {
            total: options.total || 0,
            currentPage: options.currentPage || 1,
            pageSize: options.pageSize || 20,
            pageSizeOptions: options.pageSizeOptions || [10, 20, 50, 100],
            maxVisiblePages: options.maxVisiblePages || 7,
            onPageChange: options.onPageChange || null,
            onPageSizeChange: options.onPageSizeChange || null,
            baseUrl: options.baseUrl || window.location.pathname,
            updateURL: options.updateURL !== false,
            showPageSize: options.showPageSize !== false,
            showTotal: options.showTotal !== false,
            ...options
        };
        
        super(containerId, unifiedOptions);
    }
    
    /**
     * Static factory method for easy instantiation
     */
    static create(containerId, options = {}) {
        return new UnifiedPagination(containerId, options);
    }
    
    /**
     * Update pagination with new data
     */
    updateData(data) {
        this.update({
            total: data.total || this.options.total,
            currentPage: data.currentPage || this.options.currentPage,
            pageSize: data.pageSize || this.options.pageSize
        });
    }
    
    /**
     * Reset to first page
     */
    reset() {
        this.goToPage(1);
    }
    
    /**
     * Go to next page
     */
    next() {
        if (this.options.currentPage < this.totalPages) {
            this.goToPage(this.options.currentPage + 1);
        }
    }
    
    /**
     * Go to previous page
     */
    previous() {
        if (this.options.currentPage > 1) {
            this.goToPage(this.options.currentPage - 1);
        }
    }
    
    /**
     * Check if on first page
     */
    isFirstPage() {
        return this.options.currentPage === 1;
    }
    
    /**
     * Check if on last page
     */
    isLastPage() {
        return this.options.currentPage === this.totalPages;
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.UnifiedPagination = UnifiedPagination;
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = UnifiedPagination;
}

// Also export DashboardPagination for backward compatibility
if (typeof window !== 'undefined') {
    window.UnifiedPagination.DashboardPagination = DashboardPagination;
}
