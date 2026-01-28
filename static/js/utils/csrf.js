/**
 * CSRF Token Utility
 * 
 * Helper functions for working with Django CSRF tokens
 */

/**
 * Get CSRF token from cookies
 */
function getCSRFToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    
    return cookieValue;
}

/**
 * Get CSRF token from meta tag (if available)
 */
function getCSRFTokenFromMeta() {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag) {
        return metaTag.getAttribute('content');
    }
    return null;
}

/**
 * Get CSRF token (tries meta tag first, then cookies)
 */
function getCSRFTokenSafe() {
    return getCSRFTokenFromMeta() || getCSRFToken();
}

/**
 * Add CSRF token to fetch headers
 */
function addCSRFToHeaders(headers = {}) {
    const token = getCSRFTokenSafe();
    if (token) {
        headers['X-CSRFToken'] = token;
    }
    return headers;
}

// Export for global use
window.getCSRFToken = getCSRFToken;
window.getCSRFTokenFromMeta = getCSRFTokenFromMeta;
window.getCSRFTokenSafe = getCSRFTokenSafe;
window.addCSRFToHeaders = addCSRFToHeaders;
