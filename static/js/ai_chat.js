document.addEventListener('DOMContentLoaded', async () => {
    const toggleBtn = document.getElementById('ai-chat-toggle');
    const chatBox = document.getElementById('ai-chat-box');
    const closeBtn = document.getElementById('ai-chat-close');
    const messages = document.getElementById('ai-chat-messages');
    const input = document.getElementById('ai-chat-input');
    const sendBtn = document.getElementById('ai-chat-send');

    let lang = 'eng';
    let aiAvailable = false;

    async function checkAI() {
        try {
            const res = await fetch('http://localhost:5001/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: 'ping', lang: 'eng' })
            });

            // Если OPTIONS — res.ok = true, но нет JSON
            if (res.status === 200) {
                try {
                    const data = await res.json();
                    aiAvailable = data.reply === 'pong';
                } catch {
                    aiAvailable = true; // если JSON не нужен (OPTIONS)
                }
            } else {
                aiAvailable = false;
            }
        } catch (e) {
            aiAvailable = false;
        }
        updateStatus();
    }

    function updateStatus() {
        messages.innerHTML = '';

        if (!aiAvailable) {
            addBotMessage('ИИ-помощник сейчас недоступен. Повторите позже.');
            const retryBtn = document.createElement('button');
            retryBtn.textContent = 'Повторить попытку';
            retryBtn.className = 'retry-btn';
            retryBtn.onclick = async () => {
                messages.innerHTML = '<div class="msg bot">Проверка подключения...</div>';
                await checkAI();
            };
            messages.appendChild(retryBtn);
            input.disabled = true;
            sendBtn.disabled = true;
        } else {
            addBotMessage('Привет! Чем помочь?');
            input.disabled = false;
            sendBtn.disabled = false;
            input.focus();
        }
    }

    async function loadSession() {
        try {
            const res = await fetch('/ai/session');
            const data = await res.json();
            lang = data.lang || 'eng';
        } catch (e) {}
    }

    toggleBtn.addEventListener('click', async () => {
        await loadSession();
        toggleBtn.style.display = 'none';
        chatBox.style.display = 'flex';
        await checkAI();
    });

    closeBtn.addEventListener('click', () => {
        chatBox.style.display = 'none';
        toggleBtn.style.display = 'flex';
    });

    function addMessage(content, type) {
        const div = document.createElement('div');
        div.className = `msg ${type}`;
        if (typeof content === 'string') {
            div.textContent = content;
        } else {
            div.appendChild(content);
        }
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
    }

    function addBotMessage(html) {
        const div = document.createElement('div');
        div.className = 'msg bot';
        div.innerHTML = html;
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
    }
    function addUserMessage(text) { addMessage(text, 'user'); }

    async function sendMessage() {
        const text = input.value.trim();
        if (!text || !aiAvailable) return;
        addUserMessage(text);
        input.value = '';

        try {
            const res = await fetch('http://localhost:5001/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text, lang })
            });
            const data = await res.json();
            addBotMessage(data.reply);
        } catch (e) {
            addBotMessage('Ошибка связи. Попробуйте позже.');
            aiAvailable = false;
            updateStatus();
        }
    }

    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keypress', e => {
        if (e.key === 'Enter') sendMessage();
    });
});