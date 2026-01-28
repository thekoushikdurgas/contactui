/**
 * Access Control Editor Component
 * 
 * Provides a visual matrix editor for AccessControl with:
 * - Roles × Permissions matrix
 * - Checkboxes for can_view, can_edit, can_delete
 * - Restricted components editor for each role
 * - Default values based on role hierarchy
 */

class AccessControlEditor {
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
        
        this.roles = ['super_admin', 'admin', 'pro_user', 'free_user', 'guest'];
        this.permissions = ['can_view', 'can_edit', 'can_delete'];
        this.data = this.initializeData(this.options.data);
        this.init();
    }
    
    initializeData(initialData) {
        if (!initialData || typeof initialData !== 'object') {
            // Default access control
            return {
                super_admin: { can_view: true, can_edit: true, can_delete: true, restricted_components: [] },
                admin: { can_view: true, can_edit: true, can_delete: false, restricted_components: [] },
                pro_user: { can_view: true, can_edit: false, can_delete: false, restricted_components: [] },
                free_user: { can_view: true, can_edit: false, can_delete: false, restricted_components: [] },
                guest: { can_view: false, can_edit: false, can_delete: false, restricted_components: [] }
            };
        }
        
        // Ensure all roles exist with defaults
        const data = {};
        this.roles.forEach(role => {
            if (initialData[role]) {
                data[role] = {
                    can_view: initialData[role].can_view !== undefined ? initialData[role].can_view : true,
                    can_edit: initialData[role].can_edit !== undefined ? initialData[role].can_edit : false,
                    can_delete: initialData[role].can_delete !== undefined ? initialData[role].can_delete : false,
                    restricted_components: Array.isArray(initialData[role].restricted_components) 
                        ? [...initialData[role].restricted_components] 
                        : []
                };
            } else {
                // Set defaults based on role hierarchy
                if (role === 'super_admin') {
                    data[role] = { can_view: true, can_edit: true, can_delete: true, restricted_components: [] };
                } else if (role === 'admin') {
                    data[role] = { can_view: true, can_edit: true, can_delete: false, restricted_components: [] };
                } else if (role === 'guest') {
                    data[role] = { can_view: false, can_edit: false, can_delete: false, restricted_components: [] };
                } else {
                    data[role] = { can_view: true, can_edit: false, can_delete: false, restricted_components: [] };
                }
            }
        });
        
        return data;
    }
    
    init() {
        this.container.innerHTML = '';
        this.container.classList.add('access-control-editor');
        this.render();
        this.setupEventListeners();
    }
    
    render() {
        const html = `
            <div class="access-control-matrix">
                <div class="mb-4">
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">Access Control Matrix</h3>
                    <p class="text-sm text-gray-600 dark:text-gray-400">Configure permissions for each user role</p>
                </div>
                
                <!-- Matrix Table -->
                <div class="overflow-x-auto">
                    <table class="w-full border-collapse border border-gray-300 dark:border-gray-600">
                        <thead>
                            <tr class="bg-gray-100 dark:bg-gray-800">
                                <th class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-left text-sm font-semibold text-gray-900 dark:text-gray-100">Role</th>
                                <th class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-center text-sm font-semibold text-gray-900 dark:text-gray-100">View</th>
                                <th class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-center text-sm font-semibold text-gray-900 dark:text-gray-100">Edit</th>
                                <th class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-center text-sm font-semibold text-gray-900 dark:text-gray-100">Delete</th>
                                <th class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-left text-sm font-semibold text-gray-900 dark:text-gray-100">Restricted Components</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${this.roles.map(role => this.renderRoleRow(role)).join('')}
                        </tbody>
                    </table>
                </div>
                
                <!-- Restricted Components Details (Collapsible) -->
                <div class="mt-6">
                    <button 
                        type="button"
                        class="toggle-restricted-details w-full text-left px-4 py-2 bg-gray-100 dark:bg-gray-800 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                    >
                        <span class="font-semibold text-gray-900 dark:text-gray-100">Restricted Components Details</span>
                        <span class="float-right">▼</span>
                    </button>
                    <div class="restricted-details-content hidden mt-4 space-y-4">
                        ${this.roles.map(role => this.renderRestrictedComponents(role)).join('')}
                    </div>
                </div>
            </div>
        `;
        
        this.container.innerHTML = html;
    }
    
    renderRoleRow(role) {
        const roleData = this.data[role] || {};
        const roleLabel = this.formatRoleLabel(role);
        
        return `
            <tr class="hover:bg-gray-50 dark:hover:bg-gray-800">
                <td class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm font-medium text-gray-900 dark:text-gray-100">
                    ${roleLabel}
                </td>
                <td class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-center">
                    <input 
                        type="checkbox" 
                        class="permission-checkbox w-5 h-5 text-blue-600 rounded border-gray-300 dark:border-gray-600"
                        data-role="${role}"
                        data-permission="can_view"
                        ${roleData.can_view ? 'checked' : ''}
                        ${this.options.readOnly ? 'disabled' : ''}
                    />
                </td>
                <td class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-center">
                    <input 
                        type="checkbox" 
                        class="permission-checkbox w-5 h-5 text-blue-600 rounded border-gray-300 dark:border-gray-600"
                        data-role="${role}"
                        data-permission="can_edit"
                        ${roleData.can_edit ? 'checked' : ''}
                        ${this.options.readOnly ? 'disabled' : ''}
                    />
                </td>
                <td class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-center">
                    <input 
                        type="checkbox" 
                        class="permission-checkbox w-5 h-5 text-blue-600 rounded border-gray-300 dark:border-gray-600"
                        data-role="${role}"
                        data-permission="can_delete"
                        ${roleData.can_delete ? 'checked' : ''}
                        ${this.options.readOnly ? 'disabled' : ''}
                    />
                </td>
                <td class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm text-gray-700 dark:text-gray-300">
                    ${(roleData.restricted_components || []).length > 0 
                        ? `${roleData.restricted_components.length} component(s)` 
                        : 'None'}
                </td>
            </tr>
        `;
    }
    
    renderRestrictedComponents(role) {
        const roleData = this.data[role] || {};
        const components = roleData.restricted_components || [];
        const roleLabel = this.formatRoleLabel(role);
        
        return `
            <div class="restricted-components-section bg-gray-50 dark:bg-gray-800 rounded-lg p-4" data-role="${role}">
                <h4 class="text-md font-semibold text-gray-900 dark:text-gray-100 mb-3">${roleLabel} - Restricted Components</h4>
                <div class="restricted-components-list space-y-2">
                    ${components.length === 0 ? `
                        <p class="text-gray-500 dark:text-gray-400 text-sm">No restricted components</p>
                    ` : components.map((component, index) => `
                        <div class="flex items-center gap-2 restricted-component-item" data-index="${index}">
                            <input 
                                type="text" 
                                value="${this.escapeHtml(component)}"
                                ${this.options.readOnly ? 'readonly' : ''}
                                class="restricted-component-input flex-1 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm"
                                placeholder="Component name"
                                data-role="${role}"
                                data-index="${index}"
                            />
                            ${!this.options.readOnly ? `
                                <button 
                                    type="button" 
                                    class="remove-component-btn px-3 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm"
                                    data-role="${role}"
                                    data-index="${index}"
                                >
                                    Remove
                                </button>
                            ` : ''}
                        </div>
                    `).join('')}
                </div>
                ${!this.options.readOnly ? `
                    <button 
                        type="button" 
                        class="add-component-btn mt-3 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
                        data-role="${role}"
                    >
                        + Add Component
                    </button>
                ` : ''}
            </div>
        `;
    }
    
    setupEventListeners() {
        if (this.options.readOnly) return;
        
        // Permission checkboxes
        const checkboxes = this.container.querySelectorAll('.permission-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const role = e.target.getAttribute('data-role');
                const permission = e.target.getAttribute('data-permission');
                this.updatePermission(role, permission, e.target.checked);
            });
        });
        
        // Toggle restricted details
        const toggleBtn = this.container.querySelector('.toggle-restricted-details');
        const detailsContent = this.container.querySelector('.restricted-details-content');
        if (toggleBtn && detailsContent) {
            toggleBtn.addEventListener('click', () => {
                detailsContent.classList.toggle('hidden');
                const arrow = toggleBtn.querySelector('span:last-child');
                if (arrow) {
                    arrow.textContent = detailsContent.classList.contains('hidden') ? '▼' : '▲';
                }
            });
        }
        
        // Add component buttons
        const addBtns = this.container.querySelectorAll('.add-component-btn');
        addBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const role = e.target.getAttribute('data-role');
                this.addRestrictedComponent(role);
            });
        });
        
        // Remove component buttons
        const removeBtns = this.container.querySelectorAll('.remove-component-btn');
        removeBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const role = e.target.getAttribute('data-role');
                const index = parseInt(e.target.getAttribute('data-index'));
                this.removeRestrictedComponent(role, index);
            });
        });
        
        // Restricted component input changes
        const componentInputs = this.container.querySelectorAll('.restricted-component-input');
        componentInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                const role = e.target.getAttribute('data-role');
                const index = parseInt(e.target.getAttribute('data-index'));
                this.updateRestrictedComponent(role, index, e.target.value);
            });
        });
    }
    
    updatePermission(role, permission, value) {
        if (!this.data[role]) {
            this.data[role] = { can_view: false, can_edit: false, can_delete: false, restricted_components: [] };
        }
        this.data[role][permission] = value;
        this.triggerChange();
    }
    
    addRestrictedComponent(role) {
        if (!this.data[role]) {
            this.data[role] = { can_view: false, can_edit: false, can_delete: false, restricted_components: [] };
        }
        if (!this.data[role].restricted_components) {
            this.data[role].restricted_components = [];
        }
        this.data[role].restricted_components.push('');
        this.render();
        this.setupEventListeners();
        
        // Focus on the new input
        const section = this.container.querySelector(`.restricted-components-section[data-role="${role}"]`);
        if (section) {
            const inputs = section.querySelectorAll('.restricted-component-input');
            if (inputs.length > 0) {
                inputs[inputs.length - 1].focus();
            }
        }
    }
    
    removeRestrictedComponent(role, index) {
        if (this.data[role] && this.data[role].restricted_components && index >= 0 && index < this.data[role].restricted_components.length) {
            this.data[role].restricted_components.splice(index, 1);
            this.render();
            this.setupEventListeners();
            this.triggerChange();
        }
    }
    
    updateRestrictedComponent(role, index, value) {
        if (this.data[role] && this.data[role].restricted_components && index >= 0 && index < this.data[role].restricted_components.length) {
            this.data[role].restricted_components[index] = value.trim();
            this.triggerChange();
        }
    }
    
    formatRoleLabel(role) {
        return role
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }
    
    escapeHtml(text) {
        if (text === null || text === undefined) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    triggerChange() {
        const event = new CustomEvent('access-control-change', {
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
    module.exports = AccessControlEditor;
}
