/**
 * Enhanced Endpoints Form Component
 * 
 * Manages the enhanced endpoints form with:
 * - Tab navigation
 * - Dynamic field rendering
 * - JSON tree editors for complex fields
 * - Real-time validation
 * - JSON preview modal
 * - Form data management
 */

class EndpointsFormEnhanced {
    constructor(formId, options = {}) {
        this.form = typeof formId === 'string' ? document.getElementById(formId) : formId;
        this.options = {
            isEdit: options.isEdit || false,
            initialData: options.initialData || {},
            schemaServiceUrl: options.schemaServiceUrl || '/docs/api/schemas/',
            autoSave: options.autoSave !== false,
            autoSaveInterval: options.autoSaveInterval || 30000,
            ...options
        };
        
        if (!this.form) {
            throw new Error('Form element not found: ' + formId);
        }
        
        // Initialize form data
        this.formData = this.initializeFormData(this.options.initialData);
        
        // Component instances
        this.validators = {};
        this.editors = {};
        this.autoSaveTimer = null;
        this.skeletonLoader = null;
        this.errorHandler = null;
        
        this.init();
    }
    
    init() {
        try {
            this.setupTabs();
        } catch (error) {
            console.error('[EndpointsFormEnhanced] Error in setupTabs():', error);
        }
        
        try {
            this.setupBasicFields();
            this.setupLambdaServicesEditor();
            this.setupFilesEditor();
            this.setupMethodsEditor();
            this.setupUsedByPagesEditor();
            this.setupAccessControlEditor();
            this.setupAdvancedFields();
            this.setupJSONPreview();
            this.setupFormSubmission();
        } catch (error) {
            console.error('[EndpointsFormEnhanced] Error in setup methods:', error);
        }
        
        try {
            this.setupValidation();
        } catch (error) {
            console.error('[EndpointsFormEnhanced] Error in setupValidation (non-critical):', error);
        }
        
        if (this.options.autoSave) {
            try {
                this.setupAutoSave();
            } catch (error) {
                console.error('[EndpointsFormEnhanced] Error in setupAutoSave:', error);
            }
        }
    }
    
    initializeFormData(initialData) {
        // Transform initial data to form-friendly structure
        const data = {
            endpoint_id: initialData.endpoint_id || '',
            endpoint_path: initialData.endpoint_path || '',
            method: initialData.method || '',
            api_version: initialData.api_version || '',
            description: initialData.description || '',
            endpoint_state: initialData.endpoint_state || 'development',
            created_at: initialData.created_at || new Date().toISOString(),
            updated_at: initialData.updated_at || new Date().toISOString(),
            lambda_services: initialData.lambda_services || null,
            files: initialData.files || null,
            methods: initialData.methods || null,
            used_by_pages: initialData.used_by_pages || [],
            access_control: initialData.access_control || null,
            rate_limit: initialData.rate_limit || null,
            graphql_operation: initialData.graphql_operation || null,
            sql_file: initialData.sql_file || null,
            // Legacy fields
            service_file: initialData.service_file || null,
            router_file: initialData.router_file || null,
            service_methods: initialData.service_methods || [],
            repository_methods: initialData.repository_methods || []
        };
        
        return data;
    }
    
