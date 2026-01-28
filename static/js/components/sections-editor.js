/**
 * Sections Editor Component
 * 
 * Provides a visual editor for PageSections with:
 * - Tabbed interface for each section element type
 * - Add/remove items for each type
 * - Form fields for each element's properties
 * - Support for all section element types
 */

class SectionsEditor {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.options = {
            data: options.data || {},
            readOnly: options.readOnly || false,
            ...options
        };
        
        if (!this.container) {
            throw new Error('Container element not found');
        }
        
        this.sectionTypes = [
            { key: 'headings', label: 'Headings', elementType: 'HeadingElement' },
            { key: 'subheadings', label: 'Subheadings', elementType: 'HeadingElement' },
            { key: 'tabs', label: 'Tabs', elementType: 'TabElement' },
            { key: 'buttons', label: 'Buttons', elementType: 'ButtonElement' },
            { key: 'input_boxes', label: 'Input Boxes', elementType: 'InputBoxElement' },
            { key: 'text_blocks', label: 'Text Blocks', elementType: 'TextBlockElement' },
            { key: 'components', label: 'Components', elementType: 'ComponentReference' },
            { key: 'utilities', label: 'Utilities', elementType: 'UtilityReference' },
            { key: 'services', label: 'Services', elementType: 'ServiceReference' },
            { key: 'hooks', label: 'Hooks', elementType: 'HookReference' },
            { key: 'contexts', label: 'Contexts', elementType: 'ContextReference' },
            { key: 'ui_components', label: 'UI Components', elementType: 'ComponentReference' },
            { key: 'endpoints', label: 'Endpoints', elementType: 'EndpointReferenceInSection' }
        ];
        
