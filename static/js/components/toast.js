/**
 * Toast Notification System
 * 
 * A modern toast notification system for DocsAI.
 * 
 * Usage:
 *   Toast.success('Changes saved successfully!');
 *   Toast.error('Something went wrong', 'Error');
 *   Toast.warning('This action cannot be undone');
 *   Toast.info('New updates available');
 *   
 *   // With options
 *   Toast.show({
 *     type: 'success',
 *     title: 'Saved!',
 *     message: 'Your changes have been saved.',
 *     duration: 5000,
 *     action: { text: 'Undo', url: '/undo' }
 *   });
 */

class ToastManager {
    constructor() {
        this.container = null;
        this.toasts = new Map();
        this.defaultDuration = 5000;
        this.maxToasts = 5;
        this.position = 'top-right';
        this.init();
    }

    init() {
        // Create toast container
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.className = this.getPositionClasses();
            this.container.setAttribute('aria-live', 'polite');
            this.container.setAttribute('aria-atomic', 'true');
            document.body.appendChild(this.container);
        }
    }

    getPositionClasses() {
        const positions = {
            'top-right': 'fixed top-20 right-4 z-[100] flex flex-col gap-3',
            'top-left': 'fixed top-20 left-4 z-[100] flex flex-col gap-3',
            'bottom-right': 'fixed bottom-4 right-4 z-[100] flex flex-col-reverse gap-3',
            'bottom-left': 'fixed bottom-4 left-4 z-[100] flex flex-col-reverse gap-3',
            'top-center': 'fixed top-20 left-1/2 -translate-x-1/2 z-[100] flex flex-col gap-3',
            'bottom-center': 'fixed bottom-4 left-1/2 -translate-x-1/2 z-[100] flex flex-col-reverse gap-3',
        };
        return positions[this.position] || positions['top-right'];
    }

    show(options) {
        const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        
        const config = {
            id,
            type: options.type || 'info',
            title: options.title || '',
            message: options.message || '',
            duration: options.duration !== undefined ? options.duration : this.defaultDuration,
            dismissible: options.dismissible !== false,
            action: options.action || null,
            icon: options.icon || null,
        };

        // Limit number of toasts
        if (this.toasts.size >= this.maxToasts) {
            const oldest = this.toasts.keys().next().value;
            this.dismiss(oldest);
        }

        const toast = this.createToastElement(config);
        this.container.appendChild(toast);
        this.toasts.set(id, { element: toast, config });

        // Auto-dismiss
        if (config.duration > 0) {
            setTimeout(() => this.dismiss(id), config.duration);
        }

        return id;
    }

    createToastElement(config) {
        const toast = document.createElement('div');
        toast.id = config.id;
        toast.className = this.getToastClasses(config.type);
        toast.setAttribute('role', 'alert');

        toast.innerHTML = `
            <div class="flex-shrink-0 mt-0.5">
                ${this.getIcon(config.type, config.icon)}
            </div>
            <div class="flex-1 min-w-0">
                ${config.title ? `<h4 class="font-semibold text-sm ${this.getTitleColorClass(config.type)}">${this.escapeHtml(config.title)}</h4>` : ''}
                <p class="text-sm ${config.title ? 'mt-0.5' : ''} ${this.getMessageColorClass(config.type)}">${this.escapeHtml(config.message)}</p>
                ${config.action ? `
                    <div class="mt-2">
                        <a href="${config.action.url || '#'}" class="text-sm font-semibold underline ${this.getActionColorClass(config.type)}" onclick="${config.action.onClick || ''}">
                            ${this.escapeHtml(config.action.text)}
                        </a>
                    </div>
                ` : ''}
            </div>
            ${config.dismissible ? `
                <button type="button" class="flex-shrink-0 p-1 rounded-lg transition-colors ${this.getCloseButtonClass(config.type)}" aria-label="Dismiss">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            ` : ''}
        `;

        // Add close button handler
        const closeBtn = toast.querySelector('button[aria-label="Dismiss"]');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.dismiss(config.id));
        }

        return toast;
    }

    getToastClasses(type) {
        const baseClasses = 'toast flex items-start gap-3 p-4 rounded-xl shadow-xl border backdrop-blur-sm max-w-[400px] animate-slide-in-right';
        const typeClasses = {
            success: 'bg-green-50/95 dark:bg-green-900/95 border-green-200 dark:border-green-700',
            error: 'bg-red-50/95 dark:bg-red-900/95 border-red-200 dark:border-red-700',
            warning: 'bg-amber-50/95 dark:bg-amber-900/95 border-amber-200 dark:border-amber-700',
            info: 'bg-blue-50/95 dark:bg-blue-900/95 border-blue-200 dark:border-blue-700',
        };
        return `${baseClasses} ${typeClasses[type] || typeClasses.info}`;
    }

    getIcon(type, customIcon) {
        if (customIcon) return customIcon;
        
        const icons = {
            success: `<svg class="w-5 h-5 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>`,
            error: `<svg class="w-5 h-5 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>`,
            warning: `<svg class="w-5 h-5 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
            </svg>`,
            info: `<svg class="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>`,
        };
        return icons[type] || icons.info;
    }

    getTitleColorClass(type) {
        const colors = {
            success: 'text-green-800 dark:text-green-200',
            error: 'text-red-800 dark:text-red-200',
            warning: 'text-amber-800 dark:text-amber-200',
            info: 'text-blue-800 dark:text-blue-200',
        };
        return colors[type] || colors.info;
    }

    getMessageColorClass(type) {
        const colors = {
            success: 'text-green-700 dark:text-green-300',
            error: 'text-red-700 dark:text-red-300',
            warning: 'text-amber-700 dark:text-amber-300',
            info: 'text-blue-700 dark:text-blue-300',
        };
        return colors[type] || colors.info;
    }

    getActionColorClass(type) {
        const colors = {
            success: 'text-green-800 dark:text-green-200 hover:text-green-900',
            error: 'text-red-800 dark:text-red-200 hover:text-red-900',
            warning: 'text-amber-800 dark:text-amber-200 hover:text-amber-900',
            info: 'text-blue-800 dark:text-blue-200 hover:text-blue-900',
        };
        return colors[type] || colors.info;
    }

    getCloseButtonClass(type) {
        const colors = {
            success: 'text-green-500 hover:bg-green-100 dark:hover:bg-green-800',
            error: 'text-red-500 hover:bg-red-100 dark:hover:bg-red-800',
            warning: 'text-amber-500 hover:bg-amber-100 dark:hover:bg-amber-800',
            info: 'text-blue-500 hover:bg-blue-100 dark:hover:bg-blue-800',
        };
        return colors[type] || colors.info;
    }

    dismiss(id) {
        const toastData = this.toasts.get(id);
        if (!toastData) return;

        const { element } = toastData;
        element.classList.remove('animate-slide-in-right');
        element.classList.add('animate-slide-out-right');
        
        element.addEventListener('animationend', () => {
            element.remove();
            this.toasts.delete(id);
        }, { once: true });
    }

    dismissAll() {
        this.toasts.forEach((_, id) => this.dismiss(id));
    }

    escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // Convenience methods
    success(message, title = '') {
        return this.show({ type: 'success', message, title });
    }

    error(message, title = '') {
        return this.show({ type: 'error', message, title });
    }

    warning(message, title = '') {
        return this.show({ type: 'warning', message, title });
    }

    info(message, title = '') {
        return this.show({ type: 'info', message, title });
    }
}

// Create global Toast instance
window.Toast = new ToastManager();

// Add CSS animations to document
const style = document.createElement('style');
style.textContent = `
    @keyframes slide-in-right {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slide-out-right {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    .animate-slide-in-right { animation: slide-in-right 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
    .animate-slide-out-right { animation: slide-out-right 0.2s ease forwards; }
`;
document.head.appendChild(style);
