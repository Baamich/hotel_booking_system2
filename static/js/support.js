let lastTimestamp = null;
let pollingInterval;

function initializeWebSocket(chatId) {
    const chatData = document.getElementById('chat-data');
    const isAdmin = chatData.dataset.isAdmin === 'True';
    const userName = chatData.dataset.userName;
    const adminName = chatData.dataset.adminName;
    
    const form = document.getElementById('message-form');
    const input = document.getElementById('message-input');
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        if (input.value.trim()) {
            const formData = new FormData(form);
            fetch(form.action, {
                method: 'POST',
                body: formData,
                credentials: 'include'
            }).then(response => {
                if (!response.ok) {
                    console.error('Send failed:', response.status, response.statusText);
                    return;
                }
                input.value = '';
                lastTimestamp = null;
                fetchMessages(chatId, isAdmin, userName, adminName);
                setTimeout(() => fetchMessages(chatId, isAdmin, userName, adminName), 1000);
            }).catch(error => console.error('Send error:', error));
        }
    });
    
    input.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            form.dispatchEvent(new Event('submit'));
        }
    });

    fetchMessages(chatId, isAdmin, userName, adminName);
    
    pollingInterval = setInterval(() => {
        fetchMessages(chatId, isAdmin, userName, adminName);
    }, 3000);
}

function fetchMessages(chatId, isAdmin, userName, adminName, retryCount = 0) {
    const url = isAdmin ? `/admin/chat/${chatId}/messages` : `/chat/${chatId}/messages`;
    console.log('Fetching from:', url);
    
    fetch(url, {
        credentials: 'include',
        headers: {
            'Accept': 'application/json'
        }
    })
        .then(response => {
            console.log('Response status:', response.status);
            if (!response.ok) {
                console.error('Fetch failed:', response.status, response.statusText, 'URL:', url);
                // Retry при 400 (3 раза, пауза 500ms)
                if (response.status === 400 && retryCount < 3) {
                    console.log(`Retrying fetch #${retryCount + 1}...`);
                    setTimeout(() => fetchMessages(chatId, isAdmin, userName, adminName, retryCount + 1), 500);
                    return null;
                }
                return null;
            }
            return response.json();
        })
        .then(data => {
            if (!data || data.error) {
                console.error('Fetch error:', data ? data.error : 'No data', 'URL:', url);
                return;
            }
            
            console.log('New messages:', data.messages.length);
            
            const messagesContainer = document.getElementById('chat-messages');
            const newMessages = data.messages.filter(msg => 
                !lastTimestamp || new Date(msg.timestamp) > new Date(lastTimestamp)
            );
            
            console.log('Adding new messages:', newMessages.length);
            
            newMessages.forEach(msg => {
                const messageDiv = document.createElement('div');
                messageDiv.className = 'mb-2';
                let senderName = msg.sender;
                if (msg.sender === 'user') {
                    senderName = userName;
                } else if (msg.sender === 'support') {
                    senderName = adminName || 'Служба поддержки';
                }
                messageDiv.innerHTML = `
                    <strong>${senderName}:</strong> ${msg.content}
                    <small class="text-muted float-end">${msg.time_str}</small>
                `;
                messagesContainer.appendChild(messageDiv);
            });
            
            if (data.messages.length > 0) {
                lastTimestamp = data.messages[data.messages.length - 1].timestamp;
            }
            
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        })
        .catch(error => {
            console.error('Polling error:', error, 'URL:', url);
        });
}