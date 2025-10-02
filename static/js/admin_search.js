function filterChats(type) {
    let items, searchId, searchUser, dateFrom, dateTo;
    
    if (type === 'new') {
        items = document.querySelectorAll('#new-chats-list .chat-item');
        searchId = document.getElementById('search-id').value.toLowerCase();
        searchUser = document.getElementById('search-user').value.toLowerCase();
        dateFrom = document.getElementById('search-date-from').value;
        dateTo = document.getElementById('search-date-to').value;
    } else if (type === 'history') {
        items = document.querySelectorAll('#history-list .chat-item');
        searchId = document.getElementById('search-history-id').value.toLowerCase();
        searchUser = document.getElementById('search-history-user').value.toLowerCase();
        dateFrom = document.getElementById('search-history-date-from').value;
        dateTo = document.getElementById('search-history-date-to').value;
    }

    items.forEach(item => {
        let id = item.dataset.id.toLowerCase();
        let user = item.dataset.user.toLowerCase();
        let date = item.dataset.date;

        let show = true;

        // Поиск по ID
        if (searchId && !id.includes(searchId)) show = false;

        // Поиск по имени
        if (searchUser && !user.includes(searchUser)) show = false;

        // Поиск по дате
        if (dateFrom && date < dateFrom) show = false;
        if (dateTo && date > dateTo) show = false;

        item.style.display = show ? 'block' : 'none';
    });
}

function clearSearch(type) {
    if (type === 'new') {
        document.getElementById('search-id').value = '';
        document.getElementById('search-user').value = '';
        document.getElementById('search-date-from').value = '';
        document.getElementById('search-date-to').value = '';
    } else if (type === 'history') {
        document.getElementById('search-history-id').value = '';
        document.getElementById('search-history-user').value = '';
        document.getElementById('search-history-date-from').value = '';
        document.getElementById('search-history-date-to').value = '';
    }
    filterChats(type);
}