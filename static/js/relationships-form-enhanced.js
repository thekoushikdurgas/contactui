/**
 * Enhanced Relationships Form Component
 * 
 * Manages the enhanced relationships form with:
 * - Tab navigation
 * - Dynamic field rendering
 * - Specialized editors for complex fields
 * - Real-time validation
 * - JSON preview modal
 */

class RelationshipsFormEnhanced {
    constructor(formId, options = {}) {
        this.form = typeof formId === 'string' ? document.getElementById(formId) : formId;
        this.options = {
            isEdit: options.isEdit || false,
            initialData: options.initialData || {},
            schemaServiceUrl: options.schemaServiceUrl || '/docs/api/schemas/',
            ...options
        };
        
        if (!this.form) {
            throw new Error('Form element not found');
        }
        
        this.formData = this.initializeFormData(this.options.initialData);
        this.validators = {};
        this.editors = {};
        this.skeletonLoader = null;
        this.errorHandler = null;
        
        this.init();
    }
    
    init() {
        this.setupErrorHandler();
        this.setupLoadingStates();
        this.setupKeyboardNavigation();
        
        this.setupTabs();
        this.setupBasicFields();
        this.setupConnectionEditor();
        this.setupDataFlowEditor();
        this.setupReferencesEditors();
        this.setupAdvancedEditors();
        this.setupJSONPreview();
        this.setupFormSubmission();
        this.setupValidation();
    }
    
    setupErrorHandler() {
        let errorContainer = document.getElementById('form-error-container');
        if (!errorContainer) {
            errorContainer = document.createElement('div');
            errorContainer.id = 'form-error-container';
            this.form.insertBefore(errorContainer, this.form.firstChild);
        }
        this.errorHandler = new ErrorHandler(errorContainer, {
            showRetry: true,
            autoHide: false
        });
    }
    
    setupLoadingStates() {
        const formContent = this.form.querySelector('.tab-content');
        if (formContent) {
            const skeletonContainer = document.createElement('div');
            skeletonContainer.id = 'form-skeleton-loader';
            skeletonContainer.className = 'hidden';
            formContent.parentNode.insertBefore(skeletonContainer, formContent);
            this.skeletonLoader = new SkeletonLoader(skeletonContainer, {
                type: 'form',
                count: 1
            });
        }
    }
    
