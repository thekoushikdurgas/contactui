/**
 * JSON Schema Validator Component
 * 
 * Provides real-time validation against Lambda API schemas with:
 * - Field-level error highlighting
 * - Validation error messages
 * - Schema loading and caching
 * - Support for multiple schema versions
 */

class JSONSchemaValidator {
    constructor(options = {}) {
        this.schemaServiceUrl = options.schemaServiceUrl || '/docs/api/schemas/';
        this.resourceType = options.resourceType || 'pages';
        this.schema = options.schema || null;
        this.errors = [];
        this.warnings = [];
        this.validationCallbacks = [];
    }
    
    async loadSchema(resourceType = null) {
        const type = resourceType || this.resourceType;
        
        try {
            const response = await fetch(`${this.schemaServiceUrl}${type}/`);
            if (!response.ok) {
                throw new Error(`Failed to load schema: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.schema = data.schema || data;
            this.resourceType = type;
            
            return this.schema;
        } catch (error) {
            console.error('Failed to load schema:', error);
            return null;
        }
    }
    
    validate(data, schema = null) {
        this.errors = [];
        this.warnings = [];
        
        const validationSchema = schema || this.schema;
        if (!validationSchema) {
            this.warnings.push('No schema available for validation');
            return { valid: true, errors: [], warnings: this.warnings };
        }
        
        // Basic validation based on schema structure
        // Full JSON Schema validation would require a library like ajv
        this.validateStructure(data, validationSchema);
        this.validateRequiredFields(data, validationSchema);
        this.validateFieldTypes(data, validationSchema);
        
        const isValid = this.errors.length === 0;
        
        // Trigger callbacks
        this.validationCallbacks.forEach(callback => {
            callback({
                valid: isValid,
                errors: this.errors,
                warnings: this.warnings
            });
        });
        
        return {
            valid: isValid,
            errors: this.errors,
            warnings: this.warnings
        };
    }
    
    validateStructure(data, schema) {
        if (!data || typeof data !== 'object') {
            this.errors.push({
                path: 'root',
                message: 'Data must be an object',
                type: 'structure'
            });
            return;
        }
        
        // Validate based on resource type
        if (this.resourceType === 'pages') {
            this.validatePageStructure(data);
        } else if (this.resourceType === 'endpoints') {
            this.validateEndpointStructure(data);
        } else if (this.resourceType === 'relationships') {
            this.validateRelationshipStructure(data);
        }
    }
    
    validatePageStructure(data) {
        const requiredFields = ['page_id', 'page_type', 'metadata', 'created_at'];
        
        requiredFields.forEach(field => {
            if (!(field in data)) {
                this.errors.push({
                    path: field,
                    message: `Required field '${field}' is missing`,
                    type: 'required'
                });
            }
        });
        
        // Validate metadata structure
        if (data.metadata && typeof data.metadata === 'object') {
            const metadataRequired = ['route', 'file_path', 'purpose', 's3_key', 'last_updated'];
            metadataRequired.forEach(field => {
                if (!(field in data.metadata)) {
                    this.errors.push({
                        path: `metadata.${field}`,
                        message: `Required field 'metadata.${field}' is missing`,
                        type: 'required'
                    });
                }
            });
            
            // Validate route format
            if (data.metadata.route && !data.metadata.route.startsWith('/')) {
                this.warnings.push({
                    path: 'metadata.route',
                    message: "Route should start with '/'",
                    type: 'format'
                });
            }
            
            // Validate page_state
            const validStates = ['coming_soon', 'published', 'draft', 'development', 'test'];
            if (data.metadata.page_state && !validStates.includes(data.metadata.page_state)) {
                this.errors.push({
                    path: 'metadata.page_state',
                    message: `page_state must be one of: ${validStates.join(', ')}`,
                    type: 'enum'
                });
            }
            
            // Validate status
            const validStatuses = ['draft', 'published', 'archived', 'deleted'];
            if (data.metadata.status && !validStatuses.includes(data.metadata.status)) {
                this.errors.push({
                    path: 'metadata.status',
                    message: `status must be one of: ${validStatuses.join(', ')}`,
                    type: 'enum'
                });
            }
        }
    }
    
    validateEndpointStructure(data) {
        const requiredFields = ['endpoint_id', 'endpoint_path', 'method', 'api_version', 'description', 'created_at', 'updated_at'];
        
        requiredFields.forEach(field => {
            if (!(field in data)) {
                this.errors.push({
                    path: field,
                    message: `Required field '${field}' is missing`,
                    type: 'required'
                });
            }
        });
        
        // Validate method
        const validMethods = ['QUERY', 'MUTATION', 'GET', 'POST', 'PUT', 'DELETE', 'PATCH'];
        if (data.method && !validMethods.includes(data.method.toUpperCase())) {
            this.errors.push({
                path: 'method',
                message: `method must be one of: ${validMethods.join(', ')}`,
                type: 'enum'
            });
        }
        
        // Validate file reference requirement
        const hasServiceFile = data.service_file || (data.files && data.files.service_file);
        const hasRouterFile = data.router_file || (data.files && data.files.router_file);
        if (!hasServiceFile && !hasRouterFile) {
            this.errors.push({
                path: 'files',
                message: "At least one of 'service_file' or 'router_file' must be provided",
                type: 'required'
            });
        }
    }
    
    validateRelationshipStructure(data) {
        // Validate based on enhanced or legacy format
        if (data.relationship_id || data._id) {
            // Enhanced format
            if (data.state) {
                const validStates = ['coming_soon', 'published', 'draft', 'development', 'test'];
                if (!validStates.includes(data.state)) {
                    this.errors.push({
                        path: 'state',
                        message: `state must be one of: ${validStates.join(', ')}`,
                        type: 'enum'
                    });
                }
            }
        } else {
            // Legacy format - validate basic fields
            const requiredFields = ['page_path', 'endpoint_path', 'method', 'api_version', 'via_service'];
            requiredFields.forEach(field => {
                if (!(field in data)) {
                    this.errors.push({
                        path: field,
                        message: `Required field '${field}' is missing`,
                        type: 'required'
                    });
                }
            });
        }
    }
    
    validateRequiredFields(data, schema) {
        // This would be enhanced with full JSON Schema validation
        // For now, we use resource-specific validation
    }
    
    validateFieldTypes(data, schema) {
        // Basic type validation
        if (data.page_type && !['dashboard', 'marketing', 'docs'].includes(data.page_type)) {
            this.errors.push({
                path: 'page_type',
                message: "page_type must be one of: dashboard, marketing, docs",
                type: 'enum'
            });
        }
    }
    
    onValidation(callback) {
        this.validationCallbacks.push(callback);
    }
    
    highlightErrors(container, errors) {
        // Remove existing error highlights
        container.querySelectorAll('.json-validation-error').forEach(el => {
            el.classList.remove('json-validation-error');
        });
        
        // Add error highlights
        errors.forEach(error => {
            const element = container.querySelector(`[data-path="${error.path}"]`);
            if (element) {
                element.classList.add('json-validation-error');
                element.title = error.message;
            }
        });
    }
    
    getErrorSummary() {
        if (this.errors.length === 0) {
            return null;
        }
        
        return {
            total: this.errors.length,
            byType: this.groupErrorsByType(),
            byPath: this.groupErrorsByPath()
        };
    }
    
    groupErrorsByType() {
        const grouped = {};
        this.errors.forEach(error => {
            grouped[error.type] = (grouped[error.type] || 0) + 1;
        });
        return grouped;
    }
    
    groupErrorsByPath() {
        const grouped = {};
        this.errors.forEach(error => {
            if (!grouped[error.path]) {
                grouped[error.path] = [];
            }
            grouped[error.path].push(error);
        });
        return grouped;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = JSONSchemaValidator;
}
