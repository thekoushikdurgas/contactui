/**
 * Sidebar Keyboard Navigation
 * Provides keyboard navigation support for sidebar menu
 */

(function() {
    'use strict';

    /**
     * Get all focusable elements in sidebar
     */
    function getFocusableElements() {
        const sidebar = document.getElementById('app-sidebar');
        if (!sidebar) return [];

        return Array.from(sidebar.querySelectorAll(
            'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])'
        )).filter(el => {
            // Filter out hidden elements
            return el.offsetParent !== null && 
                   !el.classList.contains('hidden') &&
                   window.getComputedStyle(el).visibility !== 'hidden';
        });
    }

    /**
     * Get current focused element index
     */
    function getCurrentIndex(elements) {
        return elements.findIndex(el => el === document.activeElement);
    }

    /**
     * Focus element at index
     */
    function focusElement(elements, index) {
        if (index >= 0 && index < elements.length) {
            elements[index].focus();
            // Scroll into view if needed
            elements[index].scrollIntoView({ 
                behavior: 'smooth', 
                block: 'nearest' 
            });
        }
    }

    /**
     * Handle keyboard navigation
     */
    function handleKeyboardNavigation(e) {
        const sidebar = document.getElementById('app-sidebar');
        if (!sidebar || !sidebar.contains(document.activeElement)) {
            return;
        }

        const focusableElements = getFocusableElements();
        if (focusableElements.length === 0) return;

        const currentIndex = getCurrentIndex(focusableElements);
        let newIndex = currentIndex;

        switch(e.key) {
            case 'ArrowDown':
                e.preventDefault();
                newIndex = (currentIndex + 1) % focusableElements.length;
                focusElement(focusableElements, newIndex);
                break;

            case 'ArrowUp':
                e.preventDefault();
                newIndex = currentIndex <= 0 
                    ? focusableElements.length - 1 
                    : currentIndex - 1;
                focusElement(focusableElements, newIndex);
                break;

            case 'ArrowRight':
                e.preventDefault();
                const currentElement = focusableElements[currentIndex];
                // If it's a group header or item with children, expand it
                if (currentElement.classList.contains('group-header')) {
                    toggleSidebarGroup(currentElement);
                } else if (currentElement.closest('.sidebar-link-item-wrapper')) {
                    const wrapper = currentElement.closest('.sidebar-link-item-wrapper');
                    const hasChildren = wrapper.querySelector('.nested-children');
                    if (hasChildren && typeof toggleNestedChildren === 'function') {
                        toggleNestedChildren(wrapper);
                        // Focus first child if expanded
                        setTimeout(() => {
                            const children = wrapper.querySelectorAll('.nested-children a');
                            if (children.length > 0) {
                                children[0].focus();
                            }
                        }, 100);
                    }
                }
                break;

            case 'ArrowLeft':
                e.preventDefault();
                const activeElement = focusableElements[currentIndex];
                // If it's a nested item, collapse parent
                if (activeElement.closest('.nested-children')) {
                    const wrapper = activeElement.closest('.sidebar-link-item-wrapper');
                    if (wrapper && typeof toggleNestedChildren === 'function') {
                        toggleNestedChildren(wrapper);
                        // Focus parent
                        const parentLink = wrapper.querySelector('a');
                        if (parentLink) {
                            parentLink.focus();
                        }
                    }
                } else if (activeElement.closest('.group-items')) {
                    // If it's a group item, collapse group
                    const group = activeElement.closest('.sidebar-group');
                    if (group) {
                        const groupHeader = group.querySelector('.group-header');
                        if (groupHeader && typeof toggleSidebarGroup === 'function') {
                            toggleSidebarGroup(groupHeader);
                            // Focus group header
                            groupHeader.focus();
                        }
                    }
                }
                break;

            case 'Enter':
            case ' ':
                // Allow default behavior (link navigation or button click)
                // But prevent if it's a toggle button
                const target = focusableElements[currentIndex];
                if (target.classList.contains('group-header') || 
                    target.onclick || 
                    target.getAttribute('onclick')) {
                    // Let the onclick handler run
                    return;
                }
                // For links, allow default navigation
                break;

            case 'Home':
                e.preventDefault();
                focusElement(focusableElements, 0);
                break;

            case 'End':
                e.preventDefault();
                focusElement(focusableElements, focusableElements.length - 1);
                break;

            case 'Escape':
                // Close sidebar on mobile
                if (window.innerWidth < 768) {
                    const sidebarBtn = document.getElementById('sidebar-menu-btn');
                    const overlay = document.getElementById('sidebar-overlay');
                    if (sidebarBtn && overlay && !overlay.classList.contains('hidden')) {
                        sidebarBtn.click();
                    }
                }
                break;
        }
    }

    /**
     * Initialize keyboard navigation
     */
    function initKeyboardNavigation() {
        // Add keyboard event listener
        document.addEventListener('keydown', handleKeyboardNavigation);

        // Add ARIA attributes for better screen reader support
        const sidebar = document.getElementById('app-sidebar');
        if (sidebar) {
            sidebar.setAttribute('role', 'navigation');
            sidebar.setAttribute('aria-label', 'Main navigation');

            // Mark groups as menus
            const groups = sidebar.querySelectorAll('.sidebar-group');
            groups.forEach(group => {
                const groupHeader = group.querySelector('.group-header');
                const groupItems = group.querySelector('.group-items');
                
                if (groupHeader && groupItems) {
                    groupHeader.setAttribute('role', 'button');
                    groupHeader.setAttribute('aria-haspopup', 'true');
                    groupItems.setAttribute('role', 'menu');
                    
                    // Update aria-expanded on toggle
                    const observer = new MutationObserver(() => {
                        const isExpanded = !groupItems.classList.contains('hidden');
                        groupHeader.setAttribute('aria-expanded', isExpanded.toString());
                    });
                    observer.observe(groupItems, { 
                        attributes: true, 
                        attributeFilter: ['class'] 
                    });
                }
            });

            // Mark link items
            const linkItems = sidebar.querySelectorAll('.sidebar-link-item-wrapper');
            linkItems.forEach(wrapper => {
                const link = wrapper.querySelector('a');
                const children = wrapper.querySelector('.nested-children');
                
                if (link) {
                    link.setAttribute('role', 'menuitem');
                    
                    if (children) {
                        link.setAttribute('aria-haspopup', 'true');
                        link.setAttribute('aria-expanded', 
                            children.classList.contains('hidden') ? 'false' : 'true');
                    }
                }
            });

            // Mark nested items
            const nestedItems = sidebar.querySelectorAll('.nested-children a');
            nestedItems.forEach(item => {
                item.setAttribute('role', 'menuitem');
            });
        }
    }

    /**
     * Enhanced toggle functions with ARIA updates
     */
    function enhanceToggleFunctions() {
        // Enhance toggleSidebarGroup if it exists
        if (typeof window.toggleSidebarGroup === 'function') {
            const originalToggle = window.toggleSidebarGroup;
            window.toggleSidebarGroup = function(button) {
                originalToggle(button);
                const groupItems = button.nextElementSibling;
                if (groupItems) {
                    const isExpanded = !groupItems.classList.contains('hidden');
                    button.setAttribute('aria-expanded', isExpanded.toString());
                }
            };
        }

        // Enhance toggleNestedChildren if it exists
        if (typeof window.toggleNestedChildren === 'function') {
            const originalToggle = window.toggleNestedChildren;
            window.toggleNestedChildren = function(wrapper) {
                originalToggle(wrapper);
                const children = wrapper.querySelector('.nested-children');
                const link = wrapper.querySelector('a');
                if (children && link) {
                    const isExpanded = !children.classList.contains('hidden');
                    link.setAttribute('aria-expanded', isExpanded.toString());
                }
            };
        }
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            initKeyboardNavigation();
            enhanceToggleFunctions();
        });
    } else {
        initKeyboardNavigation();
        enhanceToggleFunctions();
    }

    // Export functions for external use
    window.SidebarKeyboard = {
        getFocusableElements: getFocusableElements,
        focusElement: focusElement,
        handleKeyboardNavigation: handleKeyboardNavigation
    };

})();
