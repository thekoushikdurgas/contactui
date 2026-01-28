/**
 * Statistics Loader
 * 
 * Fetches and displays statistics from Lambda API v1 endpoints.
 * Used in the documentation dashboard to show real-time statistics.
 */

class StatsLoader {
    constructor(options = {}) {
        // Use new statistics API endpoints instead of API v1
        this.apiBase = options.apiBase || '/docs/api/statistics';
        this.containers = {
            pages: options.pagesContainer || 'pages-stats-panel',
            endpoints: options.endpointsContainer || 'endpoints-stats-panel',
            relationships: options.relationshipsContainer || 'relationships-stats-panel',
            postman: options.postmanContainer || 'postman-stats-panel'
        };
        this.loaded = { pages: false, endpoints: false, relationships: false, postman: false };
        this.data = {};
        this.loading = false;
    }
    
    /**
     * Initialize and load all statistics
     */
    async init() {
        if (this.loading) return;
        this.loading = true;
        
        try {
            // Load all stats in parallel
            await Promise.all([
                this.loadPagesStats(),
                this.loadEndpointsStats(),
                this.loadRelationshipsStats(),
                this.loadPostmanStats()
            ]);
        } catch (error) {
            console.error('Error loading statistics:', error);
        } finally {
            this.loading = false;
        }
    }
    
    /**
     * Load pages statistics
     */
    async loadPagesStats() {
        try {
            const [statsRes, typesRes] = await Promise.all([
                fetch(`${this.apiBase}/pages/statistics/`),
                fetch(`${this.apiBase}/pages/types/`)
            ]);
            
            if (!statsRes.ok || !typesRes.ok) {
                throw new Error('Failed to fetch pages stats');
            }
            
            const stats = await statsRes.json();
            const types = await typesRes.json();
            
            this.data.pages = { stats, types };
            this.renderPagesStats(stats, types);
            this.loaded.pages = true;
        } catch (error) {
            console.error('Failed to load pages stats:', error);
            this.renderErrorState('pages', 'Failed to load pages statistics');
        }
    }
    
    /**
     * Load endpoints statistics
     */
    async loadEndpointsStats() {
        try {
            const [versionsRes, methodsRes] = await Promise.all([
                fetch(`${this.apiBase}/endpoints/api-versions/`),
                fetch(`${this.apiBase}/endpoints/methods/`)
            ]);
            
            if (!versionsRes.ok || !methodsRes.ok) {
                throw new Error('Failed to fetch endpoints stats');
            }
            
            const versions = await versionsRes.json();
            const methods = await methodsRes.json();
            
            this.data.endpoints = { versions, methods };
            this.renderEndpointsStats(versions, methods);
            this.loaded.endpoints = true;
        } catch (error) {
            console.error('Failed to load endpoints stats:', error);
            this.renderErrorState('endpoints', 'Failed to load endpoints statistics');
        }
    }
    
    /**
     * Load relationships statistics
     */
    async loadRelationshipsStats() {
        try {
            const response = await fetch(`${this.apiBase}/relationships/statistics/`);
            
            if (!response.ok) {
                throw new Error('Failed to fetch relationships stats');
            }
            
            const stats = await response.json();
            
            this.data.relationships = stats;
            this.renderRelationshipsStats(stats);
            this.loaded.relationships = true;
        } catch (error) {
            console.error('Failed to load relationships stats:', error);
            this.renderErrorState('relationships', 'Failed to load relationships statistics');
        }
    }
    
    /**
     * Load postman statistics
     */
    async loadPostmanStats() {
        try {
            const response = await fetch(`${this.apiBase}/postman/statistics/`);
            
            if (!response.ok) {
                throw new Error('Failed to fetch postman stats');
            }
            
            const stats = await response.json();
            
            this.data.postman = stats;
            this.renderPostmanStats(stats);
            this.loaded.postman = true;
        } catch (error) {
            console.error('Failed to load postman stats:', error);
            this.renderErrorState('postman', 'Failed to load postman statistics');
        }
    }
    
