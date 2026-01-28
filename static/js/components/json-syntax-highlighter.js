/**
 * JSON Syntax Highlighter Component
 * 
 * Provides syntax highlighting for JSON strings with:
 * - Color-coded syntax highlighting
 * - Line numbers (optional)
 * - Copy to clipboard functionality
 * - Dark mode support
 */

class JSONSyntaxHighlighter {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.options = {
            json: options.json || null,
            showLineNumbers: options.showLineNumbers !== false,
            showCopyButton: options.showCopyButton !== false,
            theme: options.theme || 'auto', // 'light', 'dark', 'auto'
            ...options
        };
        
        if (!this.container) {
            throw new Error('Container element not found');
        }
        
        this.init();
    }
    
    init() {
        this.container.innerHTML = '';
        this.container.classList.add('json-syntax-highlighter');
        this.render();
    }
    
    render() {
        const jsonString = this.options.json 
            ? (typeof this.options.json === 'string' ? this.options.json : JSON.stringify(this.options.json, null, 2))
            : '';
        
        const html = `
            <div class="json-highlighter-wrapper">
                ${this.options.showCopyButton ? `
                    <div class="json-highlighter-toolbar flex justify-end mb-2">
                        <button 
                            type="button" 
                            class="copy-json-btn px-3 py-1 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
                            title="Copy to clipboard"
                        >
                            📋 Copy
                        </button>
                    </div>
                ` : ''}
                <div class="json-highlighter-content relative">
                    ${this.options.showLineNumbers ? '<div class="json-line-numbers"></div>' : ''}
                    <pre class="json-highlighted-code"><code>${this.highlightJSON(jsonString)}</code></pre>
                </div>
            </div>
        `;
        
        this.container.innerHTML = html;
        
        if (this.options.showLineNumbers) {
            this.updateLineNumbers(jsonString);
        }
        
        if (this.options.showCopyButton) {
            this.setupCopyButton();
        }
    }
    
    highlightJSON(jsonString) {
        if (!jsonString) return '';
        
        // Escape HTML
        let escaped = jsonString
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
        
        // Highlight JSON syntax
        escaped = escaped
            // Strings (double-quoted)
            .replace(/"([^"\\]|\\.)*"/g, '<span class="json-string">$&</span>')
            // Numbers
            .replace(/\b(-?\d+\.?\d*)\b/g, '<span class="json-number">$1</span>')
            // Booleans and null
            .replace(/\b(true|false|null)\b/g, '<span class="json-literal">$1</span>')
            // Keys
            .replace(/"([^"]+)":/g, '<span class="json-key">"$1"</span>:')
            // Brackets and braces
            .replace(/([{}[\]])/g, '<span class="json-bracket">$1</span>');
        
        return escaped;
    }
    
    updateLineNumbers(jsonString) {
        const lineNumbersDiv = this.container.querySelector('.json-line-numbers');
        if (!lineNumbersDiv) return;
        
        const lines = jsonString.split('\n');
        lineNumbersDiv.innerHTML = lines.map((_, index) => 
            `<span class="json-line-number">${index + 1}</span>`
        ).join('\n');
    }
    
    setupCopyButton() {
        const copyBtn = this.container.querySelector('.copy-json-btn');
        if (!copyBtn) return;
        
        copyBtn.addEventListener('click', async () => {
            const jsonString = this.options.json 
                ? (typeof this.options.json === 'string' ? this.options.json : JSON.stringify(this.options.json, null, 2))
                : '';
            
            try {
                await navigator.clipboard.writeText(jsonString);
                const originalText = copyBtn.textContent;
                copyBtn.textContent = '✓ Copied!';
                copyBtn.classList.add('bg-green-600');
                copyBtn.classList.remove('bg-blue-600');
                
                setTimeout(() => {
                    copyBtn.textContent = originalText;
                    copyBtn.classList.remove('bg-green-600');
                    copyBtn.classList.add('bg-blue-600');
                }, 2000);
            } catch (error) {
                console.error('Failed to copy:', error);
                copyBtn.textContent = '✗ Failed';
                setTimeout(() => {
                    copyBtn.textContent = '📋 Copy';
                }, 2000);
            }
        });
    }
    
    setJSON(json) {
        this.options.json = json;
        this.render();
    }
    
    getJSON() {
        return this.options.json;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = JSONSyntaxHighlighter;
}
