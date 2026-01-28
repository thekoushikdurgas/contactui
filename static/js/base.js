// Base JavaScript for DocsAI Django App - React Design Patterns

// Animation utilities
const AnimationUtils = {
    // Fade in animation
    fadeIn: function(element, duration = 500) {
        element.style.opacity = '0';
        element.style.transition = `opacity ${duration}ms ease-in-out`;
        setTimeout(() => {
            element.style.opacity = '1';
        }, 10);
    },
    
    // Slide in animation
    slideIn: function(element, direction = 'bottom', duration = 300) {
        const transforms = {
            'bottom': 'translateY(20px)',
            'top': 'translateY(-20px)',
            'left': 'translateX(-20px)',
            'right': 'translateX(20px)'
        };
        
        element.style.opacity = '0';
        element.style.transform = transforms[direction] || transforms['bottom'];
        element.style.transition = `opacity ${duration}ms ease-out, transform ${duration}ms ease-out`;
        
        setTimeout(() => {
            element.style.opacity = '1';
            element.style.transform = 'translate(0, 0)';
        }, 10);
    },
    
    // Zoom in animation
    zoomIn: function(element, duration = 300) {
        element.style.opacity = '0';
        element.style.transform = 'scale(0.95)';
        element.style.transition = `opacity ${duration}ms ease-out, transform ${duration}ms ease-out`;
        
        setTimeout(() => {
            element.style.opacity = '1';
            element.style.transform = 'scale(1)';
        }, 10);
    }
};

// Notification system
document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss notifications after 3 seconds
    const notifications = document.querySelectorAll('.fixed.top-20');
    notifications.forEach(notification => {
        AnimationUtils.fadeIn(notification);
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    });
    
    // Animate elements with animate-in class
    const animateElements = document.querySelectorAll('.animate-in');
    animateElements.forEach((el, index) => {
        setTimeout(() => {
            AnimationUtils.fadeIn(el, 500);
        }, index * 50);
    });
    
    // Animate zoom-in elements
    const zoomElements = document.querySelectorAll('.animate-zoom-in, .animate-zoom-in-95');
    zoomElements.forEach((el, index) => {
        setTimeout(() => {
            AnimationUtils.zoomIn(el, 300);
        }, index * 50);
    });
});

// Form handling utilities
function handleFormSubmit(formId, url, method = 'POST') {
    const form = document.getElementById(formId);
    if (!form) return;
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(form);
        const data = Object.fromEntries(formData);
        
        try {
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                body: JSON.stringify(data),
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    window.location.reload();
                } else {
                    alert(result.error || 'An error occurred');
                }
            }
        } catch (error) {
            console.error('Form submission error:', error);
            alert('An error occurred while submitting the form');
        }
    });
}

// Get CSRF token
function getCsrfToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return '';
}

// AJAX utilities
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
        },
    };
    
    const mergedOptions = { ...defaultOptions, ...options };
    if (options.body && typeof options.body === 'object') {
        mergedOptions.body = JSON.stringify(options.body);
    }
    
    try {
        const response = await fetch(url, mergedOptions);
        return await response.json();
    } catch (error) {
        console.error('API request error:', error);
        throw error;
    }
}

// Error handling
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
});

// Theme toggle integration
document.addEventListener('DOMContentLoaded', function() {
    // Listen for theme changes
    window.addEventListener('themechange', function(e) {
        // Update any theme-dependent elements
        const theme = e.detail.theme;
        document.documentElement.setAttribute('data-theme', theme);
    });
});

// Form enhancements
function enhanceForms() {
    // Auto-resize textareas
    const textareas = document.querySelectorAll('textarea[data-auto-resize]');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 192) + 'px';
        });
    });
    
    // Add focus ring animations
    const inputs = document.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement?.classList.add('ring-4', 'ring-blue-500/10');
        });
        input.addEventListener('blur', function() {
            this.parentElement?.classList.remove('ring-4', 'ring-blue-500/10');
        });
    });
    
    // Add loading states to submit buttons
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton && !submitButton.disabled) {
                const originalText = submitButton.innerHTML;
                submitButton.disabled = true;
                submitButton.innerHTML = `
                    <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin inline-block mr-2"></div>
                    Processing...
                `;
                
                // Re-enable after 10 seconds as fallback
                setTimeout(() => {
                    submitButton.disabled = false;
                    submitButton.innerHTML = originalText;
                }, 10000);
            }
        });
    });
}

// UI interaction enhancements
function enhanceUIInteractions() {
    // Add hover scale effects to cards
    const cards = document.querySelectorAll('.group');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            const icon = this.querySelector('.group-hover\\:scale-110');
            if (icon) {
                icon.style.transform = 'scale(1.1)';
            }
        });
        card.addEventListener('mouseleave', function() {
            const icon = this.querySelector('.group-hover\\:scale-110');
            if (icon) {
                icon.style.transform = 'scale(1)';
            }
        });
    });
    
    // Add active scale effects to buttons
    const buttons = document.querySelectorAll('button, a[class*="button"], .active\\:scale-90, .active\\:scale-95');
    buttons.forEach(button => {
        button.addEventListener('mousedown', function() {
            this.style.transform = 'scale(0.95)';
        });
        button.addEventListener('mouseup', function() {
            this.style.transform = 'scale(1)';
        });
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });
    
    // Smooth scroll to element
    window.smoothScrollTo = function(element, offset = 0) {
        const elementPosition = element.getBoundingClientRect().top + window.pageYOffset;
        const offsetPosition = elementPosition - offset;
        
        window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
        });
    };
}

// Initialize enhancements on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    enhanceForms();
    enhanceUIInteractions();
});

// Utility functions
window.DocsAI = {
    // Get CSRF token
    getCsrfToken: getCsrfToken,
    
    // API request helper
    apiRequest: apiRequest,
    
    // Form handler
    handleFormSubmit: handleFormSubmit,
    
    // Animation utilities
    animate: AnimationUtils,
    
    // Show notification
    showNotification: function(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-20 right-8 z-[100] animate-in fade-in zoom-in-95 duration-300 px-6 py-3 rounded-2xl shadow-2xl border flex items-center gap-3 ${
            type === 'success' ? 'bg-white border-green-100 text-green-700' :
            type === 'error' ? 'bg-white border-red-100 text-red-700' :
            'bg-white border-blue-100 text-blue-700'
        }`;
        notification.innerHTML = `
            <div class="w-2 h-2 rounded-full ${
                type === 'success' ? 'bg-green-500' :
                type === 'error' ? 'bg-red-500' :
                'bg-blue-500'
            } animate-pulse"></div>
            <span class="text-sm font-bold">${message}</span>
        `;
        document.body.appendChild(notification);
        
        AnimationUtils.zoomIn(notification, 300);
        
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    },
    
    // Scroll to element smoothly
    scrollTo: function(selector, offset = 0) {
        const element = document.querySelector(selector);
        if (element) {
            window.smoothScrollTo(element, offset);
        }
    }
};