    setupTabs() {
        // Tab buttons are OUTSIDE the form element, so search from document
        // Find the form's parent container or search from document
        const formContainer = this.form.closest('.p-6') || this.form.parentElement || document;
        let tabButtonsNodeList = formContainer.querySelectorAll('.tab-button[data-tab]');
        const tabContentsNodeList = this.form.querySelectorAll('.tab-content');
        
        // Convert NodeLists to arrays to avoid closure issues
        let tabButtons = Array.from(tabButtonsNodeList);
        const tabContents = Array.from(tabContentsNodeList);
        
        // Fallback: search from document if not found in container
        if (tabButtons.length === 0) {
            tabButtons = Array.from(document.querySelectorAll('.tab-button[data-tab]'));
        }
        
        // CRITICAL: Ensure all tab button text spans are visible from the start
        tabButtons.forEach(button => {
            const spanElement = button.querySelector('span');
            if (spanElement) {
                // Force visibility of tab text for ALL tabs (active and inactive)
                spanElement.style.setProperty('display', 'inline-block', 'important');
                spanElement.style.setProperty('visibility', 'visible', 'important');
                spanElement.style.setProperty('opacity', '1', 'important');
                spanElement.style.setProperty('width', 'auto', 'important');
                spanElement.style.setProperty('max-width', 'none', 'important');
                spanElement.style.setProperty('min-width', 'fit-content', 'important');
                // CRITICAL: Remove any transform that might hide the text (prevents scaleX(0) issue)
                spanElement.style.setProperty('transform', 'none', 'important');
            }
        });
        
        if (tabButtons.length === 0) {
            console.error('[EndpointsFormEnhanced] No tab buttons found');
            return;
        }
        
        if (tabContents.length === 0) {
            console.error('[EndpointsFormEnhanced] No tab contents found');
            return;
        }
        
        const switchToTab = (tabId) => {
            // Re-query buttons from DOM to ensure we're working with current buttons
            // This fixes the issue where cloned buttons weren't being updated
            const currentTabButtons = Array.from(document.querySelectorAll('.tab-button[data-tab]'));
            
            // Update button states - FIRST remove active from ALL, then add to target
            // This prevents multiple tabs from being active simultaneously
            // CRITICAL: Remove active from ALL buttons first in a separate loop to ensure clean state
            const buttonsWithActive = [];
            currentTabButtons.forEach(btn => {
                const hadActive = btn.classList.contains('active');
                if (hadActive) {
                    buttonsWithActive.push(btn.getAttribute('data-tab'));
                }
                // Force remove all active-related classes and attributes
                btn.classList.remove('active');
                btn.setAttribute('aria-selected', 'false');
                btn.classList.remove('text-purple-600', 'dark:text-purple-400', 'border-purple-600', 'dark:border-purple-400');
                btn.classList.add('text-gray-600', 'dark:text-gray-400', 'border-transparent');
                
                // Reset underline indicator - DO NOT manipulate text span transform
                // The underline is handled via border-bottom CSS, not a separate span
            });
            
            // Now add active state ONLY to the target tab
            currentTabButtons.forEach(btn => {
                const btnTabId = btn.getAttribute('data-tab');
                const isActive = btnTabId === tabId;
                const spanElement = btn.querySelector('span');
                
                if (isActive) {
                    btn.classList.add('active');
                    btn.setAttribute('aria-selected', 'true');
                    btn.classList.remove('text-gray-600', 'dark:text-gray-400', 'border-transparent');
                    btn.classList.add('text-purple-600', 'dark:text-purple-400', 'border-purple-600', 'dark:border-purple-400');
                    
                    // Underline is handled via border-bottom CSS, not a separate span transform
                    // DO NOT manipulate text span transform as it hides the text
                    
                    // Ensure span text is visible for active tab
                    if (spanElement) {
                        spanElement.style.setProperty('display', 'inline-block', 'important');
                        spanElement.style.setProperty('visibility', 'visible', 'important');
                        spanElement.style.setProperty('opacity', '1', 'important');
                        // CRITICAL: Remove any transform that might hide the text
                        spanElement.style.setProperty('transform', 'none', 'important');
                    }
                } else {
                    // Ensure span text is visible for inactive tabs too
                    if (spanElement) {
                        spanElement.style.setProperty('display', 'inline-block', 'important');
                        spanElement.style.setProperty('visibility', 'visible', 'important');
                        spanElement.style.setProperty('opacity', '1', 'important');
                        // CRITICAL: Remove any transform that might hide the text
                        spanElement.style.setProperty('transform', 'none', 'important');
                    }
                }
            });
            
            // Update content visibility - FIRST remove active from ALL, then add to target
            // CRITICAL: Remove active class and hide ALL tab contents first
            tabContents.forEach(content => {
                // Force remove active class and hide
                content.classList.remove('active');
                content.style.setProperty('display', 'none', 'important');
                content.style.setProperty('visibility', 'hidden', 'important');
                content.style.setProperty('opacity', '0', 'important');
                content.setAttribute('aria-hidden', 'true');
            });
            
            // Now show ONLY the target tab content
            tabContents.forEach(content => {
                const contentId = content.id;
                const contentTabId = contentId.replace('tab-', '');
                const isActive = contentTabId === tabId;
                
                if (isActive) {
                    content.classList.add('active');
                    // Use setProperty with important to override inline styles
                    content.style.setProperty('display', 'block', 'important');
                    content.style.setProperty('visibility', 'visible', 'important');
                    content.style.setProperty('opacity', '1', 'important');
                    content.setAttribute('aria-hidden', 'false');
                    
                    // Ensure editors are initialized/rendered when tab becomes active
                    this.ensureEditorRendered(tabId, content);
                } else {
                    // Double-check: ensure inactive tabs are definitely hidden
                    content.style.setProperty('display', 'none', 'important');
                    content.style.setProperty('visibility', 'hidden', 'important');
                    content.style.setProperty('opacity', '0', 'important');
                }
            });
        };
        
        // Add click handlers - for links, update tab state but allow navigation
        // Don't clone buttons as that breaks link navigation
        tabButtons.forEach((button) => {
            const tabId = button.getAttribute('data-tab');
            
            // Only add listener if it's not already a link with href
            if (button.tagName === 'A' && button.href) {
                // For links, update tab state on click but allow navigation
                button.addEventListener('click', (e) => {
                    const clickedTabId = button.getAttribute('data-tab');
                    // Update tab state immediately (before navigation)
                    try {
                        switchToTab(clickedTabId);
                    } catch (error) {
                        console.error('[EndpointsFormEnhanced] Error in switchToTab:', error);
                    }
                    // Let the link navigate naturally - don't prevent default
                }, false);
            } else {
                // For non-link buttons, handle programmatically
                button.addEventListener('click', (e) => {
                    e.preventDefault();
                    const clickedTabId = button.getAttribute('data-tab');
                    try {
                        switchToTab(clickedTabId);
                    } catch (error) {
                        console.error('[EndpointsFormEnhanced] Error in switchToTab:', error);
                    }
                }, false);
            }
        });
        
        // Initialize first tab (search from document since buttons are outside form)
        // Get active tab from URL or use the first button
        const urlParams = new URLSearchParams(window.location.search);
        const activeTabFromUrl = urlParams.get('tab') || (tabButtons[0] ? tabButtons[0].getAttribute('data-tab') : 'basic');
        const firstActiveButton = document.querySelector('.tab-button.active') || 
                                 Array.from(tabButtons).find(btn => btn.getAttribute('data-tab') === activeTabFromUrl) ||
                                 tabButtons[0];
        if (firstActiveButton) {
            const firstTabId = firstActiveButton.getAttribute('data-tab');
            switchToTab(firstTabId);
        }
    }
    
