/**
 * PharmAssist - Chat UI Application
 * Handles SSE streaming, message rendering, and bilingual support
 */

// ========================================
// State
// ========================================

const state = {
    messages: [],
    isStreaming: false,
    showToolEvents: false,
};

// ========================================
// DOM Elements
// ========================================

const elements = {
    chatMessages: document.getElementById('chatMessages'),
    messageInput: document.getElementById('messageInput'),
    userIdentifier: document.getElementById('userIdentifier'),
    userIdentifierRow: document.getElementById('userIdentifierRow'),
    sendButton: document.getElementById('sendButton'),
    showToolEvents: document.getElementById('showToolEvents'),
};

// ========================================
// Utilities
// ========================================

/**
 * Detect if text contains Hebrew characters
 */
function containsHebrew(text) {
    return /[\u0590-\u05FF]/.test(text);
}

/**
 * Detect if text is primarily RTL (Hebrew)
 */
function isRTL(text) {
    const hebrewChars = (text.match(/[\u0590-\u05FF]/g) || []).length;
    const latinChars = (text.match(/[a-zA-Z]/g) || []).length;
    return hebrewChars > latinChars;
}

/**
 * Simple markdown-like formatting
 */
function formatMessage(text) {
    return text
        // Escape HTML
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        // Bold
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        // Line breaks
        .replace(/\n/g, '<br>')
        // Lists (simple)
        .replace(/^- (.+)$/gm, '<li>$1</li>')
        .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
}

/**
 * Scroll chat to bottom
 */
function scrollToBottom() {
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

/**
 * Auto-resize textarea
 */
function autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
}

// ========================================
// Message Rendering
// ========================================

/**
 * Remove welcome card if present
 */
function removeWelcomeCard() {
    const welcomeCard = elements.chatMessages.querySelector('.welcome-card');
    if (welcomeCard) {
        welcomeCard.remove();
    }
}

/**
 * Create message element
 */
function createMessageElement(role, content) {
    const isUser = role === 'user';
    const rtl = isRTL(content);

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}${rtl ? ' rtl' : ''}`;

    const avatarSvg = isUser
        ? '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>'
        : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M12 4v16M4 12h16"/></svg>';

    messageDiv.innerHTML = `
        <div class="message-avatar">${avatarSvg}</div>
        <div class="message-content">
            <div class="message-bubble">${formatMessage(content)}</div>
        </div>
    `;

    return messageDiv;
}

/**
 * Create typing indicator
 */
function createTypingIndicator() {
    const div = document.createElement('div');
    div.className = 'typing-indicator';
    div.id = 'typingIndicator';
    div.innerHTML = `
        <div class="message-avatar">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
                <path d="M12 4v16M4 12h16"/>
            </svg>
        </div>
        <div class="typing-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    return div;
}

/**
 * Create tool event element
 */
function createToolEventElement(type, data) {
    const div = document.createElement('div');
    div.className = 'tool-event';

    const icon = type === 'tool_call'
        ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>'
        : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>';

    const title = type === 'tool_call' ? `Calling: ${data.tool}` : `Result: ${data.tool}`;
    const content = type === 'tool_call'
        ? JSON.stringify(data.input, null, 2)
        : (typeof data.result === 'string' ? data.result : JSON.stringify(data.result, null, 2));

    div.innerHTML = `
        <div class="tool-event-header">${icon} ${title}</div>
        <div class="tool-event-content">${content}</div>
    `;

    return div;
}

/**
 * Create error message element
 */
function createErrorElement(message) {
    const div = document.createElement('div');
    div.className = 'error-message';
    div.textContent = `Error: ${message}`;
    return div;
}

/**
 * Add message to chat
 */
function addMessage(role, content) {
    removeWelcomeCard();
    const messageEl = createMessageElement(role, content);
    elements.chatMessages.appendChild(messageEl);
    scrollToBottom();
    return messageEl;
}

/**
 * Show typing indicator
 */
function showTypingIndicator() {
    removeWelcomeCard();
    const indicator = createTypingIndicator();
    elements.chatMessages.appendChild(indicator);
    scrollToBottom();
}

/**
 * Remove typing indicator
 */
function removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

// ========================================
// Streaming Handler
// ========================================

/**
 * Stream chat response from API
 */
