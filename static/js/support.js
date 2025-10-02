function initializeWebSocket(chatId) {
    // Подключаем Socket.IO
    const socket = io();

    socket.on('connect', () => {
        socket.emit('join', { chat_id: chatId });
    });

    socket.on('new_message', (data) => {
        if (data.chat_id === chatId) {
            window.location.reload(); // Обновляем страницу при новом сообщении
        }
    });

    // Отправка сообщения по нажатию Enter
    const form = document.getElementById('message-form');
    const input = document.getElementById('message-input');
    input.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault(); // Предотвращаем переход на новую строку
            if (input.value.trim()) { // Проверяем, что поле не пустое
                form.submit(); // Отправляем форму
            }
        }
    });
}