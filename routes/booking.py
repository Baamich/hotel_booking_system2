from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db
from bson import ObjectId
import datetime

booking_bp = Blueprint('booking', __name__, template_folder='templates')

@booking_bp.route('/book/<hotel_id>', methods=['POST'])
def book_hotel(hotel_id):
    if 'user_id' not in session:
        flash('Войдите в аккаунт для бронирования!')
        return redirect(url_for('auth.login'))
    
    # Создаём бронь (простая, без оплаты)
    booking_data = {
        'user_id': ObjectId(session['user_id']),
        'hotel_id': ObjectId(hotel_id),
        'date_from': request.form.get('date_from'),
        'date_to': request.form.get('date_to'),
        'room_type': request.form.get('room_type', 'standard'),
        'created_at': datetime.datetime.utcnow()
    }
    result = db.bookings.insert_one(booking_data)
    booking_id = str(result.inserted_id)
    
    # Добавляем в историю пользователя
    from models.user import User
    User.add_booking(session['user_id'], booking_id)
    
    # Обновляем доступность отеля
    from models.hotel import Hotel
    Hotel.update_availability(hotel_id, booking_data['room_type'], False)  # Уменьшаем доступность (упрощённо)
    
    flash('Бронь создана!')
    return redirect(url_for('auth.profile'))

@booking_bp.route('/cancel/<booking_id>')
def cancel_booking(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    booking = db.bookings.find_one({'_id': ObjectId(booking_id), 'user_id': ObjectId(session['user_id'])})
    if booking:
        # Восстанавливаем доступность
        hotel = db.hotels.find_one({'_id': ObjectId(booking['hotel_id'])})
        if hotel:
            from models.hotel import Hotel
            Hotel.update_availability(str(booking['hotel_id']), booking['room_type'], True)
        
        db.bookings.delete_one({'_id': ObjectId(booking_id)})
        flash('Бронь отменена!')
    
    return redirect(url_for('auth.profile'))