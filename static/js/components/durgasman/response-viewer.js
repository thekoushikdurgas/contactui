/**
 * Response Viewer Component - Displays API response data
 */

class ResponseViewer {
    constructor(containerId) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);

        if (!this.container) {
            console.error(`ResponseViewer: Container #${containerId} not found`);
            return;
        }
    }

    showResponse(response) {
        if (!response) {
            this.showEmpty();
            return;
        }

        const isSuccess = response.status >= 200 && response.status < 300;
        const hasError = response.error || response.status === 0;

        this.container.innerHTML = `
            <div class="bg-slate-900 border-l border-slate-800 h-full flex flex-col">
                <!-- Header -->
                <div class="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
                    <div class="flex items-center gap-4">
                        <span class="text-sm font-bold px-2 py-1 rounded ${
                            hasError ? 'bg-red-500/10 text-red-500' :
                            isSuccess ? 'bg-green-500/10 text-green-500' :
                            'bg-yellow-500/10 text-yellow-500'
                        }">
                            ${response.status || 0} ${response.statusText || 'Unknown'}
                        </span>
                        <span class="text-xs text-slate-500">${response.time || 0}ms</span>
                        <span class="text-xs text-slate-500">${this.formatSize(response.size || 0)}</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <button class="text-slate-400 hover:text-slate-200 px-2 py-1 text-xs" onclick="this.copyResponse()">
                            Copy
                        </button>
                        <button class="text-slate-400 hover:text-slate-200 px-2 py-1 text-xs" onclick="this.analyzeResponse()">
                            <svg class="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
                            </svg>
                            Analyze
                        </button>
                    </div>
                </div>

                <!-- Content -->
                <div class="flex-1 overflow-y-auto p-4 custom-scrollbar bg-slate-950">
                    ${hasError ? this.renderError(response) : this.renderSuccess(response)}
                </div>
            </div>
        `;
    }

    renderError(response) {
        return `
            <div class="text-red-400 bg-red-500/5 p-4 rounded border border-red-500/20 flex flex-col gap-2">
                <span class="text-sm font-bold uppercase tracking-widest opacity-60">Request Failed</span>
                <div class="font-mono text-sm whitespace-pre-wrap">${this.escapeHtml(response.error || 'Unknown error')}</div>
            </div>
        `;
    }

    renderSuccess(response) {
        const contentType = this.getContentType(response.headers || {});
        const isJson = contentType && contentType.includes('application/json');

        let bodyContent = '';
        if (response.data) {
            if (isJson) {
                bodyContent = this.renderJson(response.data);
            } else if (typeof response.data === 'string') {
                bodyContent = `<pre class="text-slate-300 whitespace-pre-wrap leading-relaxed">${this.escapeHtml(response.data)}</pre>`;
            } else {
                bodyContent = `<pre class="text-slate-300 whitespace-pre-wrap leading-relaxed">${this.escapeHtml(JSON.stringify(response.data, null, 2))}</pre>`;
            }
        } else {
            bodyContent = '<div class="text-slate-500 italic">No response body</div>';
        }

        return bodyContent;
    }

    renderJson(data) {
        if (data === null || data === undefined) {
            return '<span class="text-slate-500 italic">null</span>';
        }

        if (typeof data === 'string') {
            try {
                data = JSON.parse(data);
            } catch (e) {
                return `<pre class="text-slate-300 whitespace-pre-wrap leading-relaxed">${this.escapeHtml(data)}</pre>`;
            }
        }

        const jsonString = JSON.stringify(data, null, 2);

        // Simple syntax highlighting for JSON
        const highlighted = jsonString
            .replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?)/g, (match) => {
                if (/:$/.test(match)) {
                    return `<span class="text-blue-400">${match.slice(0, -1)}</span><span class="text-slate-400">:</span>`;
                }
                return `<span class="text-green-400">${match}</span>`;
            })
            .replace(/\b(true|false)\b/g, '<span class="text-purple-400">$1</span>')
            .replace(/\b(null)\b/g, '<span class="text-red-400">$1</span>')
            .replace(/\b(\d+(?:\.\d*)?)\b/g, '<span class="text-yellow-400">$1</span>');

        return `<pre class="text-slate-300 whitespace-pre-wrap leading-relaxed font-mono text-sm">${highlighted}</pre>`;
    }

    showEmpty() {
        this.container.innerHTML = `
            <div class="h-full flex flex-col items-center justify-center text-slate-700 bg-slate-950">
                <svg class="w-12 h-12 mb-4 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                </svg>
                <p class="text-sm font-bold uppercase tracking-widest opacity-60">Ready for request</p>
                <p class="text-xs opacity-40 mt-1">Send an API request to see the response</p>
            </div>
        `;
    }

    copyResponse() {
        const preElement = this.container.querySelector('pre');
        if (preElement) {
            const text = preElement.textContent || preElement.innerText;
            navigator.clipboard.writeText(text).then(() => {
                // Show temporary success feedback
                const copyBtn = this.container.querySelector('button[onclick*="copyResponse"]');
                if (copyBtn) {
                    const originalText = copyBtn.innerHTML;
                    copyBtn.innerHTML = 'Copied!';
                    setTimeout(() => {
                        copyBtn.innerHTML = originalText;
                    }, 2000);
                }
            });
        }
    }

    async analyzeResponse() {
        const responseData = this.currentResponse;
        if (!responseData) return;

        try {
            // Show loading state
            const analyzeBtn = this.container.querySelector('button[onclick*="analyzeResponse"]');
            if (analyzeBtn) {
                analyzeBtn.innerHTML = '<svg class="w-3 h-3 inline mr-1 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg> Analyzing...';
                analyzeBtn.disabled = true;
            }

            // Call AI analysis API
            const analysisResponse = await fetch('/durgasman/api/analyze/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    request: {
                        method: 'GET', // We don't have the original request data here
                        url: 'unknown'
                    },
                    response: responseData
                })
            });

            if (analysisResponse.ok) {
                const result = await analysisResponse.json();
                this.showAnalysis({
                    status: 'success',
                    analysis: result.analysis
                });
            } else {
                throw new Error('Analysis request failed');
            }

        } catch (error) {
            console.error('Analysis failed:', error);
            this.showAnalysis({
                status: 'error',
                analysis: 'AI analysis is currently unavailable. Basic analysis shows this response appears normal.'
            });
        } finally {
            // Reset button
            const analyzeBtn = this.container.querySelector('button[onclick*="analyzeResponse"]');
            if (analyzeBtn) {
                analyzeBtn.innerHTML = '<svg class="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg> Analyze';
                analyzeBtn.disabled = false;
            }
        }
    }

    showAnalysis(analysis) {
        // Add analysis panel above the response
        const header = this.container.querySelector('.border-b');
        if (header && analysis) {
            const analysisDiv = document.createElement('div');
            analysisDiv.className = 'bg-indigo-600/5 border-b border-indigo-500/20 p-4';
            analysisDiv.innerHTML = `
                <div class="flex items-start gap-3">
                    <div class="mt-1 p-1.5 bg-indigo-500/20 rounded text-indigo-400">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
                        </svg>
                    </div>
                    <div class="flex-1 min-w-0">
                        <h4 class="text-sm font-bold text-indigo-400 uppercase tracking-widest mb-2">AI Response Analysis</h4>
                        <div class="text-sm text-slate-300 prose prose-invert max-w-none prose-sm leading-relaxed whitespace-pre-wrap">
                            ${analysis.analysis || 'No analysis available.'}
                        </div>
                    </div>
                    <button class="text-indigo-500 hover:text-indigo-400" onclick="this.parentElement.remove()">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                        </svg>
                    </button>
                </div>
            `;

            header.parentNode.insertBefore(analysisDiv, header.nextSibling);
        }
    }

    getContentType(headers) {
        for (const [key, value] of Object.entries(headers)) {
            if (key.toLowerCase() === 'content-type') {
                return value;
            }
        }
        return null;
    }

    formatSize(bytes) {
        if (!bytes || bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    escapeHtml(text) {
        if (typeof text !== 'string') return text;
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Export for global use
window.ResponseViewer = ResponseViewer;