document.addEventListener('DOMContentLoaded', async () => {
    const toggleBtn = document.getElementById('ai-chat-toggle');
    const chatBox = document.getElementById('ai-chat-box');
    const closeBtn = document.getElementById('ai-chat-close');
    const messages = document.getElementById('ai-chat-messages');
    const input = document.getElementById('ai-chat-input');
    const sendBtn = document.getElementById('ai-chat-send');

    let lang = 'eng';
    let aiAvailable = false;

    // === ЗАГРУЗКА ЯЗЫКА ===
    async function loadSession() {
        try {
            const res = await fetch('/ai/session');
            const data = await res.json();
            lang = data.lang || 'eng';
        } catch (e) {
            lang = 'eng';
        }
    }

    // === ПРОВЕРКА ИИ ===
    async function checkAI() {
        try {
            const res = await fetch('http://localhost:5001/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: 'ping', lang: 'eng' })
            });
            if (res.ok) {
                const data = await res.json();
                aiAvailable = data.reply === 'pong';
            } else {
                aiAvailable = false;
            }
        } catch (e) {
            aiAvailable = false;
        }
        await updateStatus();
    }

    // === ПРИВЕТСТВИЕ ===
    async function updateStatus() {
        messages.innerHTML = '';
        if (!aiAvailable) {
            addBotMessage(gettext('lang_not_supported') + '<br>' + gettext('lang_please_use') + ' ' + 
                Object.values(FLAGS).join(' '));
            const retryBtn = document.createElement('button');
            retryBtn.textContent = gettext('retry') || 'Retry';
            retryBtn.className = 'retry-btn';
            retryBtn.onclick = async () => {
                messages.innerHTML = '<div class="msg bot">' + gettext('checking_connection') + '...</div>';
                await checkAI();
            };
            messages.appendChild(retryBtn);
            input.disabled = true;
            sendBtn.disabled = true;
        } else {
            const greeting = await getTranslatedGreeting();
            addBotMessage(greeting);
            input.disabled = false;
            sendBtn.disabled = false;
            input.focus();
        }
    }

    async function getTranslatedGreeting() {
        try {
            const res = await fetch('http://localhost:5001/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: '', lang })
            });
            const data = await res.json();
            return data.reply;
        } catch {
            return `${gettext('greeting', lang)}<br>${gettext('greeting_hint', lang)}`;
        }
    }

    // === ОТКРЫТИЕ ЧАТА ===
    toggleBtn.addEventListener('click', async () => {
        await loadSession();
        toggleBtn.style.display = 'none';
        chatBox.style.display = 'flex';
        await checkAI();

        // === ПЕРЕВОД ШАПКИ ===
        const headerText = document.getElementById('ai-header-text');
        if (headerText) {
            const translations = {
                rus: 'ИИ-помощник',
                eng: 'AI Assistant',
                rom: 'Asistent AI'
            };
            headerText.textContent = translations[lang] || 'AI Assistant';
        }
    });

    closeBtn.addEventListener('click', () => {
        chatBox.style.display = 'none';
        toggleBtn.style.display = 'flex';
    });

    // === ОТПРАВКА СООБЩЕНИЯ ===
    async function sendMessageToAI(text) {
        if (!aiAvailable || !text.trim()) return;
        addUserMessage(text);
        try {
            const res = await fetch('http://localhost:5001/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text, lang })
            });
            const data = await res.json();
            addBotMessage(data.reply);
        } catch (e) {
            addBotMessage(gettext('connection_error') + ' ' + gettext('try_later'));
            aiAvailable = false;
            await updateStatus();
        }
    }

    // === КОМАНДЫ: СВОДКА ===
    async function sendMessage() {
        const text = input.value.trim();
        if (!text || !aiAvailable) return;
        input.value = '';

        const summaryTriggers = {
            'rus': ['сводка', 'примеры'],
            'eng': ['summary', 'examples'],
            'rom': ['rezumat', 'exemple']
        };

        const trigger = summaryTriggers[lang]?.find(kw => text.toLowerCase().includes(kw));
        if (trigger) {
            addUserMessage(text);
            addBotMessage(await getSummary());
            return;
        }

        const helloTriggers = {
            'rus': ['привет', 'здравствуй'],
            'eng': ['hello', 'hi'],
            'rom': ['bună', 'salut']
        };

        if (helloTriggers[lang]?.some(kw => text.toLowerCase().includes(kw))) {
            addUserMessage(text);
            addBotMessage(`${gettext('greeting', lang)}<br>${gettext('greeting_hint', lang)}`);
            return;
        }

        await sendMessageToAI(text);
    }

    // === ПОЛУЧИТЬ СВОДКУ НА НУЖНОМ ЯЗЫКЕ ===
    async function getSummary() {
        const triggerWord = lang === 'rus' ? 'сводка' : lang === 'eng' ? 'summary' : 'rezumat';
        try {
            const res = await fetch('http://localhost:5001/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: triggerWord, lang })
            });
            const data = await res.json();
            return data.reply;
        } catch {
            return gettext('examples_error');
        }
    }

    // === КНОПКИ ===
    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keypress', e => {
        if (e.key === 'Enter') sendMessage();
    });

    // === ВСПОМОГАТЕЛЬНЫЕ ===
    function addBotMessage(html) {
        const div = document.createElement('div');
        div.className = 'msg bot';
        div.innerHTML = html;
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
    }

    function addUserMessage(text) {
        const div = document.createElement('div');
        div.className = 'msg user';
        div.textContent = text;
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
    }

    // === gettext (локальная копия) ===
    function gettext(key, lng = lang) {
        const t = {
            rus: {
                greeting: 'Здравствуйте, я текстовый ИИ-помощник, чем вам помочь?',
                greeting_hint: 'Введите <strong>сводка</strong>, чтобы увидеть примеры запросов.',
                lang_not_supported: 'Я не понимаю этот язык.',
                lang_please_use: 'Пожалуйста, пишите на одном из доступных языков:',
                connection_error: 'Ошибка связи.',
                try_later: 'Попробуйте позже.',
                examples_error: 'Не удалось загрузить примеры.',
                checking_connection: 'Проверка подключения',
                retry: 'Повторить попытку'
            },
            eng: {
                greeting: 'Hello, I am a text AI assistant, how can I help you?',
                greeting_hint: 'Type <strong>summary</strong> to see examples of requests.',
                lang_not_supported: 'I don\'t understand this language.',
                lang_please_use: 'Please write in one of the available languages:',
                connection_error: 'Connection error.',
                try_later: 'Try again later.',
                examples_error: 'Failed to load examples.',
                checking_connection: 'Checking connection',
                retry: 'Retry'
            },
            rom: {
                greeting: 'Bună, sunt un asistent AI textual, cu ce vă pot ajuta?',
                greeting_hint: 'Scrieți <strong>rezumat</strong> pentru a vedea exemple de cereri.',
                lang_not_supported: 'Nu înțeleg această limbă.',
                lang_please_use: 'Vă rugăm să scrieți într-una din limbile disponibile:',
                connection_error: 'Eroare de conexiune.',
                try_later: 'Încercați mai târziu.',
                examples_error: 'Nu am putut încărca exemplele.',
                checking_connection: 'Verific conexiunea',
                retry: 'Reîncearcă'
            }
        };
        return t[lng]?.[key] || key;
    }
});