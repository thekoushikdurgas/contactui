/**
 * Bulk Operations Component
 * 
 * Handles bulk selection and operations for dashboard lists
 */

class BulkOperations {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`Bulk operations container not found: ${containerId}`);
            return;
        }
        
        this.options = {
            onSelectionChange: options.onSelectionChange || null,
            onBulkAction: options.onBulkAction || null,
            selectAllText: options.selectAllText || 'Select All',
            selectedText: options.selectedText || 'selected',
            actions: options.actions || [],
            ...options
        };
        
        this.selectedItems = new Set();
        this.allItems = [];
        this.isSelectAll = false;
        
        this.init();
    }
    
    init() {
        this.createBulkBar();
        this.attachEventListeners();
    }
    
    /**
     * Create bulk operations bar
     */
    createBulkBar() {
        const bulkBar = document.createElement('div');
        bulkBar.className = 'bulk-operations-bar';
        bulkBar.id = `${this.container.id}-bulk-bar`;
        bulkBar.style.display = 'none';
        bulkBar.setAttribute('role', 'toolbar');
        bulkBar.setAttribute('aria-label', 'Bulk operations');
        
        bulkBar.innerHTML = `
            <div class="bulk-operations-info">
                <input type="checkbox" 
                       id="${this.container.id}-select-all" 
                       class="bulk-select-all"
                       aria-label="Select all items">
                <label for="${this.container.id}-select-all" class="bulk-select-all-label">
                    <span id="${this.container.id}-selected-count">0</span> ${this.options.selectedText}
                </label>
            </div>
            <div class="bulk-operations-actions">
                ${this.options.actions.map((action, index) => `
                    <button type="button" 
                            class="bulk-action-btn bulk-action-${action.type || 'default'}"
                            data-action="${action.id || index}"
                            aria-label="${action.label || action.text}">
                        ${action.icon || ''}
                        <span>${action.text}</span>
                    </button>
                `).join('')}
            </div>
        `;
        
        // Insert before container
        this.container.parentNode.insertBefore(bulkBar, this.container);
        this.bulkBar = bulkBar;
        this.selectAllCheckbox = bulkBar.querySelector('.bulk-select-all');
        this.selectedCountSpan = bulkBar.querySelector(`#${this.container.id}-selected-count`);
    }
    
    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Select all checkbox
        if (this.selectAllCheckbox) {
            this.selectAllCheckbox.addEventListener('change', (e) => {
                this.toggleSelectAll(e.target.checked);
            });
        }
        
        // Bulk action buttons
        this.bulkBar.querySelectorAll('.bulk-action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const actionId = e.currentTarget.getAttribute('data-action');
                this.handleBulkAction(actionId);
            });
        });
    }
    
    /**
     * Register items for bulk selection
     */
    registerItem(itemId, itemElement) {
        this.allItems.push({ id: itemId, element: itemElement });
        
        // Add checkbox to item if not present
        if (!itemElement.querySelector('.bulk-item-checkbox')) {
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'bulk-item-checkbox';
            checkbox.value = itemId;
            checkbox.setAttribute('aria-label', `Select item ${itemId}`);
            checkbox.addEventListener('change', (e) => {
                this.toggleItem(itemId, e.target.checked);
            });
            
            // Insert at beginning of item
            itemElement.insertBefore(checkbox, itemElement.firstChild);
        }
    }
    
    /**
     * Toggle item selection
     */
    toggleItem(itemId, selected) {
        if (selected) {
            this.selectedItems.add(itemId);
        } else {
            this.selectedItems.delete(itemId);
            this.isSelectAll = false;
            if (this.selectAllCheckbox) {
                this.selectAllCheckbox.checked = false;
                this.selectAllCheckbox.indeterminate = false;
            }
        }
        
        this.updateBulkBar();
        
        if (this.options.onSelectionChange) {
            this.options.onSelectionChange(Array.from(this.selectedItems), this);
        }
    }
    
    /**
     * Toggle select all
     */
    toggleSelectAll(selectAll) {
        this.isSelectAll = selectAll;
        this.selectedItems.clear();
        
        if (selectAll) {
            this.allItems.forEach(item => {
                this.selectedItems.add(item.id);
                const checkbox = item.element.querySelector('.bulk-item-checkbox');
                if (checkbox) {
                    checkbox.checked = true;
                }
            });
        } else {
            this.allItems.forEach(item => {
                const checkbox = item.element.querySelector('.bulk-item-checkbox');
                if (checkbox) {
                    checkbox.checked = false;
                }
            });
        }
        
        this.updateBulkBar();
        
        if (this.options.onSelectionChange) {
            this.options.onSelectionChange(Array.from(this.selectedItems), this);
        }
    }
    
    /**
     * Update bulk bar visibility and state
     */
    updateBulkBar() {
        const count = this.selectedItems.size;
        
        if (count > 0) {
            this.bulkBar.style.display = 'flex';
            this.selectedCountSpan.textContent = count;
            
            // Update select all checkbox state
            if (this.selectAllCheckbox) {
                if (count === this.allItems.length) {
                    this.selectAllCheckbox.checked = true;
                    this.selectAllCheckbox.indeterminate = false;
                } else if (count > 0) {
                    this.selectAllCheckbox.checked = false;
                    this.selectAllCheckbox.indeterminate = true;
                } else {
                    this.selectAllCheckbox.checked = false;
                    this.selectAllCheckbox.indeterminate = false;
                }
            }
        } else {
            this.bulkBar.style.display = 'none';
        }
    }
    
    /**
     * Handle bulk action
     */
    handleBulkAction(actionId) {
        const action = this.options.actions.find(a => (a.id || '') === actionId);
        if (!action) {
            console.error(`Bulk action not found: ${actionId}`);
            return;
        }
        
        const selectedIds = Array.from(this.selectedItems);
        
        if (selectedIds.length === 0) {
            if (window.accessibilityManager) {
                window.accessibilityManager.announceError('No items selected');
            }
            return;
        }
        
        // Confirm if required
        if (action.confirm) {
            const confirmed = confirm(action.confirm.replace('{count}', selectedIds.length));
            if (!confirmed) {
                return;
            }
        }
        
        // Call action handler
        if (action.handler) {
            action.handler(selectedIds, this);
        } else if (this.options.onBulkAction) {
            this.options.onBulkAction(actionId, selectedIds, this);
        }
    }
    
    /**
     * Clear selection
     */
    clearSelection() {
        this.selectedItems.clear();
        this.isSelectAll = false;
        
        this.allItems.forEach(item => {
            const checkbox = item.element.querySelector('.bulk-item-checkbox');
            if (checkbox) {
                checkbox.checked = false;
            }
        });
        
        if (this.selectAllCheckbox) {
            this.selectAllCheckbox.checked = false;
            this.selectAllCheckbox.indeterminate = false;
        }
        
        this.updateBulkBar();
    }
    
    /**
     * Get selected items
     */
    getSelectedItems() {
        return Array.from(this.selectedItems);
    }
    
    /**
     * Get selected count
     */
    getSelectedCount() {
        return this.selectedItems.size;
    }
}

// Export for global use
window.BulkOperations = BulkOperations;
