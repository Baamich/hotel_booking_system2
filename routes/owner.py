from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.user import User
from models.hotel import Hotel
from translations import gettext
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
from bson import ObjectId

load_dotenv()

owner_bp = Blueprint('owner', __name__, template_folder='templates')

@owner_bp.route('/owner/submit', methods=['GET', 'POST'])
def submit_hotel():
    lang = session.get('lang', 'eng')
    if 'user_id' not in session:
        flash(gettext('flash_error_prefix', lang) + 'Войдите в аккаунт!')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        hotel_data = {
            'name': request.form.get('name'),
            'city': request.form.get('city'),
            'price_usd': float(request.form.get('price_usd', 0)),
            'category': request.form.get('category'),
            'description': request.form.get('description'),
            'photos': request.form.getlist('photos'), 
            'rooms': {
                'single': {'available': int(request.form.get('single_rooms', 0))},
                'double': {'available': int(request.form.get('double_rooms', 0))},
                'suite': {'available': int(request.form.get('suite_rooms', 0))}
            }
        }
        
        # Валидация
        if not hotel_data['name'] or not hotel_data['city'] or not hotel_data['category'] or not hotel_data['description']:
            flash(gettext('flash_error_prefix', lang) + 'Заполните все обязательные поля!')
            return render_template('owner_submit.html', lang=lang)
        
        if hotel_data['price_usd'] <= 0:
            flash(gettext('flash_error_prefix', lang) + 'Цена должна быть больше 0!')
            return render_template('owner_submit.html', lang=lang)
        
        User.submit_hotel_application(session['user_id'], hotel_data)
        flash(gettext('flash_success', lang) + 'Заявка на добавление отеля отправлена на модерацию!')
        return redirect(url_for('auth.profile'))
    
    return render_template('owner_submit.html', lang=lang)

@owner_bp.route('/moderator/panel')
def moderator_panel():
    lang = session.get('lang', 'eng')
    if 'user_id' not in session:
        flash(gettext('flash_error_prefix', lang) + 'Войдите в аккаунт!')
        return redirect(url_for('auth.login'))
    
    if not User.get_moderator_status(session['user_id']):
        flash(gettext('flash_error_prefix', lang) + 'Доступ запрещен!')
        return redirect(url_for('auth.profile'))
    
    applications = User.get_hotel_applications(status='pending')
    for app in applications:
        app['user'] = User.get_user_by_id(str(app['user_id']))
    
    return render_template('moderator_panel.html', applications=applications, lang=lang)

@owner_bp.route('/moderator/review/<application_id>', methods=['POST'])
def review_application(application_id):
    lang = session.get('lang', 'eng')
    if 'user_id' not in session or not User.get_moderator_status(session['user_id']):
        return jsonify({'success': False, 'error': gettext('flash_error_prefix', lang) + 'Доступ запрещен!'})
    
    status = request.form.get('status')
    rejection_reason = request.form.get('rejection_reason')
    
    if status not in ['approved', 'rejected']:
        return jsonify({'success': False, 'error': 'Неверный статус!'})
    
    if status == 'rejected' and not rejection_reason:
        return jsonify({'success': False, 'error': 'Укажите причину отклонения!'})
    
    application = db.hotel_applications.find_one({'_id': ObjectId(application_id)})
    if not application:
        return jsonify({'success': False, 'error': 'Заявка не найдена!'})
    
    user = User.get_user_by_id(str(application['user_id']))
    
    # Обновляем заявку
    User.update_hotel_application(application_id, status, rejection_reason)
    
    # Если одобрено, добавляем отель в базу
    if status == 'approved':
        hotel_id = Hotel.create_hotel(application['hotel_data'])
        # Можно добавить связь отеля с владельцем, если нужно
    
    # Отправка письма
    try:
        msg = MIMEText(
            f"Ваша заявка на добавление отеля {'одобрена' if status == 'approved' else 'отклонена'}.\n"
            f"{'' if status == 'approved' else f'Причина: {rejection_reason}'}",
            'plain', 'utf-8'
        )
        msg['Subject'] = 'Статус вашей заявки на добавление отеля'
        msg['From'] = os.getenv('EMAIL_FROM')
        msg['To'] = user['email']
        
        with smtplib.SMTP(os.getenv('SMTP_SERVER'), os.getenv('SMTP_PORT')) as server:
            server.starttls()
            server.login(os.getenv('EMAIL_FROM'), os.getenv('EMAIL_PASSWORD'))
            server.send_message(msg)
    except Exception as e:
        print(f"Ошибка отправки письма: {e}")
        return jsonify({'success': False, 'error': 'Ошибка отправки уведомления!'})
    
    return jsonify({'success': True})