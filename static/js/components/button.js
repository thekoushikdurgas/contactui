/**
 * Button Component JavaScript
 * 
 * Enhances button components with:
 * - Loading state management
 * - Click handlers
 * - Accessibility improvements
 */

class ButtonComponent {
    constructor(buttonElement, options = {}) {
        this.button = typeof buttonElement === 'string' 
            ? document.querySelector(buttonElement) 
            : buttonElement;
        
        if (!this.button) {
            console.error('Button element not found');
            return;
        }
        
        this.options = {
            loadingText: options.loadingText || 'Loading...',
            onClick: options.onClick || null,
            ...options
        };
        
        this.originalText = this.button.textContent.trim();
        this.isLoading = false;
        
        this.init();
    }
    
    init() {
        // Add click handler
        if (this.options.onClick) {
            this.button.addEventListener('click', (e) => {
                if (!this.isLoading && !this.button.disabled) {
                    this.options.onClick(e, this);
                }
            });
        }
        
        // Enhance accessibility
        if (!this.button.getAttribute('aria-label') && this.button.textContent) {
            this.button.setAttribute('aria-label', this.button.textContent.trim());
        }
    }
    
    /**
     * Set loading state
     */
    setLoading(loading = true) {
        this.isLoading = loading;
        
        if (loading) {
            this.button.classList.add('btn-loading');
            this.button.disabled = true;
            
            // Store original content
            const textSpan = this.button.querySelector('.btn-text');
            if (textSpan) {
                this.originalText = textSpan.textContent;
                textSpan.textContent = this.options.loadingText;
            } else {
                this.originalText = this.button.textContent;
                this.button.innerHTML = `
                    <span class="btn-spinner"></span>
                    <span class="btn-text">${this.options.loadingText}</span>
                `;
            }
        } else {
            this.button.classList.remove('btn-loading');
            this.button.disabled = false;
            
            // Restore original content
            const textSpan = this.button.querySelector('.btn-text');
            if (textSpan) {
                textSpan.textContent = this.originalText;
            } else {
                this.button.textContent = this.originalText;
            }
        }
    }
    
    /**
     * Enable button
     */
    enable() {
        this.button.disabled = false;
        this.button.classList.remove('btn-disabled');
    }
    
    /**
     * Disable button
     */
    disable() {
        this.button.disabled = true;
        this.button.classList.add('btn-disabled');
    }
    
    /**
     * Toggle button state
     */
    toggle() {
        if (this.button.disabled) {
            this.enable();
        } else {
            this.disable();
        }
    }
    
    /**
     * Static method to initialize all buttons with data attributes
     */
    static initAll(selector = '.btn') {
        document.querySelectorAll(selector).forEach(button => {
            const loadingText = button.getAttribute('data-loading-text');
            const onClickAttr = button.getAttribute('data-onclick');
            
            if (loadingText || onClickAttr) {
                new ButtonComponent(button, {
                    loadingText: loadingText,
                    onClick: onClickAttr ? new Function('e', 'btn', onClickAttr) : null
                });
            }
        });
    }
}

// Auto-initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        ButtonComponent.initAll();
    });
} else {
    ButtonComponent.initAll();
}

// Export for global use
window.ButtonComponent = ButtonComponent;
