document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('chat-container');
    if (!container) return;

    const form = document.getElementById('chat-form');
    const input = document.getElementById('chat-input');
    const messagesContainer = document.getElementById('chat-messages');
    const chatEnd = document.getElementById('chat-end');
    const sendButton = document.getElementById('send-button');
    const clearButton = document.getElementById('clear-chat');
    
    // Config from data attributes
    const sessionId = container.dataset.sessionId || '';
    const userInitials = container.dataset.userInitials || 'U';
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    const chatEndpoint = container.dataset.chatEndpoint;

    let isLoading = false;
    
    // Auto-resize textarea
    if (input) {
        input.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 192) + 'px';
        });
        
        // Handle Enter key
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                form.dispatchEvent(new Event('submit'));
            }
        });
    }
    
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const message = input.value.trim();
            if (!message || isLoading) return;
            
            isLoading = true;
            sendButton.disabled = true;
            
            // Add user message to UI
            addMessage('user', message);
            input.value = '';
            input.style.height = 'auto';
            
            // Show loading indicator
            const loadingId = showLoadingIndicator();
            
            try {
                const useContext = document.getElementById('use-context')?.checked || false;
                
                const response = await fetch(chatEndpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({
                        message: message,
                        session_id: sessionId,
                        context: useContext ? [] : []
                    })
                });
                
                const data = await response.json();
                
                // Remove loading indicator
                const loadingEl = document.getElementById(loadingId);
                if (loadingEl) loadingEl.remove();
                
                if (data.success) {
                    addMessage('assistant', data.content, data.groundingSources || []);
                } else {
                    addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
                }
            } catch (error) {
                const loadingEl = document.getElementById(loadingId);
                if (loadingEl) loadingEl.remove();
                addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
                console.error(error);
            } finally {
                isLoading = false;
                sendButton.disabled = false;
                input.focus();
            }
        });
    }
    
    if (clearButton) {
        clearButton.addEventListener('click', function() {
            const messages = messagesContainer.querySelectorAll('.chat-message');
            messages.forEach(msg => msg.remove());
            addMessage('assistant', 'Chat display cleared. Previous messages remain in your session history.');
        });
    }
    
    function addMessage(role, content, groundingSources = []) {
        const messageId = 'msg-' + Date.now();
        const messageDiv = document.createElement('div');
        messageDiv.id = messageId;
        messageDiv.className = `flex chat-message ${role === 'user' ? 'justify-end' : 'justify-start'}`;
        
        const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        let groundingHtml = '';
        if (groundingSources && groundingSources.length > 0) {
            groundingHtml = `
                <div class="mt-4 pt-4 border-t ${role === 'user' ? 'border-gray-200/20' : 'border-gray-200 dark:border-gray-600'}">
                    <p class="text-[10px] font-bold mb-2 ${role === 'user' ? 'opacity-80' : 'text-gray-500 dark:text-gray-400'} uppercase tracking-widest">Knowledge Base References:</p>
                    <div class="flex flex-wrap gap-2">
                        ${groundingSources.map(s => `
                            <a href="${s.uri || '#'}" target="_blank" rel="noopener noreferrer" class="text-[10px] px-3 py-1.5 rounded-lg transition-colors border ${role === 'user' ? 'bg-blue-500 hover:bg-blue-400 text-white border-blue-400' : 'bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300 border-gray-100 dark:border-gray-600'}">
                                ${s.title || 'Reference'}
                            </a>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        messageDiv.innerHTML = `
            <div class="max-w-[85%] flex gap-4 ${role === 'user' ? 'flex-row-reverse' : 'flex-row'}">
                <div class="w-10 h-10 rounded-2xl flex-shrink-0 flex items-center justify-center border shadow-sm transition-transform group-hover:scale-105 ${role === 'user' ? 'bg-blue-600 border-blue-700 text-white' : 'bg-white dark:bg-gray-800 border-gray-100 dark:border-gray-700 text-blue-600 dark:text-blue-400'}">
                    ${role === 'user' ? userInitials : '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" /></svg>'}
                </div>
                <div class="space-y-2">
                    <div class="p-6 rounded-3xl shadow-sm border ${role === 'user' ? 'bg-blue-600 border-blue-700 text-white rounded-tr-none' : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-600 text-gray-800 dark:text-gray-200 rounded-tl-none'}">
                        <p class="text-sm leading-relaxed whitespace-pre-wrap">${content}</p>
                        ${groundingHtml}
                    </div>
                    <div class="flex items-center gap-2 px-2 ${role === 'user' ? 'justify-end' : 'justify-start'}">
                        <span class="text-[10px] text-gray-400 dark:text-gray-500 font-bold uppercase tracking-widest">
                            ${role === 'user' ? 'You' : 'DocsAI Agent'} • ${timestamp}
                        </span>
                    </div>
                </div>
            </div>
        `;
        
        if (chatEnd) {
            messagesContainer.insertBefore(messageDiv, chatEnd);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        return messageId;
    }
    
    function showLoadingIndicator() {
        const loadingId = 'loading-' + Date.now();
        const loadingDiv = document.createElement('div');
        loadingDiv.id = loadingId;
        loadingDiv.className = 'flex justify-start';
        loadingDiv.innerHTML = `
            <div class="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 px-6 py-4 rounded-3xl flex items-center gap-4 shadow-sm">
                <div class="flex gap-1.5">
                    <span class="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></span>
                    <span class="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style="animation-delay: -0.15s"></span>
                    <span class="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style="animation-delay: -0.3s"></span>
                </div>
                <span class="text-xs font-bold text-gray-400 dark:text-gray-500 uppercase tracking-widest">Architect is thinking...</span>
            </div>
        `;
        if (chatEnd) {
            messagesContainer.insertBefore(loadingDiv, chatEnd);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        return loadingId;
    }
});
