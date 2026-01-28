/**
 * Template Selector Component
 * 
 * Provides template selection for pages and endpoints with:
 * - Template library display
 * - Template preview
 * - Apply template to form
 * - Custom template creation
 */

class TemplateSelector {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.options = {
            resourceType: options.resourceType || 'pages', // 'pages', 'endpoints', 'relationships'
            templatesUrl: options.templatesUrl || '/docs/api/templates/',
            onTemplateSelect: options.onTemplateSelect || null,
            ...options
        };
        
        if (!this.container) {
            throw new Error('Container element not found');
        }
        
        this.templates = [];
        this.selectedTemplate = null;
        this.init();
    }
    
    async init() {
        await this.loadTemplates();
        this.render();
        this.setupEventListeners();
    }
    
    async loadTemplates() {
        try {
            const response = await fetch(`${this.options.templatesUrl}${this.options.resourceType}/`);
            if (response.ok) {
                const data = await response.json();
                this.templates = data.templates || this.getDefaultTemplates();
            } else {
                this.templates = this.getDefaultTemplates();
            }
        } catch (error) {
            console.warn('Failed to load templates, using defaults:', error);
            this.templates = this.getDefaultTemplates();
        }
    }
    
    getDefaultTemplates() {
        if (this.options.resourceType === 'pages') {
            return [
                {
                    id: 'dashboard-template',
                    name: 'Dashboard Page',
                    description: 'Template for dashboard pages with common components',
                    icon: '📊',
                    data: {
                        page_type: 'dashboard',
                        metadata: {
                            route: '/dashboard',
                            purpose: 'Dashboard page',
                            status: 'draft',
                            page_state: 'development',
                            uses_endpoints: [],
                            ui_components: []
                        },
                        content: '# Dashboard\n\nWelcome to your dashboard.',
                        access_control: {
                            super_admin: { can_view: true, can_edit: true, can_delete: true, restricted_components: [] },
                            admin: { can_view: true, can_edit: true, can_delete: false, restricted_components: [] },
                            pro_user: { can_view: true, can_edit: false, can_delete: false, restricted_components: [] },
                            free_user: { can_view: true, can_edit: false, can_delete: false, restricted_components: [] },
                            guest: { can_view: false, can_edit: false, can_delete: false, restricted_components: [] }
                        }
                    }
                },
                {
                    id: 'docs-template',
                    name: 'Documentation Page',
                    description: 'Template for documentation pages',
                    icon: '📚',
                    data: {
                        page_type: 'docs',
                        metadata: {
                            route: '/docs',
                            purpose: 'Documentation page',
                            status: 'draft',
                            page_state: 'development',
                            uses_endpoints: [],
                            ui_components: []
                        },
                        content: '# Documentation\n\nDocumentation content goes here.',
                        access_control: {
                            super_admin: { can_view: true, can_edit: true, can_delete: true, restricted_components: [] },
                            admin: { can_view: true, can_edit: true, can_delete: false, restricted_components: [] },
                            pro_user: { can_view: true, can_edit: false, can_delete: false, restricted_components: [] },
                            free_user: { can_view: true, can_edit: false, can_delete: false, restricted_components: [] },
                            guest: { can_view: true, can_edit: false, can_delete: false, restricted_components: [] }
                        }
                    }
                },
                {
                    id: 'marketing-template',
                    name: 'Marketing Page',
                    description: 'Template for marketing/landing pages',
                    icon: '🎯',
                    data: {
                        page_type: 'marketing',
                        metadata: {
                            route: '/marketing',
                            purpose: 'Marketing page',
                            status: 'draft',
                            page_state: 'development',
                            uses_endpoints: [],
                            ui_components: []
                        },
                        content: '# Marketing Page\n\nMarketing content goes here.',
                        access_control: {
                            super_admin: { can_view: true, can_edit: true, can_delete: true, restricted_components: [] },
                            admin: { can_view: true, can_edit: true, can_delete: false, restricted_components: [] },
                            pro_user: { can_view: true, can_edit: false, can_delete: false, restricted_components: [] },
                            free_user: { can_view: true, can_edit: false, can_delete: false, restricted_components: [] },
                            guest: { can_view: true, can_edit: false, can_delete: false, restricted_components: [] }
                        }
                    }
                }
            ];
        } else if (this.options.resourceType === 'endpoints') {
            return [
                {
                    id: 'graphql-query-template',
                    name: 'GraphQL Query',
                    description: 'Template for GraphQL query endpoints',
                    icon: '🔍',
                    data: {
                        method: 'QUERY',
                        api_version: 'graphql',
                        endpoint_state: 'development',
                        description: 'GraphQL query endpoint',
                        lambda_services: {
                            primary: {
                                service_name: 'QueryService',
                                function_name: 'query_handler',
                                runtime: 'python3.11',
                                memory_mb: 256,
                                timeout_seconds: 30
                            },
                            dependencies: [],
                            environment: {}
                        }
                    }
                },
                {
                    id: 'graphql-mutation-template',
                    name: 'GraphQL Mutation',
                    description: 'Template for GraphQL mutation endpoints',
                    icon: '✏️',
                    data: {
                        method: 'MUTATION',
                        api_version: 'graphql',
                        endpoint_state: 'development',
                        description: 'GraphQL mutation endpoint',
                        lambda_services: {
                            primary: {
                                service_name: 'MutationService',
                                function_name: 'mutation_handler',
                                runtime: 'python3.11',
                                memory_mb: 256,
                                timeout_seconds: 30
                            },
                            dependencies: [],
                            environment: {}
                        }
                    }
                },
                {
                    id: 'rest-get-template',
                    name: 'REST GET',
                    description: 'Template for REST GET endpoints',
                    icon: '📥',
                    data: {
                        method: 'GET',
                        api_version: 'rest-v1',
                        endpoint_state: 'development',
                        description: 'REST GET endpoint',
                        lambda_services: {
                            primary: {
                                service_name: 'GetService',
                                function_name: 'get_handler',
                                runtime: 'python3.11',
                                memory_mb: 256,
                                timeout_seconds: 30
                            },
                            dependencies: [],
                            environment: {}
                        }
                    }
                }
            ];
        }
        return [];
    }
    
    render() {
        const html = `
            <div class="template-selector-wrapper">
                <div class="mb-4">
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">Select Template</h3>
                    <p class="text-sm text-gray-600 dark:text-gray-400">Choose a template to pre-fill the form</p>
                </div>
                
                <div class="templates-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    ${this.templates.map(template => this.renderTemplateCard(template)).join('')}
                </div>
                
                ${this.selectedTemplate ? `
                    <div class="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                        <div class="flex items-center justify-between">
                            <div>
                                <p class="text-sm font-medium text-blue-900 dark:text-blue-100">
                                    Template selected: <strong>${this.escapeHtml(this.selectedTemplate.name)}</strong>
                                </p>
                                <p class="text-xs text-blue-700 dark:text-blue-300 mt-1">
                                    Click "Apply Template" to use this template
                                </p>
                            </div>
                            <button 
                                type="button"
                                class="apply-template-btn px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
                            >
                                Apply Template
                            </button>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
        
        this.container.innerHTML = html;
    }
    
    renderTemplateCard(template) {
        const isSelected = this.selectedTemplate && this.selectedTemplate.id === template.id;
        
        return `
            <div 
                class="template-card cursor-pointer bg-white dark:bg-gray-800 rounded-lg border-2 p-4 transition-all hover:border-blue-500 dark:hover:border-blue-400 ${
                    isSelected 
                        ? 'border-blue-600 dark:border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
                        : 'border-gray-200 dark:border-gray-700'
                }"
                data-template-id="${template.id}"
            >
                <div class="flex items-start gap-3">
                    <div class="text-3xl">${template.icon || '📄'}</div>
                    <div class="flex-1">
                        <h4 class="font-semibold text-gray-900 dark:text-gray-100 mb-1">${this.escapeHtml(template.name)}</h4>
                        <p class="text-sm text-gray-600 dark:text-gray-400">${this.escapeHtml(template.description || '')}</p>
                    </div>
                </div>
            </div>
        `;
    }
    
    setupEventListeners() {
        // Template card selection
        const templateCards = this.container.querySelectorAll('.template-card');
        templateCards.forEach(card => {
            card.addEventListener('click', (e) => {
                const templateId = e.currentTarget.getAttribute('data-template-id');
                const template = this.templates.find(t => t.id === templateId);
                if (template) {
                    this.selectedTemplate = template;
                    this.render();
                    this.setupEventListeners();
                }
            });
        });
        
        // Apply template button
        const applyBtn = this.container.querySelector('.apply-template-btn');
        if (applyBtn) {
            applyBtn.addEventListener('click', () => {
                if (this.selectedTemplate && this.options.onTemplateSelect) {
                    this.options.onTemplateSelect(this.selectedTemplate.data);
                }
                this.triggerTemplateApplied(this.selectedTemplate.data);
            });
        }
    }
    
    triggerTemplateApplied(templateData) {
        const event = new CustomEvent('template-applied', {
            detail: { templateData: templateData }
        });
        this.container.dispatchEvent(event);
    }
    
    escapeHtml(text) {
        if (text === null || text === undefined) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    getSelectedTemplate() {
        return this.selectedTemplate;
    }
    
    setTemplates(templates) {
        this.templates = templates;
        this.render();
        this.setupEventListeners();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TemplateSelector;
}
