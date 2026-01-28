/**
 * Accessibility Enhancements
 * 
 * Provides accessibility features including:
 * - Keyboard navigation detection
 * - ARIA live region announcements
 * - Focus management
 * - Skip link functionality
 */

class AccessibilityManager {
    constructor() {
        this.isKeyboardUser = false;
        this.liveRegion = null;
        this.alertRegion = null;
        
        this.init();
    }
    
    init() {
        // Detect keyboard vs mouse usage
        this.detectInputMethod();
        
        // Get ARIA live regions
        this.liveRegion = document.getElementById('aria-live-region');
        this.alertRegion = document.getElementById('aria-live-alert');
        
        // Setup keyboard navigation
        this.setupKeyboardNavigation();
        
        // Setup skip links
        this.setupSkipLinks();
    }
    
    /**
     * Detect if user is using keyboard or mouse
     */
    detectInputMethod() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                this.isKeyboardUser = true;
                document.body.classList.add('keyboard-user');
                document.body.classList.remove('mouse-user');
            }
        });
        
        document.addEventListener('mousedown', () => {
            if (!this.isKeyboardUser) {
                document.body.classList.add('mouse-user');
                document.body.classList.remove('keyboard-user');
            }
        });
    }
    
    /**
     * Announce message to screen readers
     */
    announce(message, priority = 'polite') {
        const region = priority === 'assertive' ? this.alertRegion : this.liveRegion;
        
        if (region) {
            // Clear previous message
            region.textContent = '';
            
            // Set new message (with slight delay to ensure screen readers pick it up)
            setTimeout(() => {
                region.textContent = message;
                
                // Clear after announcement
                setTimeout(() => {
                    region.textContent = '';
                }, 1000);
            }, 100);
        }
    }
    
    /**
     * Announce error message
     */
    announceError(message) {
        this.announce(message, 'assertive');
    }
    
    /**
     * Announce success message
     */
    announceSuccess(message) {
        this.announce(message, 'polite');
    }
    
    /**
     * Announce loading state
     */
    announceLoading(message = 'Loading...') {
        this.announce(message, 'polite');
    }
    
    /**
     * Setup keyboard navigation enhancements
     */
    setupKeyboardNavigation() {
        // Handle Tab navigation in modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                const modal = document.querySelector('.modal-container.modal-open');
                if (modal) {
                    // Focus trap is handled by Modal component
                    // This is just for additional enhancements
                }
            }
        });
        
        // Handle Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                // Close any open modals (handled by Modal component)
                // Close any open dropdowns
                const dropdowns = document.querySelectorAll('[aria-expanded="true"]');
                dropdowns.forEach(dropdown => {
                    dropdown.setAttribute('aria-expanded', 'false');
                    const target = document.querySelector(dropdown.getAttribute('aria-controls'));
                    if (target) {
                        target.hidden = true;
                    }
                });
            }
        });
    }
    
    /**
     * Setup skip links
     */
    setupSkipLinks() {
        const skipLinks = document.querySelectorAll('.skip-link');
        skipLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                const targetId = link.getAttribute('href').substring(1);
                const target = document.getElementById(targetId);
                
                if (target) {
                    e.preventDefault();
                    target.setAttribute('tabindex', '-1');
                    target.focus();
                    
                    // Remove tabindex after focus
                    setTimeout(() => {
                        target.removeAttribute('tabindex');
                    }, 100);
                }
            });
        });
    }
    
    /**
     * Move focus to element
     */
    focusElement(element) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        
        if (element) {
            element.setAttribute('tabindex', '-1');
            element.focus();
            
            // Scroll into view
            element.scrollIntoView({ behavior: 'smooth', block: 'center' });
            
            // Remove tabindex after focus
            setTimeout(() => {
                element.removeAttribute('tabindex');
            }, 100);
        }
    }
    
    /**
     * Trap focus within element
     */
    trapFocus(container) {
        const focusableElements = container.querySelectorAll(
            'a[href], button:not([disabled]), textarea:not([disabled]), ' +
            'input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
        );
        
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        container.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                if (e.shiftKey) {
                    // Shift + Tab
                    if (document.activeElement === firstElement) {
                        e.preventDefault();
                        lastElement.focus();
                    }
                } else {
                    // Tab
                    if (document.activeElement === lastElement) {
                        e.preventDefault();
                        firstElement.focus();
                    }
                }
            }
        });
    }
    
    /**
     * Make element focusable
     */
    makeFocusable(element) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        
        if (element) {
            element.setAttribute('tabindex', '0');
        }
    }
    
    /**
     * Make element not focusable
     */
    makeNotFocusable(element) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        
        if (element) {
            element.setAttribute('tabindex', '-1');
        }
    }
}

// Initialize accessibility manager
let accessibilityManager;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        accessibilityManager = new AccessibilityManager();
        window.accessibilityManager = accessibilityManager;
    });
} else {
    accessibilityManager = new AccessibilityManager();
    window.accessibilityManager = accessibilityManager;
}

// Export for use in other scripts
window.AccessibilityManager = AccessibilityManager;
