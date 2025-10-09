from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.user import User
from models.hotel import Hotel
from models.hotel_application import HotelApplication
from config import Config
from translations import gettext
from currencies import CURRENCIES, convert_price, get_symbol
import re
import base64

auth_bp = Blueprint('auth', __name__, template_folder='templates')

def is_valid_password(password, email):
    """Проверка пароля: мин 8 символов, 1 upper, 1 lower, 1 digit, 1 special, не равен email"""
    if len(password) < 8:
        return False, "Пароль должен быть минимум 8 символов."
    if password.lower() == email.lower():
        return False, "Пароль не может быть равен email."
    if not re.search(r"[A-Z]", password):
        return False, "Пароль должен содержать минимум 1 заглавную букву."
    if not re.search(r"[a-z]", password):
        return False, "Пароль должен содержать минимум 1 строчную букву."
    if not re.search(r"\d", password):
        return False, "Пароль должен содержать минимум 1 цифру."
    if not re.search(r"[!@#$%^&*()]", password):
        return False, "Пароль должен содержать минимум 1 специальный символ (!@#$%^&*())."
    return True, ""

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    lang = session.get('lang', 'eng')
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form.get('confirm_password', '')
        name = request.form['name']
        
        if password != confirm_password:
            flash(gettext('flash_error_prefix', lang) + 'Пароли не совпадают!')
            return render_template('register.html', lang=lang)
        
        existing_user = User.get_user_by_email(email)
        if existing_user:
            flash(gettext('flash_error_prefix', lang) + 'Email уже зарегистрирован!')
            return redirect(url_for('auth.register'))
        
        is_valid, error_msg = is_valid_password(password, email)
        if not is_valid:
            flash(gettext('flash_error_prefix', lang) + error_msg)
            return render_template('register.html', lang=lang)
        
        user_id = User.create_user(email, password, name)  # admin=False, moderator=False по умолчанию
        flash(gettext('flash_success', lang) + 'Регистрация успешна! Войдите в аккаунт.')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html', lang=lang)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    lang = session.get('lang', 'eng')
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.get_user_by_email(email)
        if user and User.check_password(user, password):
            session['user_id'] = str(user['_id'])
            session['user_email'] = email
            session['user_name'] = user['name']
            flash(gettext('flash_success', lang) + 'Вход успешен!')
            return redirect(url_for('search.search_hotels'))
        else:
            flash(gettext('flash_error_prefix', lang) + 'Неверный email или пароль!')
    
    return render_template('login.html', lang=lang)

@auth_bp.route('/logout')
def logout():
    lang = session.get('lang', 'eng')
    session.clear()
    flash(gettext('flash_success', lang) + 'Вы вышли из аккаунта.')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
def profile():
    lang = session.get('lang', 'eng')
    if 'user_id' not in session:
        flash(gettext('flash_error_prefix', lang) + 'Войдите в аккаунт!')
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    bookings = User.get_user_bookings(user_id)
    applications = HotelApplication.get_user_applications(user_id)
    # Сортировка заявок по created_at (от новых к старым)
    applications = sorted(applications, key=lambda x: x['created_at'], reverse=True)
    
    return render_template('profile.html', user=session, bookings=bookings, applications=applications, lang=lang)

@auth_bp.route('/profile/history')
def profile_history():
    lang = session.get('lang', 'eng')
    currency = session.get('currency', 'usd')
    if 'user_id' not in session:
        flash(gettext('flash_error_prefix', lang) + 'Войдите в аккаунт!')
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    viewed_hotels = User.get_viewed_hotels(user_id)  # Отсортировано по viewed_at
    viewed_hotels = [h for h in viewed_hotels if h]
    for hotel in viewed_hotels:
        if 'price_usd' not in hotel:
            hotel['display_price'] = 0
        else:
            hotel['display_price'] = convert_price(hotel['price_usd'], 'usd', currency)
    currency_symbol = get_symbol(currency)
    
    return render_template('profile_history.html', viewed_hotels=viewed_hotels, lang=lang, currency_symbol=currency_symbol)

@auth_bp.route('/profile/history/clear', methods=['POST'])
def clear_history():
    lang = session.get('lang', 'eng')
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': gettext('flash_error_prefix', lang) + 'Войдите в аккаунт!'})
    
    hotel_ids = request.form.getlist('hotel_ids')
    if not hotel_ids:
        return jsonify({'success': False, 'error': gettext('flash_error_prefix', lang) + 'Выберите хотя бы один отель для удаления!'})
    
    User.clear_viewed_hotels(session['user_id'], hotel_ids)
    return jsonify({'success': True})

@auth_bp.route('/set_lang', methods=['POST'])
def set_lang():
    lang = request.form.get('lang')
    if lang in ['rus', 'eng', 'rom']:
        session['lang'] = lang
    return jsonify({'success': True})

@auth_bp.route('/set_currency', methods=['POST'])
def set_currency():
    cur = request.form.get('currency')
    if cur in CURRENCIES:
        session['currency'] = cur
    return jsonify({'success': True})

@auth_bp.route('/check_email', methods=['POST'])
def check_email():
    email = request.form.get('email')
    exists = User.get_user_by_email(email) is not None
    return jsonify({'exists': exists})

@auth_bp.route('/owner_form', methods=['GET', 'POST'])
def owner_form():
    lang = session.get('lang', 'eng')
    if 'user_id' not in session:
        flash(gettext('flash_error_prefix', lang) + 'Войдите в аккаунт!')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        name = request.form.get('name')
        city = request.form.get('city')
        price_usd = request.form.get('price_usd')
        category = request.form.get('category')
        description = request.form.get('description')
        photos = request.files.getlist('photos')

        if not all([name, city, price_usd, category, description]):
            flash(gettext('flash_error_prefix', lang) + 'Заполните все поля!')
            return render_template('owner_form.html', lang=lang)

        try:
            price_usd = float(price_usd)
            if price_usd <= 0:
                raise ValueError
        except ValueError:
            flash(gettext('flash_error_prefix', lang) + 'Цена должна быть числом больше 0!')
            return render_template('owner_form.html', lang=lang)

        # Конвертация фотографий в Base64
        photo_data = []
        for photo in photos:
            if photo:
                photo_b64 = base64.b64encode(photo.read()).decode('utf-8')
                photo_data.append(photo_b64)

        hotel_data = {
            'name': name,
            'city': city,
            'price_usd': price_usd,
            'category': int(category),
            'description': description,
            'photos': photo_data,
            'reviews': [],
            'rooms': {'standard': {'available': True}, 'deluxe': {'available': True}}
        }

        HotelApplication.create_application(session['user_id'], hotel_data)
        flash(gettext('flash_success', lang) + 'Заявка отправлена на модерацию!')
        return redirect(url_for('auth.profile'))

    return render_template('owner_form.html', lang=lang)