/**
 * Durgasman Controller - Main application controller
 */

class DurgasmanController {
    constructor(options = {}) {
        this.options = options;
        this.activeRequest = null;
        this.collections = [];
        this.environments = [];
        this.history = [];

        // Initialize components
        this.requestBuilder = null;
        this.responseViewer = null;
        this.sidebar = null;

        this.init();
    }

    init() {
        console.log('Initializing Durgasman Controller...');
        this.loadCollections();
        this.loadEnvironments();
        this.loadHistory();

        // Initialize components if containers exist
        this.initComponents();
    }

    initComponents() {
        // Initialize request builder
        const requestBuilderEl = document.getElementById('request-builder-content');
        if (requestBuilderEl && typeof RequestBuilder !== 'undefined') {
            this.requestBuilder = new RequestBuilder('request-builder-content');
        }

        // Initialize response viewer
        const responseViewerEl = document.getElementById('response-viewer-content');
        if (responseViewerEl && typeof ResponseViewer !== 'undefined') {
            this.responseViewer = new ResponseViewer('response-viewer-content');
        }

        // Initialize sidebar
        const sidebarEl = document.getElementById('sidebar-content');
        if (sidebarEl && typeof Sidebar !== 'undefined') {
            this.sidebar = new Sidebar('sidebar-content');
        }
    }

    async loadCollections() {
        try {
            const response = await fetch('/durgasman/api/collections/');
            if (response.ok) {
                const data = await response.json();
                this.collections = data.collections || [];
                this.updateCollectionsUI();
            }
        } catch (error) {
            console.error('Failed to load collections:', error);
        }
    }

    async loadEnvironments() {
        try {
            const response = await fetch('/durgasman/api/environments/');
            if (response.ok) {
                const data = await response.json();
                this.environments = data.environments || [];
            }
        } catch (error) {
            console.error('Failed to load environments:', error);
        }
    }

    async loadHistory() {
        try {
            const response = await fetch('/durgasman/api/history/?limit=10');
            if (response.ok) {
                const data = await response.json();
                this.history = data.history || [];
                this.updateHistoryUI();
            }
        } catch (error) {
            console.error('Failed to load history:', error);
        }
    }

    updateCollectionsUI() {
        // Update sidebar if it exists
        if (this.sidebar && typeof this.sidebar.updateCollections === 'function') {
            this.sidebar.updateCollections(this.collections);
        }
    }

    updateHistoryUI() {
        // Update any history displays
        const historyContainer = document.getElementById('history-container');
        if (historyContainer) {
            this.renderHistory(historyContainer);
        }
    }

    renderHistory(container) {
        if (!container) return;

        if (this.history.length === 0) {
            container.innerHTML = '<div class="text-center py-8 text-slate-500">No test history yet</div>';
            return;
        }

        container.innerHTML = this.history.map(item => `
            <div class="flex items-center justify-between p-3 bg-slate-800 rounded-lg mb-2">
                <div class="flex items-center space-x-2">
                    <span class="px-2 py-1 text-xs font-bold rounded ${
                        item.response_status >= 200 && item.response_status < 300 ? 'bg-green-500/20 text-green-400' :
                        'bg-red-500/20 text-red-400'
                    }">${item.method}</span>
                    <div>
                        <div class="text-sm font-medium text-white truncate max-w-xs">${item.url}</div>
                        <div class="text-xs text-slate-500">${new Date(item.timestamp).toLocaleString()}</div>
                    </div>
                </div>
                <div class="flex items-center space-x-2">
                    <span class="px-2 py-1 text-xs rounded ${
                        item.response_status >= 200 && item.response_status < 300 ? 'bg-green-500/20 text-green-400' :
                        'bg-red-500/20 text-red-400'
                    }">${item.response_status}</span>
                    <span class="text-xs text-slate-500">${item.response_time_ms}ms</span>
                </div>
            </div>
        `).join('');
    }

    async executeRequest(requestData) {
        if (!requestData || !requestData.url) {
            throw new Error('Request data is required');
        }

        // Show loading state
        this.showLoading(true);

        try {
            const response = await fetch('/durgasman/api/execute/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify(requestData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            // Update response viewer
            if (this.responseViewer) {
                this.responseViewer.showResponse(result);
            }

            // Reload history
            this.loadHistory();

            return result;

        } catch (error) {
            console.error('Request execution failed:', error);

            // Show error in response viewer
            if (this.responseViewer) {
                this.responseViewer.showResponse({
                    status: 0,
                    statusText: 'Error',
                    error: error.message,
                    time: 0,
                    size: 0
                });
            }

            throw error;
        } finally {
            this.showLoading(false);
        }
    }

    showLoading(loading) {
        // Show/hide loading indicators
        const loadingElements = document.querySelectorAll('.durgasman-loading');
        loadingElements.forEach(el => {
            el.style.display = loading ? 'block' : 'none';
        });
    }

    getCsrfToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    // Utility methods
    formatSize(bytes) {
        if (!bytes || bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    formatDate(dateString) {
        try {
            return new Date(dateString).toLocaleString();
        } catch (e) {
            return dateString;
        }
    }
}

// Initialize globally
window.DurgasmanController = DurgasmanController;

// Auto-initialize if DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (document.querySelector('.durgasman-container') && typeof DurgasmanController !== 'undefined') {
        window.durgasmanController = new DurgasmanController();
    }
});