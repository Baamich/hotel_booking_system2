let socket;

function initializeWebSocket(chatId) {
    const chatData = document.getElementById('chat-data');
    const isAdmin = chatData.dataset.isAdmin === 'True';
    const userName = chatData.dataset.userName;
    let adminName = chatData.dataset.adminName;
    
    // Инициализация Socket.IO с правильным путём
    socket = io.connect('http://127.0.0.1:5000');

    socket.on('connect', () => {
        console.log('Connected to Socket.IO');
        socket.emit('join', { chat_id: chatId });
    });

    socket.on('joined', (data) => {
        console.log('Joined chat:', data.message);
    });

    socket.on('new_message', (data) => {
        const messagesContainer = document.getElementById('chat-messages');
        let senderName = data.sender;
        if (data.sender === 'user') {
            senderName = userName;
        } else if (data.sender === 'support') {
            senderName = adminName || 'Служба поддержки';
        }
        const messageDiv = document.createElement('div');
        messageDiv.className = 'mb-2';
        messageDiv.innerHTML = `
            <strong>${senderName}:</strong> ${data.content}
            <small class="text-muted float-end">${data.time_str}</small>
        `;
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    });

    socket.on('update_admin_name', (data) => {
        adminName = data.admin_name;
        const header = document.getElementById('support-header');
        if (header && !isAdmin) {
            header.textContent = `Служба поддержки${adminName ? ` ${adminName}` : ''}`;
        }
        // Обновляем существующие сообщения
        const messages = document.querySelectorAll('#chat-messages .mb-2');
        messages.forEach(msg => {
            const strong = msg.querySelector('strong');
            if (strong && strong.textContent === 'Служба поддержки') {
                strong.textContent = adminName || 'Служба поддержки';
            }
        });
    });

    socket.on('chat_released', (data) => {
        if (data.chat_id === chatId && !isAdmin) {
            adminName = null; // Сбрасываем имя админа на null
            const header = document.getElementById('support-header');
            if (header) {
                header.textContent = 'Служба поддержки'; 
            }
            // Обновляем все сообщения, где отображается имя админа
            const messages = document.querySelectorAll('#chat-messages .mb-2');
            messages.forEach(msg => {
                const strong = msg.querySelector('strong');
                if (strong && strong.textContent !== userName) {
                    strong.textContent = 'Служба поддержки'; 
                }
            });
        }
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from Socket.IO');
    });

    // Отправка сообщения
    const form = document.getElementById('message-form');
    const input = document.getElementById('message-input');
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        if (input.value.trim()) {
            socket.emit('send_message', {
                chat_id: chatId,
                message: input.value
            });
            input.value = '';
        }
    });

    input.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            form.dispatchEvent(new Event('submit'));
        }
    });
}

document.addEventListener('DOMContentLoaded', function() {
    const chatData = document.getElementById('chat-data');
    const chatId = chatData.dataset.chatId;
    initializeWebSocket(chatId);
});