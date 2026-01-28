/**
 * Endpoint Files Editor Component
 * 
 * Provides a specialized editor for EndpointFiles with:
 * - File reference inputs for all file types
 * - Validation for required files
 */

class EndpointFilesEditor {
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
        
        this.fileTypes = [
            { key: 'service_file', label: 'Service File', description: 'Service file path' },
            { key: 'router_file', label: 'Router File', description: 'Router file path' },
            { key: 'repository_file', label: 'Repository File', description: 'Repository file path' },
            { key: 'schema_file', label: 'Schema File', description: 'Schema file path' },
            { key: 'test_file', label: 'Test File', description: 'Test file path' },
            { key: 'graphql_file', label: 'GraphQL File', description: 'GraphQL file path' },
            { key: 'sql_file', label: 'SQL File', description: 'SQL file path' }
        ];
        
        this.data = this.initializeData(this.options.data);
        this.init();
    }
    
    initializeData(initialData) {
        if (!initialData || typeof initialData !== 'object') {
            const data = {};
            this.fileTypes.forEach(fileType => {
                data[fileType.key] = null;
            });
            return data;
        }
        
        const data = {};
        this.fileTypes.forEach(fileType => {
            data[fileType.key] = initialData[fileType.key] || null;
        });
        return data;
    }
    
    init() {
        this.container.innerHTML = '';
        this.container.classList.add('endpoint-files-editor');
        this.render();
        this.setupEventListeners();
    }
    
    render() {
        const html = `
            <div class="endpoint-files-editor-wrapper">
                <div class="mb-4">
                    <p class="text-sm text-gray-600 dark:text-gray-400">
                        At least one of <strong>Service File</strong> or <strong>Router File</strong> must be provided.
                    </p>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    ${this.fileTypes.map(fileType => this.renderFileInput(fileType)).join('')}
                </div>
            </div>
        `;
        
        this.container.innerHTML = html;
    }
    
    renderFileInput(fileType) {
        const value = this.data[fileType.key] || '';
        const isRequired = fileType.key === 'service_file' || fileType.key === 'router_file';
        
        return `
            <div class="file-input-wrapper">
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    ${fileType.label}
                    ${isRequired ? '<span class="text-red-500">*</span>' : ''}
                </label>
                <input 
                    type="text" 
                    class="file-input w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                    data-file-type="${fileType.key}"
                    value="${this.escapeHtml(value)}"
                    ${this.options.readOnly ? 'readonly' : ''}
                    ${isRequired ? 'required' : ''}
                    placeholder="${fileType.description}"
                />
                <small class="text-gray-500 dark:text-gray-400 text-xs mt-1 block">${fileType.description}</small>
            </div>
        `;
    }
    
    setupEventListeners() {
        if (this.options.readOnly) return;
        
        const fileInputs = this.container.querySelectorAll('.file-input');
        fileInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                const fileType = e.target.getAttribute('data-file-type');
                const value = e.target.value.trim() || null;
                this.data[fileType] = value;
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
        const event = new CustomEvent('endpoint-files-change', {
            detail: { data: this.data }
        });
        this.container.dispatchEvent(event);
    }
    
    getData() {
        // Return null if all fields are empty
        const hasAnyFile = Object.values(this.data).some(value => value !== null && value !== '');
        return hasAnyFile ? JSON.parse(JSON.stringify(this.data)) : null;
    }
    
    setData(data) {
        this.data = this.initializeData(data);
        this.render();
        this.setupEventListeners();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EndpointFilesEditor;
}
