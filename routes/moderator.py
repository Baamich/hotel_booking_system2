from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.hotel_application import HotelApplication
from models.hotel import Hotel
from models.user import User
from translations import gettext
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
import base64

load_dotenv()

moderator_bp = Blueprint('moderator', __name__, template_folder='templates')

def send_email(to_email, subject, body):
    """Отправка email"""
    email_from = os.getenv('EMAIL_FROM')
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT'))
    email_password = os.getenv('EMAIL_PASSWORD')

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = email_from
    msg['To'] = to_email

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_from, email_password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False

@moderator_bp.route('/moderator_panel')
def moderator_panel():
    lang = session.get('lang', 'eng')
    if 'user_id' not in session or not User.get_moderator_status(session['user_id']):
        flash(gettext('flash_error_prefix', lang) + 'Доступ запрещен!')
        return redirect(url_for('auth.login'))

    pending_applications = HotelApplication.get_pending_applications()
    applications = []
    for app in pending_applications:
        # Преобразуем ObjectId в строку
        app_data = {
            '_id': str(app['_id']),
            'user_id': str(app['user_id']),
            'hotel_data': app.get('hotel_data', {}), 
            'status': app.get('status', 'pending'),
            'rejection_reason': app.get('rejection_reason', None),
            'created_at': app.get('created_at', None),
            'updated_at': app.get('updated_at', None)
        }
        user = User.get_user_by_id(app_data['user_id'])
        app_data['user_name'] = user['name'] if user else 'Unknown'
        app_data['user_email'] = user['email'] if user else 'Unknown'
        applications.append(app_data)

    return render_template('moderator_panel.html', applications=applications, lang=lang)

@moderator_bp.route('/moderate/<application_id>', methods=['POST'])
def moderate_application(application_id):
    lang = session.get('lang', 'eng')
    if 'user_id' not in session or not User.get_moderator_status(session['user_id']):
        return jsonify({'success': False, 'error': gettext('flash_error_prefix', lang) + 'Доступ запрещен!'})

    action = request.form.get('action')
    application = HotelApplication.get_application_by_id(application_id)
    if not application:
        return jsonify({'success': False, 'error': gettext('flash_error_prefix', lang) + 'Заявка не найдена!'})

    user = User.get_user_by_id(str(application['user_id']))
    if not user:
        return jsonify({'success': False, 'error': gettext('flash_error_prefix', lang) + 'Пользователь не найден!'})

    if action == 'approve':
        # Добавляем отель в коллекцию hotels
        hotel_data = application.get('hotel_data', {})
        if not hotel_data:
            return jsonify({'success': False, 'error': gettext('flash_error_prefix', lang) + 'Данные отеля отсутствуют!'})
        hotel_id = Hotel.create_hotel(hotel_data)
        HotelApplication.update_application_status(application_id, 'approved')
        # Отправляем email
        send_email(
            user['email'],
            gettext('hotel_approved', lang),
            gettext('hotel_approved', lang)
        )
        return jsonify({'success': True, 'message': gettext('flash_success', lang) + 'Отель одобрен!'})

    elif action == 'reject':
        rejection_reason = request.form.get('rejection_reason')
        if not rejection_reason:
            return jsonify({'success': False, 'error': gettext('flash_error_prefix', lang) + 'Укажите причину отклонения!'})
        HotelApplication.update_application_status(application_id, 'rejected', rejection_reason)
        # Отправляем email
        send_email(
            user['email'],
            gettext('hotel_rejected', lang).format(reason=rejection_reason),
            gettext('hotel_rejected', lang).format(reason=rejection_reason)
        )
        return jsonify({'success': True, 'message': gettext('flash_success', lang) + 'Заявка отклонена!'})

    return jsonify({'success': False, 'error': gettext('flash_error_prefix', lang) + 'Неверное действие!'})