// Configuration
const API_BASE_URL = window.location.origin;
let sessionId = null;

// DOM Elements
const chatContainer = document.getElementById('chatContainer');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');
const resetButton = document.getElementById('resetButton');
const intentValue = document.getElementById('intentValue');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    userInput.focus();
    
    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    resetButton.addEventListener('click', resetConversation);
});

// Send message function
async function sendMessage() {
    const message = userInput.value.trim();
    
    if (!message) return;
    
    // Disable input while processing
    setInputState(false);
    
    // Add user message to chat
    addMessage(message, 'user');
    
    // Clear input
    userInput.value = '';
    
    try {
        // Send to API
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to get response from server');
        }
        
        const data = await response.json();
        
        // Update session ID
        sessionId = data.session_id;
        
        // Update intent indicator
        updateIntentIndicator(data.intent_level);
        
        // Add bot response
        addMessage(data.response, 'bot');
        
        // Show notification if booking was made
        if (data.booking_made) {
            showNotification('🎉 Booking confirmed! Check your email for details.');
        }
        
    } catch (error) {
        console.error('Error:', error);
        addMessage('Sorry, I encountered an error. Please try again.', 'bot');
    } finally {
        setInputState(true);
        userInput.focus();
    }
}

// Add message to chat
function addMessage(content, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    if (type === 'bot') {
        contentDiv.innerHTML = `<strong>Agent:</strong><p>${formatMessage(content)}</p>`;
    } else {
        contentDiv.innerHTML = `<p>${formatMessage(content)}</p>`;
    }
    
    messageDiv.appendChild(contentDiv);
    chatContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Format message (basic markdown-like formatting)
function formatMessage(text) {
    // Convert line breaks
    text = text.replace(/\n/g, '<br>');
    
    // Bold text
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Italic text
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Numbered lists
    text = text.replace(/^\d+\.\s/gm, '<br>• ');
    
    return text;
}

// Update intent indicator
function updateIntentIndicator(intentLevel) {
    if (!intentLevel) return;
    
    intentValue.textContent = intentLevel;
    intentValue.className = 'intent-value';
    
    switch(intentLevel.toLowerCase()) {
        case 'high':
            intentValue.classList.add('intent-high');
            break;
        case 'medium':
            intentValue.classList.add('intent-medium');
            break;
        case 'low':
            intentValue.classList.add('intent-low');
            break;
    }
}

// Set input state (enabled/disabled)
function setInputState(enabled) {
    userInput.disabled = !enabled;
    sendButton.disabled = !enabled;
    
    if (enabled) {
        sendButton.innerHTML = '<span>Send</span>';
    } else {
        sendButton.innerHTML = '<div class="loading"></div>';
    }
}

// Reset conversation
async function resetConversation() {
    if (!confirm('Are you sure you want to reset the conversation?')) {
        return;
    }
    
    try {
        if (sessionId) {
            await fetch(`${API_BASE_URL}/reset-session/${sessionId}`, {
                method: 'POST'
            });
        }
        
        // Clear chat (keep first message)
        const messages = chatContainer.querySelectorAll('.message');
        messages.forEach((msg, index) => {
            if (index > 0) msg.remove();
        });
        
        // Reset session
        sessionId = null;
        
        // Reset intent indicator
        intentValue.textContent = '-';
        intentValue.className = 'intent-value';
        
        showNotification('Conversation reset successfully!');
        
    } catch (error) {
        console.error('Error resetting conversation:', error);
        showNotification('Error resetting conversation');
    }
}

// Show notification
function showNotification(message) {
    // Simple notification - you can enhance this
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #10b981;
        color: white;
        padding: 15px 25px;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 1000;
        animation: slideInRight 0.3s ease-out;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add animation keyframes
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);