    ensureEditorRendered(tabId, contentElement) {
        // Ensure editors are properly rendered when their tab becomes active
        // Some editors may need to re-render when they become visible
        try {
            switch(tabId) {
                case 'lambda-services':
                    if (this.editors.lambdaServices && typeof this.editors.lambdaServices.render === 'function') {
                        this.editors.lambdaServices.render();
                    }
                    break;
                case 'files':
                    if (this.editors.files && typeof this.editors.files.render === 'function') {
                        this.editors.files.render();
                    }
                    break;
                case 'methods':
                    if (this.editors.methods && typeof this.editors.methods.render === 'function') {
                        this.editors.methods.render();
                    }
                    break;
                case 'used-by-pages':
                    if (this.editors.usedByPages && typeof this.editors.usedByPages.render === 'function') {
                        this.editors.usedByPages.render();
                    }
                    break;
                case 'access-control':
                    if (this.editors.accessControl && typeof this.editors.accessControl.render === 'function') {
                        this.editors.accessControl.render();
                    }
                    break;
            }
        } catch (error) {
            console.warn(`Error rendering editor for tab ${tabId}:`, error);
        }
    }
    
    setupBasicFields() {
        const fields = ['endpoint_id', 'endpoint_path', 'api_version', 'method', 'endpoint_state', 'description'];
        
        fields.forEach(fieldName => {
            const field = this.form.querySelector(`#${fieldName}`);
            if (field) {
                field.addEventListener('change', (e) => {
                    this.formData[fieldName] = e.target.value;
                    // Auto-uppercase method
                    if (fieldName === 'method' && e.target.value) {
                        this.formData[fieldName] = e.target.value.toUpperCase();
                        e.target.value = this.formData[fieldName];
                    }
                    this.updateFormData();
                });
            }
        });
    }
    
