/**
 * Relationship Connection Editor Component
 * 
 * Provides a specialized editor for RelationshipConnection with:
 * - Via service/hook inputs with autocomplete
 * - Usage type and context dropdowns
 * - Invocation pattern and caching strategy
 * - Retry policy configuration
 */

class RelationshipConnectionEditor {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.options = {
            data: options.data || null,
            readOnly: options.readOnly || false,
            autocompleteUrl: options.autocompleteUrl || '/docs/api/autocomplete/',
            ...options
        };
        
        if (!this.container) {
            throw new Error('Container element not found');
        }
        
        this.data = this.initializeData(this.options.data);
        this.autocompleteCache = {
            services: [],
            hooks: []
        };
        this.init();
    }
    
    initializeData(initialData) {
        if (!initialData || typeof initialData !== 'object') {
            return {
                via_service: '',
                via_hook: null,
                usage_type: 'primary',
                usage_context: 'data_fetching',
                invocation_pattern: 'on_mount',
                caching_strategy: null,
                retry_policy: null
            };
        }
        
        return {
            via_service: initialData.via_service || '',
            via_hook: initialData.via_hook || null,
            usage_type: initialData.usage_type || 'primary',
            usage_context: initialData.usage_context || 'data_fetching',
            invocation_pattern: initialData.invocation_pattern || 'on_mount',
            caching_strategy: initialData.caching_strategy || null,
            retry_policy: initialData.retry_policy || null
        };
    }
    
    init() {
        this.container.innerHTML = '';
        this.container.classList.add('relationship-connection-editor');
        this.render();
        this.setupEventListeners();
        this.loadAutocompleteData();
    }
    
    async loadAutocompleteData() {
        // Load services and hooks for autocomplete
        // This would typically come from an API endpoint
        try {
            // For now, we'll use empty arrays - can be enhanced with actual API calls
            this.autocompleteCache.services = [];
            this.autocompleteCache.hooks = [];
        } catch (error) {
            console.warn('Failed to load autocomplete data:', error);
        }
    }
    
    render() {
        const html = `
            <div class="relationship-connection-editor-wrapper space-y-6">
                <!-- Via Service with Autocomplete -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Via Service <span class="text-red-500">*</span>
                    </label>
                    <div class="autocomplete-wrapper relative">
                        <input 
                            type="text" 
                            id="via-service-input"
                            class="autocomplete-input w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            value="${this.escapeHtml(this.data.via_service)}"
                            ${this.options.readOnly ? 'readonly' : ''}
                            required
                            placeholder="Enter service name..."
                            autocomplete="off"
                        />
                        <div id="via-service-suggestions" class="autocomplete-suggestions hidden absolute z-10 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg max-h-60 overflow-auto"></div>
                    </div>
                    <small class="text-gray-500 dark:text-gray-400 text-xs mt-1 block">Service name that connects page to endpoint</small>
                </div>
                
                <!-- Via Hook with Autocomplete -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Via Hook
                    </label>
                    <div class="autocomplete-wrapper relative">
                        <input 
                            type="text" 
                            id="via-hook-input"
                            class="autocomplete-input w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            value="${this.escapeHtml(this.data.via_hook || '')}"
                            ${this.options.readOnly ? 'readonly' : ''}
                            placeholder="Enter hook name (e.g., useUserStats)..."
                            autocomplete="off"
                        />
                        <div id="via-hook-suggestions" class="autocomplete-suggestions hidden absolute z-10 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg max-h-60 overflow-auto"></div>
                    </div>
                    <small class="text-gray-500 dark:text-gray-400 text-xs mt-1 block">React hook name (optional)</small>
                </div>
                
                <!-- Usage Type and Context -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Usage Type
                        </label>
                        <select 
                            id="usage-type-select"
                            ${this.options.readOnly ? 'disabled' : ''}
                            class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        >
                            <option value="primary" ${this.data.usage_type === 'primary' ? 'selected' : ''}>Primary</option>
                            <option value="secondary" ${this.data.usage_type === 'secondary' ? 'selected' : ''}>Secondary</option>
                            <option value="conditional" ${this.data.usage_type === 'conditional' ? 'selected' : ''}>Conditional</option>
                            <option value="lazy" ${this.data.usage_type === 'lazy' ? 'selected' : ''}>Lazy</option>
                            <option value="prefetch" ${this.data.usage_type === 'prefetch' ? 'selected' : ''}>Prefetch</option>
                        </select>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Usage Context
                        </label>
                        <select 
                            id="usage-context-select"
                            ${this.options.readOnly ? 'disabled' : ''}
                            class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        >
                            <option value="data_fetching" ${this.data.usage_context === 'data_fetching' ? 'selected' : ''}>Data Fetching</option>
                            <option value="data_mutation" ${this.data.usage_context === 'data_mutation' ? 'selected' : ''}>Data Mutation</option>
                            <option value="authentication" ${this.data.usage_context === 'authentication' ? 'selected' : ''}>Authentication</option>
                            <option value="analytics" ${this.data.usage_context === 'analytics' ? 'selected' : ''}>Analytics</option>
                            <option value="realtime" ${this.data.usage_context === 'realtime' ? 'selected' : ''}>Realtime</option>
                            <option value="background" ${this.data.usage_context === 'background' ? 'selected' : ''}>Background</option>
                        </select>
                    </div>
                </div>
                
                <!-- Invocation Pattern and Caching Strategy -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Invocation Pattern
                        </label>
                        <select 
                            id="invocation-pattern-select"
                            ${this.options.readOnly ? 'disabled' : ''}
                            class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        >
                            <option value="on_mount" ${this.data.invocation_pattern === 'on_mount' ? 'selected' : ''}>On Mount</option>
                            <option value="on_click" ${this.data.invocation_pattern === 'on_click' ? 'selected' : ''}>On Click</option>
                            <option value="on_change" ${this.data.invocation_pattern === 'on_change' ? 'selected' : ''}>On Change</option>
                            <option value="on_submit" ${this.data.invocation_pattern === 'on_submit' ? 'selected' : ''}>On Submit</option>
                            <option value="manual" ${this.data.invocation_pattern === 'manual' ? 'selected' : ''}>Manual</option>
                        </select>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Caching Strategy
                        </label>
                        <input 
                            type="text" 
                            id="caching-strategy-input"
                            class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            value="${this.escapeHtml(this.data.caching_strategy || '')}"
                            ${this.options.readOnly ? 'readonly' : ''}
                            placeholder="e.g., cache-first, network-first"
                        />
                    </div>
                </div>
                
                <!-- Retry Policy -->
                <div class="retry-policy-section">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">Retry Policy</h3>
                        ${!this.options.readOnly ? `
                            <button 
                                type="button" 
                                class="toggle-retry-policy-btn px-4 py-2 ${this.data.retry_policy ? 'bg-red-600 hover:bg-red-700' : 'bg-blue-600 hover:bg-blue-700'} text-white rounded-lg transition-colors text-sm"
                            >
                                ${this.data.retry_policy ? 'Remove Retry Policy' : 'Add Retry Policy'}
                            </button>
                        ` : ''}
                    </div>
                    ${this.data.retry_policy ? this.renderRetryPolicy(this.data.retry_policy) : `
                        <div class="text-center py-4 text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                            <p>No retry policy configured</p>
                        </div>
                    `}
                </div>
            </div>
        `;
        
        this.container.innerHTML = html;
    }
    
    renderRetryPolicy(retryPolicy) {
        return `
            <div class="retry-policy-form bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Max Retries (0-10)
                        </label>
                        <input 
                            type="number" 
                            class="retry-policy-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            data-field="max_retries"
                            value="${retryPolicy.max_retries !== undefined ? retryPolicy.max_retries : 3}"
                            ${this.options.readOnly ? 'readonly' : ''}
                            min="0"
                            max="10"
                        />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Backoff (ms, min: 100)
                        </label>
                        <input 
                            type="number" 
                            class="retry-policy-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            data-field="backoff_ms"
                            value="${retryPolicy.backoff_ms !== undefined ? retryPolicy.backoff_ms : 1000}"
                            ${this.options.readOnly ? 'readonly' : ''}
                            min="100"
                        />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Timeout (ms, min: 1000)
                        </label>
                        <input 
                            type="number" 
                            class="retry-policy-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            data-field="timeout_ms"
                            value="${retryPolicy.timeout_ms !== undefined ? retryPolicy.timeout_ms : 5000}"
                            ${this.options.readOnly ? 'readonly' : ''}
                            min="1000"
                        />
                    </div>
                </div>
            </div>
        `;
    }
    
    setupEventListeners() {
        if (this.options.readOnly) return;
        
        // Via Service Autocomplete
        this.setupAutocomplete('via-service-input', 'via-service-suggestions', 'services');
        
        // Via Hook Autocomplete
        this.setupAutocomplete('via-hook-input', 'via-hook-suggestions', 'hooks');
        
        // Field changes
        const viaServiceInput = this.container.querySelector('#via-service-input');
        if (viaServiceInput) {
            viaServiceInput.addEventListener('change', (e) => {
                this.data.via_service = e.target.value;
                this.triggerChange();
            });
        }
        
        const viaHookInput = this.container.querySelector('#via-hook-input');
        if (viaHookInput) {
            viaHookInput.addEventListener('change', (e) => {
                this.data.via_hook = e.target.value || null;
                this.triggerChange();
            });
        }
        
        const usageTypeSelect = this.container.querySelector('#usage-type-select');
        if (usageTypeSelect) {
            usageTypeSelect.addEventListener('change', (e) => {
                this.data.usage_type = e.target.value;
                this.triggerChange();
            });
        }
        
        const usageContextSelect = this.container.querySelector('#usage-context-select');
        if (usageContextSelect) {
            usageContextSelect.addEventListener('change', (e) => {
                this.data.usage_context = e.target.value;
                this.triggerChange();
            });
        }
        
        const invocationPatternSelect = this.container.querySelector('#invocation-pattern-select');
        if (invocationPatternSelect) {
            invocationPatternSelect.addEventListener('change', (e) => {
                this.data.invocation_pattern = e.target.value;
                this.triggerChange();
            });
        }
        
        const cachingStrategyInput = this.container.querySelector('#caching-strategy-input');
        if (cachingStrategyInput) {
            cachingStrategyInput.addEventListener('change', (e) => {
                this.data.caching_strategy = e.target.value || null;
                this.triggerChange();
            });
        }
        
        // Retry Policy Toggle
        const toggleRetryBtn = this.container.querySelector('.toggle-retry-policy-btn');
        if (toggleRetryBtn) {
            toggleRetryBtn.addEventListener('click', () => {
                if (this.data.retry_policy) {
                    this.data.retry_policy = null;
                } else {
                    this.data.retry_policy = {
                        max_retries: 3,
                        backoff_ms: 1000,
                        timeout_ms: 5000
                    };
                }
                this.render();
                this.setupEventListeners();
                this.triggerChange();
            });
        }
        
        // Retry Policy Fields
        const retryPolicyFields = this.container.querySelectorAll('.retry-policy-field');
        retryPolicyFields.forEach(field => {
            field.addEventListener('change', (e) => {
                const fieldName = e.target.getAttribute('data-field');
                let value = parseInt(e.target.value);
                if (fieldName === 'max_retries') {
                    value = Math.max(0, Math.min(10, value));
                } else if (fieldName === 'backoff_ms') {
                    value = Math.max(100, value);
                } else if (fieldName === 'timeout_ms') {
                    value = Math.max(1000, value);
                }
                this.data.retry_policy[fieldName] = value;
                e.target.value = value;
                this.triggerChange();
            });
        });
    }
    
    setupAutocomplete(inputId, suggestionsId, type) {
        const input = this.container.querySelector(`#${inputId}`);
        const suggestionsDiv = this.container.querySelector(`#${suggestionsId}`);
        
        if (!input || !suggestionsDiv) return;
        
        let debounceTimeout;
        
        input.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            
            clearTimeout(debounceTimeout);
            
            if (query.length < 2) {
                suggestionsDiv.classList.add('hidden');
                return;
            }
            
            debounceTimeout = setTimeout(() => {
                this.showSuggestions(query, suggestionsDiv, type);
            }, 300);
        });
        
        input.addEventListener('blur', () => {
            // Hide suggestions after a short delay to allow click
            setTimeout(() => {
                suggestionsDiv.classList.add('hidden');
            }, 200);
        });
        
        input.addEventListener('focus', () => {
            if (input.value.trim().length >= 2) {
                this.showSuggestions(input.value.trim(), suggestionsDiv, type);
            }
        });
    }
    
    showSuggestions(query, suggestionsDiv, type) {
        const suggestions = this.getSuggestions(query, type);
        
        if (suggestions.length === 0) {
            suggestionsDiv.classList.add('hidden');
            return;
        }
        
        suggestionsDiv.innerHTML = suggestions.map(suggestion => `
            <div class="autocomplete-suggestion px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer" data-value="${this.escapeHtml(suggestion)}">
                ${this.escapeHtml(suggestion)}
            </div>
        `).join('');
        
        suggestionsDiv.classList.remove('hidden');
        
        // Add click handlers
        suggestionsDiv.querySelectorAll('.autocomplete-suggestion').forEach(item => {
            item.addEventListener('click', (e) => {
                const value = e.target.getAttribute('data-value');
                const input = suggestionsDiv.previousElementSibling;
                if (input) {
                    input.value = value;
                    input.dispatchEvent(new Event('change'));
                }
                suggestionsDiv.classList.add('hidden');
            });
        });
    }
    
    getSuggestions(query, type) {
        // Simple local filtering - can be enhanced with API calls
        const cache = this.autocompleteCache[type] || [];
        const lowerQuery = query.toLowerCase();
        return cache.filter(item => 
            item.toLowerCase().includes(lowerQuery)
        ).slice(0, 10);
    }
    
    escapeHtml(text) {
        if (text === null || text === undefined) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    triggerChange() {
        const event = new CustomEvent('relationship-connection-change', {
            detail: { data: this.data }
        });
        this.container.dispatchEvent(event);
    }
    
    getData() {
        return JSON.parse(JSON.stringify(this.data));
    }
    
    setData(data) {
        this.data = this.initializeData(data);
        this.render();
        this.setupEventListeners();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RelationshipConnectionEditor;
}
