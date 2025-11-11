from models import db
from bson import ObjectId
from datetime import datetime
import requests

class Hotel:
    @staticmethod
    def create_hotel(data):
        """Создание отеля в базе"""
        hotel = {
            'name': data.get('name'),
            'city': data.get('city'),
            'price_usd': float(data.get('price_usd', 0)),
            'category': int(data.get('category', 0)),
            'description': data.get('description', ''),
            'photos': data.get('photos', []),
            'reviews': data.get('reviews', []),
            'rooms': data.get('rooms', {'standard': {'available': True}, 'deluxe': {'available': True}}),
            'created_at': datetime.utcnow(),
            'location_address': data.get('location_address'),  
            'latitude': float(data.get('latitude')) if data.get('latitude') else None,  
            'longitude': float(data.get('longitude')) if data.get('longitude') else None  
        }
        result = db.hotels.insert_one(hotel)
        return str(result.inserted_id)

    @staticmethod
    def get_hotel_by_id(hotel_id):
        """Получение отеля по ID"""
        hotel = db.hotels.find_one({'_id': ObjectId(hotel_id)})
        if hotel:
            hotel['_id'] = str(hotel['_id'])
            hotel['photos'] = hotel.get('photos', [])
            return hotel
        return None

    @staticmethod
    def get_all_hotels():
        """Получение всех отелей"""
        hotels = list(db.hotels.find())
        for hotel in hotels:
            hotel['_id'] = str(hotel['_id'])
            hotel['photos'] = hotel.get('photos', [])
        return hotels

    @staticmethod
    def search_hotels(city=None, min_price=None, max_price=None, category=None):
        """Поиск отелей с фильтрами"""
        query = {}
        if city and city != 'all':
            query['city'] = city
        if min_price is not None:
            query['price_usd'] = {'$gte': float(min_price)}
        if max_price is not None:
            query['price_usd'] = query.get('price_usd', {})
            query['price_usd']['$lte'] = float(max_price)
        if category and category != 'all':
            query['category'] = int(category)
        
        hotels = list(db.hotels.find(query))
        for hotel in hotels:
            hotel['_id'] = str(hotel['_id'])
            hotel['photos'] = hotel.get('photos', [])
        return hotels

    @staticmethod
    def add_review(hotel_id, review):
        """Добавление отзыва к отелю"""
        db.hotels.update_one(
            {'_id': ObjectId(hotel_id)},
            {'$push': {'reviews': review}}
        )

    @staticmethod
    def get_cities():
        """Получение списка уникальных городов"""
        return list(db.hotels.distinct('city'))

    @staticmethod
    def get_categories():
        """Получение списка уникальных категорий"""
        return list(db.hotels.distinct('category'))