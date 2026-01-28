/**
 * Modal Component
 * 
 * A reusable modal/dialog component with:
 * - Open/close animations
 * - Backdrop click to close
 * - ESC key to close
 * - Focus trap
 * - Accessibility (ARIA)
 * - Multiple sizes
 * - Customizable content
 */

class Modal {
    constructor(options = {}) {
        this.options = {
            id: options.id || `modal-${Date.now()}`,
            title: options.title || '',
            content: options.content || '',
            size: options.size || 'md', // sm, md, lg, xl, full
            closable: options.closable !== false, // Default true
            backdrop: options.backdrop !== false, // Default true
            backdropClose: options.backdropClose !== false, // Default true
            keyboardClose: options.keyboardClose !== false, // Default true
            onOpen: options.onOpen || null,
            onClose: options.onClose || null,
            onConfirm: options.onConfirm || null,
            showFooter: options.showFooter !== false, // Default true
            confirmText: options.confirmText || 'Confirm',
            cancelText: options.cancelText || 'Cancel',
            showCancel: options.showCancel !== false, // Default true
            ...options
        };
        
        this.isOpen = false;
        this.previousFocus = null;
        this.focusableElements = [];
        this.firstFocusable = null;
        this.lastFocusable = null;
        
        this.createModal();
        this.attachEventListeners();
    }
    
    /**
     * Create modal HTML structure
     */
    createModal() {
        // Remove existing modal if any
        const existing = document.getElementById(this.options.id);
        if (existing) {
            existing.remove();
        }
        
        const modal = document.createElement('div');
        modal.id = this.options.id;
        modal.className = 'modal-container';
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');
        modal.setAttribute('aria-labelledby', `${this.options.id}-title`);
        modal.setAttribute('aria-hidden', 'true');
        modal.style.display = 'none';
        
        const sizeClasses = {
            sm: 'max-w-sm',
            md: 'max-w-md',
            lg: 'max-w-lg',
            xl: 'max-w-xl',
            '2xl': 'max-w-2xl',
            full: 'max-w-full mx-4'
        };
        
        modal.innerHTML = `
            <div class="modal-backdrop"></div>
            <div class="modal-dialog ${sizeClasses[this.options.size] || sizeClasses.md}">
                <div class="modal-content">
                    ${this.options.title ? `
                        <div class="modal-header">
                            <h2 id="${this.options.id}-title" class="modal-title">${this.options.title}</h2>
                            ${this.options.closable ? `
                                <button type="button" class="modal-close" aria-label="Close modal">
                                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                </button>
                            ` : ''}
                        </div>
                    ` : ''}
                    <div class="modal-body">
                        ${this.options.content}
                    </div>
                    ${this.options.showFooter ? `
                        <div class="modal-footer">
                            ${this.options.showCancel ? `
                                <button type="button" class="modal-btn modal-btn-cancel">${this.options.cancelText}</button>
                            ` : ''}
                            <button type="button" class="modal-btn modal-btn-confirm">${this.options.confirmText}</button>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        this.modal = modal;
        this.backdrop = modal.querySelector('.modal-backdrop');
        this.dialog = modal.querySelector('.modal-dialog');
        this.closeBtn = modal.querySelector('.modal-close');
        this.cancelBtn = modal.querySelector('.modal-btn-cancel');
        this.confirmBtn = modal.querySelector('.modal-btn-confirm');
    }
    
    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Close button
        if (this.closeBtn) {
            this.closeBtn.addEventListener('click', () => this.close());
        }
        
        // Cancel button
        if (this.cancelBtn) {
            this.cancelBtn.addEventListener('click', () => this.close());
        }
        
        // Confirm button
        if (this.confirmBtn) {
            this.confirmBtn.addEventListener('click', () => {
                if (this.options.onConfirm) {
                    this.options.onConfirm(this);
                } else {
                    this.close();
                }
            });
        }
        
        // Backdrop click
        if (this.options.backdropClose && this.backdrop) {
            this.backdrop.addEventListener('click', (e) => {
                if (e.target === this.backdrop) {
                    this.close();
                }
            });
        }
        
