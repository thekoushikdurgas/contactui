/**
 * JSON Tree Editor Component
 * 
 * Provides a collapsible tree structure for editing nested JSON with:
 * - Inline editing for all value types
 * - Add/remove for objects and arrays
 * - Drag-and-drop reordering
 * - Search and filter functionality
 * - Syntax highlighting
 */

class JSONTreeEditor {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.options = {
            data: options.data || {},
            readOnly: options.readOnly || false,
            showRoot: options.showRoot !== false,
            searchEnabled: options.searchEnabled !== false,
            ...options
        };
        this.data = this.options.data;
        this.searchTerm = '';
        this.expandedPaths = new Set(['root']);
        
        if (!this.container) {
            throw new Error('Container element not found');
        }
        
        this.init();
    }
    
    init() {
        this.container.innerHTML = '';
        this.container.classList.add('json-tree-editor');
        
        // Add search bar if enabled
        if (this.options.searchEnabled) {
            this.renderSearchBar();
        }
        
        // Render tree
        this.treeContainer = document.createElement('div');
        this.treeContainer.className = 'json-tree-container';
        this.container.appendChild(this.treeContainer);
        
        this.render();
    }
    
    renderSearchBar() {
        const searchBar = document.createElement('div');
        searchBar.className = 'json-tree-search';
        searchBar.innerHTML = `
            <input type="text" 
                   class="json-tree-search-input" 
                   placeholder="Search in JSON..." 
                   value="${this.searchTerm}">
            <button class="json-tree-search-clear" title="Clear search">×</button>
        `;
        
        const input = searchBar.querySelector('.json-tree-search-input');
        const clearBtn = searchBar.querySelector('.json-tree-search-clear');
        
        input.addEventListener('input', (e) => {
            this.searchTerm = e.target.value.toLowerCase();
            this.render();
        });
        
        clearBtn.addEventListener('click', () => {
            input.value = '';
            this.searchTerm = '';
            this.render();
        });
        
        this.container.appendChild(searchBar);
    }
    
    render() {
        this.treeContainer.innerHTML = '';
        
        if (this.options.showRoot) {
            const rootNode = this.createNode('root', this.data, 'root', 0);
            this.treeContainer.appendChild(rootNode);
        } else {
            // Render children directly
            if (Array.isArray(this.data)) {
                this.data.forEach((item, index) => {
                    const node = this.createNode(index, item, `root[${index}]`, 0);
                    this.treeContainer.appendChild(node);
                });
            } else if (typeof this.data === 'object' && this.data !== null) {
                Object.keys(this.data).forEach(key => {
                    const node = this.createNode(key, this.data[key], `root.${key}`, 0);
                    this.treeContainer.appendChild(node);
                });
            }
        }
    }
    
    createNode(key, value, path, depth) {
        const node = document.createElement('div');
        node.className = 'json-tree-node';
        node.dataset.path = path;
        node.dataset.depth = depth;
        
        const isExpanded = this.expandedPaths.has(path);
        const isObject = typeof value === 'object' && value !== null && !Array.isArray(value);
        const isArray = Array.isArray(value);
        const isComplex = isObject || isArray;
        
        // Check if matches search
        const matchesSearch = !this.searchTerm || 
            key.toLowerCase().includes(this.searchTerm) ||
            (typeof value === 'string' && value.toLowerCase().includes(this.searchTerm));
        
        if (!matchesSearch && isComplex) {
            // Check children
            const childrenMatch = this.searchInValue(value, this.searchTerm);
            if (!childrenMatch) {
                node.style.display = 'none';
            }
        }
        
        const nodeContent = document.createElement('div');
        nodeContent.className = 'json-tree-node-content';
        
        // Expand/collapse button for complex types
        if (isComplex) {
            const expandBtn = document.createElement('button');
            expandBtn.className = `json-tree-expand ${isExpanded ? 'expanded' : ''}`;
            expandBtn.innerHTML = isExpanded ? '▼' : '▶';
            expandBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleExpand(path);
            });
            nodeContent.appendChild(expandBtn);
        } else {
            const spacer = document.createElement('span');
            spacer.className = 'json-tree-spacer';
            nodeContent.appendChild(spacer);
        }
        
        // Key display/editor
        const keyElement = this.createKeyElement(key, path, depth);
        nodeContent.appendChild(keyElement);
        
        // Value display/editor
        const valueElement = this.createValueElement(value, path, depth);
        nodeContent.appendChild(valueElement);
        
        // Actions (add, remove, etc.)
        if (!this.options.readOnly) {
            const actions = this.createActions(path, isComplex);
            nodeContent.appendChild(actions);
        }
        
        node.appendChild(nodeContent);
        
        // Children (if expanded and complex)
        if (isComplex && isExpanded) {
            const childrenContainer = document.createElement('div');
            childrenContainer.className = 'json-tree-children';
            
            if (isArray) {
                value.forEach((item, index) => {
                    const childPath = `${path}[${index}]`;
                    const childNode = this.createNode(index, item, childPath, depth + 1);
                    childrenContainer.appendChild(childNode);
                });
                
                // Add item button
                if (!this.options.readOnly) {
                    const addBtn = document.createElement('button');
                    addBtn.className = 'json-tree-add-item';
                    addBtn.textContent = '+ Add Item';
                    addBtn.addEventListener('click', () => {
                        this.addArrayItem(path);
                    });
                    childrenContainer.appendChild(addBtn);
                }
            } else if (isObject) {
                Object.keys(value).forEach(childKey => {
                    const childPath = `${path}.${childKey}`;
                    const childNode = this.createNode(childKey, value[childKey], childPath, depth + 1);
                    childrenContainer.appendChild(childNode);
                });
                
                // Add property button
                if (!this.options.readOnly) {
                    const addBtn = document.createElement('button');
                    addBtn.className = 'json-tree-add-property';
                    addBtn.textContent = '+ Add Property';
                    addBtn.addEventListener('click', () => {
                        this.addObjectProperty(path);
                    });
                    childrenContainer.appendChild(addBtn);
                }
            }
            
            node.appendChild(childrenContainer);
        }
        
        return node;
    }
    
    createKeyElement(key, path, depth) {
        const keySpan = document.createElement('span');
        keySpan.className = 'json-tree-key';
        keySpan.textContent = typeof key === 'number' ? `[${key}]` : `${key}:`;
        keySpan.style.paddingLeft = `${depth * 20}px`;
        return keySpan;
    }
    
    createValueElement(value, path, depth) {
        const valueSpan = document.createElement('span');
        valueSpan.className = 'json-tree-value';
        
        if (this.options.readOnly) {
            valueSpan.textContent = this.formatValue(value);
            valueSpan.classList.add('readonly');
        } else {
            // Create editable input based on type
            if (typeof value === 'string') {
                const input = document.createElement('input');
                input.type = 'text';
                input.value = value;
                input.className = 'json-tree-input';
                input.addEventListener('change', (e) => {
                    this.updateValue(path, e.target.value);
                });
                valueSpan.appendChild(input);
            } else if (typeof value === 'number') {
                const input = document.createElement('input');
                input.type = 'number';
                input.value = value;
                input.className = 'json-tree-input';
                input.addEventListener('change', (e) => {
                    this.updateValue(path, parseFloat(e.target.value));
                });
                valueSpan.appendChild(input);
            } else if (typeof value === 'boolean') {
                const select = document.createElement('select');
                select.className = 'json-tree-select';
                select.innerHTML = '<option value="true">true</option><option value="false">false</option>';
                select.value = value.toString();
                select.addEventListener('change', (e) => {
                    this.updateValue(path, e.target.value === 'true');
                });
                valueSpan.appendChild(select);
            } else if (value === null) {
                valueSpan.textContent = 'null';
                valueSpan.classList.add('json-null');
            } else {
                // Complex type - show type indicator
                const typeIndicator = document.createElement('span');
                typeIndicator.className = 'json-tree-type';
                if (Array.isArray(value)) {
                    typeIndicator.textContent = `Array[${value.length}]`;
                } else {
                    typeIndicator.textContent = `Object{${Object.keys(value).length}}`;
                }
                valueSpan.appendChild(typeIndicator);
            }
        }
        
        return valueSpan;
    }
    
    createActions(path, isComplex) {
        const actions = document.createElement('div');
        actions.className = 'json-tree-actions';
        
        if (isComplex) {
            // Add child button
            const addBtn = document.createElement('button');
            addBtn.className = 'json-tree-action-add';
            addBtn.textContent = '+';
            addBtn.title = 'Add child';
            addBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (Array.isArray(this.getValue(path))) {
                    this.addArrayItem(path);
                } else {
                    this.addObjectProperty(path);
                }
            });
            actions.appendChild(addBtn);
        }
        
        // Remove button (not for root)
        if (path !== 'root') {
            const removeBtn = document.createElement('button');
            removeBtn.className = 'json-tree-action-remove';
            removeBtn.textContent = '×';
            removeBtn.title = 'Remove';
            removeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.removeValue(path);
            });
            actions.appendChild(removeBtn);
        }
        
        return actions;
    }
    
    formatValue(value) {
        if (value === null) return 'null';
        if (typeof value === 'string') return `"${value}"`;
        if (Array.isArray(value)) return `Array[${value.length}]`;
        if (typeof value === 'object') return `Object{${Object.keys(value).length}}`;
        return String(value);
    }
    
    toggleExpand(path) {
        if (this.expandedPaths.has(path)) {
            this.expandedPaths.delete(path);
        } else {
            this.expandedPaths.add(path);
        }
        this.render();
    }
    
    getValue(path) {
        const parts = path.split(/[\.\[\]]+/).filter(p => p && p !== 'root');
        let value = this.data;
        for (const part of parts) {
            if (value === undefined || value === null) return undefined;
            value = value[part];
        }
        return value;
    }
    
    setValue(path, newValue) {
        const parts = path.split(/[\.\[\]]+/).filter(p => p && p !== 'root');
        let target = this.data;
        
        for (let i = 0; i < parts.length - 1; i++) {
            const part = parts[i];
            if (target[part] === undefined) {
                target[part] = {};
            }
            target = target[part];
        }
        
        const lastPart = parts[parts.length - 1];
        if (lastPart) {
            target[lastPart] = newValue;
        } else {
            this.data = newValue;
        }
        
        this.render();
        this.triggerChange();
    }
    
    updateValue(path, newValue) {
        this.setValue(path, newValue);
    }
    
    addArrayItem(path) {
        const array = this.getValue(path);
        if (!Array.isArray(array)) return;
        
        array.push(null);
        this.render();
        this.triggerChange();
    }
    
    addObjectProperty(path) {
        const obj = this.getValue(path);
        if (typeof obj !== 'object' || Array.isArray(obj) || obj === null) return;
        
        const newKey = prompt('Enter property name:');
        if (newKey) {
            obj[newKey] = null;
            this.render();
            this.triggerChange();
        }
    }
    
    removeValue(path) {
        if (path === 'root') return;
        
        const parts = path.split(/[\.\[\]]+/).filter(p => p && p !== 'root');
        let target = this.data;
        
        for (let i = 0; i < parts.length - 1; i++) {
            target = target[parts[i]];
        }
        
        const lastPart = parts[parts.length - 1];
        if (Array.isArray(target)) {
            target.splice(parseInt(lastPart), 1);
        } else {
            delete target[lastPart];
        }
        
        this.render();
        this.triggerChange();
    }
    
    searchInValue(value, searchTerm) {
        if (!searchTerm) return true;
        
        if (typeof value === 'string') {
            return value.toLowerCase().includes(searchTerm);
        }
        
        if (Array.isArray(value)) {
            return value.some(item => this.searchInValue(item, searchTerm));
        }
        
        if (typeof value === 'object' && value !== null) {
            return Object.values(value).some(item => this.searchInValue(item, searchTerm));
        }
        
        return false;
    }
    
    getData() {
        return this.data;
    }
    
    setData(data) {
        this.data = data;
        this.render();
    }
    
    triggerChange() {
        const event = new CustomEvent('json-tree-change', {
            detail: { data: this.data }
        });
        this.container.dispatchEvent(event);
    }
    
    expandAll() {
        this.expandRecursive(this.data, 'root');
        this.render();
    }
    
    collapseAll() {
        this.expandedPaths.clear();
        this.expandedPaths.add('root');
        this.render();
    }
    
    expandRecursive(value, path) {
        this.expandedPaths.add(path);
        
        if (Array.isArray(value)) {
            value.forEach((item, index) => {
                this.expandRecursive(item, `${path}[${index}]`);
            });
        } else if (typeof value === 'object' && value !== null) {
            Object.keys(value).forEach(key => {
                this.expandRecursive(value[key], `${path}.${key}`);
            });
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = JSONTreeEditor;
}
