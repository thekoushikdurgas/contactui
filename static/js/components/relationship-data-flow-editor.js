/**
 * Relationship Data Flow Editor Component
 * 
 * Provides a specialized editor for RelationshipDataFlow with:
 * - Request data flow (params, headers, body_schema)
 * - Response data flow (data_fields, error_handling, loading_state)
 * - Data transforms array
 */

class RelationshipDataFlowEditor {
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
                request: {
                    params: [],
                    headers: [],
                    body_schema: null
                },
                response: {
                    data_fields: [],
                    error_handling: 'console',
                    loading_state: 'spinner'
                },
                transforms: []
            };
        }
        
        return {
            request: {
                params: Array.isArray(initialData.request?.params) ? [...initialData.request.params] : [],
                headers: Array.isArray(initialData.request?.headers) ? [...initialData.request.headers] : [],
                body_schema: initialData.request?.body_schema || null
            },
            response: {
                data_fields: Array.isArray(initialData.response?.data_fields) ? [...initialData.response.data_fields] : [],
                error_handling: initialData.response?.error_handling || 'console',
                loading_state: initialData.response?.loading_state || 'spinner'
            },
            transforms: Array.isArray(initialData.transforms) ? [...initialData.transforms] : []
        };
    }
    
    init() {
        this.container.innerHTML = '';
        this.container.classList.add('relationship-data-flow-editor');
        this.render();
        this.setupEventListeners();
    }
    
    render() {
        const html = `
            <div class="relationship-data-flow-editor-wrapper space-y-6">
                <!-- Request Data Flow -->
                <div class="request-section">
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Request Data Flow</h3>
                    <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700 space-y-4">
                        <!-- Params -->
                        <div>
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                URL/Query Params
                            </label>
                            <div class="params-list space-y-2">
                                ${this.data.request.params.length === 0 ? `
                                    <p class="text-gray-500 dark:text-gray-400 text-sm">No params added</p>
                                ` : this.data.request.params.map((param, index) => this.renderArrayItem('request.params', param, index)).join('')}
                            </div>
                            ${!this.options.readOnly ? `
                                <button 
                                    type="button" 
                                    class="add-array-item-btn mt-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
                                    data-path="request.params"
                                >
                                    + Add Param
                                </button>
                            ` : ''}
                        </div>
                        
                        <!-- Headers -->
                        <div>
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Required Headers
                            </label>
                            <div class="headers-list space-y-2">
                                ${this.data.request.headers.length === 0 ? `
                                    <p class="text-gray-500 dark:text-gray-400 text-sm">No headers added</p>
                                ` : this.data.request.headers.map((header, index) => this.renderArrayItem('request.headers', header, index)).join('')}
                            </div>
                            ${!this.options.readOnly ? `
                                <button 
                                    type="button" 
                                    class="add-array-item-btn mt-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
                                    data-path="request.headers"
                                >
                                    + Add Header
                                </button>
                            ` : ''}
                        </div>
                        
                        <!-- Body Schema -->
                        <div>
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Body Schema
                            </label>
                            <input 
                                type="text" 
                                class="body-schema-input w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                                value="${this.escapeHtml(this.data.request.body_schema || '')}"
                                ${this.options.readOnly ? 'readonly' : ''}
                                placeholder="Schema name (e.g., CreateUserRequest)"
                            />
                        </div>
                    </div>
                </div>
                
                <!-- Response Data Flow -->
                <div class="response-section">
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Response Data Flow</h3>
                    <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700 space-y-4">
                        <!-- Data Fields -->
                        <div>
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Data Fields Used
                            </label>
                            <div class="data-fields-list space-y-2">
                                ${this.data.response.data_fields.length === 0 ? `
                                    <p class="text-gray-500 dark:text-gray-400 text-sm">No data fields added</p>
                                ` : this.data.response.data_fields.map((field, index) => this.renderArrayItem('response.data_fields', field, index)).join('')}
                            </div>
                            ${!this.options.readOnly ? `
                                <button 
                                    type="button" 
                                    class="add-array-item-btn mt-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
                                    data-path="response.data_fields"
                                >
                                    + Add Data Field
                                </button>
                            ` : ''}
                        </div>
                        
                        <!-- Error Handling -->
                        <div>
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Error Handling Strategy
                            </label>
                            <select 
                                id="error-handling-select"
                                ${this.options.readOnly ? 'disabled' : ''}
                                class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            >
                                <option value="console" ${this.data.response.error_handling === 'console' ? 'selected' : ''}>Console</option>
                                <option value="toast" ${this.data.response.error_handling === 'toast' ? 'selected' : ''}>Toast Notification</option>
                                <option value="modal" ${this.data.response.error_handling === 'modal' ? 'selected' : ''}>Modal Dialog</option>
                                <option value="inline" ${this.data.response.error_handling === 'inline' ? 'selected' : ''}>Inline Message</option>
                                <option value="silent" ${this.data.response.error_handling === 'silent' ? 'selected' : ''}>Silent</option>
                            </select>
                        </div>
                        
                        <!-- Loading State -->
                        <div>
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Loading State UI
                            </label>
                            <select 
                                id="loading-state-select"
                                ${this.options.readOnly ? 'disabled' : ''}
                                class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            >
                                <option value="spinner" ${this.data.response.loading_state === 'spinner' ? 'selected' : ''}>Spinner</option>
                                <option value="skeleton" ${this.data.response.loading_state === 'skeleton' ? 'selected' : ''}>Skeleton</option>
                                <option value="progress" ${this.data.response.loading_state === 'progress' ? 'selected' : ''}>Progress Bar</option>
                                <option value="none" ${this.data.response.loading_state === 'none' ? 'selected' : ''}>None</option>
                            </select>
                        </div>
                    </div>
                </div>
                
                <!-- Data Transforms -->
                <div class="transforms-section">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">Data Transforms</h3>
                        ${!this.options.readOnly ? `
                            <button 
                                type="button" 
                                class="add-transform-btn px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
                            >
                                + Add Transform
                            </button>
                        ` : ''}
                    </div>
                    <div class="transforms-list space-y-4">
                        ${this.data.transforms.length === 0 ? `
                            <div class="text-center py-8 text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                                <p>No transforms added</p>
                            </div>
                        ` : this.data.transforms.map((transform, index) => this.renderTransform(transform, index)).join('')}
                    </div>
                </div>
            </div>
        `;
        
        this.container.innerHTML = html;
    }
    
    renderArrayItem(path, value, index) {
        return `
            <div class="array-item flex items-center gap-2 bg-white dark:bg-gray-700 rounded-lg p-2 border border-gray-200 dark:border-gray-600" data-path="${path}" data-index="${index}">
                <input 
                    type="text" 
                    class="array-item-input flex-1 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm"
                    value="${this.escapeHtml(value)}"
                    ${this.options.readOnly ? 'readonly' : ''}
                    placeholder="Enter value..."
                    data-path="${path}"
                    data-index="${index}"
                />
                ${!this.options.readOnly ? `
                    <button 
                        type="button" 
                        class="remove-array-item-btn px-3 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm"
                        data-path="${path}"
                        data-index="${index}"
                    >
                        Remove
                    </button>
                ` : ''}
            </div>
        `;
    }
    
    renderTransform(transform, index) {
        return `
            <div class="transform-item bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700" data-index="${index}">
                <div class="flex justify-between items-start mb-3">
                    <h4 class="font-semibold text-gray-900 dark:text-gray-100">Transform #${index + 1}</h4>
                    ${!this.options.readOnly ? `
                        <button 
                            type="button" 
                            class="remove-transform-btn px-3 py-1 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm"
                            data-index="${index}"
                        >
                            Remove
                        </button>
                    ` : ''}
                </div>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Transform Name <span class="text-red-500">*</span>
                        </label>
                        <input 
                            type="text" 
                            class="transform-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            data-field="name"
                            data-index="${index}"
                            value="${this.escapeHtml(transform.name || '')}"
                            ${this.options.readOnly ? 'readonly' : ''}
                            required
                        />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Field <span class="text-red-500">*</span>
                        </label>
                        <input 
                            type="text" 
                            class="transform-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            data-field="field"
                            data-index="${index}"
                            value="${this.escapeHtml(transform.field || '')}"
                            ${this.options.readOnly ? 'readonly' : ''}
                            required
                        />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            File Path <span class="text-red-500">*</span>
                        </label>
                        <input 
                            type="text" 
                            class="transform-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            data-field="file_path"
                            data-index="${index}"
                            value="${this.escapeHtml(transform.file_path || '')}"
                            ${this.options.readOnly ? 'readonly' : ''}
                            required
                        />
                    </div>
                </div>
            </div>
        `;
    }
    
    setupEventListeners() {
        if (this.options.readOnly) return;
        
        // Add array item buttons
        const addBtns = this.container.querySelectorAll('.add-array-item-btn');
        addBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const path = e.target.getAttribute('data-path');
                this.addArrayItem(path);
            });
        });
        
        // Remove array item buttons
        const removeBtns = this.container.querySelectorAll('.remove-array-item-btn');
        removeBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const path = e.target.getAttribute('data-path');
                const index = parseInt(e.target.getAttribute('data-index'));
                this.removeArrayItem(path, index);
            });
        });
        
        // Array item input changes
        const arrayInputs = this.container.querySelectorAll('.array-item-input');
        arrayInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                const path = e.target.getAttribute('data-path');
                const index = parseInt(e.target.getAttribute('data-index'));
                this.updateArrayItem(path, index, e.target.value);
            });
        });
        
        // Body schema input
        const bodySchemaInput = this.container.querySelector('.body-schema-input');
        if (bodySchemaInput) {
            bodySchemaInput.addEventListener('change', (e) => {
                this.data.request.body_schema = e.target.value || null;
                this.triggerChange();
            });
        }
        
        // Error handling select
        const errorHandlingSelect = this.container.querySelector('#error-handling-select');
        if (errorHandlingSelect) {
            errorHandlingSelect.addEventListener('change', (e) => {
                this.data.response.error_handling = e.target.value;
                this.triggerChange();
            });
        }
        
        // Loading state select
        const loadingStateSelect = this.container.querySelector('#loading-state-select');
        if (loadingStateSelect) {
            loadingStateSelect.addEventListener('change', (e) => {
                this.data.response.loading_state = e.target.value;
                this.triggerChange();
            });
        }
        
        // Add transform button
        const addTransformBtn = this.container.querySelector('.add-transform-btn');
        if (addTransformBtn) {
            addTransformBtn.addEventListener('click', () => {
                this.addTransform();
            });
        }
        
        // Remove transform buttons
        const removeTransformBtns = this.container.querySelectorAll('.remove-transform-btn');
        removeTransformBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const index = parseInt(e.target.getAttribute('data-index'));
                this.removeTransform(index);
            });
        });
        
        // Transform field changes
        const transformFields = this.container.querySelectorAll('.transform-field');
        transformFields.forEach(field => {
            field.addEventListener('change', (e) => {
                const index = parseInt(e.target.getAttribute('data-index'));
                const fieldName = e.target.getAttribute('data-field');
                this.updateTransformField(index, fieldName, e.target.value);
            });
        });
    }
    
    addArrayItem(path) {
        const parts = path.split('.');
        let target = this.data;
        for (let i = 0; i < parts.length - 1; i++) {
            target = target[parts[i]];
        }
        const arrayName = parts[parts.length - 1];
        if (!Array.isArray(target[arrayName])) {
            target[arrayName] = [];
        }
        target[arrayName].push('');
        this.render();
        this.setupEventListeners();
        this.triggerChange();
    }
    
    removeArrayItem(path, index) {
        const parts = path.split('.');
        let target = this.data;
        for (let i = 0; i < parts.length - 1; i++) {
            target = target[parts[i]];
        }
        const arrayName = parts[parts.length - 1];
        if (Array.isArray(target[arrayName]) && index >= 0 && index < target[arrayName].length) {
            target[arrayName].splice(index, 1);
            this.render();
            this.setupEventListeners();
            this.triggerChange();
        }
    }
    
    updateArrayItem(path, index, value) {
        const parts = path.split('.');
        let target = this.data;
        for (let i = 0; i < parts.length - 1; i++) {
            target = target[parts[i]];
        }
        const arrayName = parts[parts.length - 1];
        if (Array.isArray(target[arrayName]) && index >= 0 && index < target[arrayName].length) {
            target[arrayName][index] = value;
            this.triggerChange();
        }
    }
    
    addTransform() {
        this.data.transforms.push({
            name: '',
            field: '',
            file_path: ''
        });
        this.render();
        this.setupEventListeners();
    }
    
    removeTransform(index) {
        if (index >= 0 && index < this.data.transforms.length) {
            this.data.transforms.splice(index, 1);
            this.render();
            this.setupEventListeners();
            this.triggerChange();
        }
    }
    
    updateTransformField(index, fieldName, value) {
        if (index >= 0 && index < this.data.transforms.length) {
            this.data.transforms[index][fieldName] = value;
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
        const event = new CustomEvent('relationship-data-flow-change', {
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
    module.exports = RelationshipDataFlowEditor;
}
