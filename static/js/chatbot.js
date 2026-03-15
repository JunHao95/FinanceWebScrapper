/**
 * chatbot.js
 * Frontend logic to manage the floating QuantAssistant chat interface.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Inject Chatbot HTML
    const chatContainer = document.createElement('div');
    chatContainer.id = 'chatbot-container';
    chatContainer.innerHTML = `
        <button id="chatbot-toggle-btn" aria-label="Open Chat">💬</button>
        <div id="chatbot-window" class="chatbot-hidden">
            <div id="chatbot-header">
                <div>
                    <h3>🤖 QuantAssistant</h3>
                    <div class="chatbot-subtitle">AI-powered financial analysis</div>
                </div>
                <button id="chatbot-close-btn" aria-label="Close chat">&times;</button>
            </div>
            <div id="chatbot-messages">
                <div class="message bot-message">
                    Hello! I'm QuantAssistant. How can I help you with your financial analysis today?
                </div>
            </div>
            <div id="chatbot-input-area">
                <input type="text" id="chatbot-input" placeholder="Ask about stocks, options, risk..." aria-label="Message input">
                <button id="chatbot-send-btn" aria-label="Send message">Send</button>
            </div>
        </div>
    `;
    document.body.appendChild(chatContainer);

    // Elements
    const toggleBtn = document.getElementById('chatbot-toggle-btn');
    const closeBtn = document.getElementById('chatbot-close-btn');
    const chatWindow = document.getElementById('chatbot-window');
    const messagesContainer = document.getElementById('chatbot-messages');
    const inputField = document.getElementById('chatbot-input');
    const sendBtn = document.getElementById('chatbot-send-btn');

    // Toggle Chat Window
    const toggleChat = () => {
        chatWindow.classList.toggle('chatbot-hidden');
        if (!chatWindow.classList.contains('chatbot-hidden')) {
            inputField.focus();
        }
    };
    toggleBtn.addEventListener('click', toggleChat);
    closeBtn.addEventListener('click', toggleChat);

    // Simple markdown renderer for bot messages
    function renderMarkdown(text) {
        return text
            // Code blocks
            .replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) =>
                `<pre><code>${escapeHtml(code.trim())}</code></pre>`)
            // Inline code
            .replace(/`([^`]+)`/g, (_, code) => `<code>${escapeHtml(code)}</code>`)
            // Bold
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            // Italic
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            // Unordered lists
            .replace(/^[-*] (.+)$/gm, '<li>$1</li>')
            .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
            // Ordered lists
            .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
            // Line breaks into paragraphs
            .replace(/\n{2,}/g, '</p><p>')
            .replace(/\n/g, '<br>')
            // Wrap in paragraph if no block elements
            .replace(/^(?!<(ul|ol|pre|li))(.+)$/, '<p>$2</p>');
    }

    function escapeHtml(str) {
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    // Sending a message
    const sendMessage = async () => {
        const text = inputField.value.trim();
        if (!text) return;

        appendMessage('user', text);
        inputField.value = '';

        // Show animated typing indicator
        const loadingId = appendTypingIndicator();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });
            
            const data = await response.json();
            removeMessage(loadingId);
            
            if (response.ok && data.reply) {
                appendMessage('bot', data.reply);
            } else {
                appendMessage('bot', `Error: ${data.error || 'Failed to get a response.'}`);
            }
        } catch (error) {
            console.error('Chat error:', error);
            removeMessage(loadingId);
            appendMessage('bot', 'Error: Cannot reach the assistant right now.');
        }
    };

    sendBtn.addEventListener('click', sendMessage);
    inputField.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    // Helpers
    function appendMessage(sender, text) {
        const msgDiv = document.createElement('div');
        msgDiv.classList.add('message');
        msgDiv.classList.add(sender === 'user' ? 'user-message' : 'bot-message');
        
        if (sender === 'bot') {
            msgDiv.innerHTML = renderMarkdown(text);
        } else {
            msgDiv.textContent = text;
        }
        
        const msgId = 'msg-' + Date.now() + Math.random();
        msgDiv.id = msgId;
        messagesContainer.appendChild(msgDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        return msgId;
    }

    function appendTypingIndicator() {
        const msgDiv = document.createElement('div');
        msgDiv.classList.add('message', 'bot-message', 'typing-indicator');
        msgDiv.innerHTML = '<span></span><span></span><span></span>';
        const msgId = 'msg-' + Date.now() + Math.random();
        msgDiv.id = msgId;
        messagesContainer.appendChild(msgDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        return msgId;
    }

    function removeMessage(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }
});