    setupLambdaServicesEditor() {
        const container = this.form.querySelector('#lambda-services-editor');
        if (!container) return;
        
        // Initialize specialized Lambda services editor
        const lambdaServicesData = this.formData.lambda_services || null;
        
        this.editors.lambdaServices = new LambdaServicesEditor(container, {
            data: lambdaServicesData,
            readOnly: false
        });
        
        // Listen for changes
        container.addEventListener('lambda-services-change', (e) => {
            this.formData.lambda_services = e.detail.data;
            this.updateFormData();
        });
    }
    
    setupFilesEditor() {
        const container = this.form.querySelector('#files-editor');
        if (!container) return;
        
        // Initialize specialized files editor
        const filesData = this.formData.files || null;
        
        this.editors.files = new EndpointFilesEditor(container, {
            data: filesData,
            readOnly: false
        });
        
        // Listen for changes
        container.addEventListener('endpoint-files-change', (e) => {
            this.formData.files = e.detail.data;
            this.updateFormData();
        });
    }
    
    setupMethodsEditor() {
        const container = this.form.querySelector('#methods-editor');
        if (!container) return;
        
        // Initialize specialized methods editor
        const methodsData = this.formData.methods || null;
        
        this.editors.methods = new EndpointMethodsEditor(container, {
            data: methodsData,
            readOnly: false
        });
        
        // Listen for changes
        container.addEventListener('endpoint-methods-change', (e) => {
            this.formData.methods = e.detail.data;
            this.updateFormData();
        });
    }
    
    setupUsedByPagesEditor() {
        const container = this.form.querySelector('#used-by-pages-editor');
        if (!container) return;
        
        // Initialize JSON tree editor for used_by_pages (will be replaced with specialized editor)
        const usedByPagesData = this.formData.used_by_pages || [];
        
        this.editors.usedByPages = new JSONTreeEditor(container, {
            data: usedByPagesData,
            readOnly: false,
            showRoot: false,
            searchEnabled: true
        });
        
        // Listen for changes
        container.addEventListener('json-tree-change', (e) => {
            this.formData.used_by_pages = e.detail.data;
            this.updateFormData();
        });
    }
    
    setupAccessControlEditor() {
        const container = this.form.querySelector('#access-control-editor');
        if (!container) return;
        
        // Initialize JSON tree editor for access_control (will be replaced with specialized editor)
        const accessControlData = this.formData.access_control || null;
        
        this.editors.accessControl = new JSONTreeEditor(container, {
            data: accessControlData || {},
            readOnly: false,
            showRoot: false,
            searchEnabled: true
        });
        
        // Listen for changes
        container.addEventListener('json-tree-change', (e) => {
            this.formData.access_control = e.detail.data;
            this.updateFormData();
        });
    }
    
