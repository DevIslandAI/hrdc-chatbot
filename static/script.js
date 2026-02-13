const chatWindow = document.getElementById('chat-window');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

// Auto-resize textarea
userInput.addEventListener('input', () => {
    userInput.style.height = 'auto';
    userInput.style.height = userInput.scrollHeight + 'px';
});

// Handle send
async function sendMessage() {
    const query = userInput.value.trim();
    if (!query) return;

    // Clear and reset textarea
    userInput.value = '';
    userInput.style.height = 'auto';

    // Add user message
    addMessage(query, 'user');

    // Add loading message
    const loadingId = addLoading();

    try {
        const response = await fetch('/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });

        const data = await response.json();
        removeLoading(loadingId);

        if (data.error) {
            addMessage(`Error: ${data.error}`, 'system');
        } else {
            addMessage(data.response, 'system', data.sources);
        }

    } catch (error) {
        removeLoading(loadingId);
        addMessage(`Connection error: ${error.message}`, 'system');
    }
}

function addMessage(text, type, sources = []) {
    const div = document.createElement('div');
    div.className = `message ${type}-message`;

    let content = '';
    if (type === 'system') {
        content = `<div class="message-content">${marked.parse(text)}</div>`;
    } else {
        content = `<div class="message-content">${text.replace(/\n/g, '<br>')}</div>`;
    }

    if (sources && sources.length > 0) {
        content += `<div class="sources"><strong>Sources:</strong>`;
        sources.forEach(source => {
            content += `<a href="${source.url}" target="_blank" class="source-item"><i class="fas fa-file-pdf"></i> ${source.title} (${source.date})</a>`;
        });
        content += `</div>`;
    }

    div.innerHTML = content;
    chatWindow.appendChild(div);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function addLoading() {
    const id = 'loading-' + Date.now();
    const div = document.createElement('div');
    div.id = id;
    div.className = 'message system-message loading-container';
    div.innerHTML = `
        <div class="loading">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    chatWindow.appendChild(div);
    chatWindow.scrollTop = chatWindow.scrollHeight;
    return id;
}

function removeLoading(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

sendBtn.addEventListener('click', sendMessage);

userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});
