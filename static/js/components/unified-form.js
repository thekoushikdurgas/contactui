/**
 * Unified Form Controller
 * 
 * A reusable form controller that handles:
 * - Field validation
 * - Error display
 * - Submit handling
 * - Draft save
 * - Form state management
 */

class UnifiedForm {
    constructor(formId, options = {}) {
        this.form = document.getElementById(formId);
        if (!this.form) {
            console.error(`Form not found: ${formId}`);
            return;
        }
        
        this.options = {
            onSubmit: options.onSubmit || null,
            onDraftSave: options.onDraftSave || null,
            validateOnChange: options.validateOnChange !== false, // Default true
            validateOnBlur: options.validateOnBlur !== false, // Default true
            showErrors: options.showErrors !== false, // Default true
            autoSave: options.autoSave || false,
            autoSaveInterval: options.autoSaveInterval || 30000, // 30 seconds
            validationRules: options.validationRules || {},
            ...options
        };
        
        this.errors = {};
        this.autoSaveTimer = null;
        this.init();
    }
    
    /**
     * Initialize the form
     */
    init() {
        this.attachEventListeners();
        
        // Auto-save if enabled
        if (this.options.autoSave) {
            this.startAutoSave();
        }
        
        // Load draft if exists
        this.loadDraft();
    }
    
    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Form submit
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSubmit();
        });
        
        // Field validation
        if (this.options.validateOnChange || this.options.validateOnBlur) {
            const fields = this.form.querySelectorAll('input, select, textarea');
            fields.forEach(field => {
                if (this.options.validateOnChange) {
                    field.addEventListener('input', () => {
                        this.validateField(field);
                    });
                }
                
                if (this.options.validateOnBlur) {
                    field.addEventListener('blur', () => {
                        this.validateField(field);
                    });
                }
            });
        }
        
        // Draft save button
        const draftButton = this.form.querySelector('[data-draft-save]');
        if (draftButton) {
            draftButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleDraftSave();
            });
        }
        
        // Form change tracking for auto-save
        if (this.options.autoSave) {
            this.form.addEventListener('input', () => {
                this.scheduleAutoSave();
            });
        }
    }
    
    /**
     * Validate a single field
     */
    validateField(field) {
        const fieldName = field.name || field.id;
        const value = field.value;
        const rules = this.options.validationRules[fieldName] || [];
        
        let fieldErrors = [];
        
        rules.forEach(rule => {
            const error = this.validateRule(field, value, rule);
            if (error) {
                fieldErrors.push(error);
            }
        });
        
        if (fieldErrors.length > 0) {
            this.errors[fieldName] = fieldErrors;
            this.showFieldError(field, fieldErrors[0]);
        } else {
            delete this.errors[fieldName];
            this.clearFieldError(field);
        }
        
        return fieldErrors.length === 0;
    }
    
    /**
     * Validate a rule
     */
    validateRule(field, value, rule) {
        if (rule.required && !value.trim()) {
            return rule.message || `${field.getAttribute('data-label') || field.name} is required`;
        }
        
        if (rule.minLength && value.length < rule.minLength) {
            return rule.message || `${field.getAttribute('data-label') || field.name} must be at least ${rule.minLength} characters`;
        }
        
        if (rule.maxLength && value.length > rule.maxLength) {
            return rule.message || `${field.getAttribute('data-label') || field.name} must be no more than ${rule.maxLength} characters`;
        }
        
        if (rule.pattern && !rule.pattern.test(value)) {
            return rule.message || `${field.getAttribute('data-label') || field.name} format is invalid`;
        }
        
        if (rule.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
            return rule.message || `${field.getAttribute('data-label') || field.name} must be a valid email`;
        }
        
        if (rule.url && !/^https?:\/\/.+/.test(value)) {
            return rule.message || `${field.getAttribute('data-label') || field.name} must be a valid URL`;
        }
        
        if (rule.custom && typeof rule.custom === 'function') {
            const customError = rule.custom(value, field);
            if (customError) {
                return customError;
            }
        }
        
        return null;
    }
    
    /**
     * Validate entire form
     */
    validateForm() {
        this.errors = {};
        const fields = this.form.querySelectorAll('input, select, textarea');
        let isValid = true;
        
        fields.forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
            }
        });
        
        return isValid;
    }
    
    /**
     * Show field error
     */
    showFieldError(field, errorMessage) {
        if (!this.options.showErrors) {
            return;
        }
        
        // Remove existing error
        this.clearFieldError(field);
        
        // Add error class
        field.classList.add('border-red-500', 'dark:border-red-400');
        
        // Create error message element
        const errorElement = document.createElement('p');
        errorElement.className = 'mt-1 text-sm text-red-600 dark:text-red-400';
        errorElement.textContent = errorMessage;
        errorElement.setAttribute('role', 'alert');
        errorElement.setAttribute('data-field-error', field.name || field.id);
        
        // Insert after field
        field.parentNode.insertBefore(errorElement, field.nextSibling);
    }
    
    /**
     * Clear field error
     */
    clearFieldError(field) {
        field.classList.remove('border-red-500', 'dark:border-red-400');
        
        const errorElement = field.parentNode.querySelector(`[data-field-error="${field.name || field.id}"]`);
        if (errorElement) {
            errorElement.remove();
        }
    }
    
    /**
     * Show form-level errors
     */
    showFormErrors(errors) {
        const errorContainer = this.form.querySelector('.form-errors') || this.createErrorContainer();
        
        let html = '<div class="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">';
        html += '<h4 class="font-semibold text-red-800 dark:text-red-300 mb-2">Please fix the following errors:</h4>';
        html += '<ul class="list-disc list-inside space-y-1 text-sm text-red-700 dark:text-red-400">';
        
        if (Array.isArray(errors)) {
            errors.forEach(error => {
                html += `<li>${error}</li>`;
            });
        } else if (typeof errors === 'object') {
            Object.entries(errors).forEach(([field, fieldErrors]) => {
                if (Array.isArray(fieldErrors)) {
                    fieldErrors.forEach(error => {
                        html += `<li>${error}</li>`;
                    });
                } else {
                    html += `<li>${fieldErrors}</li>`;
                }
            });
        } else {
            html += `<li>${errors}</li>`;
        }
        
        html += '</ul></div>';
        
        errorContainer.innerHTML = html;
    }
    
    /**
     * Create error container
     */
    createErrorContainer() {
        const container = document.createElement('div');
        container.className = 'form-errors';
        this.form.insertBefore(container, this.form.firstChild);
        return container;
    }
    
    /**
     * Clear form errors
     */
    clearFormErrors() {
        const errorContainer = this.form.querySelector('.form-errors');
        if (errorContainer) {
            errorContainer.innerHTML = '';
        }
    }
    
    /**
     * Handle form submit
     */
    async handleSubmit() {
        // Clear previous errors
        this.clearFormErrors();
        
        // Validate form
        if (!this.validateForm()) {
            this.showFormErrors('Please fix the errors below');
            return;
        }
        
        // Get form data
        const formData = this.getFormData();
        
        // Show loading state
        this.setLoading(true);
        
        try {
            if (this.options.onSubmit) {
                await this.options.onSubmit(formData, this);
            } else {
                // Default: submit form normally
                this.form.submit();
            }
        } catch (error) {
            this.setLoading(false);
            this.showFormErrors(error.message || 'An error occurred while submitting the form');
        }
    }
    
    /**
     * Handle draft save
     */
    async handleDraftSave() {
        const formData = this.getFormData();
        
        // Save to localStorage
        localStorage.setItem(`form_draft_${this.form.id}`, JSON.stringify(formData));
        
        // Call callback if provided
        if (this.options.onDraftSave) {
            try {
                await this.options.onDraftSave(formData, this);
            } catch (error) {
                console.error('Error saving draft:', error);
            }
        }
        
        // Show success message
        this.showSuccessMessage('Draft saved');
    }
    
    /**
     * Load draft
     */
    loadDraft() {
        const draftData = localStorage.getItem(`form_draft_${this.form.id}`);
        if (draftData) {
            try {
                const data = JSON.parse(draftData);
                this.setFormData(data);
            } catch (e) {
                console.error('Error loading draft:', e);
            }
        }
    }
    
    /**
     * Get form data
     */
    getFormData() {
        const formData = new FormData(this.form);
        const data = {};
        
        for (const [key, value] of formData.entries()) {
            if (data[key]) {
                // Handle multiple values (e.g., checkboxes)
                if (Array.isArray(data[key])) {
                    data[key].push(value);
                } else {
                    data[key] = [data[key], value];
                }
            } else {
                data[key] = value;
            }
        }
        
        return data;
    }
    
    /**
     * Set form data
     */
    setFormData(data) {
        Object.entries(data).forEach(([key, value]) => {
            const field = this.form.querySelector(`[name="${key}"]`);
            if (field) {
                if (field.type === 'checkbox') {
                    field.checked = value;
                } else if (field.type === 'radio') {
                    const radio = this.form.querySelector(`[name="${key}"][value="${value}"]`);
                    if (radio) {
                        radio.checked = true;
                    }
                } else {
                    field.value = value;
                }
            }
        });
    }
    
    /**
     * Set loading state
     */
    setLoading(loading) {
        const submitButton = this.form.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = loading;
            if (loading) {
                submitButton.classList.add('opacity-50', 'cursor-not-allowed');
                submitButton.innerHTML = '<span class="btn-spinner"></span> Submitting...';
            } else {
                submitButton.classList.remove('opacity-50', 'cursor-not-allowed');
                // Restore original button text (would need to store it)
            }
        }
    }
    
    /**
     * Show success message
     */
    showSuccessMessage(message) {
        // Create toast or notification
        // This is a simple implementation
        const toast = document.createElement('div');
        toast.className = 'fixed bottom-4 right-4 px-4 py-3 bg-green-500 text-white rounded-lg shadow-lg z-50';
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
    
    /**
     * Start auto-save
     */
    startAutoSave() {
        this.scheduleAutoSave();
    }
    
    /**
     * Schedule auto-save
     */
    scheduleAutoSave() {
        if (this.autoSaveTimer) {
            clearTimeout(this.autoSaveTimer);
        }
        
        this.autoSaveTimer = setTimeout(() => {
            this.handleDraftSave();
        }, this.options.autoSaveInterval);
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UnifiedForm;
}