    setupAdvancedFields() {
        const fields = ['rate_limit', 'graphql_operation', 'sql_file'];
        
        fields.forEach(fieldName => {
            const field = this.form.querySelector(`#${fieldName}`);
            if (field) {
                field.addEventListener('change', (e) => {
                    this.formData[fieldName] = e.target.value || null;
                    this.updateFormData();
                });
            }
        });
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
        
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !previewModal.classList.contains('hidden')) {
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
            
            const submitBtn = this.form.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.disabled = true;
            submitBtn.textContent = 'Saving...';
            
            try {
                this.prepareFormForSubmission(submissionData);
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
    
    prepareFormForSubmission(data) {
        const existingInput = this.form.querySelector('input[name="endpoint_data"]');
        if (existingInput) {
            existingInput.remove();
        }
        
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = 'endpoint_data';
        hiddenInput.value = JSON.stringify(data);
        this.form.appendChild(hiddenInput);
    }
    
    getFormDataForSubmission() {
        const data = {
            endpoint_id: this.formData.endpoint_id,
            endpoint_path: this.formData.endpoint_path,
            method: this.formData.method,
            api_version: this.formData.api_version,
            description: this.formData.description,
            endpoint_state: this.formData.endpoint_state || 'development',
            created_at: this.formData.created_at || new Date().toISOString(),
            updated_at: new Date().toISOString(),
            lambda_services: this.formData.lambda_services || null,
            files: this.formData.files || null,
            methods: this.formData.methods || null,
            used_by_pages: this.formData.used_by_pages || [],
            access_control: this.formData.access_control || null,
            rate_limit: this.formData.rate_limit || null,
            graphql_operation: this.formData.graphql_operation || null,
            sql_file: this.formData.sql_file || null
        };
        
        // Add _id if editing
        if (this.options.isEdit && this.options.initialData._id) {
            data._id = this.options.initialData._id;
        }
        
        // Legacy fields for backward compatibility
        if (this.formData.service_file) {
            data.service_file = this.formData.service_file;
        }
        if (this.formData.router_file) {
            data.router_file = this.formData.router_file;
        }
        if (this.formData.service_methods && this.formData.service_methods.length > 0) {
            data.service_methods = this.formData.service_methods;
        }
        if (this.formData.repository_methods && this.formData.repository_methods.length > 0) {
            data.repository_methods = this.formData.repository_methods;
        }
        
        return data;
    }
    
    setupValidation() {
        this.validators.endpoint = new JSONSchemaValidator({
            schemaServiceUrl: this.options.schemaServiceUrl,
            resourceType: 'endpoints'
        });
        
        this.validators.endpoint.loadSchema('endpoints').then(() => {
            this.setupRealtimeValidation();
        }).catch(err => {
            console.warn('Failed to load schema for validation:', err);
        });
    }
    
    setupRealtimeValidation() {
        const validate = () => {
            const formData = this.getFormDataForSubmission();
            const result = this.validators.endpoint.validate(formData);
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
                // Lambda services editor
                editor.container.addEventListener('lambda-services-change', debouncedValidate);
                // Files editor
                editor.container.addEventListener('endpoint-files-change', debouncedValidate);
                // Methods editor
                editor.container.addEventListener('endpoint-methods-change', debouncedValidate);
                // Used by pages editor
                editor.container.addEventListener('json-tree-change', debouncedValidate);
                // Access control editor
                editor.container.addEventListener('json-tree-change', debouncedValidate);
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
        if (!this.validators.endpoint) {
            return true;
        }
        
        const formData = this.getFormDataForSubmission();
        const result = this.validators.endpoint.validate(formData);
        
        this.displayValidationErrors(result.errors, result.warnings);
        
        return result.errors.length === 0;
    }
    
    setupAutoSave() {
        this.autoSaveTimer = setInterval(() => {
            this.saveDraft();
        }, this.options.autoSaveInterval);
        
        window.addEventListener('beforeunload', () => {
            this.saveDraft();
        });
    }
    
    async saveDraft() {
        try {
            const formData = this.getFormDataForSubmission();
            const response = await fetch('/docs/api/endpoints/draft/', {
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
        const event = new CustomEvent('endpoints-form-data-change', {
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
    
    destroy() {
        if (this.autoSaveTimer) {
            clearInterval(this.autoSaveTimer);
        }
        
        Object.values(this.editors).forEach(editor => {
            if (editor && editor.destroy) {
                editor.destroy();
            }
        });
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EndpointsFormEnhanced;
}
