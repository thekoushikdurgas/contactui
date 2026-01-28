/**
 * Error Handler Component
 * 
 * Provides consistent error display with:
 * - Error message display
 * - Retry functionality
 * - Error logging
 * - User-friendly messages
 */

class ErrorHandler {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.options = {
            showRetry: options.showRetry !== false,
            autoHide: options.autoHide || false,
            autoHideDelay: options.autoHideDelay || 5000,
            ...options
        };
        
        if (!this.container) {
            throw new Error('Container element not found');
        }
        
        this.errors = [];
    }
    
    showError(error, options = {}) {
        const errorObj = {
            id: Date.now() + Math.random(),
            message: this.formatErrorMessage(error),
            type: options.type || 'error',
            retry: options.retry || null,
            timestamp: new Date()
        };
        
        this.errors.push(errorObj);
        this.render();
        
        if (this.options.autoHide) {
            setTimeout(() => {
                this.removeError(errorObj.id);
            }, this.options.autoHideDelay);
        }
    }
    
    showSuccess(message) {
        this.showError(message, { type: 'success' });
    }
    
    showWarning(message) {
        this.showError(message, { type: 'warning' });
    }
    
    showInfo(message) {
        this.showError(message, { type: 'info' });
    }
    
    formatErrorMessage(error) {
        if (typeof error === 'string') {
            return error;
        }
        if (error instanceof Error) {
            return error.message;
        }
        if (error && error.message) {
            return error.message;
        }
        return 'An unexpected error occurred';
    }
    
    render() {
        if (this.errors.length === 0) {
            this.container.innerHTML = '';
            return;
        }
        
        const html = `
            <div class="error-handler-container space-y-2">
                ${this.errors.map(error => this.renderError(error)).join('')}
            </div>
        `;
        
        this.container.innerHTML = html;
        this.setupEventListeners();
    }
    
    renderError(error) {
        const typeClasses = {
            'error': 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-800 dark:text-red-200',
            'success': 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800 text-green-800 dark:text-green-200',
            'warning': 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800 text-yellow-800 dark:text-yellow-200',
            'info': 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800 text-blue-800 dark:text-blue-200'
        };
        
        const icon = {
            'error': '⚠️',
            'success': '✓',
            'warning': '⚠️',
            'info': 'ℹ️'
        };
        
        return `
            <div 
                class="error-message ${typeClasses[error.type] || typeClasses.error} border rounded-lg p-4 flex items-start justify-between gap-4"
                data-error-id="${error.id}"
            >
                <div class="flex items-start gap-3 flex-1">
                    <span class="text-xl">${icon[error.type] || '⚠️'}</span>
                    <div class="flex-1">
                        <p class="font-medium">${this.escapeHtml(error.message)}</p>
                        ${error.timestamp ? `
                            <p class="text-xs mt-1 opacity-75">${this.formatTimestamp(error.timestamp)}</p>
                        ` : ''}
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    ${error.retry && this.options.showRetry ? `
                        <button 
                            type="button"
                            class="retry-btn px-3 py-1 rounded text-sm font-medium hover:opacity-80 transition-opacity"
                            data-error-id="${error.id}"
                        >
                            Retry
                        </button>
                    ` : ''}
                    <button 
                        type="button"
                        class="dismiss-error-btn text-xl leading-none opacity-50 hover:opacity-100 transition-opacity"
                        data-error-id="${error.id}"
                    >
                        ×
                    </button>
                </div>
            </div>
        `;
    }
    
    setupEventListeners() {
        // Dismiss buttons
        const dismissBtns = this.container.querySelectorAll('.dismiss-error-btn');
        dismissBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const errorId = parseFloat(e.target.getAttribute('data-error-id'));
                this.removeError(errorId);
            });
        });
        
        // Retry buttons
        const retryBtns = this.container.querySelectorAll('.retry-btn');
        retryBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const errorId = parseFloat(e.target.getAttribute('data-error-id'));
                const error = this.errors.find(e => e.id === errorId);
                if (error && error.retry) {
                    error.retry();
                    this.removeError(errorId);
                }
            });
        });
    }
    
    removeError(errorId) {
        this.errors = this.errors.filter(e => e.id !== errorId);
        this.render();
    }
    
    clear() {
        this.errors = [];
        this.render();
    }
    
    formatTimestamp(timestamp) {
        const now = new Date();
        const diff = now - timestamp;
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        
        if (seconds < 60) {
            return 'Just now';
        } else if (minutes < 60) {
            return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
        } else {
            return timestamp.toLocaleTimeString();
        }
    }
    
    escapeHtml(text) {
        if (text === null || text === undefined) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ErrorHandler;
}
