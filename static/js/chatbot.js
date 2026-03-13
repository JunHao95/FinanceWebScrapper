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
                <h3>🤖 QuantAssistant</h3>
                <button id="chatbot-close-btn">&times;</button>
            </div>
            <div id="chatbot-messages">
                <div class="message bot-message">
                    Hello! I'm QuantAssistant. How can I help you with your financial analysis today?
                </div>
            </div>
            <div id="chatbot-input-area">
                <input type="text" id="chatbot-input" placeholder="Type a message..." aria-label="Message input">
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

    // Sending a message
    const sendMessage = async () => {
        const text = inputField.value.trim();
        if (!text) return;

        // Display user message
        appendMessage('user', text);
        inputField.value = '';

        // Show typing indicator
        const loadingId = appendMessage('bot', '...', true);

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
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
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Helpers
    function appendMessage(sender, text, isLoading = false) {
        const msgDiv = document.createElement('div');
        msgDiv.classList.add('message');
        msgDiv.classList.add(sender === 'user' ? 'user-message' : 'bot-message');
        if (isLoading) {
            msgDiv.classList.add('loading-message');
        }
        msgDiv.textContent = text;
        const msgId = 'msg-' + Date.now() + Math.random();
        msgDiv.id = msgId;
        
        messagesContainer.appendChild(msgDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        return msgId;
    }

    function removeMessage(id) {
        const el = document.getElementById(id);
        if (el) {
            el.remove();
        }
    }
});
