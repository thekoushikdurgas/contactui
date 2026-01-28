/**
 * Form Field Builder Component
 * 
 * Dynamically generates form fields from Lambda API schemas with support for:
 * - All field types (string, number, boolean, object, array, enum)
 * - Custom components for complex types
 * - Field grouping and sections
 * - Conditional field display
 */

class FormFieldBuilder {
    constructor(container, schema, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.schema = schema;
        this.options = {
            data: options.data || {},
            readOnly: options.readOnly || false,
            showLabels: options.showLabels !== false,
            ...options
        };
        this.data = this.options.data;
        this.fields = {};
        
        if (!this.container) {
            throw new Error('Container element not found');
        }
        
        this.init();
    }
    
    init() {
        this.container.innerHTML = '';
        this.container.classList.add('form-field-builder');
        this.render();
    }
    
    render() {
        if (!this.schema || !this.schema.examples) {
            this.container.innerHTML = '<p>No schema available</p>';
            return;
        }
        
        // Get create example as template
        const createExample = this.schema.examples.create || this.schema.examples.update || {};
        this.renderFields(createExample, this.data, 'root');
    }
    
    renderFields(schemaFields, data, prefix) {
        Object.keys(schemaFields).forEach(key => {
            const fieldPath = prefix === 'root' ? key : `${prefix}.${key}`;
            const fieldValue = this.getValue(data, fieldPath);
            const fieldSchema = schemaFields[key];
            
            const fieldElement = this.createField(key, fieldSchema, fieldValue, fieldPath);
            this.container.appendChild(fieldElement);
            this.fields[fieldPath] = fieldElement;
        });
    }
    
    createField(key, schema, value, path) {
        const fieldWrapper = document.createElement('div');
        fieldWrapper.className = 'form-field-wrapper';
        fieldWrapper.dataset.path = path;
        
        // Determine field type
        const fieldType = this.determineFieldType(schema, value);
        
        // Create label
        if (this.options.showLabels) {
            const label = document.createElement('label');
            label.className = 'form-field-label';
            label.textContent = this.formatLabel(key);
            label.setAttribute('for', `field-${path.replace(/\./g, '-')}`);
            fieldWrapper.appendChild(label);
        }
        
        // Create input based on type
        const input = this.createInput(fieldType, key, schema, value, path);
        fieldWrapper.appendChild(input);
        
        // Add help text if available
        if (schema.description) {
            const helpText = document.createElement('small');
            helpText.className = 'form-field-help';
            helpText.textContent = schema.description;
            fieldWrapper.appendChild(helpText);
        }
        
        return fieldWrapper;
    }
    
