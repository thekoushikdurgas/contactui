/**
 * Search and Autocomplete Component
 * 
 * Provides enhanced search functionality with:
 * - Real-time search
 * - Autocomplete suggestions
 * - Search history
 * - Advanced filters
 */

class SearchAutocomplete {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.options = {
            searchUrl: options.searchUrl || '/docs/api/search/',
            resourceType: options.resourceType || 'all', // 'pages', 'endpoints', 'relationships', 'all'
            placeholder: options.placeholder || 'Search...',
            minQueryLength: options.minQueryLength || 2,
            debounceMs: options.debounceMs || 300,
            maxSuggestions: options.maxSuggestions || 10,
            onSelect: options.onSelect || null,
            ...options
        };
        
        if (!this.container) {
            throw new Error('Container element not found');
        }
        
        this.suggestions = [];
        this.searchHistory = this.loadSearchHistory();
        this.init();
    }
    
    init() {
        this.container.innerHTML = '';
        this.container.classList.add('search-autocomplete-wrapper');
        this.render();
        this.setupEventListeners();
    }
    
    render() {
        const html = `
            <div class="search-autocomplete">
                <div class="relative">
                    <input 
                        type="text" 
                        id="search-input"
                        class="search-input w-full px-4 py-2 pl-10 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="${this.escapeHtml(this.options.placeholder)}"
                        autocomplete="off"
                    />
                    <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                        </svg>
                    </div>
                    <button 
                        type="button"
                        id="clear-search-btn"
                        class="hidden absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    >
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                
                <!-- Suggestions Dropdown -->
                <div id="suggestions-dropdown" class="hidden absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg max-h-96 overflow-auto">
                    <div id="suggestions-list" class="suggestions-list"></div>
                </div>
            </div>
        `;
        
        this.container.innerHTML = html;
    }
    
    setupEventListeners() {
        const searchInput = this.container.querySelector('#search-input');
        const clearBtn = this.container.querySelector('#clear-search-btn');
        const suggestionsDropdown = this.container.querySelector('#suggestions-dropdown');
        
        if (!searchInput) return;
        
        let debounceTimeout;
        
        // Search input
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            
            // Show/hide clear button
            if (clearBtn) {
                if (query.length > 0) {
                    clearBtn.classList.remove('hidden');
                } else {
                    clearBtn.classList.add('hidden');
                }
            }
            
            clearTimeout(debounceTimeout);
            
            if (query.length < this.options.minQueryLength) {
                this.hideSuggestions();
                return;
            }
            
            debounceTimeout = setTimeout(() => {
                this.performSearch(query);
            }, this.options.debounceMs);
        });
        
        searchInput.addEventListener('focus', () => {
            if (searchInput.value.trim().length >= this.options.minQueryLength) {
                this.performSearch(searchInput.value.trim());
            } else if (this.searchHistory.length > 0) {
                this.showSearchHistory();
            }
        });
        
        searchInput.addEventListener('blur', () => {
            // Hide suggestions after a delay to allow clicks
            setTimeout(() => {
                this.hideSuggestions();
            }, 200);
        });
        
        // Clear button
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                searchInput.value = '';
                searchInput.focus();
                this.hideSuggestions();
                clearBtn.classList.add('hidden');
                this.triggerSearchChange('');
            });
        }
        
        // Keyboard navigation
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                this.navigateSuggestions(1);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                this.navigateSuggestions(-1);
            } else if (e.key === 'Enter') {
                e.preventDefault();
                this.selectHighlightedSuggestion();
            } else if (e.key === 'Escape') {
                this.hideSuggestions();
            }
        });
    }
    
    async performSearch(query) {
        try {
            const response = await fetch(`${this.options.searchUrl}?q=${encodeURIComponent(query)}&type=${this.options.resourceType}&limit=${this.options.maxSuggestions}`);
            if (response.ok) {
                const data = await response.json();
                this.suggestions = data.results || data.suggestions || [];
                this.showSuggestions();
            } else {
                // Fallback to local search
                this.suggestions = this.localSearch(query);
                this.showSuggestions();
            }
        } catch (error) {
            console.warn('Search API failed, using local search:', error);
            this.suggestions = this.localSearch(query);
            this.showSuggestions();
        }
    }
    
    localSearch(query) {
        // Simple local search implementation
        // This would typically search through cached items
        return [];
    }
    
    showSuggestions() {
        const suggestionsDropdown = this.container.querySelector('#suggestions-dropdown');
        const suggestionsList = this.container.querySelector('#suggestions-list');
        
        if (!suggestionsDropdown || !suggestionsList) return;
        
        if (this.suggestions.length === 0) {
            suggestionsList.innerHTML = `
                <div class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 text-center">
                    No results found
                </div>
            `;
        } else {
            suggestionsList.innerHTML = this.suggestions.map((suggestion, index) => `
                <div 
                    class="suggestion-item px-4 py-3 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer border-b border-gray-200 dark:border-gray-700 ${index === 0 ? 'bg-gray-50 dark:bg-gray-800' : ''}"
                    data-index="${index}"
                    data-value="${this.escapeHtml(JSON.stringify(suggestion))}"
                >
                    <div class="flex items-center gap-3">
                        <div class="flex-1">
                            <div class="font-medium text-gray-900 dark:text-gray-100">${this.escapeHtml(suggestion.title || suggestion.name || suggestion.id || '')}</div>
                            ${suggestion.description ? `
                                <div class="text-sm text-gray-500 dark:text-gray-400 mt-1">${this.escapeHtml(suggestion.description)}</div>
                            ` : ''}
                        </div>
                        <div class="text-xs text-gray-400 dark:text-gray-500">
                            ${suggestion.type || this.options.resourceType}
                        </div>
                    </div>
                </div>
            `).join('');
            
            // Add click handlers
            suggestionsList.querySelectorAll('.suggestion-item').forEach(item => {
                item.addEventListener('click', (e) => {
                    const index = parseInt(e.target.closest('.suggestion-item').getAttribute('data-index'));
                    this.selectSuggestion(this.suggestions[index]);
                });
            });
        }
        
        suggestionsDropdown.classList.remove('hidden');
    }
    
    showSearchHistory() {
        const suggestionsDropdown = this.container.querySelector('#suggestions-dropdown');
        const suggestionsList = this.container.querySelector('#suggestions-list');
        
        if (!suggestionsDropdown || !suggestionsList) return;
        
        suggestionsList.innerHTML = `
            <div class="px-4 py-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase border-b border-gray-200 dark:border-gray-700">
                Recent Searches
            </div>
            ${this.searchHistory.slice(0, 5).map(term => `
                <div 
                    class="suggestion-item px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer"
                    data-term="${this.escapeHtml(term)}"
                >
                    <div class="flex items-center gap-2">
                        <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                        <span class="text-sm text-gray-700 dark:text-gray-300">${this.escapeHtml(term)}</span>
                    </div>
                </div>
            `).join('')}
        `;
        
        suggestionsList.querySelectorAll('.suggestion-item').forEach(item => {
            item.addEventListener('click', () => {
                const term = item.getAttribute('data-term');
                const searchInput = this.container.querySelector('#search-input');
                if (searchInput) {
                    searchInput.value = term;
                    this.performSearch(term);
                }
            });
        });
        
        suggestionsDropdown.classList.remove('hidden');
    }
    
    hideSuggestions() {
        const suggestionsDropdown = this.container.querySelector('#suggestions-dropdown');
        if (suggestionsDropdown) {
            suggestionsDropdown.classList.add('hidden');
        }
    }
    
    selectSuggestion(suggestion) {
        this.addToSearchHistory(suggestion.title || suggestion.name || '');
        this.hideSuggestions();
        
        if (this.options.onSelect) {
            this.options.onSelect(suggestion);
        }
        
        const event = new CustomEvent('suggestion-selected', {
            detail: { suggestion: suggestion }
        });
        this.container.dispatchEvent(event);
    }
    
    navigateSuggestions(direction) {
        const suggestionsList = this.container.querySelector('#suggestions-list');
        if (!suggestionsList) return;
        
        const items = suggestionsList.querySelectorAll('.suggestion-item');
        const currentHighlighted = suggestionsList.querySelector('.suggestion-item.bg-blue-100');
        
        let nextIndex = 0;
        if (currentHighlighted) {
            const currentIndex = parseInt(currentHighlighted.getAttribute('data-index'));
            nextIndex = currentIndex + direction;
            if (nextIndex < 0) nextIndex = items.length - 1;
            if (nextIndex >= items.length) nextIndex = 0;
            currentHighlighted.classList.remove('bg-blue-100', 'dark:bg-blue-900');
        }
        
        if (items[nextIndex]) {
            items[nextIndex].classList.add('bg-blue-100', 'dark:bg-blue-900');
        }
    }
    
    selectHighlightedSuggestion() {
        const suggestionsList = this.container.querySelector('#suggestions-list');
        if (!suggestionsList) return;
        
        const highlighted = suggestionsList.querySelector('.suggestion-item.bg-blue-100');
        if (highlighted) {
            const index = parseInt(highlighted.getAttribute('data-index'));
            if (this.suggestions[index]) {
                this.selectSuggestion(this.suggestions[index]);
            }
        }
    }
    
    addToSearchHistory(term) {
        if (!term || term.trim().length === 0) return;
        
        this.searchHistory = this.searchHistory.filter(t => t !== term);
        this.searchHistory.unshift(term);
        this.searchHistory = this.searchHistory.slice(0, 10); // Keep last 10
        
        this.saveSearchHistory();
    }
    
    loadSearchHistory() {
        try {
            const stored = localStorage.getItem(`search_history_${this.options.resourceType}`);
            return stored ? JSON.parse(stored) : [];
        } catch (error) {
            return [];
        }
    }
    
    saveSearchHistory() {
        try {
            localStorage.setItem(`search_history_${this.options.resourceType}`, JSON.stringify(this.searchHistory));
        } catch (error) {
            console.warn('Failed to save search history:', error);
        }
    }
    
    triggerSearchChange(query) {
        const event = new CustomEvent('search-change', {
            detail: { query: query }
        });
        this.container.dispatchEvent(event);
    }
    
    escapeHtml(text) {
        if (text === null || text === undefined) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    getQuery() {
        const searchInput = this.container.querySelector('#search-input');
        return searchInput ? searchInput.value.trim() : '';
    }
    
    setQuery(query) {
        const searchInput = this.container.querySelector('#search-input');
        if (searchInput) {
            searchInput.value = query;
            if (query.length >= this.options.minQueryLength) {
                this.performSearch(query);
            }
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SearchAutocomplete;
}
