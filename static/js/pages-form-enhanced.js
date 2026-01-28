/**
 * Enhanced Pages Form Component
 * 
 * Manages the enhanced pages form with:
 * - Tab navigation
 * - Dynamic field rendering
 * - JSON tree editors for complex fields
 * - Real-time validation
 * - Markdown preview
 * - JSON preview modal
 * - Form data management
 */

class PagesFormEnhanced {
    constructor(formId, options = {}) {
        this.form = typeof formId === 'string' ? document.getElementById(formId) : formId;
        this.options = {
            isEdit: options.isEdit || false,
            initialData: options.initialData || {},
            schemaServiceUrl: options.schemaServiceUrl || '/docs/api/schemas/',
            autoSave: options.autoSave !== false,
            autoSaveInterval: options.autoSaveInterval || 30000, // 30 seconds
            ...options
        };
        
        if (!this.form) {
            throw new Error('Form element not found');
        }
        
        // Initialize form data
        this.formData = this.initializeFormData(this.options.initialData);
        
        // Component instances
        this.validators = {};
        this.editors = {};
        this.autoSaveTimer = null;
        
        this.init();
    }
    
    init() {
        this.setupErrorHandler();
        this.setupLoadingStates();
        this.setupKeyboardNavigation();
        
        if (!this.options.isEdit) {
            this.setupTemplateSelector();
        }
        this.setupTabs();
        this.setupBasicFields();
        this.setupContentEditor();
        this.setupMetadataEditor();
        this.setupEndpointsEditor();
        this.setupComponentsEditor();
        this.setupAccessControlEditor();
        this.setupSectionsEditor();
        this.setupAdvancedEditors();
        this.setupJSONPreview();
        this.setupFormSubmission();
        this.setupValidation();
        
        if (this.options.autoSave) {
            this.setupAutoSave();
        }
    }
    
    setupErrorHandler() {
        // Create error handler container if it doesn't exist
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
        // Show skeleton loader while form is initializing
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
        // Tab navigation with keyboard
        const tabButtons = this.form.querySelectorAll('.tab-button');
        tabButtons.forEach((button, index) => {
            button.addEventListener('keydown', (e) => {
                if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
                    e.preventDefault();
                    const direction = e.key === 'ArrowRight' ? 1 : -1;
                    const nextIndex = (index + direction + tabButtons.length) % tabButtons.length;
                    tabButtons[nextIndex].focus();
                    tabButtons[nextIndex].click();
                } else if (e.key === 'Home') {
                    e.preventDefault();
                    tabButtons[0].focus();
                    tabButtons[0].click();
                } else if (e.key === 'End') {
                    e.preventDefault();
                    tabButtons[tabButtons.length - 1].focus();
                    tabButtons[tabButtons.length - 1].click();
                }
            });
        });
        
        // Form field navigation
        const formFields = this.form.querySelectorAll('input, select, textarea, button');
        formFields.forEach((field, index) => {
            field.addEventListener('keydown', (e) => {
                if (e.key === 'Tab' && !e.shiftKey && index === formFields.length - 1) {
                    // Last field, wrap to first
                    e.preventDefault();
                    formFields[0].focus();
                }
            });
        });
        
