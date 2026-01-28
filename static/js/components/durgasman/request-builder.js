/**
 * Request Builder Component - Builds and configures API requests
 */

class RequestBuilder {
    constructor(containerId, initialRequest = null) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.request = initialRequest || this.getDefaultRequest();
        this.activeTab = 'params';

        if (!this.container) {
            console.error(`RequestBuilder: Container #${containerId} not found`);
            return;
        }

        this.init();
    }

    getDefaultRequest() {
        return {
            id: null,
            name: 'New Request',
            method: 'GET',
            url: 'https://jsonplaceholder.typicode.com/posts/1',
            headers: [
                { key: 'Accept', value: 'application/json', enabled: true },
                { key: 'Content-Type', value: 'application/json', enabled: true }
            ],
            params: [],
            body: '',
            auth_type: 'None'
        };
    }

    init() {
        this.render();
        this.attachEventListeners();
    }

    render() {
        this.container.innerHTML = `
            <div class="bg-slate-900 border-b border-slate-800 p-4">
                <!-- Method and URL Bar -->
                <div class="flex gap-2 mb-4">
                    <select id="method-select" class="bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm font-bold text-orange-400 outline-none focus:ring-1 focus:ring-orange-500">
                        ${['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'].map(method =>
                            `<option value="${method}" ${this.request.method === method ? 'selected' : ''}>${method}</option>`
                        ).join('')}
                    </select>
                    <input type="text" id="url-input" value="${this.escapeHtml(this.request.url)}"
                           class="flex-1 bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm text-slate-200 placeholder-slate-500 outline-none focus:ring-1 focus:ring-orange-500"
                           placeholder="https://api.example.com/v1/resource">
                    <button id="send-btn" class="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium px-6 py-2 rounded flex items-center gap-2 transition-all shadow-lg disabled:cursor-not-allowed">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
                        </svg>
                        <span id="send-text">Send</span>
                    </button>
                    <button id="save-btn" class="px-4 py-2 rounded flex items-center gap-2 transition-all border border-slate-700 ${
                        this.request.id ? 'bg-orange-600/10 hover:bg-orange-600/20 text-orange-500 border-orange-500/30' : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
                    }">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"/>
                        </svg>
                        Save
                    </button>
                </div>

                <!-- Tabs -->
                <div class="flex border-b border-slate-800">
                    ${['params', 'headers', 'body', 'auth', 'tests'].map(tab => `
                        <button class="px-4 py-2 text-xs font-medium border-b-2 transition-colors ${
                            this.activeTab === tab ? 'border-orange-500 text-orange-500' : 'border-transparent text-slate-500 hover:text-slate-300'
                        }" data-tab="${tab}">${this.capitalize(tab)}</button>
                    `).join('')}
                </div>
            </div>

            <!-- Tab Content -->
            <div class="flex-1 overflow-y-auto p-4 custom-scrollbar">
                <div id="params-tab" class="tab-content ${this.activeTab === 'params' ? '' : 'hidden'}">
                    ${this.renderKeyValueEditor(this.request.params || [], 'params')}
                </div>
                <div id="headers-tab" class="tab-content ${this.activeTab === 'headers' ? '' : 'hidden'}">
                    ${this.renderKeyValueEditor(this.request.headers || [], 'headers')}
                </div>
                <div id="body-tab" class="tab-content ${this.activeTab === 'body' ? '' : 'hidden'}">
                    <div class="h-full flex flex-col">
                        <div class="flex gap-4 mb-3 text-xs text-slate-500">
                            <label class="flex items-center gap-1 cursor-pointer">
                                <input type="radio" name="body-type" value="json" checked>
                                raw (JSON)
                            </label>
                        </div>
                        <textarea id="body-textarea" class="flex-1 w-full bg-slate-900 border border-slate-800 rounded p-4 text-sm font-mono text-blue-300 placeholder-slate-700 outline-none focus:ring-1 focus:ring-orange-500 min-h-[300px] resize-none"
                                  placeholder='{"key": "value"}'>${this.escapeHtml(this.request.body || '')}</textarea>
                    </div>
                </div>
                <div id="auth-tab" class="tab-content ${this.activeTab === 'auth' ? '' : 'hidden'}">
                    <div class="flex flex-col items-center justify-center h-full text-slate-600 opacity-50">
                        <svg class="w-12 h-12 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/>
                        </svg>
                        <p class="text-sm">Authentication config goes here</p>
                        <p class="text-xs text-center mt-1">Bearer Token, API Key, Basic Auth, etc.</p>
                    </div>
                </div>
                <div id="tests-tab" class="tab-content ${this.activeTab === 'tests' ? '' : 'hidden'}">
                    <div class="flex flex-col items-center justify-center h-full text-slate-600 opacity-50">
                        <svg class="w-12 h-12 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                        <p class="text-sm">Test scripts go here</p>
                        <p class="text-xs text-center mt-1">Pre-request and test scripts</p>
                    </div>
                </div>
            </div>
        `;
    }

    renderKeyValueEditor(items, type) {
        const title = type === 'params' ? 'Query Parameters' : 'Headers';

        return `
            <div class="space-y-2">
                <div class="flex items-center justify-between mb-2">
                    <h3 class="text-xs font-semibold text-slate-500 uppercase tracking-wider">${title}</h3>
                    <button class="text-blue-500 hover:text-blue-400 text-xs flex items-center gap-1 add-kv-btn" data-type="${type}">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
                        </svg>
                        Add ${type.slice(0, -1)}
                    </button>
                </div>
                <div class="border border-slate-800 rounded overflow-hidden">
                    <table class="w-full text-left text-xs">
                        <thead class="bg-slate-800/50 text-slate-400">
                            <tr>
                                <th class="px-3 py-2 w-10"></th>
                                <th class="px-3 py-2 border-l border-slate-800">Key</th>
                                <th class="px-3 py-2 border-l border-slate-800">Value</th>
                                <th class="px-3 py-2 border-l border-slate-800 w-10"></th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-800">
                            ${items.map((item, index) => `
                                <tr class="hover:bg-slate-800/30">
                                    <td class="px-3 py-1">
                                        <input type="checkbox" class="kv-enabled" data-index="${index}" ${item.enabled !== false ? 'checked' : ''}>
                                    </td>
                                    <td class="border-l border-slate-800">
                                        <input type="text" value="${this.escapeHtml(item.key || '')}" class="kv-key w-full bg-transparent px-3 py-2 text-slate-300 outline-none" data-index="${index}" placeholder="Key">
                                    </td>
                                    <td class="border-l border-slate-800">
                                        <input type="text" value="${this.escapeHtml(item.value || '')}" class="kv-value w-full bg-transparent px-3 py-2 text-slate-300 outline-none" data-index="${index}" placeholder="Value">
                                    </td>
                                    <td class="px-3 py-1 text-center">
                                        <button class="text-slate-600 hover:text-red-500 transition-colors remove-kv-btn" data-index="${index}" data-type="${type}">
                                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                                            </svg>
                                        </button>
                                    </td>
                                </tr>
                            `).join('')}
                            ${items.length === 0 ? `
                                <tr>
                                    <td colspan="4" class="px-3 py-8 text-center text-slate-600 italic">No items defined</td>
                                </tr>
                            ` : ''}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }

    attachEventListeners() {
        const container = this.container;

        // Tab switching
        container.querySelectorAll('[data-tab]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tabName = e.target.dataset.tab;
                this.switchTab(tabName);
            });
        });

        // Method and URL changes
        const methodSelect = container.querySelector('#method-select');
        const urlInput = container.querySelector('#url-input');

        if (methodSelect) {
            methodSelect.addEventListener('change', (e) => {
                this.request.method = e.target.value;
            });
        }

        if (urlInput) {
            urlInput.addEventListener('input', (e) => {
                this.request.url = e.target.value;
            });
        }

        // Send button
        const sendBtn = container.querySelector('#send-btn');
        if (sendBtn) {
            sendBtn.addEventListener('click', () => {
                this.sendRequest();
            });
        }

        // Save button
        const saveBtn = container.querySelector('#save-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => {
                this.saveRequest();
            });
        }

        // Add key-value buttons
        container.querySelectorAll('.add-kv-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const type = e.currentTarget.dataset.type;
                this.addKeyValueItem(type);
            });
        });

        // Remove key-value buttons
        container.querySelectorAll('.remove-kv-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const type = e.currentTarget.dataset.type;
                const index = parseInt(e.currentTarget.dataset.index);
                this.removeKeyValueItem(type, index);
            });
        });

        // Key-value input changes
        container.addEventListener('input', (e) => {
            if (e.target.classList.contains('kv-key') || e.target.classList.contains('kv-value')) {
                const index = parseInt(e.target.dataset.index);
                const field = e.target.classList.contains('kv-key') ? 'key' : 'value';
                const type = e.target.closest('.tab-content').id.replace('-tab', '');
                this.updateKeyValueItem(type, index, field, e.target.value);
            }
        });

        // Key-value enabled checkboxes
        container.addEventListener('change', (e) => {
            if (e.target.classList.contains('kv-enabled')) {
                const index = parseInt(e.target.dataset.index);
                const type = e.target.closest('.tab-content').id.replace('-tab', '');
                this.updateKeyValueItem(type, index, 'enabled', e.target.checked);
            }
        });

        // Body textarea
        const bodyTextarea = container.querySelector('#body-textarea');
        if (bodyTextarea) {
            bodyTextarea.addEventListener('input', (e) => {
                this.request.body = e.target.value;
            });
        }
    }

    switchTab(tabName) {
        this.activeTab = tabName;

        // Hide all tabs
        this.container.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.add('hidden');
        });

        // Show selected tab
        const selectedTab = this.container.querySelector(`#${tabName}-tab`);
        if (selectedTab) {
            selectedTab.classList.remove('hidden');
        }

        // Update tab button styles
        this.container.querySelectorAll('[data-tab]').forEach(btn => {
            if (btn.dataset.tab === tabName) {
                btn.classList.add('border-orange-500', 'text-orange-500');
                btn.classList.remove('border-transparent', 'text-slate-500');
            } else {
                btn.classList.remove('border-orange-500', 'text-orange-500');
                btn.classList.add('border-transparent', 'text-slate-500');
            }
        });
    }

    async sendRequest() {
        const sendBtn = this.container.querySelector('#send-btn');
        const sendText = this.container.querySelector('#send-text');

        if (!sendBtn || !sendText) return;

        // Show loading state
        sendBtn.disabled = true;
        sendText.textContent = 'Sending...';

        try {
            const requestData = {
                method: this.request.method,
                url: this.request.url,
                headers: this.request.headers.filter(h => h.enabled !== false),
                body: this.request.body
            };

            // Use global controller if available
            if (window.durgasmanController) {
                await window.durgasmanController.executeRequest(requestData);
            } else {
                // Fallback: direct API call
                const response = await fetch('/durgasman/api/execute/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCsrfToken()
                    },
                    body: JSON.stringify(requestData)
                });

                const result = await response.json();

                if (window.responseViewer) {
                    window.responseViewer.showResponse(result);
                }
            }

        } catch (error) {
            console.error('Request failed:', error);
            if (window.responseViewer) {
                window.responseViewer.showResponse({
                    status: 0,
                    statusText: 'Error',
                    error: error.message,
                    time: 0,
                    size: 0
                });
            }
        } finally {
            // Reset button state
            sendBtn.disabled = false;
            sendText.textContent = 'Send';
        }
    }

    async saveRequest() {
        // Implementation for saving request
        console.log('Save request functionality to be implemented');
    }

    addKeyValueItem(type) {
        if (!this.request[type]) {
            this.request[type] = [];
        }

        this.request[type].push({
            key: '',
            value: '',
            enabled: true
        });

        // Re-render the current tab
        this.switchTab(this.activeTab);
        this.attachEventListeners(); // Re-attach listeners
    }

    removeKeyValueItem(type, index) {
        if (this.request[type] && this.request[type][index]) {
            this.request[type].splice(index, 1);
            this.switchTab(this.activeTab);
            this.attachEventListeners(); // Re-attach listeners
        }
    }

    updateKeyValueItem(type, index, field, value) {
        if (this.request[type] && this.request[type][index]) {
            this.request[type][index][field] = value;
        }
    }

    loadRequest(requestData) {
        this.request = { ...requestData };
        this.render();
        this.attachEventListeners();
    }

    getCsrfToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    capitalize(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Export for global use
window.RequestBuilder = RequestBuilder;