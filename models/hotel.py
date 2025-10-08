from models import db
from bson import ObjectId
import datetime
from models.hotel_photo import HotelPhoto

class Hotel:
    @staticmethod
    def create_hotel(data):
        """Создание отеля. data: dict с полями: name, city, price_usd, category, description, photo_ids, reviews"""
        data['created_at'] = datetime.datetime.utcnow()
        result = db.hotels.insert_one(data)
        return str(result.inserted_id)

    @staticmethod
    def get_all_hotels():
        hotels = list(db.hotels.find())
        for hotel in hotels:
            if 'price_usd' in hotel and 'price' not in hotel:
                hotel['price'] = hotel['price_usd']  # Совместимость
            hotel['photos'] = HotelPhoto.get_photos_by_application(hotel.get('_id', '')) if hotel.get('photo_ids') else []
        return hotels

    @staticmethod
    def get_hotel_by_id(hotel_id):
        hotel = db.hotels.find_one({'_id': ObjectId(hotel_id)})
        if hotel:
            if 'price_usd' in hotel and 'price' not in hotel:
                hotel['price'] = hotel['price_usd']  # Совместимость
            hotel['photos'] = HotelPhoto.get_photos_by_application(hotel_id) if hotel.get('photo_ids') else []
        return hotel

    @staticmethod
    def update_availability(hotel_id, room_type, available):
        """Обновление доступности номеров"""
        db.hotels.update_one(
            {'_id': ObjectId(hotel_id)},
            {'$set': {f'rooms.{room_type}.available': available}}
        )

    @staticmethod
    def add_review(hotel_id, review_data):
        """Добавление отзыва к отелю"""
        db.hotels.update_one(
            {'_id': ObjectId(hotel_id)},
            {'$push': {'reviews': review_data}}
        )