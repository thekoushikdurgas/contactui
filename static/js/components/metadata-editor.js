/**
 * Metadata Editor Component
 * 
 * Provides a specialized form editor for PageMetadata with:
 * - All PageMetadata fields as form inputs
 * - Real-time validation
 * - Auto-calculation of computed fields
 * - Integration with parent form
 */

class MetadataEditor {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.options = {
            data: options.data || {},
            readOnly: options.readOnly || false,
            pageId: options.pageId || '',
            ...options
        };
        
        if (!this.container) {
            throw new Error('Container element not found');
        }
        
        this.data = this.initializeData(this.options.data);
        this.init();
    }
    
    initializeData(initialData) {
        return {
            route: initialData.route || '',
            file_path: initialData.file_path || '',
            purpose: initialData.purpose || '',
            s3_key: initialData.s3_key || (this.options.pageId ? `data/pages/${this.options.pageId}.json` : ''),
            status: initialData.status || 'published',
            authentication: initialData.authentication || 'Not required',
            authorization: initialData.authorization || null,
            page_state: initialData.page_state || 'development',
            last_updated: initialData.last_updated || new Date().toISOString(),
            uses_endpoints: initialData.uses_endpoints || [],
            ui_components: initialData.ui_components || [],
            versions: initialData.versions || [],
            endpoint_count: initialData.endpoint_count || 0,
            api_versions: initialData.api_versions || [],
            content_sections: initialData.content_sections || null
        };
    }
    
    init() {
        this.container.innerHTML = '';
        this.container.classList.add('metadata-editor');
        this.render();
        this.setupEventListeners();
    }
    
    render() {
        const html = `
            <div class="metadata-editor-grid grid grid-cols-1 md:grid-cols-2 gap-4">
                <!-- Required Fields -->
                <div class="md:col-span-2">
                    <label for="metadata-route" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Route <span class="text-red-500">*</span>
                    </label>
                    <input 
                        type="text" 
                        id="metadata-route" 
                        name="metadata.route"
                        value="${this.escapeHtml(this.data.route)}"
                        required
                        ${this.options.readOnly ? 'readonly' : ''}
                        class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        placeholder="/dashboard"
                    />
                    <small class="text-gray-500 dark:text-gray-400 text-xs mt-1 block">Page route (e.g., /dashboard). Will be auto-fixed to start with /</small>
                </div>
                
                <div>
                    <label for="metadata-file-path" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        File Path <span class="text-red-500">*</span>
                    </label>
                    <input 
                        type="text" 
                        id="metadata-file-path" 
                        name="metadata.file_path"
                        value="${this.escapeHtml(this.data.file_path)}"
                        required
                        ${this.options.readOnly ? 'readonly' : ''}
                        class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        placeholder="pages/dashboard.tsx"
                    />
                    <small class="text-gray-500 dark:text-gray-400 text-xs mt-1 block">Source file path</small>
                </div>
                
                <div>
                    <label for="metadata-s3-key" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        S3 Key <span class="text-red-500">*</span>
                    </label>
                    <input 
                        type="text" 
                        id="metadata-s3-key" 
                        name="metadata.s3_key"
                        value="${this.escapeHtml(this.data.s3_key)}"
                        required
                        ${this.options.readOnly ? 'readonly' : ''}
                        class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        placeholder="data/pages/dashboard.json"
                    />
                    <small class="text-gray-500 dark:text-gray-400 text-xs mt-1 block">S3 key for JSON file</small>
                </div>
                
                <div class="md:col-span-2">
                    <label for="metadata-purpose" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Purpose <span class="text-red-500">*</span>
                    </label>
                    <textarea 
                        id="metadata-purpose" 
                        name="metadata.purpose"
                        rows="3"
                        required
                        ${this.options.readOnly ? 'readonly' : ''}
                        class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        placeholder="Page purpose/description"
                    >${this.escapeHtml(this.data.purpose)}</textarea>
                    <small class="text-gray-500 dark:text-gray-400 text-xs mt-1 block">Page purpose/description</small>
                </div>
                
                <!-- Optional Fields -->
                <div>
                    <label for="metadata-status" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Status
                    </label>
                    <select 
                        id="metadata-status" 
                        name="metadata.status"
                        ${this.options.readOnly ? 'disabled' : ''}
                        class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                    >
                        <option value="draft" ${this.data.status === 'draft' ? 'selected' : ''}>Draft</option>
                        <option value="published" ${this.data.status === 'published' ? 'selected' : ''}>Published</option>
                        <option value="archived" ${this.data.status === 'archived' ? 'selected' : ''}>Archived</option>
                        <option value="deleted" ${this.data.status === 'deleted' ? 'selected' : ''}>Deleted</option>
                    </select>
                </div>
                
                <div>
                    <label for="metadata-page-state" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Page State
                    </label>
                    <select 
                        id="metadata-page-state" 
                        name="metadata.page_state"
                        ${this.options.readOnly ? 'disabled' : ''}
                        class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                    >
                        <option value="coming_soon" ${this.data.page_state === 'coming_soon' ? 'selected' : ''}>Coming Soon</option>
                        <option value="published" ${this.data.page_state === 'published' ? 'selected' : ''}>Published</option>
                        <option value="draft" ${this.data.page_state === 'draft' ? 'selected' : ''}>Draft</option>
                        <option value="development" ${this.data.page_state === 'development' ? 'selected' : ''}>Development</option>
                        <option value="test" ${this.data.page_state === 'test' ? 'selected' : ''}>Test</option>
                    </select>
                </div>
                
                <div>
                    <label for="metadata-authentication" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Authentication
                    </label>
                    <input 
                        type="text" 
                        id="metadata-authentication" 
                        name="metadata.authentication"
                        value="${this.escapeHtml(this.data.authentication || 'Not required')}"
                        ${this.options.readOnly ? 'readonly' : ''}
                        class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        placeholder="Not required"
                    />
                </div>
                
                <div>
                    <label for="metadata-authorization" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Authorization
                    </label>
                    <input 
                        type="text" 
                        id="metadata-authorization" 
                        name="metadata.authorization"
                        value="${this.escapeHtml(this.data.authorization || '')}"
                        ${this.options.readOnly ? 'readonly' : ''}
                        class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        placeholder="Authorization requirement/notes"
                    />
                </div>
                
                <div>
                    <label for="metadata-last-updated" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Last Updated <span class="text-red-500">*</span>
                    </label>
                    <input 
                        type="datetime-local" 
                        id="metadata-last-updated" 
                        name="metadata.last_updated"
                        value="${this.formatDateTimeLocal(this.data.last_updated)}"
                        required
                        ${this.options.readOnly ? 'readonly' : ''}
                        class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                    />
                </div>
                
                <!-- Computed Fields (Read-only) -->
                <div>
                    <label for="metadata-endpoint-count" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Endpoint Count
                    </label>
                    <input 
                        type="number" 
                        id="metadata-endpoint-count" 
                        name="metadata.endpoint_count"
                        value="${this.data.endpoint_count || 0}"
                        readonly
                        class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 cursor-not-allowed"
                    />
                    <small class="text-gray-500 dark:text-gray-400 text-xs mt-1 block">Auto-calculated from uses_endpoints</small>
                </div>
                
                <div class="md:col-span-2">
                    <label for="metadata-api-versions" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        API Versions
                    </label>
                    <input 
                        type="text" 
                        id="metadata-api-versions" 
                        name="metadata.api_versions"
                        value="${this.escapeHtml((this.data.api_versions || []).join(', '))}"
                        readonly
                        class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 cursor-not-allowed"
                        placeholder="graphql, rest-v1"
                    />
                    <small class="text-gray-500 dark:text-gray-400 text-xs mt-1 block">Auto-derived from uses_endpoints</small>
                </div>
                
                <!-- Versions Array -->
                <div class="md:col-span-2">
                    <label for="metadata-versions" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Versions
                    </label>
                    <div id="metadata-versions-list" class="space-y-2">
                        ${this.renderVersionsList()}
                    </div>
                    ${!this.options.readOnly ? `
                        <button 
                            type="button" 
                            id="add-version-btn"
                            class="mt-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
                        >
                            + Add Version
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
        
        this.container.innerHTML = html;
    }
    
    renderVersionsList() {
        if (!this.data.versions || this.data.versions.length === 0) {
            return '<p class="text-gray-500 dark:text-gray-400 text-sm">No versions added</p>';
        }
        
        return this.data.versions.map((version, index) => `
            <div class="flex items-center gap-2 version-item" data-index="${index}">
                <input 
                    type="text" 
                    name="metadata.versions[${index}]"
                    value="${this.escapeHtml(version)}"
                    ${this.options.readOnly ? 'readonly' : ''}
                    class="flex-1 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                />
                ${!this.options.readOnly ? `
                    <button 
                        type="button" 
                        class="remove-version-btn px-3 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm"
                        data-index="${index}"
                    >
                        Remove
                    </button>
                ` : ''}
            </div>
        `).join('');
    }
    
    setupEventListeners() {
        if (this.options.readOnly) return;
        
        // Route auto-fix
        const routeInput = this.container.querySelector('#metadata-route');
        if (routeInput) {
            routeInput.addEventListener('blur', (e) => {
                let route = e.target.value.trim();
                if (route && !route.startsWith('/')) {
                    route = '/' + route;
                    e.target.value = route;
                }
                this.data.route = route;
                this.triggerChange();
            });
        }
        
        // All input fields
        const inputs = this.container.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            if (input.readOnly || input.disabled) return;
            
            input.addEventListener('change', (e) => {
                const name = e.target.name;
                if (name.startsWith('metadata.')) {
                    const field = name.replace('metadata.', '');
                    this.updateField(field, e.target.value);
                }
            });
        });
        
        // Add version button
        const addVersionBtn = this.container.querySelector('#add-version-btn');
        if (addVersionBtn) {
            addVersionBtn.addEventListener('click', () => {
                this.addVersion();
            });
        }
        
        // Remove version buttons
        const removeVersionBtns = this.container.querySelectorAll('.remove-version-btn');
        removeVersionBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const index = parseInt(e.target.getAttribute('data-index'));
                this.removeVersion(index);
            });
        });
    }
    
    updateField(field, value) {
        // Handle array fields
        if (field.startsWith('versions[')) {
            const match = field.match(/versions\[(\d+)\]/);
            if (match) {
                const index = parseInt(match[1]);
                if (!this.data.versions) {
                    this.data.versions = [];
                }
                this.data.versions[index] = value;
            }
        } else {
            // Handle special cases
            if (field === 'last_updated') {
                // Convert datetime-local to ISO string
                const date = new Date(value);
                this.data[field] = date.toISOString();
            } else if (field === 'api_versions') {
                // This is computed, don't update directly
                return;
            } else {
                this.data[field] = value;
            }
        }
        
        // Auto-update computed fields
        this.updateComputedFields();
        
        this.triggerChange();
    }
    
    updateComputedFields() {
        // Update endpoint_count
        this.data.endpoint_count = (this.data.uses_endpoints || []).length;
        
        // Update api_versions
        const apiVersionsSet = new Set();
        (this.data.uses_endpoints || []).forEach(endpoint => {
            if (endpoint && endpoint.api_version) {
                apiVersionsSet.add(endpoint.api_version);
            }
        });
        this.data.api_versions = Array.from(apiVersionsSet).sort();
        
        // Update UI
        const endpointCountInput = this.container.querySelector('#metadata-endpoint-count');
        if (endpointCountInput) {
            endpointCountInput.value = this.data.endpoint_count;
        }
        
        const apiVersionsInput = this.container.querySelector('#metadata-api-versions');
        if (apiVersionsInput) {
            apiVersionsInput.value = this.data.api_versions.join(', ');
        }
    }
    
    addVersion() {
        if (!this.data.versions) {
            this.data.versions = [];
        }
        this.data.versions.push('');
        this.render();
        this.setupEventListeners();
        
        // Focus on the new input
        const versionInputs = this.container.querySelectorAll('input[name^="metadata.versions["]');
        if (versionInputs.length > 0) {
            versionInputs[versionInputs.length - 1].focus();
        }
    }
    
    removeVersion(index) {
        if (this.data.versions && this.data.versions.length > index) {
            this.data.versions.splice(index, 1);
            this.render();
            this.setupEventListeners();
            this.triggerChange();
        }
    }
    
    formatDateTimeLocal(isoString) {
        if (!isoString) return '';
        const date = new Date(isoString);
        if (isNaN(date.getTime())) return '';
        return date.toISOString().slice(0, 16);
    }
    
    escapeHtml(text) {
        if (text === null || text === undefined) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    triggerChange() {
        const event = new CustomEvent('metadata-change', {
            detail: { data: this.data }
        });
        this.container.dispatchEvent(event);
    }
    
    getData() {
        return { ...this.data };
    }
    
    setData(data) {
        this.data = this.initializeData(data);
        this.render();
        this.setupEventListeners();
    }
    
    setUsesEndpoints(usesEndpoints) {
        this.data.uses_endpoints = usesEndpoints || [];
        this.updateComputedFields();
        this.triggerChange();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MetadataEditor;
}