        // Keyboard events
        if (this.options.keyboardClose) {
            this.modal.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.isOpen) {
                    this.close();
                } else if (e.key === 'Tab') {
                    this.handleTabKey(e);
                }
            });
        }
    }
    
    /**
     * Handle Tab key for focus trap
     */
    handleTabKey(e) {
        this.updateFocusableElements();
        
        if (e.shiftKey) {
            // Shift + Tab
            if (document.activeElement === this.firstFocusable) {
                e.preventDefault();
                this.lastFocusable.focus();
            }
        } else {
            // Tab
            if (document.activeElement === this.lastFocusable) {
                e.preventDefault();
                this.firstFocusable.focus();
            }
        }
    }
    
    /**
     * Update list of focusable elements
     */
    updateFocusableElements() {
        const focusableSelectors = [
            'a[href]',
            'button:not([disabled])',
            'textarea:not([disabled])',
            'input:not([disabled])',
            'select:not([disabled])',
            '[tabindex]:not([tabindex="-1"])'
        ].join(', ');
        
        this.focusableElements = Array.from(
            this.modal.querySelectorAll(focusableSelectors)
        ).filter(el => {
            return el.offsetParent !== null && !el.hasAttribute('disabled');
        });
        
        this.firstFocusable = this.focusableElements[0];
        this.lastFocusable = this.focusableElements[this.focusableElements.length - 1];
    }
    
    /**
     * Open modal
     */
    open() {
        if (this.isOpen) return;
        
        // Store previous focus
        this.previousFocus = document.activeElement;
        
        // Show modal
        this.modal.style.display = 'block';
        this.modal.setAttribute('aria-hidden', 'false');
        
        // Trigger reflow for animation
        void this.modal.offsetWidth;
        
        // Add open class
        this.modal.classList.add('modal-open');
        this.isOpen = true;
        
        // Prevent body scroll
        document.body.style.overflow = 'hidden';
        
        // Update focusable elements
        this.updateFocusableElements();
        
        // Focus first element or close button
        setTimeout(() => {
            if (this.closeBtn) {
                this.closeBtn.focus();
            } else if (this.firstFocusable) {
                this.firstFocusable.focus();
            }
        }, 100);
        
        // Call onOpen callback
        if (this.options.onOpen) {
            this.options.onOpen(this);
        }
    }
    
    /**
     * Close modal
     */
    close() {
        if (!this.isOpen) return;
        
        // Remove open class
        this.modal.classList.remove('modal-open');
        this.modal.classList.add('modal-closing');
        
        // Wait for animation
        setTimeout(() => {
            this.modal.style.display = 'none';
            this.modal.setAttribute('aria-hidden', 'true');
            this.modal.classList.remove('modal-closing');
            this.isOpen = false;
            
            // Restore body scroll
            document.body.style.overflow = '';
            
            // Restore focus
            if (this.previousFocus && typeof this.previousFocus.focus === 'function') {
                this.previousFocus.focus();
            }
            
            // Call onClose callback
            if (this.options.onClose) {
                this.options.onClose(this);
            }
        }, 200); // Match CSS transition duration
    }
    
    /**
     * Update modal content
     */
    setContent(content) {
        const body = this.modal.querySelector('.modal-body');
        if (body) {
            body.innerHTML = content;
            this.updateFocusableElements();
        }
    }
    
    /**
     * Update modal title
     */
    setTitle(title) {
        const titleEl = this.modal.querySelector('.modal-title');
        if (titleEl) {
            titleEl.textContent = title;
        }
    }
    
    /**
     * Destroy modal
     */
    destroy() {
        this.close();
        setTimeout(() => {
            if (this.modal && this.modal.parentNode) {
                this.modal.parentNode.removeChild(this.modal);
            }
        }, 300);
    }
    
    /**
     * Static method to create and show a simple modal
     */
    static show(options) {
        const modal = new Modal(options);
        modal.open();
        return modal;
    }
    
    /**
     * Static method to create a confirmation dialog
     */
    static confirm(options) {
        return new Promise((resolve, reject) => {
            const modal = new Modal({
                ...options,
                showCancel: true,
                onConfirm: () => {
                    modal.close();
                    resolve(true);
                },
                onClose: () => {
                    resolve(false);
                }
            });
            modal.open();
        });
    }
    
    /**
     * Static method to create an alert dialog
     */
    static alert(message, title = 'Alert') {
        return new Promise((resolve) => {
            const modal = new Modal({
                title: title,
                content: `<p>${message}</p>`,
                showCancel: false,
                confirmText: 'OK',
                onConfirm: () => {
                    modal.close();
                    resolve();
                }
            });
            modal.open();
        });
    }
}

// Export for global use
window.Modal = Modal;
