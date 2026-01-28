// Animation utilities for DocsAI - React Design Patterns

/**
 * Intersection Observer for scroll animations
 */
const ScrollAnimations = {
    init: function() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                    entry.target.style.opacity = '1';
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);
        
        // Observe elements with data-animate attribute
        document.querySelectorAll('[data-animate]').forEach(el => {
            el.style.opacity = '0';
            observer.observe(el);
        });
    }
};

/**
 * Stagger animation for lists
 */
function staggerAnimation(selector, delay = 50) {
    const elements = document.querySelectorAll(selector);
    elements.forEach((el, index) => {
        setTimeout(() => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(20px)';
            el.style.transition = 'opacity 0.5s ease-out, transform 0.5s ease-out';
            
            requestAnimationFrame(() => {
                el.style.opacity = '1';
                el.style.transform = 'translateY(0)';
            });
        }, index * delay);
    });
}

/**
 * Pulse animation for loading states
 */
function pulseAnimation(element) {
    if (!element) return;
    
    element.classList.add('animate-pulse');
    return () => {
        element.classList.remove('animate-pulse');
    };
}

/**
 * Spin animation for loading spinners
 */
function spinAnimation(element) {
    if (!element) return;
    
    element.classList.add('animate-spin');
    return () => {
        element.classList.remove('animate-spin');
    };
}

/**
 * Bounce animation for notifications
 */
function bounceAnimation(element) {
    if (!element) return;
    
    element.classList.add('animate-bounce');
    setTimeout(() => {
        element.classList.remove('animate-bounce');
    }, 1000);
}

/**
 * Initialize all animations on DOM ready
 */
document.addEventListener('DOMContentLoaded', function() {
    ScrollAnimations.init();
    
    // Stagger animation for lists
    const lists = document.querySelectorAll('[data-stagger]');
    lists.forEach(list => {
        staggerAnimation(list.children, 50);
    });
});

// Export for use in other scripts
window.AnimationUtils = {
    stagger: staggerAnimation,
    pulse: pulseAnimation,
    spin: spinAnimation,
    bounce: bounceAnimation
};
