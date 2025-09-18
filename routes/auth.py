from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.user import User
from config import Config
from translations import gettext
from currencies import CURRENCIES
import re  # Для regex валидации пароля

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
        
        # Проверка повторения пароля
        if password != confirm_password:
            flash(gettext('flash_error_prefix', lang) + 'Пароли не совпадают!')
            return render_template('register.html', lang=lang)
        
        # Проверяем, существует ли пользователь
        existing_user = User.get_user_by_email(email)
        if existing_user:
            flash(gettext('flash_error_prefix', lang) + 'Email уже зарегистрирован!')
            return redirect(url_for('auth.register'))
        
        # Проверка пароля
        is_valid, error_msg = is_valid_password(password, email)
        if not is_valid:
            flash(gettext('flash_error_prefix', lang) + error_msg)
            return render_template('register.html', lang=lang)
        
        # Создаём пользователя
        user_id = User.create_user(email, password, name)
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
    bookings = User.get_user_bookings(user_id)  # История бронирований (пока пустая)
    
    return render_template('profile.html', user=session, bookings=bookings, lang=lang)

# Роут для установки языка
@auth_bp.route('/set_lang', methods=['POST'])
def set_lang():
    lang = request.form.get('lang')
    if lang in ['rus', 'eng', 'rom']:
        session['lang'] = lang
    return jsonify({'success': True})  # JSON для AJAX

# Роут для установки валюты (фикс: JSON вместо редиректа)
@auth_bp.route('/set_currency', methods=['POST'])
def set_currency():
    cur = request.form.get('currency')
    if cur in CURRENCIES:
        session['currency'] = cur
    return jsonify({'success': True})

# Роут для проверки email (AJAX)
@auth_bp.route('/check_email', methods=['POST'])
def check_email():
    email = request.form.get('email')
    exists = User.get_user_by_email(email) is not None
    return jsonify({'exists': exists})