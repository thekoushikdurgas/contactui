/**
 * Lambda Services Editor Component
 * 
 * Provides a specialized editor for LambdaServices with:
 * - Primary Lambda service form
 * - Dependencies array editor
 * - Environment variables editor
 */

class LambdaServicesEditor {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.options = {
            data: options.data || null,
            readOnly: options.readOnly || false,
            ...options
        };
        
        if (!this.container) {
            throw new Error('Container element not found');
        }
        
        this.data = this.initializeData(this.options.data);
        this.init();
    }
    
    initializeData(initialData) {
        if (!initialData || typeof initialData !== 'object') {
            return {
                primary: null,
                dependencies: [],
                environment: {}
            };
        }
        
        return {
            primary: initialData.primary || null,
            dependencies: Array.isArray(initialData.dependencies) ? [...initialData.dependencies] : [],
            environment: initialData.environment && typeof initialData.environment === 'object' 
                ? {...initialData.environment} 
                : {}
        };
    }
    
    init() {
        this.container.innerHTML = '';
        this.container.classList.add('lambda-services-editor');
        this.render();
        this.setupEventListeners();
    }
    
    render() {
        const html = `
            <div class="lambda-services-editor-wrapper space-y-6">
                <!-- Primary Lambda Service -->
                <div class="primary-service-section">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">Primary Lambda Service</h3>
                        ${!this.options.readOnly ? `
                            <button 
                                type="button" 
                                class="toggle-primary-btn px-4 py-2 ${this.data.primary ? 'bg-red-600 hover:bg-red-700' : 'bg-blue-600 hover:bg-blue-700'} text-white rounded-lg transition-colors text-sm"
                            >
                                ${this.data.primary ? 'Remove Primary Service' : 'Add Primary Service'}
                            </button>
                        ` : ''}
                    </div>
                    ${this.data.primary ? this.renderPrimaryService(this.data.primary) : `
                        <div class="text-center py-8 text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                            <p>No primary service configured</p>
                        </div>
                    `}
                </div>
                
                <!-- Dependencies -->
                <div class="dependencies-section">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">Dependencies</h3>
                        ${!this.options.readOnly ? `
                            <button 
                                type="button" 
                                class="add-dependency-btn px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
                            >
                                + Add Dependency
                            </button>
                        ` : ''}
                    </div>
                    <div class="dependencies-list space-y-4">
                        ${this.data.dependencies.length === 0 ? `
                            <div class="text-center py-8 text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                                <p>No dependencies added</p>
                            </div>
                        ` : this.data.dependencies.map((dep, index) => this.renderDependency(dep, index)).join('')}
                    </div>
                </div>
                
                <!-- Environment Variables -->
                <div class="environment-section">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">Environment Variables</h3>
                        ${!this.options.readOnly ? `
                            <button 
                                type="button" 
                                class="add-env-var-btn px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
                            >
                                + Add Variable
                            </button>
                        ` : ''}
                    </div>
                    <div class="environment-vars-list space-y-2">
                        ${Object.keys(this.data.environment).length === 0 ? `
                            <div class="text-center py-4 text-gray-500 dark:text-gray-400">
                                <p>No environment variables</p>
                            </div>
                        ` : Object.entries(this.data.environment).map(([key, value], index) => this.renderEnvVar(key, value, index)).join('')}
                    </div>
                </div>
            </div>
        `;
        
        this.container.innerHTML = html;
    }
    
    renderPrimaryService(primary) {
        return `
            <div class="primary-service-form bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Service Name <span class="text-red-500">*</span>
                        </label>
                        <input 
                            type="text" 
                            class="primary-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            data-field="service_name"
                            value="${this.escapeHtml(primary.service_name || '')}"
                            ${this.options.readOnly ? 'readonly' : ''}
                            required
                        />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Function Name <span class="text-red-500">*</span>
                        </label>
                        <input 
                            type="text" 
                            class="primary-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            data-field="function_name"
                            value="${this.escapeHtml(primary.function_name || '')}"
                            ${this.options.readOnly ? 'readonly' : ''}
                            required
                        />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Runtime
                        </label>
                        <input 
                            type="text" 
                            class="primary-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            data-field="runtime"
                            value="${this.escapeHtml(primary.runtime || 'python3.11')}"
                            ${this.options.readOnly ? 'readonly' : ''}
                            placeholder="python3.11"
                        />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Memory (MB)
                        </label>
                        <input 
                            type="number" 
                            class="primary-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            data-field="memory_mb"
                            value="${primary.memory_mb || 256}"
                            ${this.options.readOnly ? 'readonly' : ''}
                            min="128"
                            step="64"
                        />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Timeout (seconds)
                        </label>
                        <input 
                            type="number" 
                            class="primary-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            data-field="timeout_seconds"
                            value="${primary.timeout_seconds || 30}"
                            ${this.options.readOnly ? 'readonly' : ''}
                            min="1"
                        />
                    </div>
                </div>
            </div>
        `;
    }
    
    renderDependency(dep, index) {
        return `
            <div class="dependency-item bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700" data-index="${index}">
                <div class="flex justify-between items-start mb-3">
                    <h4 class="font-semibold text-gray-900 dark:text-gray-100">Dependency #${index + 1}</h4>
                    ${!this.options.readOnly ? `
                        <button 
                            type="button" 
                            class="remove-dependency-btn px-3 py-1 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm"
                            data-index="${index}"
                        >
                            Remove
                        </button>
                    ` : ''}
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Service Name <span class="text-red-500">*</span>
                        </label>
                        <input 
                            type="text" 
                            class="dependency-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            data-field="service_name"
                            data-index="${index}"
                            value="${this.escapeHtml(dep.service_name || '')}"
                            ${this.options.readOnly ? 'readonly' : ''}
                            required
                        />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Function Name <span class="text-red-500">*</span>
                        </label>
                        <input 
                            type="text" 
                            class="dependency-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            data-field="function_name"
                            data-index="${index}"
                            value="${this.escapeHtml(dep.function_name || '')}"
                            ${this.options.readOnly ? 'readonly' : ''}
                            required
                        />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Invocation Type
                        </label>
                        <select 
                            class="dependency-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            data-field="invocation_type"
                            data-index="${index}"
                            ${this.options.readOnly ? 'disabled' : ''}
                        >
                            <option value="sync" ${dep.invocation_type === 'sync' ? 'selected' : ''}>Sync</option>
                            <option value="async" ${dep.invocation_type === 'async' ? 'selected' : ''}>Async</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Purpose <span class="text-red-500">*</span>
                        </label>
                        <input 
                            type="text" 
                            class="dependency-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            data-field="purpose"
                            data-index="${index}"
                            value="${this.escapeHtml(dep.purpose || '')}"
                            ${this.options.readOnly ? 'readonly' : ''}
                            required
                        />
                    </div>
                </div>
            </div>
        `;
    }
    
    renderEnvVar(key, value, index) {
        return `
            <div class="env-var-item flex items-center gap-2 bg-gray-50 dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700" data-key="${this.escapeHtml(key)}">
                <input 
                    type="text" 
                    class="env-var-key flex-1 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm"
                    value="${this.escapeHtml(key)}"
                    ${this.options.readOnly ? 'readonly' : ''}
                    placeholder="Variable name"
                />
                <span class="text-gray-400">=</span>
                <input 
                    type="text" 
                    class="env-var-value flex-1 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm"
                    value="${this.escapeHtml(value)}"
                    ${this.options.readOnly ? 'readonly' : ''}
                    placeholder="Variable value"
                />
                ${!this.options.readOnly ? `
                    <button 
                        type="button" 
                        class="remove-env-var-btn px-3 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm"
                        data-key="${this.escapeHtml(key)}"
                    >
                        Remove
                    </button>
                ` : ''}
            </div>
        `;
    }
    
    setupEventListeners() {
        if (this.options.readOnly) return;
        
        // Toggle primary service
        const toggleBtn = this.container.querySelector('.toggle-primary-btn');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => {
                if (this.data.primary) {
                    this.data.primary = null;
                } else {
                    this.data.primary = {
                        service_name: '',
                        function_name: '',
                        runtime: 'python3.11',
                        memory_mb: 256,
                        timeout_seconds: 30
                    };
                }
                this.render();
                this.setupEventListeners();
                this.triggerChange();
            });
        }
        
        // Primary service fields
        const primaryFields = this.container.querySelectorAll('.primary-field');
        primaryFields.forEach(field => {
            field.addEventListener('change', (e) => {
                const fieldName = e.target.getAttribute('data-field');
                let value = e.target.value;
                if (fieldName === 'memory_mb' || fieldName === 'timeout_seconds') {
                    value = parseInt(value) || (fieldName === 'memory_mb' ? 256 : 30);
                }
                this.data.primary[fieldName] = value;
                this.triggerChange();
            });
        });
        
        // Add dependency
        const addDepBtn = this.container.querySelector('.add-dependency-btn');
        if (addDepBtn) {
            addDepBtn.addEventListener('click', () => {
                this.data.dependencies.push({
                    service_name: '',
                    function_name: '',
                    invocation_type: 'sync',
                    purpose: ''
                });
                this.render();
                this.setupEventListeners();
            });
        }
        
        // Remove dependency
        const removeDepBtns = this.container.querySelectorAll('.remove-dependency-btn');
        removeDepBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const index = parseInt(e.target.getAttribute('data-index'));
                this.data.dependencies.splice(index, 1);
                this.render();
                this.setupEventListeners();
                this.triggerChange();
            });
        });
        
        // Dependency fields
        const depFields = this.container.querySelectorAll('.dependency-field');
        depFields.forEach(field => {
            field.addEventListener('change', (e) => {
                const index = parseInt(e.target.getAttribute('data-index'));
                const fieldName = e.target.getAttribute('data-field');
                this.data.dependencies[index][fieldName] = e.target.value;
                this.triggerChange();
            });
        });
        
        // Add environment variable
        const addEnvBtn = this.container.querySelector('.add-env-var-btn');
        if (addEnvBtn) {
            addEnvBtn.addEventListener('click', () => {
                const key = `VAR_${Object.keys(this.data.environment).length + 1}`;
                this.data.environment[key] = '';
                this.render();
                this.setupEventListeners();
            });
        }
        
        // Remove environment variable
        const removeEnvBtns = this.container.querySelectorAll('.remove-env-var-btn');
        removeEnvBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const key = e.target.getAttribute('data-key');
                delete this.data.environment[key];
                this.render();
                this.setupEventListeners();
                this.triggerChange();
            });
        });
        
        // Environment variable fields
        const envKeyInputs = this.container.querySelectorAll('.env-var-key');
        envKeyInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                const oldKey = e.target.closest('.env-var-item').getAttribute('data-key');
                const newKey = e.target.value.trim();
                if (newKey && newKey !== oldKey) {
                    this.data.environment[newKey] = this.data.environment[oldKey] || '';
                    delete this.data.environment[oldKey];
                    e.target.closest('.env-var-item').setAttribute('data-key', newKey);
                    this.triggerChange();
                }
            });
        });
        
        const envValueInputs = this.container.querySelectorAll('.env-var-value');
        envValueInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                const key = e.target.closest('.env-var-item').getAttribute('data-key');
                this.data.environment[key] = e.target.value;
                this.triggerChange();
            });
        });
    }
    
    escapeHtml(text) {
        if (text === null || text === undefined) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    triggerChange() {
        const event = new CustomEvent('lambda-services-change', {
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
    module.exports = LambdaServicesEditor;
}
