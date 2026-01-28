/**
 * Theme Toggle System
 * Supports light/dark mode with persistence
 */

(function() {
    'use strict';
    
    const THEME_KEY = 'docsai_theme';
    const DEFAULT_THEME = 'light';
    
    /**
     * Get current theme from server-rendered data-theme, storage, or default
     */
    function getTheme() {
        // Prefer server-rendered data-theme (Django session) to avoid flash
        const dataTheme = document.documentElement.getAttribute('data-theme');
        if (dataTheme === 'light' || dataTheme === 'dark') {
            return dataTheme;
        }
        // Try sessionStorage
        if (typeof sessionStorage !== 'undefined') {
            const stored = sessionStorage.getItem(THEME_KEY);
            if (stored) {
                return stored;
            }
        }
        // Try cookie
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'theme') {
                return decodeURIComponent(value);
            }
        }
        // System preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return DEFAULT_THEME;
    }
    
    /**
     * Set theme
     */
    function setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        
        // Store in sessionStorage
        if (typeof sessionStorage !== 'undefined') {
            sessionStorage.setItem(THEME_KEY, theme);
        }
        
        // Store in cookie for Django session
        document.cookie = `theme=${encodeURIComponent(theme)}; path=/; max-age=31536000`; // 1 year
    }
    
    /**
     * Toggle theme
     */
    function toggleTheme() {
        const currentTheme = getTheme();
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
        return newTheme;
    }
    
    /**
     * Initialize theme on page load
     */
    function initTheme() {
        const theme = getTheme();
        setTheme(theme);
        
        // Listen for system theme changes
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                // Only auto-switch if user hasn't manually set a theme
                if (!sessionStorage.getItem(THEME_KEY) && !document.cookie.includes('theme=')) {
                    setTheme(e.matches ? 'dark' : 'light');
                }
            });
        }
    }
    
    /**
     * Theme toggle button handler – client-side only
     */
    function setupThemeToggle() {
        const toggleButtons = document.querySelectorAll('[data-theme-toggle]');

        toggleButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const newTheme = toggleTheme();
                window.dispatchEvent(new CustomEvent('themechange', { detail: { theme: newTheme } }));
            });
        });
    }
    
    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            initTheme();
            setupThemeToggle();
        });
    } else {
        initTheme();
        setupThemeToggle();
    }
    
    // Export for use in other scripts
    window.ThemeManager = {
        getTheme: getTheme,
        setTheme: setTheme,
        toggleTheme: toggleTheme
    };
})();
