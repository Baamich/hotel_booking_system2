let socket;

function initializeWebSocket(chatId) {
    const chatData = document.getElementById('chat-data');
    const isAdmin = chatData.dataset.isAdmin === 'True';
    const userName = chatData.dataset.userName;
    const adminName = chatData.dataset.adminName;
    
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