from flask import Blueprint, render_template, request, jsonify, session, abort, flash, redirect, url_for
from translations import gettext
from currencies import convert_price, get_symbol
from bson import ObjectId
from models.hotel import Hotel
import os
from werkzeug.utils import secure_filename
from pymongo.errors import PyMongoError
import logging

# Настройка логирования
logging.basicConfig(level=logging.ERROR)

search_bp = Blueprint('search', __name__, template_folder='templates')

@search_bp.route('/hotels', methods=['GET'])
def search_hotels():
    lang = session.get('lang', 'eng')
    currency = session.get('currency', 'usd')
    try:
        hotels = Hotel.get_all_hotels()
        # Конвертируем цены из USD
        for hotel in hotels:
            if 'price_usd' not in hotel:
                logging.error(f"Hotel {hotel.get('name')} missing price_usd")
                hotel['display_price'] = 0  # Fallback
            else:
                hotel['display_price'] = convert_price(hotel['price_usd'], 'usd', currency)
        # Уникальные города и категории для фильтров
        cities = sorted(set(hotel['city'] for hotel in hotels))
        categories = sorted(set(hotel['category'] for hotel in hotels))
        currency_symbol = get_symbol(currency)
        return render_template('search.html', hotels=hotels, lang=lang, currency_symbol=currency_symbol, cities=cities, categories=categories)
    except PyMongoError:
        flash(gettext('flash_error_prefix', lang) + 'Ошибка соединения с БД!')
        return render_template('search.html', hotels=[], lang=lang, currency_symbol=get_symbol(currency), cities=[], categories=[])

@search_bp.route('/api/hotels', methods=['GET'])
def api_search_hotels():
    currency = request.args.get('currency', session.get('currency', 'usd'))
    city = request.args.get('city')
    min_price = request.args.get('min_price', '0')
    max_price = request.args.get('max_price', '999999')
    category = request.args.get('category')
    try:
        hotels = Hotel.get_all_hotels()
        # Фильтрация
        filtered_hotels = hotels
        if city and city != 'all':
            filtered_hotels = [h for h in filtered_hotels if h['city'] == city]
        if min_price:
            try:
                min_price = float(min_price)
                if min_price < 0:
                    logging.warning(f"Negative min_price: {min_price}")
                    return jsonify({'error': 'Минимальная цена не может быть отрицательной'})
                min_price_usd = min_price / convert_price(1, 'usd', currency)
                filtered_hotels = [h for h in filtered_hotels if h.get('price_usd', 0) >= min_price_usd]
            except (ValueError, ZeroDivisionError) as e:
                logging.error(f"Invalid min_price: {min_price}, error: {str(e)}")
                return jsonify({'error': 'Неверный формат минимальной цены'})
        if max_price:
            try:
                max_price = float(max_price)
                if max_price < 0:
                    logging.warning(f"Negative max_price: {max_price}")
                    return jsonify({'error': 'Максимальная цена не может быть отрицательной'})
                max_price_usd = max_price / convert_price(1, 'usd', currency)
                filtered_hotels = [h for h in filtered_hotels if h.get('price_usd', 0) <= max_price_usd]
            except (ValueError, ZeroDivisionError) as e:
                logging.error(f"Invalid max_price: {max_price}, error: {str(e)}")
                return jsonify({'error': 'Неверный формат максимальной цены'})
        if category and category != 'all':
            try:
                category = int(category)
                if category < 1 or category > 5:
                    logging.warning(f"Invalid category: {category}")
                    return jsonify({'error': 'Неверная категория (1–5)'})
                filtered_hotels = [h for h in filtered_hotels if h['category'] == category]
            except ValueError:
                logging.error(f"Invalid category: {category}")
                return jsonify({'error': 'Неверный формат категории'})
        # Конвертируем цены и ObjectId в строку
        for hotel in filtered_hotels:
            if 'price_usd' not in hotel:
                logging.error(f"Hotel {hotel.get('name')} missing price_usd")
                hotel['display_price'] = 0
            else:
                hotel['display_price'] = convert_price(hotel['price_usd'], 'usd', currency)
            hotel['_id'] = str(hotel['_id'])  # Преобразуем ObjectId в строку
        return jsonify(filtered_hotels)
    except Exception as e:
        logging.error(f"Error in api_search_hotels: {str(e)}")
        return jsonify({'error': 'Ошибка сервера'})

@search_bp.route('/api/convert_price', methods=['POST'])
def convert_price_api():
    try:
        data = request.form
        price_usd = float(data.get('price_usd', 0))
        currency = data.get('currency', 'usd')
        display_price = convert_price(price_usd, 'usd', currency)
        symbol = get_symbol(currency)
        return jsonify({'display_price': display_price, 'symbol': symbol})
    except Exception as e:
        logging.error(f"Error in convert_price_api: {str(e)}")
        return jsonify({'error': 'Ошибка конвертации'})

@search_bp.route('/hotel/<hotel_id>')
def hotel_detail(hotel_id):
    lang = session.get('lang', 'eng')
    currency = session.get('currency', 'usd')
    try:
        hotel = Hotel.get_hotel_by_id(hotel_id)
        if not hotel:
            abort(404)
        if 'price_usd' not in hotel:
            logging.error(f"Hotel {hotel.get('name')} missing price_usd")
            hotel['display_price'] = 0
        else:
            hotel['display_price'] = convert_price(hotel['price_usd'], 'usd', currency)
        currency_symbol = get_symbol(currency)
        return render_template('details.html', hotel=hotel, lang=lang, currency_symbol=currency_symbol)
    except PyMongoError:
        flash(gettext('flash_error_prefix', lang) + 'Ошибка соединения с БД!')
        return redirect(url_for('search.search_hotels'))

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