    setupKeyboardNavigation() {
        const tabButtons = this.form.querySelectorAll('.tab-button');
        tabButtons.forEach((button, index) => {
            button.addEventListener('keydown', (e) => {
                if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
                    e.preventDefault();
                    const direction = e.key === 'ArrowRight' ? 1 : -1;
                    const nextIndex = (index + direction + tabButtons.length) % tabButtons.length;
                    tabButtons[nextIndex].focus();
                    tabButtons[nextIndex].click();
                }
            });
        });
    }
    
    showLoading() {
        if (this.skeletonLoader) {
            this.skeletonLoader.show();
        }
        const formContent = this.form.querySelectorAll('.tab-content');
        formContent.forEach(content => {
            content.style.opacity = '0.5';
            content.style.pointerEvents = 'none';
        });
    }
    
    hideLoading() {
        if (this.skeletonLoader) {
            this.skeletonLoader.hide();
        }
        const formContent = this.form.querySelectorAll('.tab-content');
        formContent.forEach(content => {
            content.style.opacity = '1';
            content.style.pointerEvents = 'auto';
        });
    }
    
    initializeFormData(initialData) {
        return {
            relationship_id: initialData.relationship_id || '',
            state: initialData.state || 'development',
            connection: initialData.connection || null,
            data_flow: initialData.data_flow || null,
            page_reference: initialData.page_reference || null,
            endpoint_reference: initialData.endpoint_reference || null,
            access_control: initialData.access_control || null,
            files: initialData.files || null,
            performance: initialData.performance || null,
            // Legacy fields
            page_path: initialData.page_path || '',
            endpoint_path: initialData.endpoint_path || '',
            method: initialData.method || '',
            api_version: initialData.api_version || ''
        };
    }
    
    setupTabs() {
        const tabButtons = this.form.querySelectorAll('.tab-button');
        const tabContents = this.form.querySelectorAll('.tab-content');
        
        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const targetTab = button.getAttribute('data-tab');
                
                tabButtons.forEach(btn => {
                    btn.classList.remove('active', 'border-blue-600', 'text-blue-600');
                    btn.classList.add('border-transparent', 'text-gray-500');
                });
                button.classList.add('active', 'border-blue-600', 'text-blue-600');
                button.classList.remove('border-transparent', 'text-gray-500');
                
                tabContents.forEach(content => {
                    content.classList.remove('active');
                    content.setAttribute('aria-hidden', 'true');
                });
                
                const targetContent = this.form.querySelector(`#tab-${targetTab}`);
                if (targetContent) {
                    targetContent.classList.add('active');
                    targetContent.setAttribute('aria-hidden', 'false');
                }
            });
        });
    }
    
    setupBasicFields() {
        const fields = ['relationship_id', 'state', 'page_path', 'endpoint_path'];
        fields.forEach(fieldName => {
            const field = this.form.querySelector(`#${fieldName}`);
            if (field) {
                field.addEventListener('change', (e) => {
                    this.formData[fieldName] = e.target.value;
                    this.updateFormData();
                });
            }
        });
    }
    
    setupConnectionEditor() {
        const container = this.form.querySelector('#connection-editor');
        if (!container) return;
        
        const connectionData = this.formData.connection || null;
        
        this.editors.connection = new RelationshipConnectionEditor(container, {
            data: connectionData,
            readOnly: false
        });
        
        container.addEventListener('relationship-connection-change', (e) => {
            this.formData.connection = e.detail.data;
            this.updateFormData();
        });
    }
    
    setupDataFlowEditor() {
        const container = this.form.querySelector('#data-flow-editor');
        if (!container) return;
        
        const dataFlowData = this.formData.data_flow || null;
        
        this.editors.dataFlow = new RelationshipDataFlowEditor(container, {
            data: dataFlowData,
            readOnly: false
        });
        
        container.addEventListener('relationship-data-flow-change', (e) => {
            this.formData.data_flow = e.detail.data;
            this.updateFormData();
        });
    }
    
    setupReferencesEditors() {
        // Page reference
        const pageRefContainer = this.form.querySelector('#page-reference-editor');
        if (pageRefContainer) {
            this.editors.pageReference = new JSONTreeEditor(pageRefContainer, {
                data: this.formData.page_reference || {},
                readOnly: false,
                showRoot: false
            });
            
            pageRefContainer.addEventListener('json-tree-change', (e) => {
                this.formData.page_reference = e.detail.data;
                this.updateFormData();
            });
        }
        
        // Endpoint reference
        const endpointRefContainer = this.form.querySelector('#endpoint-reference-editor');
        if (endpointRefContainer) {
            this.editors.endpointReference = new JSONTreeEditor(endpointRefContainer, {
                data: this.formData.endpoint_reference || {},
                readOnly: false,
                showRoot: false
            });
            
            endpointRefContainer.addEventListener('json-tree-change', (e) => {
                this.formData.endpoint_reference = e.detail.data;
                this.updateFormData();
            });
        }
    }
    
    setupAdvancedEditors() {
        // Access control
        const accessControlContainer = this.form.querySelector('#access-control-editor');
        if (accessControlContainer) {
            this.editors.accessControl = new JSONTreeEditor(accessControlContainer, {
                data: this.formData.access_control || {},
                readOnly: false,
                showRoot: false
            });
            
            accessControlContainer.addEventListener('json-tree-change', (e) => {
                this.formData.access_control = e.detail.data;
                this.updateFormData();
            });
        }
        
        // Files
        const filesContainer = this.form.querySelector('#files-editor');
        if (filesContainer) {
            this.editors.files = new JSONTreeEditor(filesContainer, {
                data: this.formData.files || {},
                readOnly: false,
                showRoot: false
            });
            
            filesContainer.addEventListener('json-tree-change', (e) => {
                this.formData.files = e.detail.data;
                this.updateFormData();
            });
        }
        
        // Performance
        const performanceContainer = this.form.querySelector('#performance-editor');
        if (performanceContainer) {
            this.editors.performance = new JSONTreeEditor(performanceContainer, {
                data: this.formData.performance || {},
                readOnly: false,
                showRoot: false
            });
            
            performanceContainer.addEventListener('json-tree-change', (e) => {
                this.formData.performance = e.detail.data;
                this.updateFormData();
            });
        }
    }
    
    setupJSONPreview() {
        const previewBtn = document.getElementById('preview-json-btn');
        const previewModal = document.getElementById('json-preview-modal');
        const previewContent = document.getElementById('json-preview-content');
        const closePreview = document.getElementById('close-preview');
        
        if (!previewBtn || !previewModal || !previewContent) return;
        
        let highlighter = null;
        
        previewBtn.addEventListener('click', () => {
            const jsonData = this.getFormDataForSubmission();
            
            previewContent.innerHTML = '';
            
            if (!highlighter) {
                highlighter = new JSONSyntaxHighlighter(previewContent, {
                    json: jsonData,
                    showLineNumbers: true,
                    showCopyButton: true
                });
            } else {
                highlighter.setJSON(jsonData);
            }
            
            previewModal.classList.remove('hidden');
        });
        
        closePreview.addEventListener('click', () => {
            previewModal.classList.add('hidden');
        });
        
        previewModal.addEventListener('click', (e) => {
            if (e.target === previewModal) {
                previewModal.classList.add('hidden');
            }
        });
    }
    
    setupFormSubmission() {
        this.form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            this.showLoading();
            
            const isValid = await this.validateForm();
            if (!isValid) {
                this.hideLoading();
                if (this.errorHandler) {
                    this.errorHandler.showError('Please fix validation errors before submitting.');
                } else {
                    this.showError('Please fix validation errors before submitting.');
                }
                return;
            }
            
            const submissionData = this.getFormDataForSubmission();
            this.prepareFormForSubmission(submissionData);
            this.form.submit();
        });
    }
    
    prepareFormForSubmission(data) {
        const existingInput = this.form.querySelector('input[name="relationship_data"]');
        if (existingInput) {
            existingInput.remove();
        }
        
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = 'relationship_data';
        hiddenInput.value = JSON.stringify(data);
        this.form.appendChild(hiddenInput);
    }
    
    getFormDataForSubmission() {
        const data = {
            relationship_id: this.formData.relationship_id,
            state: this.formData.state || 'development',
            connection: this.formData.connection || null,
            data_flow: this.formData.data_flow || null,
            page_reference: this.formData.page_reference || null,
            endpoint_reference: this.formData.endpoint_reference || null,
            access_control: this.formData.access_control || null,
            files: this.formData.files || null,
            performance: this.formData.performance || null
        };
        
        // Legacy fields
        if (this.formData.page_path) {
            data.page_path = this.formData.page_path;
        }
        if (this.formData.endpoint_path) {
            data.endpoint_path = this.formData.endpoint_path;
        }
        if (this.formData.method) {
            data.method = this.formData.method;
        }
        if (this.formData.api_version) {
            data.api_version = this.formData.api_version;
        }
        
        if (this.options.isEdit && this.options.initialData._id) {
            data._id = this.options.initialData._id;
        }
        
        return data;
    }
    
    setupValidation() {
        this.validators.relationship = new JSONSchemaValidator({
            schemaServiceUrl: this.options.schemaServiceUrl,
            resourceType: 'relationships'
        });
        
        this.validators.relationship.loadSchema('relationships').then(() => {
            this.setupRealtimeValidation();
        }).catch(err => {
            console.warn('Failed to load schema for validation:', err);
        });
    }
    
    setupRealtimeValidation() {
        const validate = () => {
            const formData = this.getFormDataForSubmission();
            const result = this.validators.relationship.validate(formData);
            this.displayValidationErrors(result.errors, result.warnings);
        };
        
        let validationTimeout;
        const debouncedValidate = () => {
            clearTimeout(validationTimeout);
            validationTimeout = setTimeout(validate, 500);
        };
        
        this.form.addEventListener('input', debouncedValidate);
        this.form.addEventListener('change', debouncedValidate);
        
        Object.values(this.editors).forEach(editor => {
            if (editor && editor.container) {
                // JSON tree editor
                editor.container.addEventListener('json-tree-change', debouncedValidate);
                // Connection editor
                editor.container.addEventListener('relationship-connection-change', debouncedValidate);
                // Data flow editor
                editor.container.addEventListener('relationship-data-flow-change', debouncedValidate);
            }
        });
    }
    
    displayValidationErrors(errors, warnings) {
        this.form.querySelectorAll('.validation-error').forEach(el => el.remove());
        this.form.querySelectorAll('.validation-warning').forEach(el => el.remove());
        
        if (errors && errors.length > 0) {
            const errorContainer = document.createElement('div');
            errorContainer.className = 'validation-error-container bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-4';
            errorContainer.innerHTML = `
                <h4 class="text-red-800 dark:text-red-200 font-semibold mb-2">Validation Errors</h4>
                <ul class="list-disc list-inside text-red-700 dark:text-red-300">
                    ${errors.map(err => `<li>${err}</li>`).join('')}
                </ul>
            `;
            this.form.insertBefore(errorContainer, this.form.firstChild);
        }
    }
    
    async validateForm() {
        if (!this.validators.relationship) {
            return true;
        }
        
        const formData = this.getFormDataForSubmission();
        const result = this.validators.relationship.validate(formData);
        
        this.displayValidationErrors(result.errors, result.warnings);
        
        return result.errors.length === 0;
    }
    
    updateFormData() {
        const event = new CustomEvent('relationships-form-data-change', {
            detail: { formData: this.formData }
        });
        this.form.dispatchEvent(event);
    }
    
    getFormData() {
        return this.formData;
    }
    
    setFormData(data) {
        this.formData = this.initializeFormData(data);
        Object.keys(this.editors).forEach(key => {
            if (this.editors[key] && this.formData[key]) {
                this.editors[key].setData(this.formData[key]);
            }
        });
    }
    
    showError(message) {
        alert(message);
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RelationshipsFormEnhanced;
}
