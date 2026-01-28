/**
 * Dashboard Pagination Component
 * 
 * A reusable pagination component for dashboard lists with:
 * - Previous/Next navigation
 * - Page number buttons with ellipsis
 * - Page size selector
 * - URL parameter sync
 * - Accessibility support
 */

class DashboardPagination {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`Pagination container not found: ${containerId}`);
            return;
        }
        
        // Default options
        this.options = {
            total: options.total || 0,
            currentPage: options.currentPage || 1,
            pageSize: options.pageSize || 20,
            pageSizeOptions: options.pageSizeOptions || [10, 20, 50, 100],
            maxVisiblePages: options.maxVisiblePages || 7,
            onPageChange: options.onPageChange || null,
            onPageSizeChange: options.onPageSizeChange || null,
            baseUrl: options.baseUrl || window.location.pathname,
            updateURL: options.updateURL !== false, // Default true
            showPageSize: options.showPageSize !== false, // Default true
            showTotal: options.showTotal !== false, // Default true
            ...options
        };
        
        this.totalPages = Math.ceil(this.options.total / this.options.pageSize);
        this.render();
        this.attachEventListeners();
    }
    
    /**
     * Render pagination component
     */
    render() {
        if (this.options.total === 0) {
            this.container.innerHTML = '';
            return;
        }
        
        const startIndex = (this.options.currentPage - 1) * this.options.pageSize + 1;
        const endIndex = Math.min(this.options.currentPage * this.options.pageSize, this.options.total);
        
        let html = '<div class="flex flex-col sm:flex-row items-center justify-between gap-4 py-4 border-t border-gray-200 dark:border-gray-700">';
        
        // Left side: Total count and page size selector
        html += '<div class="flex items-center gap-4">';
        
        if (this.options.showTotal) {
            html += `<p class="text-sm text-gray-700 dark:text-gray-300">
                Showing <span class="font-medium">${startIndex}</span> to 
                <span class="font-medium">${endIndex}</span> of 
                <span class="font-medium">${this.options.total}</span> results
            </p>`;
        }
        
        if (this.options.showPageSize) {
            html += this.renderPageSizeSelector();
        }
        
        html += '</div>';
        
        // Right side: Page navigation
        html += '<div class="flex items-center gap-2">';
        html += this.renderPageNumbers();
        html += '</div>';
        
        html += '</div>';
        
        this.container.innerHTML = html;
    }
    
    /**
     * Render page size selector
     */
    renderPageSizeSelector() {
        return `
            <div class="flex items-center gap-2">
                <label for="page-size-select" class="text-sm text-gray-700 dark:text-gray-300">Show:</label>
                <select 
                    id="page-size-select" 
                    class="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    aria-label="Items per page"
                >
                    ${this.options.pageSizeOptions.map(size => `
                        <option value="${size}" ${size === this.options.pageSize ? 'selected' : ''}>
                            ${size}
                        </option>
                    `).join('')}
                </select>
            </div>
        `;
    }
    
    /**
     * Render page number buttons
     */
    renderPageNumbers() {
        let html = '';
        const { currentPage, maxVisiblePages } = this.options;
        const totalPages = this.totalPages;
        
        // Previous button
        html += `
            <button 
                class="px-3 py-2 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                ${currentPage === 1 ? 'disabled' : ''}
                data-page="${currentPage - 1}"
                aria-label="Previous page"
            >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                </svg>
            </button>
        `;
        
        // Page number buttons
        const pages = this.getVisiblePages(currentPage, totalPages, maxVisiblePages);
        
        pages.forEach((page, index) => {
            if (page === 'ellipsis') {
                html += `
                    <span class="px-3 py-2 text-sm text-gray-500 dark:text-gray-400">...</span>
                `;
            } else {
                const isActive = page === currentPage;
                html += `
                    <button 
                        class="px-4 py-2 text-sm font-medium rounded-lg border transition-colors ${
                            isActive 
                                ? 'bg-blue-600 dark:bg-blue-500 text-white border-blue-600 dark:border-blue-500' 
                                : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                        }"
                        data-page="${page}"
                        aria-label="Page ${page}"
                        ${isActive ? 'aria-current="page"' : ''}
                    >
                        ${page}
                    </button>
                `;
            }
        });
        
        // Next button
        html += `
            <button 
                class="px-3 py-2 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                ${currentPage === totalPages ? 'disabled' : ''}
                data-page="${currentPage + 1}"
                aria-label="Next page"
            >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
            </button>
        `;
        
        return html;
    }
    
    /**
     * Calculate visible page numbers with ellipsis
     */
    getVisiblePages(currentPage, totalPages, maxVisible) {
        const pages = [];
        
        if (totalPages <= maxVisible) {
            // Show all pages if total is less than max visible
            for (let i = 1; i <= totalPages; i++) {
                pages.push(i);
            }
        } else {
            // Always show first page
            pages.push(1);
            
            // Calculate start and end of middle section
            let start = Math.max(2, currentPage - Math.floor((maxVisible - 4) / 2));
            let end = Math.min(totalPages - 1, start + (maxVisible - 4));
            
            // Adjust if we're near the end
            if (end === totalPages - 1) {
                start = Math.max(2, totalPages - (maxVisible - 3));
            }
            
            // Add ellipsis after first page if needed
            if (start > 2) {
                pages.push('ellipsis');
            }
            
            // Add middle pages
            for (let i = start; i <= end; i++) {
                pages.push(i);
            }
            
            // Add ellipsis before last page if needed
            if (end < totalPages - 1) {
                pages.push('ellipsis');
            }
            
            // Always show last page
            pages.push(totalPages);
        }
        
        return pages;
    }
    
    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Page number buttons
        this.container.addEventListener('click', (e) => {
            const button = e.target.closest('button[data-page]');
            if (button && !button.disabled) {
                const page = parseInt(button.getAttribute('data-page'));
                this.goToPage(page);
            }
        });
        
        // Page size selector
        const pageSizeSelect = this.container.querySelector('#page-size-select');
        if (pageSizeSelect) {
            pageSizeSelect.addEventListener('change', (e) => {
                const newPageSize = parseInt(e.target.value);
                this.changePageSize(newPageSize);
            });
        }
        
        // Keyboard navigation
        this.container.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                const button = e.target.closest('button[data-page]');
                if (button && !button.disabled) {
                    e.preventDefault();
                    button.click();
                }
            }
        });
    }
    
    /**
     * Navigate to specific page
     */
    goToPage(page) {
        if (page < 1 || page > this.totalPages || page === this.options.currentPage) {
            return;
        }
        
        this.options.currentPage = page;
        this.totalPages = Math.ceil(this.options.total / this.options.pageSize);
        
        if (this.options.updateURL) {
            this.updateURL();
        }
        
        if (this.options.onPageChange) {
            this.options.onPageChange(page, this.options.pageSize);
        }
        
        this.render();
        this.attachEventListeners();
    }
    
    /**
     * Change page size
     */
    changePageSize(newPageSize) {
        if (newPageSize === this.options.pageSize) {
            return;
        }
        
        // Calculate new page to maintain position
        const firstItemIndex = (this.options.currentPage - 1) * this.options.pageSize;
        const newPage = Math.floor(firstItemIndex / newPageSize) + 1;
        
        this.options.pageSize = newPageSize;
        this.options.currentPage = Math.min(newPage, Math.ceil(this.options.total / newPageSize));
        this.totalPages = Math.ceil(this.options.total / this.options.pageSize);
        
        // Store preference
        if (typeof localStorage !== 'undefined') {
            localStorage.setItem('docsai_page_size', newPageSize.toString());
        }
        
        if (this.options.updateURL) {
            this.updateURL();
        }
        
        if (this.options.onPageSizeChange) {
            this.options.onPageSizeChange(newPageSize, this.options.currentPage);
        }
        
        this.render();
        this.attachEventListeners();
    }
    
    /**
     * Update URL parameters
     */
    updateURL() {
        const url = new URL(window.location.href);
        url.searchParams.set('page', this.options.currentPage.toString());
        url.searchParams.set('page_size', this.options.pageSize.toString());
        
        // Preserve other query parameters (like tab, filters)
        window.history.pushState({}, '', url);
    }
    
    /**
     * Update pagination data
     */
    update(options) {
        this.options = { ...this.options, ...options };
        this.totalPages = Math.ceil(this.options.total / this.options.pageSize);
        this.render();
        this.attachEventListeners();
    }
    
    /**
     * Get current state
     */
    getState() {
        return {
            currentPage: this.options.currentPage,
            pageSize: this.options.pageSize,
            total: this.options.total,
            totalPages: this.totalPages
        };
    }
}

// Export for use in other scripts
window.DashboardPagination = DashboardPagination;