        this.data = this.initializeData(this.options.data);
        this.currentSectionType = this.sectionTypes[0].key;
        this.init();
    }
    
    initializeData(initialData) {
        const data = {};
        this.sectionTypes.forEach(sectionType => {
            data[sectionType.key] = Array.isArray(initialData[sectionType.key]) 
                ? [...initialData[sectionType.key]] 
                : [];
        });
        return data;
    }
    
    init() {
        this.container.innerHTML = '';
        this.container.classList.add('sections-editor');
        this.render();
        this.setupEventListeners();
    }
    
    render() {
        const html = `
            <div class="sections-editor-wrapper">
                <div class="mb-4">
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">Page Sections</h3>
                    <p class="text-sm text-gray-600 dark:text-gray-400">Manage all section elements for this page</p>
                </div>
                
                <!-- Section Type Tabs -->
                <div class="border-b border-gray-200 dark:border-gray-700 mb-4">
                    <nav class="flex flex-wrap gap-2" role="tablist">
                        ${this.sectionTypes.map(sectionType => `
                            <button 
                                class="section-type-tab px-4 py-2 rounded-t-lg border-b-2 transition-colors ${
                                    this.currentSectionType === sectionType.key 
                                        ? 'border-blue-600 text-blue-600 bg-blue-50 dark:bg-blue-900/20' 
                                        : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
                                }"
                                data-section-type="${sectionType.key}"
                                role="tab"
                            >
                                ${sectionType.label}
                                <span class="ml-2 text-xs bg-gray-200 dark:bg-gray-700 px-2 py-0.5 rounded">
                                    ${this.data[sectionType.key].length}
                                </span>
                            </button>
                        `).join('')}
                    </nav>
                </div>
                
                <!-- Section Content -->
                <div class="section-content">
                    ${this.renderSectionTypeContent(this.currentSectionType)}
                </div>
            </div>
        `;
        
        this.container.innerHTML = html;
    }
    
    renderSectionTypeContent(sectionType) {
        const items = this.data[sectionType] || [];
        const sectionTypeInfo = this.sectionTypes.find(st => st.key === sectionType);
        
        return `
            <div class="section-type-content" data-section-type="${sectionType}">
                <div class="flex justify-between items-center mb-4">
                    <h4 class="text-md font-semibold text-gray-900 dark:text-gray-100">
                        ${sectionTypeInfo.label} (${items.length})
                    </h4>
                    ${!this.options.readOnly ? `
                        <button 
                            type="button" 
                            class="add-section-item-btn px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
                            data-section-type="${sectionType}"
                        >
                            + Add ${sectionTypeInfo.label.slice(0, -1)}
                        </button>
                    ` : ''}
                </div>
                
                <div class="section-items-list space-y-4">
                    ${items.length === 0 ? `
                        <div class="text-center py-8 text-gray-500 dark:text-gray-400">
                            <p>No ${sectionTypeInfo.label.toLowerCase()} added yet</p>
                        </div>
                    ` : items.map((item, index) => this.renderSectionItem(sectionType, item, index)).join('')}
                </div>
            </div>
        `;
    }
    
    renderSectionItem(sectionType, item, index) {
        const itemHtml = {
            'headings': this.renderHeadingElement(item, index),
            'subheadings': this.renderHeadingElement(item, index),
            'tabs': this.renderTabElement(item, index),
            'buttons': this.renderButtonElement(item, index),
            'input_boxes': this.renderInputBoxElement(item, index),
            'text_blocks': this.renderTextBlockElement(item, index),
            'components': this.renderComponentReference(item, index),
            'utilities': this.renderUtilityReference(item, index),
            'services': this.renderServiceReference(item, index),
            'hooks': this.renderHookReference(item, index),
            'contexts': this.renderContextReference(item, index),
            'ui_components': this.renderComponentReference(item, index),
            'endpoints': this.renderEndpointReference(item, index)
        };
        
        return itemHtml[sectionType] || '';
    }
    
    renderHeadingElement(item, index) {
        return `
            <div class="section-item bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700" data-index="${index}">
                <div class="flex justify-between items-start mb-3">
                    <h5 class="font-semibold text-gray-900 dark:text-gray-100">Heading #${index + 1}</h5>
                    ${!this.options.readOnly ? `
                        <button 
                            type="button" 
                            class="remove-item-btn px-3 py-1 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm"
                            data-index="${index}"
                        >
                            Remove
                        </button>
                    ` : ''}
                </div>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">ID <span class="text-red-500">*</span></label>
                        <input type="text" value="${this.escapeHtml(item.id || '')}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="id" data-index="${index}" />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Text <span class="text-red-500">*</span></label>
                        <input type="text" value="${this.escapeHtml(item.text || '')}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="text" data-index="${index}" />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Level (1-6) <span class="text-red-500">*</span></label>
                        <input type="number" min="1" max="6" value="${item.level || 1}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="level" data-index="${index}" />
                    </div>
                </div>
            </div>
        `;
    }
    
    renderTabElement(item, index) {
        return `
            <div class="section-item bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700" data-index="${index}">
                <div class="flex justify-between items-start mb-3">
                    <h5 class="font-semibold text-gray-900 dark:text-gray-100">Tab #${index + 1}</h5>
                    ${!this.options.readOnly ? `
                        <button type="button" class="remove-item-btn px-3 py-1 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm" data-index="${index}">Remove</button>
                    ` : ''}
                </div>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">ID <span class="text-red-500">*</span></label>
                        <input type="text" value="${this.escapeHtml(item.id || '')}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="id" data-index="${index}" />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Label <span class="text-red-500">*</span></label>
                        <input type="text" value="${this.escapeHtml(item.label || '')}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="label" data-index="${index}" />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Content Ref <span class="text-red-500">*</span></label>
                        <input type="text" value="${this.escapeHtml(item.content_ref || '')}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="content_ref" data-index="${index}" />
                    </div>
                </div>
            </div>
        `;
    }
    
    renderButtonElement(item, index) {
        return `
            <div class="section-item bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700" data-index="${index}">
                <div class="flex justify-between items-start mb-3">
                    <h5 class="font-semibold text-gray-900 dark:text-gray-100">Button #${index + 1}</h5>
                    ${!this.options.readOnly ? `
                        <button type="button" class="remove-item-btn px-3 py-1 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm" data-index="${index}">Remove</button>
                    ` : ''}
                </div>
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">ID <span class="text-red-500">*</span></label>
                        <input type="text" value="${this.escapeHtml(item.id || '')}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="id" data-index="${index}" />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Label <span class="text-red-500">*</span></label>
                        <input type="text" value="${this.escapeHtml(item.label || '')}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="label" data-index="${index}" />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Action <span class="text-red-500">*</span></label>
                        <input type="text" value="${this.escapeHtml(item.action || '')}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="action" data-index="${index}" />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Variant</label>
                        <input type="text" value="${this.escapeHtml(item.variant || 'primary')}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="variant" data-index="${index}" placeholder="primary" />
                    </div>
                </div>
            </div>
        `;
    }
    
    renderInputBoxElement(item, index) {
        return `
            <div class="section-item bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700" data-index="${index}">
                <div class="flex justify-between items-start mb-3">
                    <h5 class="font-semibold text-gray-900 dark:text-gray-100">Input Box #${index + 1}</h5>
                    ${!this.options.readOnly ? `
                        <button type="button" class="remove-item-btn px-3 py-1 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm" data-index="${index}">Remove</button>
                    ` : ''}
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">ID <span class="text-red-500">*</span></label>
                        <input type="text" value="${this.escapeHtml(item.id || '')}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="id" data-index="${index}" />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Label <span class="text-red-500">*</span></label>
                        <input type="text" value="${this.escapeHtml(item.label || '')}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="label" data-index="${index}" />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Input Type</label>
                        <input type="text" value="${this.escapeHtml(item.input_type || 'text')}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="input_type" data-index="${index}" placeholder="text" />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Placeholder</label>
                        <input type="text" value="${this.escapeHtml(item.placeholder || '')}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="placeholder" data-index="${index}" />
                    </div>
                    <div>
                        <label class="flex items-center gap-2">
                            <input type="checkbox" ${item.required ? 'checked' : ''} ${this.options.readOnly ? 'disabled' : ''} 
                                   class="section-field" data-field="required" data-index="${index}" />
                            <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Required</span>
                        </label>
                    </div>
                </div>
            </div>
        `;
    }
    
    renderTextBlockElement(item, index) {
        return `
            <div class="section-item bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700" data-index="${index}">
                <div class="flex justify-between items-start mb-3">
                    <h5 class="font-semibold text-gray-900 dark:text-gray-100">Text Block #${index + 1}</h5>
                    ${!this.options.readOnly ? `
                        <button type="button" class="remove-item-btn px-3 py-1 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm" data-index="${index}">Remove</button>
                    ` : ''}
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">ID <span class="text-red-500">*</span></label>
                        <input type="text" value="${this.escapeHtml(item.id || '')}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="id" data-index="${index}" />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Format</label>
                        <input type="text" value="${this.escapeHtml(item.format || 'markdown')}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="format" data-index="${index}" placeholder="markdown" />
                    </div>
                    <div class="md:col-span-2">
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Content <span class="text-red-500">*</span></label>
                        <textarea rows="4" ${this.options.readOnly ? 'readonly' : ''} 
                                  class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                                  data-field="content" data-index="${index}">${this.escapeHtml(item.content || '')}</textarea>
                    </div>
                </div>
            </div>
        `;
    }
    
    renderComponentReference(item, index) {
        return `
            <div class="section-item bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700" data-index="${index}">
                <div class="flex justify-between items-start mb-3">
                    <h5 class="font-semibold text-gray-900 dark:text-gray-100">Component #${index + 1}</h5>
                    ${!this.options.readOnly ? `
                        <button type="button" class="remove-item-btn px-3 py-1 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm" data-index="${index}">Remove</button>
                    ` : ''}
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Name <span class="text-red-500">*</span></label>
                        <input type="text" value="${this.escapeHtml(item.name || '')}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="name" data-index="${index}" />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">File Path <span class="text-red-500">*</span></label>
                        <input type="text" value="${this.escapeHtml(item.file_path || '')}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="file_path" data-index="${index}" />
                    </div>
                    <div class="md:col-span-2">
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Props (JSON)</label>
                        <textarea rows="3" ${this.options.readOnly ? 'readonly' : ''} 
                                  class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 font-mono text-sm" 
                                  data-field="props" data-index="${index}" placeholder='{"prop1": "value1"}'>${this.escapeHtml(JSON.stringify(item.props || {}, null, 2))}</textarea>
                    </div>
                </div>
            </div>
        `;
    }
    
    renderUtilityReference(item, index) {
        return `
            <div class="section-item bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700" data-index="${index}">
                <div class="flex justify-between items-start mb-3">
                    <h5 class="font-semibold text-gray-900 dark:text-gray-100">Utility #${index + 1}</h5>
                    ${!this.options.readOnly ? `
                        <button type="button" class="remove-item-btn px-3 py-1 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm" data-index="${index}">Remove</button>
                    ` : ''}
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Name <span class="text-red-500">*</span></label>
                        <input type="text" value="${this.escapeHtml(item.name || '')}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="name" data-index="${index}" />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">File Path <span class="text-red-500">*</span></label>
                        <input type="text" value="${this.escapeHtml(item.file_path || '')}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="file_path" data-index="${index}" />
                    </div>
                    <div class="md:col-span-2">
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Functions (comma-separated)</label>
                        <input type="text" value="${this.escapeHtml((item.functions || []).join(', '))}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="functions" data-index="${index}" placeholder="function1, function2" />
                    </div>
                </div>
            </div>
        `;
    }
    
    renderServiceReference(item, index) {
        return `
            <div class="section-item bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700" data-index="${index}">
                <div class="flex justify-between items-start mb-3">
                    <h5 class="font-semibold text-gray-900 dark:text-gray-100">Service #${index + 1}</h5>
                    ${!this.options.readOnly ? `
                        <button type="button" class="remove-item-btn px-3 py-1 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm" data-index="${index}">Remove</button>
                    ` : ''}
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Name <span class="text-red-500">*</span></label>
                        <input type="text" value="${this.escapeHtml(item.name || '')}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="name" data-index="${index}" />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">File Path <span class="text-red-500">*</span></label>
                        <input type="text" value="${this.escapeHtml(item.file_path || '')}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="file_path" data-index="${index}" />
                    </div>
                    <div class="md:col-span-2">
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Methods (comma-separated)</label>
                        <input type="text" value="${this.escapeHtml((item.methods || []).join(', '))}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="methods" data-index="${index}" placeholder="method1, method2" />
                    </div>
                </div>
            </div>
        `;
    }
    
    renderHookReference(item, index) {
        return `
            <div class="section-item bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700" data-index="${index}">
                <div class="flex justify-between items-start mb-3">
                    <h5 class="font-semibold text-gray-900 dark:text-gray-100">Hook #${index + 1}</h5>
                    ${!this.options.readOnly ? `
                        <button type="button" class="remove-item-btn px-3 py-1 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm" data-index="${index}">Remove</button>
                    ` : ''}
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Name <span class="text-red-500">*</span></label>
                        <input type="text" value="${this.escapeHtml(item.name || '')}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="name" data-index="${index}" />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">File Path <span class="text-red-500">*</span></label>
                        <input type="text" value="${this.escapeHtml(item.file_path || '')}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="file_path" data-index="${index}" />
                    </div>
                    <div class="md:col-span-2">
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Dependencies (comma-separated)</label>
                        <input type="text" value="${this.escapeHtml((item.dependencies || []).join(', '))}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="dependencies" data-index="${index}" placeholder="dep1, dep2" />
                    </div>
                </div>
            </div>
        `;
    }
    
    renderContextReference(item, index) {
        return `
            <div class="section-item bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700" data-index="${index}">
                <div class="flex justify-between items-start mb-3">
                    <h5 class="font-semibold text-gray-900 dark:text-gray-100">Context #${index + 1}</h5>
                    ${!this.options.readOnly ? `
                        <button type="button" class="remove-item-btn px-3 py-1 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm" data-index="${index}">Remove</button>
                    ` : ''}
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Name <span class="text-red-500">*</span></label>
                        <input type="text" value="${this.escapeHtml(item.name || '')}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="name" data-index="${index}" />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">File Path <span class="text-red-500">*</span></label>
                        <input type="text" value="${this.escapeHtml(item.file_path || '')}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="file_path" data-index="${index}" />
                    </div>
                    <div class="md:col-span-2">
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Provider</label>
                        <input type="text" value="${this.escapeHtml(item.provider || '')}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="provider" data-index="${index}" />
                    </div>
                </div>
            </div>
        `;
    }
    
    renderEndpointReference(item, index) {
        return `
            <div class="section-item bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700" data-index="${index}">
                <div class="flex justify-between items-start mb-3">
                    <h5 class="font-semibold text-gray-900 dark:text-gray-100">Endpoint #${index + 1}</h5>
                    ${!this.options.readOnly ? `
                        <button type="button" class="remove-item-btn px-3 py-1 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm" data-index="${index}">Remove</button>
                    ` : ''}
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Endpoint ID <span class="text-red-500">*</span></label>
                        <input type="text" value="${this.escapeHtml(item.endpoint_id || '')}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="endpoint_id" data-index="${index}" />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Endpoint Path <span class="text-red-500">*</span></label>
                        <input type="text" value="${this.escapeHtml(item.endpoint_path || '')}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="endpoint_path" data-index="${index}" />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Method <span class="text-red-500">*</span></label>
                        <input type="text" value="${this.escapeHtml(item.method || '')}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="method" data-index="${index}" />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">File Path</label>
                        <input type="text" value="${this.escapeHtml(item.file_path || '')}" ${this.options.readOnly ? 'readonly' : ''} 
                               class="section-field w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700" 
                               data-field="file_path" data-index="${index}" />
                    </div>
                </div>
            </div>
        `;
    }
    
    setupEventListeners() {
        if (this.options.readOnly) return;
        
        // Section type tabs
        const tabs = this.container.querySelectorAll('.section-type-tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                const sectionType = e.target.getAttribute('data-section-type');
                this.switchSectionType(sectionType);
            });
        });
        
        // Add item buttons
        const addBtns = this.container.querySelectorAll('.add-section-item-btn');
        addBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const sectionType = e.target.getAttribute('data-section-type');
                this.addSectionItem(sectionType);
            });
        });
        
        // Remove item buttons
        const removeBtns = this.container.querySelectorAll('.remove-item-btn');
        removeBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const index = parseInt(e.target.getAttribute('data-index'));
                this.removeSectionItem(this.currentSectionType, index);
            });
        });
        
        // Field changes
        const fields = this.container.querySelectorAll('.section-field');
        fields.forEach(field => {
            field.addEventListener('change', (e) => {
                const index = parseInt(e.target.getAttribute('data-index'));
                const fieldName = e.target.getAttribute('data-field');
                this.updateSectionItemField(this.currentSectionType, index, fieldName, e.target);
            });
        });
    }
    
    switchSectionType(sectionType) {
        this.currentSectionType = sectionType;
        this.render();
        this.setupEventListeners();
    }
    
    addSectionItem(sectionType) {
        const defaultItem = this.getDefaultItemForSectionType(sectionType);
        if (!this.data[sectionType]) {
            this.data[sectionType] = [];
        }
        this.data[sectionType].push(defaultItem);
        this.render();
        this.setupEventListeners();
        this.triggerChange();
    }
    
    removeSectionItem(sectionType, index) {
        if (this.data[sectionType] && index >= 0 && index < this.data[sectionType].length) {
            this.data[sectionType].splice(index, 1);
            this.render();
            this.setupEventListeners();
            this.triggerChange();
        }
    }
    
    updateSectionItemField(sectionType, index, fieldName, input) {
        if (!this.data[sectionType] || !this.data[sectionType][index]) {
            return;
        }
        
        let value = input.value;
        
        // Handle special field types
        if (fieldName === 'level' || fieldName === 'required') {
            value = fieldName === 'level' ? parseInt(value) || 1 : input.checked;
        } else if (fieldName === 'functions' || fieldName === 'methods' || fieldName === 'dependencies') {
            value = value.split(',').map(s => s.trim()).filter(s => s);
        } else if (fieldName === 'props') {
            try {
                value = JSON.parse(value || '{}');
            } catch (e) {
                value = {};
            }
        }
        
        this.data[sectionType][index][fieldName] = value;
        this.triggerChange();
    }
    
    getDefaultItemForSectionType(sectionType) {
        const defaults = {
            'headings': { id: '', text: '', level: 1 },
            'subheadings': { id: '', text: '', level: 2 },
            'tabs': { id: '', label: '', content_ref: '' },
            'buttons': { id: '', label: '', action: '', variant: 'primary' },
            'input_boxes': { id: '', label: '', input_type: 'text', placeholder: '', required: false },
            'text_blocks': { id: '', content: '', format: 'markdown' },
            'components': { name: '', file_path: '', props: {} },
            'utilities': { name: '', file_path: '', functions: [] },
            'services': { name: '', file_path: '', methods: [] },
            'hooks': { name: '', file_path: '', dependencies: [] },
            'contexts': { name: '', file_path: '', provider: '' },
            'ui_components': { name: '', file_path: '', props: {} },
            'endpoints': { endpoint_id: '', endpoint_path: '', method: '', file_path: '' }
        };
        
        return defaults[sectionType] || {};
    }
    
    escapeHtml(text) {
        if (text === null || text === undefined) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    triggerChange() {
        const event = new CustomEvent('sections-change', {
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
    module.exports = SectionsEditor;
}