    /**
     * Render pages statistics
     */
    renderPagesStats(stats, types) {
        const container = document.getElementById(this.containers.pages);
        if (!container) return;
        
        const byType = types.types || [];
        const total = stats.total || 0;
        const statistics = stats.statistics || {};
        
        // Color classes for different types
        const typeColors = {
            'docs': 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300',
            'dashboard': 'bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300',
            'marketing': 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300'
        };
        
        container.innerHTML = `
            <div class="space-y-4">
                <div class="flex items-center justify-between">
                    <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300">Pages by Type</h3>
                    <span class="text-xs text-gray-500 dark:text-gray-400">Total: ${total}</span>
                </div>
                <div class="grid grid-cols-3 gap-3">
                    ${byType.length > 0 ? byType.map(t => {
                        const colorClass = typeColors[t.type] || 'bg-gray-50 dark:bg-gray-700/50 text-gray-700 dark:text-gray-300';
                        return `
                            <div class="p-3 rounded-xl ${colorClass} text-center transition-transform hover:scale-105">
                                <p class="text-xl font-bold">${t.count || 0}</p>
                                <p class="text-xs capitalize">${this.escapeHtml(t.type)}</p>
                            </div>
                        `;
                    }).join('') : '<p class="col-span-3 text-center text-gray-500 dark:text-gray-400 text-sm">No pages found</p>'}
                </div>
                ${statistics.by_status ? `
                    <div class="pt-3 border-t border-gray-100 dark:border-gray-700">
                        <h4 class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">By Status</h4>
                        <div class="flex gap-4 text-sm">
                            ${Object.entries(statistics.by_status).map(([status, count]) => `
                                <span class="flex items-center gap-1">
                                    <span class="w-2 h-2 rounded-full ${status === 'published' ? 'bg-green-500' : status === 'draft' ? 'bg-amber-500' : 'bg-gray-400'}"></span>
                                    <span class="text-gray-600 dark:text-gray-400">${status}: ${count}</span>
                                </span>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
        container.classList.remove('hidden');
    }
    
    /**
     * Render endpoints statistics
     */
    renderEndpointsStats(versions, methods) {
        const container = document.getElementById(this.containers.endpoints);
        if (!container) return;
        
        const versionsList = versions.versions || [];
        const methodsList = methods.methods || [];
        const totalVersions = versions.total || 0;
        const totalMethods = methods.total || 0;
        
        // Color classes for different methods
        const methodColors = {
            'QUERY': 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
            'MUTATION': 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400',
            'GET': 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
            'POST': 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400',
            'PUT': 'bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-400',
            'DELETE': 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
        };
        
        container.innerHTML = `
            <div class="grid grid-cols-2 gap-6">
                <div>
                    <div class="flex items-center justify-between mb-3">
                        <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300">By API Version</h3>
                        <span class="text-xs text-gray-500 dark:text-gray-400">${totalVersions} total</span>
                    </div>
                    <div class="space-y-2">
                        ${versionsList.length > 0 ? versionsList.map(v => `
                            <div class="flex justify-between items-center p-2 rounded-lg bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                                <span class="text-sm text-gray-600 dark:text-gray-400 font-medium">${this.escapeHtml(v.version)}</span>
                                <span class="text-sm font-bold text-gray-900 dark:text-gray-100">${v.count}</span>
                            </div>
                        `).join('') : '<p class="text-center text-gray-500 dark:text-gray-400 text-sm">No versions found</p>'}
                    </div>
                </div>
                <div>
                    <div class="flex items-center justify-between mb-3">
                        <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300">By Method</h3>
                        <span class="text-xs text-gray-500 dark:text-gray-400">${totalMethods} total</span>
                    </div>
                    <div class="space-y-2">
                        ${methodsList.length > 0 ? methodsList.map(m => {
                            const colorClass = methodColors[m.method] || 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300';
                            return `
                                <div class="flex justify-between items-center p-2 rounded-lg ${colorClass}">
                                    <span class="text-sm font-medium">${this.escapeHtml(m.method)}</span>
                                    <span class="text-sm font-bold">${m.count}</span>
                                </div>
                            `;
                        }).join('') : '<p class="text-center text-gray-500 dark:text-gray-400 text-sm">No methods found</p>'}
                    </div>
                </div>
            </div>
        `;
        container.classList.remove('hidden');
    }
    
    /**
     * Render relationships statistics
     */
    renderRelationshipsStats(stats) {
        const container = document.getElementById(this.containers.relationships);
        if (!container) return;
        
        const totalRelationships = stats.total_relationships || 0;
        const uniquePages = stats.unique_pages || 0;
        const uniqueEndpoints = stats.unique_endpoints || 0;
        const pagesWithEndpoints = stats.pages_with_endpoints || 0;
        const endpointsWithPages = stats.endpoints_with_pages || 0;
        
        // Calculate coverage percentages
        const pageCoverage = uniquePages > 0 ? Math.round((pagesWithEndpoints / uniquePages) * 100) : 0;
        const endpointCoverage = uniqueEndpoints > 0 ? Math.round((endpointsWithPages / uniqueEndpoints) * 100) : 0;
        
        container.innerHTML = `
            <div class="space-y-4">
                <div class="grid grid-cols-4 gap-3">
                    <div class="p-3 rounded-xl bg-blue-50 dark:bg-blue-900/20 text-center">
                        <p class="text-xl font-bold text-blue-700 dark:text-blue-300">${totalRelationships}</p>
                        <p class="text-xs text-blue-600 dark:text-blue-400">Total</p>
                    </div>
                    <div class="p-3 rounded-xl bg-green-50 dark:bg-green-900/20 text-center">
                        <p class="text-xl font-bold text-green-700 dark:text-green-300">${uniquePages}</p>
                        <p class="text-xs text-green-600 dark:text-green-400">Unique Pages</p>
                    </div>
                    <div class="p-3 rounded-xl bg-purple-50 dark:bg-purple-900/20 text-center">
                        <p class="text-xl font-bold text-purple-700 dark:text-purple-300">${uniqueEndpoints}</p>
                        <p class="text-xs text-purple-600 dark:text-purple-400">Unique Endpoints</p>
                    </div>
                    <div class="p-3 rounded-xl bg-amber-50 dark:bg-amber-900/20 text-center">
                        <p class="text-xl font-bold text-amber-700 dark:text-amber-300">${pageCoverage}%</p>
                        <p class="text-xs text-amber-600 dark:text-amber-400">Page Coverage</p>
                    </div>
                </div>
                <div class="pt-3 border-t border-gray-100 dark:border-gray-700">
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <div class="flex justify-between text-sm mb-1">
                                <span class="text-gray-600 dark:text-gray-400">Pages with endpoints</span>
                                <span class="font-medium text-gray-900 dark:text-gray-100">${pagesWithEndpoints} / ${uniquePages}</span>
                            </div>
                            <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                                <div class="bg-green-500 h-2 rounded-full transition-all duration-500" style="width: ${pageCoverage}%"></div>
                            </div>
                        </div>
                        <div>
                            <div class="flex justify-between text-sm mb-1">
                                <span class="text-gray-600 dark:text-gray-400">Endpoints with pages</span>
                                <span class="font-medium text-gray-900 dark:text-gray-100">${endpointsWithPages} / ${uniqueEndpoints}</span>
                            </div>
                            <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                                <div class="bg-purple-500 h-2 rounded-full transition-all duration-500" style="width: ${endpointCoverage}%"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        container.classList.remove('hidden');
    }
    
    /**
     * Render postman statistics
     */
    renderPostmanStats(stats) {
        const container = document.getElementById(this.containers.postman);
        if (!container) return;
        
        const total = stats.total || 0;
        const statistics = stats.statistics || {};
        const byState = statistics.by_state || {};
        
        container.innerHTML = `
            <div class="space-y-3">
                <div class="flex items-center justify-between">
                    <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300">Postman Configurations</h3>
                    <span class="text-xs text-gray-500 dark:text-gray-400">Total: ${total}</span>
                </div>
                ${Object.keys(byState).length > 0 ? `
                    <div class="flex gap-4">
                        ${Object.entries(byState).map(([state, count]) => {
                            const stateColors = {
                                'published': 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
                                'draft': 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400',
                                'development': 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
                                'test': 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400'
                            };
                            const colorClass = stateColors[state] || 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300';
                            return `
                                <div class="px-3 py-2 rounded-lg ${colorClass}">
                                    <span class="text-sm font-medium capitalize">${this.escapeHtml(state)}: ${count}</span>
                                </div>
                            `;
                        }).join('')}
                    </div>
                ` : '<p class="text-sm text-gray-500 dark:text-gray-400">No configuration stats available</p>'}
            </div>
        `;
        container.classList.remove('hidden');
    }
    
    /**
     * Render error state for a container
     */
    renderErrorState(type, message) {
        const container = document.getElementById(this.containers[type]);
        if (!container) return;
        
        container.innerHTML = `
            <div class="p-4 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 text-sm">
                <div class="flex items-center gap-2">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>${this.escapeHtml(message)}</span>
                </div>
            </div>
        `;
        container.classList.remove('hidden');
    }
    
    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(str) {
        if (typeof str !== 'string') return str;
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
    
    /**
     * Refresh all statistics
     */
    async refresh() {
        this.loaded = { pages: false, endpoints: false, relationships: false, postman: false };
        await this.init();
    }
    
    /**
     * Get loaded data
     */
    getData() {
        return this.data;
    }
    
    /**
     * Check if all stats are loaded
     */
    isFullyLoaded() {
        return Object.values(this.loaded).every(v => v === true);
    }
}

// Export for global use
window.StatsLoader = StatsLoader;