        // Escape key to close modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const modals = document.querySelectorAll('.modal:not(.hidden)');
                modals.forEach(modal => {
                    modal.classList.add('hidden');
                });
            }
        });
    }
    
    setupTemplateSelector() {
        const container = document.getElementById('template-selector-container');
        if (!container) return;
        
        this.templateSelector = new TemplateSelector(container, {
            resourceType: 'pages',
            onTemplateSelect: (templateData) => {
                this.applyTemplate(templateData);
            }
        });
        
        container.addEventListener('template-applied', (e) => {
            this.applyTemplate(e.detail.templateData);
        });
    }
    
    applyTemplate(templateData) {
        // Merge template data into form data
        Object.keys(templateData).forEach(key => {
            if (key === 'metadata' && templateData[key]) {
                // Deep merge metadata
                this.formData.metadata = { ...this.formData.metadata, ...templateData[key] };
            } else if (Array.isArray(templateData[key])) {
                // For arrays, replace if empty, otherwise merge
                if (!this.formData[key] || this.formData[key].length === 0) {
                    this.formData[key] = [...templateData[key]];
                }
            } else if (typeof templateData[key] === 'object' && templateData[key] !== null) {
                // Deep merge objects
                this.formData[key] = { ...this.formData[key], ...templateData[key] };
            } else {
                // Simple assignment for primitives
                if (!this.formData[key]) {
                    this.formData[key] = templateData[key];
                }
            }
        });
        
        // Update form fields
        this.setFormData(this.formData);
        
        // Show success message
        this.showSuccess('Template applied successfully!');
    }
    
    showSuccess(message) {
        // Simple success notification
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg z-50';
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
    
    initializeFormData(initialData) {
        // Transform initial data to form-friendly structure
        const data = {
            page_id: initialData.page_id || '',
            page_type: initialData.page_type || 'docs',
            content: initialData.content || '',
            metadata: initialData.metadata || {
                route: '',
                file_path: '',
                purpose: '',
                s3_key: '',
                status: 'published',
                authentication: 'Not required',
                authorization: null,
                page_state: 'development',
                last_updated: new Date().toISOString(),
                uses_endpoints: [],
                ui_components: [],
                versions: [],
                endpoint_count: 0,
                api_versions: []
            },
            uses_endpoints: initialData.metadata?.uses_endpoints || [],
            ui_components: initialData.metadata?.ui_components || [],
            access_control: initialData.access_control || null,
            sections: initialData.sections || {
                headings: [],
                subheadings: [],
                tabs: [],
                buttons: [],
                input_boxes: [],
                text_blocks: [],
                components: [],
                utilities: [],
                services: [],
                hooks: [],
                contexts: [],
                ui_components: [],
                endpoints: []
            },
            fallback_data: initialData.fallback_data || [],
            mock_data: initialData.mock_data || [],
            demo_data: initialData.demo_data || []
        };
        
        return data;
    }
    
    setupTabs() {
        // Tab buttons are outside the form element, so search from parent or document
        const formContainer = this.form.closest('.bg-white, .bg-gray-800') || this.form.parentElement || document;
        const tabButtons = formContainer.querySelectorAll('.tab-button');
        const tabContents = this.form.querySelectorAll('.tab-content');
        
        tabButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const targetTab = button.getAttribute('data-tab');
                
                // Update button states
                tabButtons.forEach(btn => {
                    btn.classList.remove('active');
                    btn.classList.remove('border-blue-600', 'text-blue-600');
                    btn.classList.add('border-transparent', 'text-gray-500');
                });
                button.classList.add('active');
                button.classList.add('border-blue-600', 'text-blue-600');
                button.classList.remove('border-transparent', 'text-gray-500');
                
                // Update content visibility
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
        const pageIdInput = this.form.querySelector('#page_id');
        const pageTypeSelect = this.form.querySelector('#page_type');
        
        if (pageIdInput) {
            pageIdInput.addEventListener('change', (e) => {
                this.formData.page_id = e.target.value;
                this.updateFormData();
            });
        }
        
        if (pageTypeSelect) {
            pageTypeSelect.addEventListener('change', (e) => {
                this.formData.page_type = e.target.value;
                this.updateFormData();
            });
        }
    }
    
    setupContentEditor() {
        const contentTextarea = this.form.querySelector('#content');
        const previewDiv = this.form.querySelector('#content-preview');
        
        if (!contentTextarea || !previewDiv) return;
        
        // Update form data on change
        contentTextarea.addEventListener('input', (e) => {
            this.formData.content = e.target.value;
            this.updateFormData();
            this.updateMarkdownPreview(e.target.value, previewDiv);
        });
        
        // Initial preview
        this.updateMarkdownPreview(this.formData.content, previewDiv);
    }
    
    updateMarkdownPreview(markdown, previewDiv) {
        if (!markdown) {
            previewDiv.innerHTML = '<p class="text-gray-500 dark:text-gray-400">Preview will appear here...</p>';
            return;
        }
        
        // Simple markdown rendering (can be enhanced with a markdown library)
        let html = markdown
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^\*\*(.*)\*\*/gim, '<strong>$1</strong>')
            .replace(/^\*(.*)\*/gim, '<em>$1</em>')
            .replace(/^\n/gim, '<br>');
        
        previewDiv.innerHTML = html || '<p class="text-gray-500 dark:text-gray-400">Preview will appear here...</p>';
    }
    
    setupMetadataEditor() {
        const container = this.form.querySelector('#metadata-editor');
        if (!container) return;
        
        // Initialize specialized metadata editor
        const metadataData = this.formData.metadata || {};
        
        this.editors.metadata = new MetadataEditor(container, {
            data: metadataData,
            readOnly: false,
            pageId: this.formData.page_id
        });
        
        // Listen for changes
        container.addEventListener('metadata-change', (e) => {
            this.formData.metadata = e.detail.data;
            this.updateFormData();
        });
    }
    
    setupEndpointsEditor() {
        const container = this.form.querySelector('#uses-endpoints-editor');
        if (!container) return;
        
        // Initialize specialized endpoints usage editor
        const endpointsData = this.formData.uses_endpoints || [];
        
        this.editors.endpoints = new EndpointsUsageEditor(container, {
            data: endpointsData,
            readOnly: false
        });
        
        // Listen for changes
        container.addEventListener('endpoints-usage-change', (e) => {
            this.formData.uses_endpoints = e.detail.data;
            // Update metadata.uses_endpoints as well
            if (!this.formData.metadata) {
                this.formData.metadata = {};
            }
            this.formData.metadata.uses_endpoints = e.detail.data;
            // Update metadata editor's computed fields
            if (this.editors.metadata) {
                this.editors.metadata.setUsesEndpoints(e.detail.data);
            }
            this.updateFormData();
        });
    }
    
    setupComponentsEditor() {
        const container = this.form.querySelector('#ui-components-editor');
        if (!container) return;
        
        // Initialize JSON tree editor for ui_components array
        const componentsData = this.formData.ui_components || [];
        
        this.editors.components = new JSONTreeEditor(container, {
            data: componentsData,
            readOnly: false,
            showRoot: false,
            searchEnabled: true
        });
        
        // Listen for changes
        container.addEventListener('json-tree-change', (e) => {
            this.formData.ui_components = e.detail.data;
            // Update metadata.ui_components as well
            if (!this.formData.metadata) {
                this.formData.metadata = {};
            }
            this.formData.metadata.ui_components = e.detail.data;
            this.updateFormData();
        });
    }
    
    setupAccessControlEditor() {
        const container = this.form.querySelector('#access-control-editor');
        if (!container) return;
        
        // Initialize specialized access control editor
        const accessControlData = this.formData.access_control || null;
        
        this.editors.accessControl = new AccessControlEditor(container, {
            data: accessControlData,
            readOnly: false
        });
        
        // Listen for changes
        container.addEventListener('access-control-change', (e) => {
            this.formData.access_control = e.detail.data;
            this.updateFormData();
        });
    }
    
    setupSectionsEditor() {
        const container = this.form.querySelector('#sections-editor');
        if (!container) return;
        
        // Initialize specialized sections editor
        const sectionsData = this.formData.sections || {};
        
        this.editors.sections = new SectionsEditor(container, {
            data: sectionsData,
            readOnly: false
        });
        
        // Listen for changes
        container.addEventListener('sections-change', (e) => {
            this.formData.sections = e.detail.data;
            this.updateFormData();
        });
    }
    
    setupAdvancedEditors() {
        // Fallback data editor
        const fallbackContainer = this.form.querySelector('#fallback-data-editor');
        if (fallbackContainer) {
            this.editors.fallbackData = new JSONTreeEditor(fallbackContainer, {
                data: this.formData.fallback_data || [],
                readOnly: false,
                showRoot: false,
                searchEnabled: true
            });
            
            fallbackContainer.addEventListener('json-tree-change', (e) => {
                this.formData.fallback_data = e.detail.data;
                this.updateFormData();
            });
        }
        
        // Mock data editor
        const mockContainer = this.form.querySelector('#mock-data-editor');
        if (mockContainer) {
            this.editors.mockData = new JSONTreeEditor(mockContainer, {
                data: this.formData.mock_data || [],
                readOnly: false,
                showRoot: false,
                searchEnabled: true
            });
            
            mockContainer.addEventListener('json-tree-change', (e) => {
                this.formData.mock_data = e.detail.data;
                this.updateFormData();
            });
        }
        
        // Demo data editor
        const demoContainer = this.form.querySelector('#demo-data-editor');
        if (demoContainer) {
            this.editors.demoData = new JSONTreeEditor(demoContainer, {
                data: this.formData.demo_data || [],
                readOnly: false,
                showRoot: false,
                searchEnabled: true
            });
            
            demoContainer.addEventListener('json-tree-change', (e) => {
                this.formData.demo_data = e.detail.data;
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
            
            // Clear previous content
            previewContent.innerHTML = '';
            
            // Initialize or update syntax highlighter
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
        
        // Close on outside click
        previewModal.addEventListener('click', (e) => {
            if (e.target === previewModal) {
                previewModal.classList.add('hidden');
            }
        });
        
        // Close on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !previewModal.classList.contains('hidden')) {
                previewModal.classList.add('hidden');
            }
        });
    }
    
    setupFormSubmission() {
        this.form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            // Show loading state
            this.showLoading();
            
            // Validate form
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
            
            // Get form data
            const submissionData = this.getFormDataForSubmission();
            
            // Show loading state
            const submitBtn = this.form.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.disabled = true;
            submitBtn.textContent = 'Saving...';
            
            try {
                // Submit form (Django will handle the POST)
                const formData = new FormData();
                formData.append('page_data', JSON.stringify(submissionData));
                
                this.prepareFormForSubmission(submissionData);
                
                // Submit the form
                this.form.submit();
            } catch (error) {
                console.error('Form submission error:', error);
                this.hideLoading();
                if (this.errorHandler) {
                    this.errorHandler.showError('Failed to submit form. Please try again.', {
                        retry: () => {
                            this.form.dispatchEvent(new Event('submit', { cancelable: true }));
                        }
                    });
                } else {
                    this.showError('Failed to submit form. Please try again.');
                }
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
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
    
    prepareFormForSubmission(data) {
        // Remove any existing hidden page_data input
        const existingInput = this.form.querySelector('input[name="page_data"]');
        if (existingInput) {
            existingInput.remove();
        }
        
        // Create hidden input with JSON data
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = 'page_data';
        hiddenInput.value = JSON.stringify(data);
        this.form.appendChild(hiddenInput);
    }
    
    getFormDataForSubmission() {
        // Transform form data to Lambda API format
        const data = {
            page_id: this.formData.page_id,
            page_type: this.formData.page_type,
            content: this.formData.content || null,
            metadata: {
                ...this.formData.metadata,
                uses_endpoints: this.formData.uses_endpoints || [],
                ui_components: this.formData.ui_components || []
            },
            access_control: this.formData.access_control || null,
            sections: this.formData.sections || null,
            fallback_data: this.formData.fallback_data || [],
            mock_data: this.formData.mock_data || [],
            demo_data: this.formData.demo_data || []
        };
        
        // Add _id if editing
        if (this.options.isEdit && this.options.initialData._id) {
            data._id = this.options.initialData._id;
        }
        
        // Ensure metadata has required fields
        if (!data.metadata.route) {
            data.metadata.route = `/${this.formData.page_id}`;
        }
        if (!data.metadata.file_path) {
            data.metadata.file_path = `pages/${this.formData.page_id}.tsx`;
        }
        if (!data.metadata.purpose) {
            data.metadata.purpose = `Documentation page for ${this.formData.page_id}`;
        }
        if (!data.metadata.s3_key) {
            data.metadata.s3_key = `data/pages/${this.formData.page_id}.json`;
        }
        if (!data.metadata.last_updated) {
            data.metadata.last_updated = new Date().toISOString();
        }
        
        return data;
    }
    
    setupValidation() {
        // Initialize schema validator
        this.validators.page = new JSONSchemaValidator({
            schemaServiceUrl: this.options.schemaServiceUrl,
            resourceType: 'pages'
        });
        
        // Load schema
        this.validators.page.loadSchema('pages').then(() => {
            // Set up real-time validation
            this.setupRealtimeValidation();
        }).catch(err => {
            console.warn('Failed to load schema for validation:', err);
        });
    }
    
    setupRealtimeValidation() {
        // Validate on form data changes
        const validate = () => {
            const formData = this.getFormDataForSubmission();
            const result = this.validators.page.validate(formData);
            
            // Display validation errors
            this.displayValidationErrors(result.errors, result.warnings);
        };
        
        // Debounce validation
        let validationTimeout;
        const debouncedValidate = () => {
            clearTimeout(validationTimeout);
            validationTimeout = setTimeout(validate, 500);
        };
        
        // Listen to all form changes
        this.form.addEventListener('input', debouncedValidate);
        this.form.addEventListener('change', debouncedValidate);
        
        // Listen to editor changes
        Object.values(this.editors).forEach(editor => {
            if (editor && editor.container) {
                // JSON tree editor
                editor.container.addEventListener('json-tree-change', debouncedValidate);
                // Metadata editor
                editor.container.addEventListener('metadata-change', debouncedValidate);
                // Endpoints usage editor
                editor.container.addEventListener('endpoints-usage-change', debouncedValidate);
                // Access control editor
                editor.container.addEventListener('access-control-change', debouncedValidate);
                // Sections editor
                editor.container.addEventListener('sections-change', debouncedValidate);
            }
        });
    }
    
    displayValidationErrors(errors, warnings) {
        // Remove existing error messages
        this.form.querySelectorAll('.validation-error').forEach(el => el.remove());
        this.form.querySelectorAll('.validation-warning').forEach(el => el.remove());
        
        // Display errors
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
        
        // Display warnings
        if (warnings && warnings.length > 0) {
            const warningContainer = document.createElement('div');
            warningContainer.className = 'validation-warning-container bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 mb-4';
            warningContainer.innerHTML = `
                <h4 class="text-yellow-800 dark:text-yellow-200 font-semibold mb-2">Validation Warnings</h4>
                <ul class="list-disc list-inside text-yellow-700 dark:text-yellow-300">
                    ${warnings.map(warn => `<li>${warn}</li>`).join('')}
                </ul>
            `;
            this.form.insertBefore(warningContainer, this.form.firstChild);
        }
    }
    
    async validateForm() {
        if (!this.validators.page) {
            return true; // Skip validation if validator not loaded
        }
        
        const formData = this.getFormDataForSubmission();
        const result = this.validators.page.validate(formData);
        
        this.displayValidationErrors(result.errors, result.warnings);
        
        return result.errors.length === 0;
    }
    
    setupAutoSave() {
        // Auto-save every 30 seconds
        this.autoSaveTimer = setInterval(() => {
            this.saveDraft();
        }, this.options.autoSaveInterval);
        
        // Save draft before page unload
        window.addEventListener('beforeunload', () => {
            this.saveDraft();
        });
    }
    
    async saveDraft() {
        try {
            const formData = this.getFormDataForSubmission();
            const response = await fetch('/docs/api/pages/draft/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(formData)
            });
            
            if (response.ok) {
                console.log('Draft saved successfully');
            }
        } catch (error) {
            console.warn('Failed to save draft:', error);
        }
    }
    
    getCSRFToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return '';
    }
    
    updateFormData() {
        // Trigger custom event for external listeners
        const event = new CustomEvent('pages-form-data-change', {
            detail: { formData: this.formData }
        });
        this.form.dispatchEvent(event);
    }
    
    getFormData() {
        return this.formData;
    }
    
    setFormData(data) {
        this.formData = this.initializeFormData(data);
        // Update all editors
        Object.keys(this.editors).forEach(key => {
            if (this.editors[key]) {
                if (key === 'metadata' && this.formData.metadata) {
                    this.editors[key].setData(this.formData.metadata);
                } else if (this.formData[key]) {
                    this.editors[key].setData(this.formData[key]);
                }
            }
        });
        
        // Update metadata editor's uses_endpoints when endpoints change
        if (this.editors.metadata && this.editors.endpoints) {
            this.editors.metadata.setUsesEndpoints(this.formData.uses_endpoints);
        }
    }
    
    showError(message) {
        // Simple error display (can be enhanced)
        alert(message);
    }
    
    destroy() {
        // Cleanup
        if (this.autoSaveTimer) {
            clearInterval(this.autoSaveTimer);
        }
        
        // Remove event listeners
        Object.values(this.editors).forEach(editor => {
            if (editor && editor.destroy) {
                editor.destroy();
            }
        });
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PagesFormEnhanced;
}
