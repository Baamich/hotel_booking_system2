document.addEventListener('DOMContentLoaded', function() {
    const selectAllCheckbox = document.getElementById('select-all');
    const hotelCheckboxes = document.querySelectorAll('.hotel-checkbox');
    const clearForm = document.getElementById('clear-history-form');
    const lang = document.body.getAttribute('lang') || 'eng';

    // Функция для перевода
    function gettext(key) {
        const translations = {
            'rus': {
                'flash_error_prefix': 'Ошибка! ',
                'flash_success': 'Успех! ',
                'no_viewed_hotels': 'Нет просмотренных отелей.',
                'clear_selected': 'Очистить выбранное',
                'select_all': 'Выбрать все'
            },
            'eng': {
                'flash_error_prefix': 'Error! ',
                'flash_success': 'Success! ',
                'no_viewed_hotels': 'No viewed hotels.',
                'clear_selected': 'Clear Selected',
                'select_all': 'Select All'
            },
            'rom': {
                'flash_error_prefix': 'Eroare! ',
                'flash_success': 'Succes! ',
                'no_viewed_hotels': 'Nu există hoteluri vizualizate.',
                'clear_selected': 'Șterge selectate',
                'select_all': 'Selectează tot'
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
        setTimeout(() => {
            bsToast.hide();
            toastDiv.remove(); 
        }, 3000);
    }

    // Чекбокс "Выбрать все"
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            hotelCheckboxes.forEach(checkbox => {
                checkbox.checked = selectAllCheckbox.checked;
            });
        });
    }

    // Очистка истории через AJAX
    if (clearForm) {
        clearForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const selectedHotels = Array.from(hotelCheckboxes)
                .filter(checkbox => checkbox.checked)
                .map(checkbox => checkbox.value);
            
            if (selectedHotels.length === 0) {
                showToast(gettext('flash_error_prefix') + 'Выберите хотя бы один отель!', true);
                return;
            }

            fetch('/auth/profile/history/clear', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: selectedHotels.map(id => `hotel_ids=${encodeURIComponent(id)}`).join('&')
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast(gettext('flash_success') + 'Выбранные отели удалены!', false);
                    selectedHotels.forEach(id => {
                        const card = document.querySelector(`input[value="${id}"]`)?.closest('.col-md-4');
                        if (card) card.remove();
                    });
                    if (!document.querySelector('.hotel-checkbox')) {
                        const row = document.querySelector('.row');
                        row.innerHTML = `<p>${gettext('no_viewed_hotels')}</p>`;
                    }
                } else {
                    showToast(gettext('flash_error_prefix') + (data.error || 'Ошибка при очистке истории!'), true);
                }
            })
            .catch(error => {
                console.error('Clear history error:', error);
                showToast(gettext('flash_error_prefix') + 'Ошибка при очистке истории!', true);
            });
        });
    }
});