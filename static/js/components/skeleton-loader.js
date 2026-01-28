/**
 * Skeleton Loader Component
 * 
 * Provides skeleton loading states with:
 * - Various skeleton patterns
 * - Animated loading effect
 * - Customizable appearance
 */

class SkeletonLoader {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.options = {
            type: options.type || 'default', // 'default', 'form', 'list', 'table', 'card'
            count: options.count || 1,
            ...options
        };
        
        if (!this.container) {
            throw new Error('Container element not found');
        }
        
        this.init();
    }
    
    init() {
        this.render();
    }
    
    render() {
        const html = this.generateSkeletonHTML();
        this.container.innerHTML = html;
    }
    
    generateSkeletonHTML() {
        switch (this.options.type) {
            case 'form':
                return this.renderFormSkeleton();
            case 'list':
                return this.renderListSkeleton();
            case 'table':
                return this.renderTableSkeleton();
            case 'card':
                return this.renderCardSkeleton();
            default:
                return this.renderDefaultSkeleton();
        }
    }
    
    renderDefaultSkeleton() {
        return Array(this.options.count).fill(0).map(() => `
            <div class="skeleton-item animate-pulse">
                <div class="skeleton-line h-4 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
                <div class="skeleton-line h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
            </div>
        `).join('');
    }
    
    renderFormSkeleton() {
        return `
            <div class="skeleton-form space-y-6 animate-pulse">
                <div class="space-y-4">
                    <div class="skeleton-line h-4 bg-gray-200 dark:bg-gray-700 rounded w-24"></div>
                    <div class="skeleton-line h-10 bg-gray-200 dark:bg-gray-700 rounded"></div>
                </div>
                <div class="space-y-4">
                    <div class="skeleton-line h-4 bg-gray-200 dark:bg-gray-700 rounded w-32"></div>
                    <div class="skeleton-line h-10 bg-gray-200 dark:bg-gray-700 rounded"></div>
                </div>
                <div class="space-y-4">
                    <div class="skeleton-line h-4 bg-gray-200 dark:bg-gray-700 rounded w-28"></div>
                    <div class="skeleton-line h-24 bg-gray-200 dark:bg-gray-700 rounded"></div>
                </div>
            </div>
        `;
    }
    
    renderListSkeleton() {
        return Array(this.options.count).fill(0).map(() => `
            <div class="skeleton-list-item flex items-center gap-4 p-4 border border-gray-200 dark:border-gray-700 rounded-lg mb-4 animate-pulse">
                <div class="skeleton-circle w-12 h-12 bg-gray-200 dark:bg-gray-700 rounded-full"></div>
                <div class="flex-1 space-y-2">
                    <div class="skeleton-line h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3"></div>
                    <div class="skeleton-line h-3 bg-gray-200 dark:bg-gray-700 rounded w-2/3"></div>
                </div>
            </div>
        `).join('');
    }
    
    renderTableSkeleton() {
        return `
            <div class="skeleton-table animate-pulse">
                <div class="skeleton-table-header flex gap-4 p-4 border-b border-gray-200 dark:border-gray-700">
                    <div class="skeleton-line h-4 bg-gray-200 dark:bg-gray-700 rounded w-24"></div>
                    <div class="skeleton-line h-4 bg-gray-200 dark:bg-gray-700 rounded w-32"></div>
                    <div class="skeleton-line h-4 bg-gray-200 dark:bg-gray-700 rounded w-20"></div>
                </div>
                ${Array(5).fill(0).map(() => `
                    <div class="skeleton-table-row flex gap-4 p-4 border-b border-gray-200 dark:border-gray-700">
                        <div class="skeleton-line h-4 bg-gray-200 dark:bg-gray-700 rounded w-24"></div>
                        <div class="skeleton-line h-4 bg-gray-200 dark:bg-gray-700 rounded w-32"></div>
                        <div class="skeleton-line h-4 bg-gray-200 dark:bg-gray-700 rounded w-20"></div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    renderCardSkeleton() {
        return Array(this.options.count).fill(0).map(() => `
            <div class="skeleton-card bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 animate-pulse">
                <div class="skeleton-line h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-4"></div>
                <div class="skeleton-line h-4 bg-gray-200 dark:bg-gray-700 rounded w-full mb-2"></div>
                <div class="skeleton-line h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-4"></div>
                <div class="skeleton-line h-10 bg-gray-200 dark:bg-gray-700 rounded w-24"></div>
            </div>
        `).join('');
    }
    
    show() {
        if (this.container) {
            this.container.style.display = 'block';
        }
    }
    
    hide() {
        if (this.container) {
            this.container.style.display = 'none';
        }
    }
    
    remove() {
        if (this.container) {
            this.container.innerHTML = '';
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SkeletonLoader;
}
