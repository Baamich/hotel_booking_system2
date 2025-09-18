from flask import Blueprint, render_template, request, jsonify, session, abort, flash, redirect, url_for
from translations import gettext
from currencies import convert_price, get_symbol
from bson import ObjectId
from models.hotel import Hotel
import os
from werkzeug.utils import secure_filename
from pymongo.errors import PyMongoError  # Новый импорт для except

search_bp = Blueprint('search', __name__, template_folder='templates')

@search_bp.route('/hotels', methods=['GET'])
def search_hotels():
    lang = session.get('lang', 'eng')
    currency = session.get('currency', 'usd')
    try:
        hotels = Hotel.get_all_hotels()
        # Конвертируем цены из USD
        for hotel in hotels:
            hotel['display_price'] = convert_price(hotel['price_usd'], 'usd', currency)
        currency_symbol = get_symbol(currency)
        return render_template('search.html', hotels=hotels, lang=lang, currency_symbol=currency_symbol)
    except PyMongoError:
        flash(gettext('flash_error_prefix', lang) + 'Ошибка соединения с БД!')
        return render_template('search.html', hotels=[], lang=lang, currency_symbol=get_symbol(currency))

@search_bp.route('/api/hotels', methods=['GET'])
def api_search_hotels():
    currency = request.args.get('currency', session.get('currency', 'usd'))
    try:
        hotels = Hotel.get_all_hotels()
        # Конвертируем цены из USD
        for hotel in hotels:
            hotel['display_price'] = convert_price(hotel['price_usd'], 'usd', currency)
        return jsonify(hotels)
    except PyMongoError:
        return jsonify({'error': 'Connection error'})

# Роут для деталей отеля
@search_bp.route('/hotel/<hotel_id>')
def hotel_detail(hotel_id):
    lang = session.get('lang', 'eng')
    currency = session.get('currency', 'usd')
    try:
        hotel = Hotel.get_hotel_by_id(hotel_id)
        if not hotel:
            abort(404)
        # Конвертируем цену из USD
        hotel['display_price'] = convert_price(hotel['price_usd'], 'usd', currency)
        currency_symbol = get_symbol(currency)
        return render_template('details.html', hotel=hotel, lang=lang, currency_symbol=currency_symbol)
    except PyMongoError:
        flash(gettext('flash_error_prefix', lang) + 'Ошибка соединения с БД!')
        return redirect(url_for('search.search_hotels'))

# Роут для добавления отзыва
@search_bp.route('/add_review/<hotel_id>', methods=['POST'])
def add_review(hotel_id):
    if 'user_id' not in session:
        flash(gettext('flash_error_prefix', session.get('lang', 'eng')) + 'Войдите в аккаунт для оставления отзыва!')
        return redirect(url_for('auth.login'))
    
    try:
        text = request.form.get('text', '').strip()
        rating = int(request.form.get('rating', 5))
        photos = []
        upload_folder = 'static/uploads'
        os.makedirs(upload_folder, exist_ok=True)
        
        if 'photo' in request.files:
            files = request.files.getlist('photo')
            for file in files:
                if file.filename:
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(upload_folder, filename))
                    photos.append(filename)
        
        review_data = {
            'user': session['user_name'],
            'text': text,
            'rating': rating,
            'photos': photos
        }
        
        Hotel.add_review(hotel_id, review_data)
        flash(gettext('flash_success', session.get('lang', 'eng')) + 'Отзыв добавлен!')
    except PyMongoError:
        flash(gettext('flash_error_prefix', session.get('lang', 'eng')) + 'Ошибка соединения с БД!')
    
    return redirect(url_for('search.hotel_detail', hotel_id=hotel_id))