async function streamResponse(userMessage) {
    state.isStreaming = true;
    updateUI();

    // Add user message to state and UI
    state.messages.push({ role: 'user', content: userMessage });
    addMessage('user', userMessage);

    // Show typing indicator
    showTypingIndicator();

    // Prepare request
    const requestBody = {
        messages: state.messages.map(m => ({ role: m.role, content: m.content })),
    };

    // Add user identifier if provided
    const identifier = elements.userIdentifier.value.trim();
    if (identifier) {
        requestBody.user_identifier = identifier;
    }

    let assistantContent = '';
    let assistantMessageEl = null;

    try {
        const response = await fetch('/chat/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        // Create callbacks object ONCE (so _firstTokenReceived persists)
        const callbacks = {
            _firstTokenReceived: false,
            onFirstToken: () => {
                removeTypingIndicator();
                assistantMessageEl = addMessage('assistant', '');
            },
            onToken: (text) => {
                assistantContent += text;
                if (assistantMessageEl) {
                    const bubble = assistantMessageEl.querySelector('.message-bubble');
                    bubble.innerHTML = formatMessage(assistantContent);

                    // Update RTL class based on content
                    if (isRTL(assistantContent)) {
                        assistantMessageEl.classList.add('rtl');
                    }
                }
                scrollToBottom();
            },
            onToolEvent: (type, data) => {
                const toolEl = createToolEventElement(type, data);
                elements.chatMessages.appendChild(toolEl);
                scrollToBottom();
            },
            onError: (message) => {
                removeTypingIndicator();
                elements.chatMessages.appendChild(createErrorElement(message));
                scrollToBottom();
            },
        };

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // Process complete SSE events
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Keep incomplete line in buffer

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const jsonStr = line.slice(6);
                    if (!jsonStr) continue;

                    try {
                        const event = JSON.parse(jsonStr);
                        handleStreamEvent(event, callbacks);
                    } catch (e) {
                        console.error('Failed to parse SSE event:', e, jsonStr);
                    }
                }
            }
        }

        // Save assistant message to state
        if (assistantContent) {
            state.messages.push({ role: 'assistant', content: assistantContent });
        }

    } catch (error) {
        removeTypingIndicator();
        elements.chatMessages.appendChild(createErrorElement(error.message));
        scrollToBottom();
    } finally {
        state.isStreaming = false;
        updateUI();
    }
}

/**
 * Handle individual stream event
 */
function handleStreamEvent(event, callbacks) {
    const { type, data } = event;

    switch (type) {
        case 'token':
            if (data.text) {
                if (!callbacks._firstTokenReceived) {
                    callbacks.onFirstToken();
                    callbacks._firstTokenReceived = true;
                }
                callbacks.onToken(data.text);
            }
            break;

        case 'tool_call':
        case 'tool_result':
            callbacks.onToolEvent(type, data);
            break;

        case 'error':
            callbacks.onError(data.message || 'Unknown error');
            break;

        case 'done':
            // Stream complete
            break;
    }
}

// ========================================
// UI Updates
// ========================================

/**
 * Update UI based on state
 */
function updateUI() {
    // Send button state
    elements.sendButton.disabled = state.isStreaming || !elements.messageInput.value.trim();

    // Tool events visibility
    if (state.showToolEvents) {
        elements.chatMessages.classList.add('show-tools');
    } else {
        elements.chatMessages.classList.remove('show-tools');
    }
}

/**
 * Check if prescription-related query
 */
function checkPrescriptionQuery(text) {
    const prescriptionKeywords = [
        'prescription', 'refill', 'my medication', 'my prescriptions',
        'מרשם', 'מרשמים', 'התרופות שלי'
    ];
    const lower = text.toLowerCase();
    return prescriptionKeywords.some(kw => lower.includes(kw));
}

// ========================================
// Event Handlers
// ========================================

/**
 * Handle send message
 */
function handleSend() {
    const message = elements.messageInput.value.trim();
    if (!message || state.isStreaming) return;

    // Check if prescription query - show identifier input
    if (checkPrescriptionQuery(message) && !elements.userIdentifier.value.trim()) {
        elements.userIdentifierRow.classList.add('visible');
    }

    elements.messageInput.value = '';
    autoResizeTextarea(elements.messageInput);
    streamResponse(message);
}

/**
 * Handle hint pill click
 */
function handleHintClick(event) {
    if (event.target.classList.contains('hint-pill')) {
        const hint = event.target.dataset.hint;
        if (hint) {
            // Check if prescription hint - show identifier input
            if (hint.includes('prescription')) {
                elements.userIdentifierRow.classList.add('visible');
            }
            elements.messageInput.value = hint;
            autoResizeTextarea(elements.messageInput);
            elements.messageInput.focus();
        }
    }
}

// ========================================
// Initialization
// ========================================

function init() {
    // Send button click
    elements.sendButton.addEventListener('click', handleSend);

    // Enter to send (Shift+Enter for newline)
    elements.messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });

    // Auto-resize textarea
    elements.messageInput.addEventListener('input', () => {
        autoResizeTextarea(elements.messageInput);
        updateUI();
    });

    // Tool events toggle
    elements.showToolEvents.addEventListener('change', (e) => {
        state.showToolEvents = e.target.checked;
        updateUI();
    });

    // Hint pills
    elements.chatMessages.addEventListener('click', handleHintClick);

    // Initial UI state
    updateUI();

    // Focus input
    elements.messageInput.focus();
}

// Start app
document.addEventListener('DOMContentLoaded', init);
