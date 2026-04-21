const messagesDiv = document.getElementById('messages');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const logoutBtn = document.getElementById('logout-btn');

function appendMessage(role, content) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.textContent = content;
    msgDiv.appendChild(bubble);
    messagesDiv.appendChild(msgDiv);
    scrollToBottom();
    return bubble;
}

function appendThinking() {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message assistant thinking-msg';
    const bubble = document.createElement('div');
    bubble.className = 'bubble thinking-bubble';
    bubble.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';
    msgDiv.appendChild(bubble);
    messagesDiv.appendChild(msgDiv);
    scrollToBottom();
    return msgDiv;
}

function scrollToBottom() {
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    userInput.value = '';
    appendMessage('user', message);

    const thinkingBubble = appendThinking();
    userInput.disabled = true;
    sendBtn.disabled = true;

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });

        if (!res.ok) {
            thinkingBubble.remove();
            appendMessage('assistant', '请求失败，请稍后重试');
            userInput.disabled = false;
            sendBtn.disabled = false;
            userInput.focus();
            return;
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let fullText = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop();

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        if (data.chunk) {
                            fullText += data.chunk;
                        }
                    } catch (e) {}
                }
            }
        }

        // Replace thinking with actual response
        thinkingBubble.remove();
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message assistant';
        const bubble = document.createElement('div');
        bubble.className = 'bubble';
        bubble.textContent = '';
        msgDiv.appendChild(bubble);
        messagesDiv.appendChild(bubble.parentElement);
        scrollToBottom();

        // Typing effect
        let i = 0;
        const typeChar = () => {
            if (i < fullText.length) {
                bubble.textContent += fullText[i];
                i++;
                scrollToBottom();
                setTimeout(typeChar, 30);
            } else {
                userInput.disabled = false;
                sendBtn.disabled = false;
                userInput.focus();
            }
        };
        typeChar();
    } catch (err) {
        thinkingBubble.remove();
        appendMessage('assistant', '网络错误，请稍后重试');
        userInput.disabled = false;
        sendBtn.disabled = false;
        userInput.focus();
    }
}

sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') sendMessage();
});

logoutBtn.addEventListener('click', async () => {
    await fetch('/api/logout', { method: 'POST' });
    window.location.href = '/login';
});
