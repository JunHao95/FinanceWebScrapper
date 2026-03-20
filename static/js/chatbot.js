/**
 * chatbot.js
 * Frontend logic to manage the floating QuantAssistant / FinancialAnalyst chat interface.
 */

document.addEventListener('DOMContentLoaded', () => {
    // ── Agent configuration ──────────────────────────────────────────────
    const AGENT_CONFIG = {
        quant: {
            name: '🤖 QuantAssistant',
            subtitle: 'AI-powered financial analysis',
            greeting: "Hello! I'm QuantAssistant. How can I help you with your financial analysis today?"
        },
        financial: {
            name: '📈 FinancialAnalyst',
            subtitle: 'Company fundamentals & market analysis',
            greeting: "Hi, I'm FinancialAnalyst. Ask me about company fundamentals, sector trends, or macro outlook."
        }
    };

    const agentHistories = { quant: [], financial: [] };
    let activeAgent = 'quant';

    // ── Inject Chatbot HTML ───────────────────────────────────────────────
    const chatContainer = document.createElement('div');
    chatContainer.id = 'chatbot-container';
    chatContainer.innerHTML = `
        <button id="chatbot-toggle-btn" aria-label="Open Chat">💬</button>
        <div id="chatbot-window" class="chatbot-hidden">
            <div id="chatbot-header">
                <div id="chatbot-header-info">
                    <h3 id="chatbot-agent-name">🤖 QuantAssistant</h3>
                    <div class="chatbot-subtitle" id="chatbot-agent-subtitle">AI-powered financial analysis</div>
                </div>
                <div id="chatbot-agent-tabs">
                    <button class="agent-pill active" data-agent="quant">QuantAssistant</button>
                    <button class="agent-pill" data-agent="financial">FinancialAnalyst</button>
                </div>
                <button id="chatbot-close-btn" aria-label="Close chat">&times;</button>
            </div>
            <div id="chatbot-messages"></div>
            <div id="chatbot-input-area">
                <input type="text" id="chatbot-input" placeholder="Ask about stocks, options, risk..." aria-label="Message input">
                <button id="chatbot-send-btn" aria-label="Send message">Send</button>
            </div>
        </div>
    `;
    document.body.appendChild(chatContainer);

    // ── Element references ────────────────────────────────────────────────
    const toggleBtn         = document.getElementById('chatbot-toggle-btn');
    const closeBtn          = document.getElementById('chatbot-close-btn');
    const chatWindow        = document.getElementById('chatbot-window');
    const messagesContainer = document.getElementById('chatbot-messages');
    const inputField        = document.getElementById('chatbot-input');
    const sendBtn           = document.getElementById('chatbot-send-btn');

    // ── Toggle Chat Window ────────────────────────────────────────────────
    const toggleChat = () => {
        chatWindow.classList.toggle('chatbot-hidden');
        if (!chatWindow.classList.contains('chatbot-hidden')) {
            inputField.focus();
        }
    };
    toggleBtn.addEventListener('click', toggleChat);
    closeBtn.addEventListener('click', toggleChat);

    // ── Simple markdown renderer ─────────────────────────────────────────
    function renderMarkdown(text) {
        return text
            .replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) =>
                `<pre><code>${escapeHtml(code.trim())}</code></pre>`)
            .replace(/`([^`]+)`/g, (_, code) => `<code>${escapeHtml(code)}</code>`)
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            .replace(/^[-*] (.+)$/gm, '<li>$1</li>')
            .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
            .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
            .replace(/\n{2,}/g, '</p><p>')
            .replace(/\n/g, '<br>')
            .replace(/^(?!<(ul|ol|pre|li))(.+)$/, '<p>$2</p>');
    }

    function escapeHtml(str) {
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    // ── Helpers ───────────────────────────────────────────────────────────
    function appendMessage(sender, text, replayMode = false) {
        if (!replayMode) {
            agentHistories[activeAgent].push({ sender, text });
        }
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

    // ── Agent switching ───────────────────────────────────────────────────
    function updateHeader(agent) {
        document.getElementById('chatbot-agent-name').textContent = AGENT_CONFIG[agent].name;
        document.getElementById('chatbot-agent-subtitle').textContent = AGENT_CONFIG[agent].subtitle;
        document.querySelectorAll('.agent-pill').forEach(pill => {
            pill.classList.toggle('active', pill.dataset.agent === agent);
        });
    }

    function switchAgent(newAgent) {
        if (newAgent === activeAgent) return;
        activeAgent = newAgent;
        messagesContainer.innerHTML = '';
        if (agentHistories[activeAgent].length === 0) {
            appendMessage('bot', AGENT_CONFIG[activeAgent].greeting);
        } else {
            agentHistories[activeAgent].forEach(({ sender, text }) =>
                appendMessage(sender, text, true)
            );
        }
        updateHeader(activeAgent);
    }

    document.getElementById('chatbot-agent-tabs').addEventListener('click', (e) => {
        const pill = e.target.closest('.agent-pill');
        if (pill) switchAgent(pill.dataset.agent);
    });

    // ── Send message ──────────────────────────────────────────────────────
    const sendMessage = async () => {
        const text = inputField.value.trim();
        if (!text) return;

        appendMessage('user', text);
        inputField.value = '';

        const loadingId = appendTypingIndicator();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text, agent: activeAgent })
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

    // ── Initialize: seed QuantAssistant greeting ──────────────────────────
    appendMessage('bot', AGENT_CONFIG.quant.greeting);
});
