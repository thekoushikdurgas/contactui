/**
 * Sidebar Component - Navigation and collections list
 */

class Sidebar {
    constructor(containerId) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);

        if (!this.container) {
            console.error(`Sidebar: Container #${containerId} not found`);
            return;
        }

        this.init();
    }

    init() {
        this.loadCollections();
    }

    async loadCollections() {
        try {
            const response = await fetch('/durgasman/api/collections/');
            if (response.ok) {
                const data = await response.json();
                this.renderCollections(data.collections || []);
            }
        } catch (error) {
            console.error('Failed to load collections:', error);
            this.renderCollections([]);
        }
    }

    renderCollections(collections) {
        this.container.innerHTML = `
            <div class="p-4 border-b border-slate-800">
                <div class="flex items-center justify-between">
                    <h2 class="text-lg font-semibold text-white">Collections</h2>
                    <button class="px-3 py-1 bg-orange-600 hover:bg-orange-500 text-white text-sm rounded transition-colors" onclick="this.createNewCollection()">
                        New
                    </button>
                </div>
            </div>
            <div class="flex-1 overflow-y-auto p-4 space-y-2">
                ${collections.map(collection => `
                    <div class="p-3 bg-slate-800 hover:bg-slate-700 rounded-lg cursor-pointer transition-colors border border-slate-600 collection-item"
                         data-collection-id="${collection.id}">
                        <div class="font-medium text-white truncate">${this.escapeHtml(collection.name)}</div>
                        <div class="text-sm text-slate-400">${collection.requests_count || 0} requests</div>
                        <div class="text-xs text-slate-500 mt-1">${this.formatDate(collection.created_at)}</div>
                    </div>
                `).join('')}

                ${collections.length === 0 ? `
                    <div class="text-center py-8 text-slate-500">
                        <div class="text-4xl mb-2">📁</div>
                        <div>No collections yet</div>
                        <div class="text-sm">Import from your documentation</div>
                    </div>
                ` : ''}
            </div>

            <!-- Environments Section -->
            <div class="p-4 border-t border-slate-800">
                <div class="flex items-center justify-between mb-3">
                    <h3 class="text-sm font-semibold text-slate-400 uppercase tracking-wider">Environments</h3>
                    <button class="px-2 py-1 bg-slate-700 hover:bg-slate-600 text-slate-300 text-xs rounded transition-colors" onclick="this.createNewEnvironment()">
                        +
                    </button>
                </div>
                <div id="environments-list" class="space-y-1">
                    <!-- Environments will be loaded here -->
                </div>
            </div>
        `;

        // Attach event listeners
        this.attachEventListeners();
        this.loadEnvironments();
    }

    async loadEnvironments() {
        try {
            const response = await fetch('/durgasman/api/environments/');
            if (response.ok) {
                const data = await response.json();
                this.renderEnvironments(data.environments || []);
            }
        } catch (error) {
            console.error('Failed to load environments:', error);
        }
    }

    renderEnvironments(environments) {
        const envList = this.container.querySelector('#environments-list');
        if (!envList) return;

        envList.innerHTML = environments.map(env => `
            <div class="text-xs text-slate-500 hover:text-slate-300 cursor-pointer py-1 px-2 rounded hover:bg-slate-800/50 transition-colors environment-item"
                 data-environment-id="${env.id}">
                ${this.escapeHtml(env.name)}
            </div>
        `).join('');

        if (environments.length === 0) {
            envList.innerHTML = '<div class="text-xs text-slate-600 italic">No environments</div>';
        }
    }

    attachEventListeners() {
        // Collection click handlers
        this.container.querySelectorAll('.collection-item').forEach(item => {
            item.addEventListener('click', () => {
                const collectionId = item.dataset.collectionId;
                this.selectCollection(collectionId);
            });
        });

        // Environment click handlers
        this.container.addEventListener('click', (e) => {
            if (e.target.classList.contains('environment-item')) {
                const envId = e.target.dataset.environmentId;
                this.selectEnvironment(envId);
            }
        });
    }

    selectCollection(collectionId) {
        // Update UI to show selected collection
        this.container.querySelectorAll('.collection-item').forEach(item => {
            item.classList.remove('ring-2', 'ring-orange-500', 'bg-slate-700');
            item.classList.add('bg-slate-800');
        });

        const selectedItem = this.container.querySelector(`[data-collection-id="${collectionId}"]`);
        if (selectedItem) {
            selectedItem.classList.remove('bg-slate-800');
            selectedItem.classList.add('bg-slate-700', 'ring-2', 'ring-orange-500');
        }

        // Trigger collection load event
        if (window.durgasmanController) {
            window.durgasmanController.loadCollectionRequests(collectionId);
        }
    }

    selectEnvironment(environmentId) {
        // Update active environment
        this.container.querySelectorAll('.environment-item').forEach(item => {
            item.classList.remove('text-orange-400', 'font-medium');
            item.classList.add('text-slate-500');
        });

        const selectedItem = this.container.querySelector(`[data-environment-id="${environmentId}"]`);
        if (selectedItem) {
            selectedItem.classList.remove('text-slate-500');
            selectedItem.classList.add('text-orange-400', 'font-medium');
        }

        // Store active environment
        localStorage.setItem('durgasman_active_env', environmentId);
    }

    createNewCollection() {
        const name = prompt('Enter collection name:');
        if (name && name.trim()) {
            // This would make an API call to create the collection
            console.log('Create collection:', name);
            // Reload collections after creation
            this.loadCollections();
        }
    }

    createNewEnvironment() {
        const name = prompt('Enter environment name:');
        if (name && name.trim()) {
            // This would make an API call to create the environment
            console.log('Create environment:', name);
            // Reload environments after creation
            this.loadEnvironments();
        }
    }

    updateCollections(collections) {
        // Method to update collections from external source
        this.renderCollections(collections);
    }

    formatDate(dateString) {
        try {
            return new Date(dateString).toLocaleDateString();
        } catch (e) {
            return dateString;
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Export for global use
window.Sidebar = Sidebar;