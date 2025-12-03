// Функция для перевода (заглушка)
function gettext(key, lang) {
    const translations = {
        'rus': {
            'flash_error_prefix': 'Ошибка! ',
            'search_btn': 'Искать',
            'search_city': 'Город',
            'min_price': 'Минимальная цена',
            'max_price': 'Максимальная цена',
            'category': 'Категория',
            'all_categories': 'Все категории',
            'stars': 'звезды',
            'per_night': 'за ночь',
            'details': 'Подробнее',
            'reset_filter': 'Сбросить фильтры'
        },
        'eng': {
            'flash_error_prefix': 'Error! ',
            'search_btn': 'Search',
            'search_city': 'City',
            'min_price': 'Min Price',
            'max_price': 'Max Price',
            'category': 'Category',
            'all_categories': 'All categories',
            'stars': 'stars',
            'per_night': 'per night',
            'details': 'Details',
            'reset_filter': 'Reset Filters'
        },
        'rom': {
            'flash_error_prefix': 'Eroare! ',
            'search_btn': 'Căutare',
            'search_city': 'Oraș',
            'min_price': 'Preț minim',
            'max_price': 'Preț maxim',
            'category': 'Categorie',
            'all_categories': 'Toate categoriile',
            'stars': 'stele',
            'per_night': 'pe noapte',
            'details': 'Detalii',
            'reset_filter': 'Resetați filtrele'
        }
    };
    return translations[lang]?.[key] || key;
}

// Функция для показа toast
function showToast(message, isError = false) {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;

    const toastDiv = document.createElement('div');
    toastDiv.className = `toast align-items-center text-white ${isError ? 'bg-danger' : 'bg-success'} border-0`;
    toastDiv.setAttribute('role', 'alert');
    toastDiv.setAttribute('aria-live', 'assertive');
    toastDiv.setAttribute('aria-atomic', 'true');
    toastDiv.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    toastContainer.appendChild(toastDiv);
    const bsToast = new bootstrap.Toast(toastDiv);
    bsToast.show();
    setTimeout(() => bsToast.hide(), 5000);
}

// Функция для рендера карточек отелей (ИСПРАВЛЕНА — теперь показывает настоящие фото!)
function renderHotels(hotels, currencySymbol, lang) {
    const hotelsRow = document.getElementById('hotels-row');
    hotelsRow.innerHTML = '';

    hotels.forEach(hotel => {
        // Определяем главное фото
        const mainPhoto = (hotel.photos && hotel.photos.length > 0)
            ? `data:image/jpeg;base64,${hotel.photos[0]}`
            : `https://via.placeholder.com/300x200?text=${encodeURIComponent(hotel.name)}`;

        const hotelDiv = document.createElement('div');
        hotelDiv.className = 'col-md-4 mb-3';

        hotelDiv.innerHTML = `
            <div class="card h-100 hotel-card" data-hotel-id="${hotel._id}" style="cursor: pointer;">
                <div class="card-body d-flex h-100">
                    <div class="card-img-container">
                        <img src="${mainPhoto}"
                             class="card-img-rect hotel-main-photo"
                             data-photo-index="0"
                             alt="${hotel.name}">
                    </div>
                    <div class="card-content flex-grow-1 ms-3">
                        <h5 class="card-title">${hotel.name}</h5>
                        <p class="card-text price-text"
                           data-price-usd="${hotel.price_usd}">
                            ${hotel.city} | ${hotel.category} ${gettext('stars', lang)} |
                            ${hotel.display_price} ${currencySymbol} ${gettext('per_night', lang)}
                        </p>
                        <a href="/search/hotel/${hotel._id}"
                           class="btn btn-primary mt-auto"
                           onclick="event.stopPropagation();">
                            ${gettext('details', lang)}
                        </a>
                    </div>
                </div>
            </div>
        `;
        hotelsRow.appendChild(hotelDiv);
    });

    // После рендера нужно заново навесить клики на карточки для лайтбокса
    attachHotelCardClicks();
}

