/**
 * Endpoint Methods Editor Component
 * 
 * Provides a specialized editor for EndpointMethods with:
 * - Array editors for each method type
 * - Add/remove functionality for each array
 */

class EndpointMethodsEditor {
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
        
        this.methodTypes = [
            { key: 'service_methods', label: 'Service Methods', description: 'Service methods used by this endpoint' },
            { key: 'repository_methods', label: 'Repository Methods', description: 'Repository methods used by this endpoint' },
            { key: 'validation_methods', label: 'Validation Methods', description: 'Validation methods used by this endpoint' },
            { key: 'middleware_methods', label: 'Middleware Methods', description: 'Middleware methods used by this endpoint' }
        ];
        
        this.data = this.initializeData(this.options.data);
        this.init();
    }
    
    initializeData(initialData) {
        if (!initialData || typeof initialData !== 'object') {
            const data = {};
            this.methodTypes.forEach(methodType => {
                data[methodType.key] = [];
            });
            return data;
        }
        
        const data = {};
        this.methodTypes.forEach(methodType => {
            data[methodType.key] = Array.isArray(initialData[methodType.key]) 
                ? [...initialData[methodType.key]] 
                : [];
        });
        return data;
    }
    
    init() {
        this.container.innerHTML = '';
        this.container.classList.add('endpoint-methods-editor');
        this.render();
        this.setupEventListeners();
    }
    
    render() {
        const html = `
            <div class="endpoint-methods-editor-wrapper space-y-6">
                ${this.methodTypes.map(methodType => this.renderMethodType(methodType)).join('')}
            </div>
        `;
        
        this.container.innerHTML = html;
    }
    
    renderMethodType(methodType) {
        const methods = this.data[methodType.key] || [];
        
        return `
            <div class="method-type-section" data-method-type="${methodType.key}">
                <div class="flex justify-between items-center mb-4">
                    <div>
                        <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">${methodType.label}</h3>
                        <p class="text-sm text-gray-600 dark:text-gray-400">${methodType.description}</p>
                    </div>
                    ${!this.options.readOnly ? `
                        <button 
                            type="button" 
                            class="add-method-btn px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
                            data-method-type="${methodType.key}"
                        >
                            + Add Method
                        </button>
                    ` : ''}
                </div>
                
                <div class="methods-list space-y-2">
                    ${methods.length === 0 ? `
                        <div class="text-center py-4 text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                            <p>No ${methodType.label.toLowerCase()} added</p>
                        </div>
                    ` : methods.map((method, index) => this.renderMethodItem(methodType.key, method, index)).join('')}
                </div>
            </div>
        `;
    }
    
    renderMethodItem(methodType, method, index) {
        return `
            <div class="method-item flex items-center gap-2 bg-gray-50 dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700" data-index="${index}">
                <input 
                    type="text" 
                    class="method-input flex-1 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                    value="${this.escapeHtml(method)}"
                    ${this.options.readOnly ? 'readonly' : ''}
                    placeholder="Method name"
                    data-method-type="${methodType}"
                    data-index="${index}"
                />
                ${!this.options.readOnly ? `
                    <button 
                        type="button" 
                        class="remove-method-btn px-3 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm"
                        data-method-type="${methodType}"
                        data-index="${index}"
                    >
                        Remove
                    </button>
                ` : ''}
            </div>
        `;
    }
    
    setupEventListeners() {
        if (this.options.readOnly) return;
        
        // Add method buttons
        const addBtns = this.container.querySelectorAll('.add-method-btn');
        addBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const methodType = e.target.getAttribute('data-method-type');
                this.addMethod(methodType);
            });
        });
        
        // Remove method buttons
        const removeBtns = this.container.querySelectorAll('.remove-method-btn');
        removeBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const methodType = e.target.getAttribute('data-method-type');
                const index = parseInt(e.target.getAttribute('data-index'));
                this.removeMethod(methodType, index);
            });
        });
        
        // Method input changes
        const methodInputs = this.container.querySelectorAll('.method-input');
        methodInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                const methodType = e.target.getAttribute('data-method-type');
                const index = parseInt(e.target.getAttribute('data-index'));
                const value = e.target.value.trim();
                this.updateMethod(methodType, index, value);
            });
        });
    }
    
    addMethod(methodType) {
        if (!this.data[methodType]) {
            this.data[methodType] = [];
        }
        this.data[methodType].push('');
        this.render();
        this.setupEventListeners();
        
        // Focus on the new input
        const section = this.container.querySelector(`.method-type-section[data-method-type="${methodType}"]`);
        if (section) {
            const inputs = section.querySelectorAll('.method-input');
            if (inputs.length > 0) {
                inputs[inputs.length - 1].focus();
            }
        }
    }
    
    removeMethod(methodType, index) {
        if (this.data[methodType] && index >= 0 && index < this.data[methodType].length) {
            this.data[methodType].splice(index, 1);
            this.render();
            this.setupEventListeners();
            this.triggerChange();
        }
    }
    
    updateMethod(methodType, index, value) {
        if (this.data[methodType] && index >= 0 && index < this.data[methodType].length) {
            this.data[methodType][index] = value;
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
        const event = new CustomEvent('endpoint-methods-change', {
            detail: { data: this.data }
        });
        this.container.dispatchEvent(event);
    }
    
    getData() {
        // Return null if all arrays are empty
        const hasAnyMethod = Object.values(this.data).some(methods => 
            Array.isArray(methods) && methods.length > 0 && methods.some(m => m && m.trim())
        );
        return hasAnyMethod ? JSON.parse(JSON.stringify(this.data)) : null;
    }
    
    setData(data) {
        this.data = this.initializeData(data);
        this.render();
        this.setupEventListeners();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EndpointMethodsEditor;
}
