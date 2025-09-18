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
    setTimeout(() => bsToast.hide(), 3000);
}

// Функция для рендера карточек отелей
function renderHotels(hotels, currencySymbol, lang) {
    const hotelsRow = document.getElementById('hotels-row');
    hotelsRow.innerHTML = '';
    hotels.forEach(hotel => {
        const hotelDiv = document.createElement('div');
        hotelDiv.className = 'col-md-4 mb-3';
        hotelDiv.innerHTML = `
            <div class="card">
                <img src="https://via.placeholder.com/300x200?text=${encodeURIComponent(hotel.name)}" class="card-img-top" alt="${hotel.name}">
                <div class="card-body">
                    <h5 class="card-title">${hotel.name}</h5>
                    <p class="card-text price-text" data-price-usd="${hotel.price_usd}">
                        ${hotel.city} | ${hotel.category} ${gettext('stars', lang)} | ${hotel.display_price} ${currencySymbol} ${gettext('per_night', lang)}
                    </p>
                    <a href="/hotel/${hotel._id}" class="btn btn-primary">${gettext('details', lang)}</a>
                </div>
            </div>
        `;
        hotelsRow.appendChild(hotelDiv);
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

    // Фильтрация отелей
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(filterForm);
            const params = new URLSearchParams({
                city: formData.get('city'),
                min_price: formData.get('min_price') || '0',
                max_price: formData.get('max_price') || '999999',
                category: formData.get('category'),
                currency: currency  // Используем текущую валюту из data-currency
            });
            fetch(`/search/api/hotels?${params}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        showToast(gettext('flash_error_prefix', lang) + data.error, true);
                        return;
                    }
                    renderHotels(data, currencySymbol, lang);
                })
                .catch(error => {
                    console.error('Fetch filter error:', error);
                    showToast(gettext('flash_error_prefix', lang) + 'Ошибка при фильтрации отелей!', true);
                });
        });
    }

    // Сброс фильтров
    if (resetFilterBtn) {
        resetFilterBtn.addEventListener('click', function() {
            filterForm.reset(); // Очистить поля формы
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
                    renderHotels(data, currencySymbol, lang);
                })
                .catch(error => {
                    console.error('Fetch reset filter error:', error);
                    showToast(gettext('flash_error_prefix', lang) + 'Ошибка при сбросе фильтров!', true);
                });
        });
    }

    // Смена валюты
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
                    // Обновить текущую валюту
                    currency = newCurrency;
                    currencySymbol = symbol;
                    document.getElementById('hotels-row').setAttribute('data-currency', currency);
                    document.getElementById('hotels-row').setAttribute('data-currency-symbol', symbol);
                    document.querySelector('.currency-icon').innerHTML = symbol;
                    document.getElementById('min_price_label').innerHTML = `${gettext('min_price', lang)} (${symbol})`;
                    document.getElementById('max_price_label').innerHTML = `${gettext('max_price', lang)} (${symbol})`;
                    // Обновить цены для каждой карточки
                    const priceEls = document.querySelectorAll('.price-text');
                    priceEls.forEach(priceEl => {
                        const priceUsd = parseFloat(priceEl.getAttribute('data-price-usd'));
                        fetch('/search/api/convert_price', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/x-www-form-urlencoded',
                                'Accept': 'application/json'
                            },
                            body: `price_usd=${priceUsd}&currency=${encodeURIComponent(newCurrency)}`
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.error) {
                                showToast(gettext('flash_error_prefix', lang) + 'Не удалось обновить валюту!', true);
                                return;
                            }
                            const parts = priceEl.innerHTML.split(' | ');
                            if (parts.length === 3) {
                                const currentPricePart = parts[2];
                                const perNight = currentPricePart.replace(/^\d+\.?\d*\s*\S+\s*/, '');
                                parts[2] = `${data.display_price} ${data.symbol} ${perNight}`;
                                priceEl.innerHTML = parts.join(' | ');
                            }
                        })
                        .catch(error => {
                            console.error('Fetch convert_price error:', error);
                            showToast(gettext('flash_error_prefix', lang) + 'Не удалось обновить валюту!', true);
                        });
                    });
                }
            })
            .catch(error => {
                console.error('Fetch set_currency error:', error);
                showToast(gettext('flash_error_prefix', lang) + 'Не удалось обновить валюту!', true);
            });
        });
    });
});