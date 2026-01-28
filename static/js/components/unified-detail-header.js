/**
 * Unified Detail Header Controller
 * 
 * A reusable detail header controller that handles:
 * - Breadcrumb rendering
 * - Title and metadata display
 * - Action buttons
 * - Status badges
 */

class UnifiedDetailHeader {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`Detail header container not found: ${containerId}`);
            return;
        }
        
        this.options = {
            title: options.title || '',
            subtitle: options.subtitle || '',
            breadcrumbs: options.breadcrumbs || [],
            resourceType: options.resourceType || null, // pages, endpoints, relationships, postman
            badges: options.badges || [],
            actions: options.actions || [],
            metadata: options.metadata || {},
            ...options
        };
        
        this.render();
    }
    
    /**
     * Render the detail header
     */
    render() {
        let html = '<div class="flex items-start justify-between">';
        
        // Left side: Icon, title, metadata
        html += '<div class="flex items-start space-x-4">';
        
        // Resource icon
        if (this.options.resourceType) {
            html += this.renderResourceIcon();
        }
        
        // Title and metadata
        html += '<div>';
        html += `<h1 class="text-xl font-bold text-gray-900 dark:text-gray-100">${this.options.title}</h1>`;
        
        if (this.options.subtitle) {
            html += `<p class="text-sm text-gray-500 dark:text-gray-400 font-mono mt-0.5">${this.options.subtitle}</p>`;
        }
        
        // Badges
        if (this.options.badges.length > 0) {
            html += '<div class="flex items-center gap-3 mt-2">';
            this.options.badges.forEach(badge => {
                html += this.renderBadge(badge);
            });
            html += '</div>';
        }
        
        html += '</div>'; // End title/metadata div
        html += '</div>'; // End left side
        
        // Right side: Actions
        if (this.options.actions.length > 0) {
            html += '<div class="flex items-center gap-2">';
            this.options.actions.forEach(action => {
                html += this.renderAction(action);
            });
            html += '</div>';
        }
        
        html += '</div>'; // End main container
        
        this.container.innerHTML = html;
    }
    
    /**
     * Render resource icon
     */
    renderResourceIcon() {
        const iconClasses = {
            pages: 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400',
            endpoints: 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400',
            relationships: 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400',
            postman: 'bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400'
        };
        
        const iconSvg = {
            pages: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />',
            endpoints: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />',
            relationships: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />',
            postman: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />'
        };
        
        const classes = iconClasses[this.options.resourceType] || 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400';
        
        return `<div class="p-3 rounded-lg ${classes}">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        ${iconSvg[this.options.resourceType] || ''}
                    </svg>
                </div>`;
    }
    
    /**
     * Render badge
     */
    renderBadge(badge) {
        if (typeof badge === 'string') {
            // Simple string badge
            return `<span class="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">${badge}</span>`;
        }
        
        // Badge object with type, text, etc.
        const type = badge.type || 'default';
        const text = badge.text || badge.label || '';
        const classes = {
            status: badge.status === 'published' || badge.status === 'active' 
                ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                : badge.status === 'draft' || badge.status === 'pending'
                ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300',
            method: this.getMethodBadgeClass(badge.method),
            default: 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300'
        };
        
        const badgeClass = classes[type] || classes.default;
        
        return `<span class="px-2 py-1 rounded-full text-xs font-medium ${badgeClass}">${text}</span>`;
    }
    
    /**
     * Get method badge class
     */
    getMethodBadgeClass(method) {
        const methodClasses = {
            GET: 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300',
            POST: 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300',
            PUT: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300',
            DELETE: 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300',
            PATCH: 'bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300',
            QUERY: 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300',
            MUTATION: 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
        };
        
        return methodClasses[method] || 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-300';
    }
    
    /**
     * Render action button
     */
    renderAction(action) {
        if (typeof action === 'string') {
            // Simple string action (URL)
            return `<a href="${action}" class="inline-flex items-center px-4 py-2 bg-blue-600 dark:bg-blue-500 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-600 transition-colors font-medium text-sm">
                        Action
                    </a>`;
        }
        
        // Action object
        const variant = action.variant || 'primary';
        const text = action.text || action.label || 'Action';
        const href = action.href || action.url;
        const onclick = action.onclick;
        const icon = action.icon;
        
        const variantClasses = {
            primary: 'bg-blue-600 dark:bg-blue-500 text-white hover:bg-blue-700 dark:hover:bg-blue-600',
            secondary: 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 hover:bg-gray-300 dark:hover:bg-gray-600',
            danger: 'bg-red-600 dark:bg-red-500 text-white hover:bg-red-700 dark:hover:bg-red-600',
            outline: 'border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800',
            ghost: 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
        };
        
        const baseClass = `inline-flex items-center px-4 py-2 rounded-lg transition-colors font-medium text-sm ${variantClasses[variant] || variantClasses.primary}`;
        
        if (href) {
            return `<a href="${href}" class="${baseClass}">
                        ${icon ? `<svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><use href="#icon-${icon}"></use></svg>` : ''}
                        ${text}
                    </a>`;
        } else if (onclick) {
            return `<button type="button" onclick="${onclick}" class="${baseClass}">
                        ${icon ? `<svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><use href="#icon-${icon}"></use></svg>` : ''}
                        ${text}
                    </button>`;
        } else {
            return `<button type="button" class="${baseClass}">
                        ${icon ? `<svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><use href="#icon-${icon}"></use></svg>` : ''}
                        ${text}
                    </button>`;
        }
    }
    
    /**
     * Update title
     */
    updateTitle(title) {
        this.options.title = title;
        const titleElement = this.container.querySelector('h1');
        if (titleElement) {
            titleElement.textContent = title;
        }
    }
    
    /**
     * Update badges
     */
    updateBadges(badges) {
        this.options.badges = badges;
        this.render();
    }
    
    /**
     * Update actions
     */
    updateActions(actions) {
        this.options.actions = actions;
        this.render();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UnifiedDetailHeader;
}