    determineFieldType(schema, value) {
        if (Array.isArray(value) || (schema && Array.isArray(schema))) {
            return 'array';
        }
        if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
            return 'object';
        }
        if (typeof value === 'boolean') {
            return 'boolean';
        }
        if (typeof value === 'number') {
            return 'number';
        }
        if (schema && schema.enum) {
            return 'enum';
        }
        if (schema && schema.type === 'date' || (typeof value === 'string' && this.isDateString(value))) {
            return 'date';
        }
        if (schema && (schema.format === 'code' || key.includes('operation') || key.includes('query'))) {
            return 'code';
        }
        return 'text';
    }
    
    createInput(type, key, schema, value, path) {
        const inputWrapper = document.createElement('div');
        inputWrapper.className = 'form-field-input-wrapper';
        
        let input;
        
        switch (type) {
            case 'text':
                input = this.createTextInput(key, value, path, schema);
                break;
            case 'number':
                input = this.createNumberInput(key, value, path, schema);
                break;
            case 'boolean':
                input = this.createBooleanInput(key, value, path);
                break;
            case 'enum':
                input = this.createSelectInput(key, value, path, schema);
                break;
            case 'date':
                input = this.createDateInput(key, value, path);
                break;
            case 'code':
                input = this.createCodeInput(key, value, path);
                break;
            case 'array':
                input = this.createArrayInput(key, value, path, schema);
                break;
            case 'object':
                input = this.createObjectInput(key, value, path, schema);
                break;
            default:
                input = this.createTextInput(key, value, path, schema);
        }
        
        inputWrapper.appendChild(input);
        return inputWrapper;
    }
    
    createTextInput(key, value, path, schema) {
        const input = document.createElement('input');
        input.type = 'text';
        input.id = `field-${path.replace(/\./g, '-')}`;
        input.name = path;
        input.value = value || '';
        input.className = 'form-field-input form-field-text';
        input.placeholder = schema?.placeholder || `Enter ${key}`;
        input.readOnly = this.options.readOnly;
        
        if (!this.options.readOnly) {
            input.addEventListener('change', (e) => {
                this.updateValue(path, e.target.value);
            });
        }
        
        return input;
    }
    
    createNumberInput(key, value, path, schema) {
        const input = document.createElement('input');
        input.type = 'number';
        input.id = `field-${path.replace(/\./g, '-')}`;
        input.name = path;
        input.value = value || 0;
        input.className = 'form-field-input form-field-number';
        input.readOnly = this.options.readOnly;
        
        if (schema?.min !== undefined) {
            input.min = schema.min;
        }
        if (schema?.max !== undefined) {
            input.max = schema.max;
        }
        
        if (!this.options.readOnly) {
            input.addEventListener('change', (e) => {
                this.updateValue(path, parseFloat(e.target.value) || 0);
            });
        }
        
        return input;
    }
    
    createBooleanInput(key, value, path) {
        const input = document.createElement('input');
        input.type = 'checkbox';
        input.id = `field-${path.replace(/\./g, '-')}`;
        input.name = path;
        input.checked = value || false;
        input.className = 'form-field-input form-field-checkbox';
        input.disabled = this.options.readOnly;
        
        if (!this.options.readOnly) {
            input.addEventListener('change', (e) => {
                this.updateValue(path, e.target.checked);
            });
        }
        
        return input;
    }
    
    createSelectInput(key, value, path, schema) {
        const select = document.createElement('select');
        select.id = `field-${path.replace(/\./g, '-')}`;
        select.name = path;
        select.className = 'form-field-input form-field-select';
        select.disabled = this.options.readOnly;
        
        const options = schema.enum || [];
        options.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option;
            optionElement.textContent = option;
            if (value === option) {
                optionElement.selected = true;
            }
            select.appendChild(optionElement);
        });
        
        if (!this.options.readOnly) {
            select.addEventListener('change', (e) => {
                this.updateValue(path, e.target.value);
            });
        }
        
        return select;
    }
    
    createDateInput(key, value, path) {
        const input = document.createElement('input');
        input.type = 'datetime-local';
        input.id = `field-${path.replace(/\./g, '-')}`;
        input.name = path;
        input.className = 'form-field-input form-field-date';
        input.readOnly = this.options.readOnly;
        
        // Convert ISO string to datetime-local format
        if (value) {
            const date = new Date(value);
            if (!isNaN(date.getTime())) {
                input.value = date.toISOString().slice(0, 16);
            }
        }
        
        if (!this.options.readOnly) {
            input.addEventListener('change', (e) => {
                const date = new Date(e.target.value);
                this.updateValue(path, date.toISOString());
            });
        }
        
        return input;
    }
    
    createCodeInput(key, value, path) {
        const textarea = document.createElement('textarea');
        textarea.id = `field-${path.replace(/\./g, '-')}`;
        textarea.name = path;
        textarea.value = value || '';
        textarea.className = 'form-field-input form-field-code';
        textarea.rows = 10;
        textarea.readOnly = this.options.readOnly;
        textarea.style.fontFamily = 'monospace';
        
        if (!this.options.readOnly) {
            textarea.addEventListener('change', (e) => {
                this.updateValue(path, e.target.value);
            });
        }
        
        return textarea;
    }
    
    createArrayInput(key, value, path, schema) {
        const arrayWrapper = document.createElement('div');
        arrayWrapper.className = 'form-field-array';
        
        const arrayItems = Array.isArray(value) ? value : [];
        
        arrayItems.forEach((item, index) => {
            const itemWrapper = document.createElement('div');
            itemWrapper.className = 'form-field-array-item';
            itemWrapper.dataset.index = index;
            
            const itemInput = this.createInput(
                this.determineFieldType(schema?.[0], item),
                `${key}[${index}]`,
                schema?.[0] || {},
                item,
                `${path}[${index}]`
            );
            itemWrapper.appendChild(itemInput);
            
            if (!this.options.readOnly) {
                const removeBtn = document.createElement('button');
                removeBtn.type = 'button';
                removeBtn.className = 'form-field-array-remove';
                removeBtn.textContent = '×';
                removeBtn.addEventListener('click', () => {
                    this.removeArrayItem(path, index);
                });
                itemWrapper.appendChild(removeBtn);
            }
            
            arrayWrapper.appendChild(itemWrapper);
        });
        
        if (!this.options.readOnly) {
            const addBtn = document.createElement('button');
            addBtn.type = 'button';
            addBtn.className = 'form-field-array-add';
            addBtn.textContent = '+ Add Item';
            addBtn.addEventListener('click', () => {
                this.addArrayItem(path, schema);
            });
            arrayWrapper.appendChild(addBtn);
        }
        
        return arrayWrapper;
    }
    
    createObjectInput(key, value, path, schema) {
        const objectWrapper = document.createElement('div');
        objectWrapper.className = 'form-field-object';
        
        const objectValue = value || {};
        const objectSchema = schema || {};
        
        Object.keys(objectSchema).forEach(subKey => {
            const subField = this.createField(
                subKey,
                objectSchema[subKey],
                objectValue[subKey] || null,
                `${path}.${subKey}`
            );
            objectWrapper.appendChild(subField);
        });
        
        return objectWrapper;
    }
    
    formatLabel(key) {
        return key
            .replace(/_/g, ' ')
            .replace(/([A-Z])/g, ' $1')
            .replace(/^./, str => str.toUpperCase())
            .trim();
    }
    
    getValue(data, path) {
        const parts = path.split(/[\.\[\]]+/).filter(p => p && p !== 'root');
        let value = data;
        for (const part of parts) {
            if (value === undefined || value === null) return undefined;
            value = value[part];
        }
        return value;
    }
    
    updateValue(path, newValue) {
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
        
        this.triggerChange();
    }
    
    addArrayItem(path, schema) {
        const array = this.getValue(this.data, path) || [];
        const itemSchema = schema?.[0] || {};
        const defaultValue = this.getDefaultValue(itemSchema);
        array.push(defaultValue);
        this.updateValue(path, array);
        this.render();
    }
    
    removeArrayItem(path, index) {
        const array = this.getValue(this.data, path) || [];
        array.splice(index, 1);
        this.updateValue(path, array);
        this.render();
    }
    
    getDefaultValue(schema) {
        if (schema.default !== undefined) {
            return schema.default;
        }
        if (schema.type === 'number') return 0;
        if (schema.type === 'boolean') return false;
        if (schema.type === 'array') return [];
        if (schema.type === 'object') return {};
        return '';
    }
    
    isDateString(value) {
        if (typeof value !== 'string') return false;
        return /^\d{4}-\d{2}-\d{2}/.test(value);
    }
    
    getData() {
        return this.data;
    }
    
    setData(data) {
        this.data = data;
        this.render();
    }
    
    triggerChange() {
        const event = new CustomEvent('form-field-change', {
            detail: { data: this.data }
        });
        this.container.dispatchEvent(event);
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FormFieldBuilder;
}
