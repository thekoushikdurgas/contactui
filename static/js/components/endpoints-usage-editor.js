/**
 * Endpoints Usage Editor Component
 * 
 * Provides a specialized editor for PageEndpointUsage array with:
 * - Add/remove endpoint usage entries
 * - Form fields for each endpoint usage
 * - Validation for method, usage_type, usage_context
 * - Integration with parent form
 */

class EndpointsUsageEditor {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.options = {
            data: options.data || [],
            readOnly: options.readOnly || false,
            endpointSearchUrl: options.endpointSearchUrl || '/docs/api/endpoints/search/',
            ...options
        };
        
        if (!this.container) {
            throw new Error('Container element not found');
        }
        
        this.data = Array.isArray(this.options.data) ? [...this.options.data] : [];
        this.init();
    }
    
    init() {
        this.container.innerHTML = '';
        this.container.classList.add('endpoints-usage-editor');
        this.render();
        this.setupEventListeners();
    }
    
    render() {
        if (this.data.length === 0) {
            this.container.innerHTML = `
                <div class="text-gray-500 dark:text-gray-400 text-center py-8">
                    <p class="mb-4">No endpoints added yet</p>
                    ${!this.options.readOnly ? `
                        <button 
                            type="button" 
                            class="add-endpoint-btn px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                        >
                            + Add Endpoint
                        </button>
                    ` : ''}
                </div>
            `;
            return;
        }
        
        const html = `
            <div class="endpoints-usage-list space-y-4">
                ${this.data.map((endpoint, index) => this.renderEndpointItem(endpoint, index)).join('')}
            </div>
            ${!this.options.readOnly ? `
                <div class="mt-4">
                    <button 
                        type="button" 
                        class="add-endpoint-btn px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                        + Add Endpoint
                    </button>
                </div>
            ` : ''}
        `;
        
        this.container.innerHTML = html;
    }
    
    renderEndpointItem(endpoint, index) {
        const item = endpoint || {};
        return `
            <div class="endpoint-usage-item bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700" data-index="${index}">
                <div class="flex justify-between items-start mb-4">
                    <h4 class="text-lg font-semibold text-gray-900 dark:text-gray-100">Endpoint Usage #${index + 1}</h4>
                    ${!this.options.readOnly ? `
                        <button 
                            type="button" 
                            class="remove-endpoint-btn px-3 py-1 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm"
                            data-index="${index}"
                        >
                            Remove
                        </button>
                    ` : ''}
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <!-- Endpoint Path -->
                    <div class="md:col-span-2">
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Endpoint Path <span class="text-red-500">*</span>
                        </label>
                        <input 
                            type="text" 
                            name="endpoint_path_${index}"
                            value="${this.escapeHtml(item.endpoint_path || '')}"
                            required
                            ${this.options.readOnly ? 'readonly' : ''}
                            class="endpoint-path-input w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            placeholder="graphql/GetUserStats"
                            data-index="${index}"
                        />
                        <small class="text-gray-500 dark:text-gray-400 text-xs mt-1 block">Endpoint path (e.g., graphql/GetUserStats)</small>
                    </div>
                    
                    <!-- Method -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Method <span class="text-red-500">*</span>
                        </label>
                        <select 
                            name="method_${index}"
                            required
                            ${this.options.readOnly ? 'disabled' : ''}
                            class="method-select w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            data-index="${index}"
                        >
                            <option value="">Select method</option>
                            <option value="QUERY" ${item.method === 'QUERY' ? 'selected' : ''}>QUERY</option>
                            <option value="MUTATION" ${item.method === 'MUTATION' ? 'selected' : ''}>MUTATION</option>
                            <option value="GET" ${item.method === 'GET' ? 'selected' : ''}>GET</option>
                            <option value="POST" ${item.method === 'POST' ? 'selected' : ''}>POST</option>
                            <option value="PUT" ${item.method === 'PUT' ? 'selected' : ''}>PUT</option>
                            <option value="DELETE" ${item.method === 'DELETE' ? 'selected' : ''}>DELETE</option>
                            <option value="PATCH" ${item.method === 'PATCH' ? 'selected' : ''}>PATCH</option>
                        </select>
                    </div>
                    
                    <!-- API Version -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            API Version <span class="text-red-500">*</span>
                        </label>
                        <input 
                            type="text" 
                            name="api_version_${index}"
                            value="${this.escapeHtml(item.api_version || '')}"
                            required
                            ${this.options.readOnly ? 'readonly' : ''}
                            class="api-version-input w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            placeholder="graphql"
                            data-index="${index}"
                        />
                        <small class="text-gray-500 dark:text-gray-400 text-xs mt-1 block">API version (e.g., graphql, rest-v1)</small>
                    </div>
                    
                    <!-- Via Service -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Via Service <span class="text-red-500">*</span>
                        </label>
                        <input 
                            type="text" 
                            name="via_service_${index}"
                            value="${this.escapeHtml(item.via_service || '')}"
                            required
                            ${this.options.readOnly ? 'readonly' : ''}
                            class="via-service-input w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            placeholder="UserService"
                            data-index="${index}"
                        />
                        <small class="text-gray-500 dark:text-gray-400 text-xs mt-1 block">Service name that uses this endpoint</small>
                    </div>
                    
                    <!-- Via Hook -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Via Hook
                        </label>
                        <input 
                            type="text" 
                            name="via_hook_${index}"
                            value="${this.escapeHtml(item.via_hook || '')}"
                            ${this.options.readOnly ? 'readonly' : ''}
                            class="via-hook-input w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            placeholder="useUserStats"
                            data-index="${index}"
                        />
                        <small class="text-gray-500 dark:text-gray-400 text-xs mt-1 block">React hook name (optional)</small>
                    </div>
                    
                    <!-- Usage Type -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Usage Type <span class="text-red-500">*</span>
                        </label>
                        <select 
                            name="usage_type_${index}"
                            required
                            ${this.options.readOnly ? 'disabled' : ''}
                            class="usage-type-select w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            data-index="${index}"
                        >
                            <option value="">Select usage type</option>
                            <option value="primary" ${item.usage_type === 'primary' ? 'selected' : ''}>Primary</option>
                            <option value="secondary" ${item.usage_type === 'secondary' ? 'selected' : ''}>Secondary</option>
                            <option value="conditional" ${item.usage_type === 'conditional' ? 'selected' : ''}>Conditional</option>
                            <option value="lazy" ${item.usage_type === 'lazy' ? 'selected' : ''}>Lazy</option>
                            <option value="prefetch" ${item.usage_type === 'prefetch' ? 'selected' : ''}>Prefetch</option>
                        </select>
                    </div>
                    
                    <!-- Usage Context -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Usage Context <span class="text-red-500">*</span>
                        </label>
                        <select 
                            name="usage_context_${index}"
                            required
                            ${this.options.readOnly ? 'disabled' : ''}
                            class="usage-context-select w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            data-index="${index}"
                        >
                            <option value="">Select usage context</option>
                            <option value="data_fetching" ${item.usage_context === 'data_fetching' ? 'selected' : ''}>Data Fetching</option>
                            <option value="data_mutation" ${item.usage_context === 'data_mutation' ? 'selected' : ''}>Data Mutation</option>
                            <option value="authentication" ${item.usage_context === 'authentication' ? 'selected' : ''}>Authentication</option>
                            <option value="analytics" ${item.usage_context === 'analytics' ? 'selected' : ''}>Analytics</option>
                            <option value="realtime" ${item.usage_context === 'realtime' ? 'selected' : ''}>Realtime</option>
                            <option value="background" ${item.usage_context === 'background' ? 'selected' : ''}>Background</option>
                        </select>
                    </div>
                    
                    <!-- Description -->
                    <div class="md:col-span-2">
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Description
                        </label>
                        <textarea 
                            name="description_${index}"
                            rows="2"
                            ${this.options.readOnly ? 'readonly' : ''}
                            class="description-textarea w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            placeholder="Description of how this endpoint is used"
                            data-index="${index}"
                        >${this.escapeHtml(item.description || '')}</textarea>
                    </div>
                </div>
            </div>
        `;
    }
    
    setupEventListeners() {
        if (this.options.readOnly) return;
        
        // Add endpoint button
        const addBtns = this.container.querySelectorAll('.add-endpoint-btn');
        addBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                this.addEndpoint();
            });
        });
        
        // Remove endpoint buttons
        const removeBtns = this.container.querySelectorAll('.remove-endpoint-btn');
        removeBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const index = parseInt(e.target.getAttribute('data-index'));
                this.removeEndpoint(index);
            });
        });
        
        // Input field changes
        const inputs = this.container.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            if (input.readOnly || input.disabled) return;
            
            // Auto-uppercase method on change
            if (input.classList.contains('method-select')) {
                input.addEventListener('change', (e) => {
                    const index = parseInt(e.target.getAttribute('data-index'));
                    if (this.data[index] && e.target.value) {
                        this.data[index].method = e.target.value.toUpperCase();
                        e.target.value = this.data[index].method;
                        this.triggerChange();
                    }
                });
            } else {
                input.addEventListener('change', (e) => {
                    const index = parseInt(e.target.getAttribute('data-index'));
                    this.updateEndpointField(index, e.target);
                });
            }
        });
    }
    
    updateEndpointField(index, input) {
        if (!this.data[index]) {
            this.data[index] = {};
        }
        
        const fieldName = input.name.replace(/_\d+$/, '');
        let value = input.value;
        
        // Auto-uppercase method
        if (fieldName === 'method') {
            value = value.toUpperCase();
            input.value = value;
        }
        
        this.data[index][fieldName] = value;
        this.triggerChange();
    }
    
    addEndpoint() {
        const newEndpoint = {
            endpoint_path: '',
            method: '',
            api_version: '',
            via_service: '',
            via_hook: null,
            usage_type: '',
            usage_context: '',
            description: null
        };
        
        this.data.push(newEndpoint);
        this.render();
        this.setupEventListeners();
        
        // Focus on the first input of the new endpoint
        const newItem = this.container.querySelector(`.endpoint-usage-item[data-index="${this.data.length - 1}"]`);
        if (newItem) {
            const firstInput = newItem.querySelector('input, select');
            if (firstInput) {
                firstInput.focus();
            }
        }
    }
    
    removeEndpoint(index) {
        if (index >= 0 && index < this.data.length) {
            this.data.splice(index, 1);
            this.render();
            this.setupEventListeners();
            this.triggerChange();
        }
    }
    
    escapeHtml(text) {
        if (text === null || text === undefined) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    triggerChange() {
        const event = new CustomEvent('endpoints-usage-change', {
            detail: { data: this.data }
        });
        this.container.dispatchEvent(event);
    }
    
    getData() {
        return [...this.data];
    }
    
    setData(data) {
        this.data = Array.isArray(data) ? [...data] : [];
        this.render();
        this.setupEventListeners();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EndpointsUsageEditor;
}