// Присоединяем обработчики кликов по карточкам (выносим в отдельную функцию, чтобы вызывать после каждого рендера)
function attachHotelCardClicks() {
    document.querySelectorAll('.hotel-card').forEach(card => {
        card.addEventListener('click', function (e) {
            if (e.target.closest('a')) return; // не открывать лайтбокс при клике на кнопку "Подробнее"
            const hotelId = this.dataset.hotelId;
            const hotel = window.hotelsData.find(h => h._id === hotelId);
            if (!hotel || !hotel.photos || hotel.photos.length === 0) return;
            openLightbox(hotel.photos, 0);
        });
    });
}

// AJAX для фильтрации и смены валюты
document.addEventListener('DOMContentLoaded', function() {
    const lang = document.getElementById('hotels-row').getAttribute('data-lang');
    const currencyForms = document.querySelectorAll('.currency-form');
    const filterForm = document.getElementById('filter-form');
    const resetFilterBtn = document.getElementById('reset-filter');
    const currencySymbols = {
        'eur': '€',
        'uah': '₴',
        'rub': '₽',
        'usd': '$',
        'mdl': 'L',
        'ron': 'lei'
    };
    let currencySymbol = document.getElementById('hotels-row').getAttribute('data-currency-symbol') || '$';
    let currency = document.getElementById('hotels-row').getAttribute('data-currency') || 'usd';

    // Изначально вешаем клики на карточки (при первой загрузке страницы)
    attachHotelCardClicks();

    // Фильтрация отелей
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(filterForm);
            const params = new URLSearchParams({
                city: formData.get('city') || 'all',
                min_price: formData.get('min_price') || '0',
                max_price: formData.get('max_price') || '999999',
                category: formData.get('category') || 'all',
                currency: currency
            });

            fetch(`/search/api/hotels?${params}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        showToast(gettext('flash_error_prefix', lang) + data.error, true);
                        return;
                    }
                    // Обновляем глобальные данные для лайтбокса (чтобы он знал актуальные фото)
                    window.hotelsData = data;
                    renderHotels(data, currencySymbol, lang);
                })
                .catch(err => {
                    console.error('Fetch filter error:', err);
                    showToast(gettext('flash_error_prefix', lang) + 'Ошибка при фильтрации отелей!', true);
                });
        });
    }

    // Сброс фильтров
    if (resetFilterBtn) {
        resetFilterBtn.addEventListener('click', function() {
            filterForm.reset();
            document.getElementById('min_price').value = '0';
            document.getElementById('max_price').value = '999999';

            const params = new URLSearchParams({ currency: currency });
            fetch(`/search/api/hotels?${params}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        showToast(gettext('flash_error_prefix', lang) + data.error, true);
                        return;
                    }
                    window.hotelsData = data;
                    renderHotels(data, currencySymbol, lang);
                })
                .catch(err => {
                    console.error('Reset filter error:', err);
                    showToast(gettext('flash_error_prefix', lang) + 'Ошибка при сбросе фильтров!', true);
                });
        });
    }

    // Смена валюты — оставляем как было, она работает корректно
    currencyForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const newCurrency = this.querySelector('input[name="currency"]').value;
            const symbol = currencySymbols[newCurrency];

            fetch('/auth/set_currency', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'
                },
                body: 'currency=' + encodeURIComponent(newCurrency)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    currency = newCurrency;
                    currencySymbol = symbol;
                    document.getElementById('hotels-row').setAttribute('data-currency', currency);
                    document.getElementById('hotels-row').setAttribute('data-currency-symbol', symbol);
                    document.querySelector('.currency-icon') && (document.querySelector('.currency-icon').innerHTML = symbol);
                    document.getElementById('min_price_label').innerHTML = `${gettext('min_price', lang)} (${symbol})`;
                    document.getElementById('max_price_label').innerHTML = `${gettext('max_price', lang)} (${symbol})`;

                    // Перезапрашиваем отели с новой валютой
                    const currentParams = new URLSearchParams(window.location.search);
                    currentParams.set('currency', newCurrency);
                    fetch(`/search/api/hotels?${currentParams}`)
                        .then(r => r.json())
                        .then(hotels => {
                            window.hotelsData = hotels;
                            renderHotels(hotels, symbol, lang);
                        });
                }
            })
            .catch(err => {
                console.error('Set currency error:', err);
                showToast(gettext('flash_error_prefix', lang) + 'Не удалось сменить валюту!', true);
            });
        });
    });
});