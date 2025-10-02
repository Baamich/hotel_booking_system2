from models import db
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
import datetime

class User:
    @staticmethod
    def create_user(email, password, name, admin=False):
        """Регистрация: хэшируем пароль с добавлением статуса admin"""
        hashed_pw = generate_password_hash(password)
        data = {
            'email': email,
            'password': hashed_pw,
            'name': name,
            'admin': admin,
            'bookings': [],
            'viewed_hotels': [],
            'created_at': datetime.datetime.utcnow()
        }
        result = db.users.insert_one(data)
        return str(result.inserted_id)

    @staticmethod
    def get_user_by_email(email):
        return db.users.find_one({'email': email})

    @staticmethod
    def check_password(user, password):
        return check_password_hash(user['password'], password)

    @staticmethod
    def add_booking(user_id, booking_id):
        db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$push': {'bookings': booking_id}}
        )

    @staticmethod
    def get_user_bookings(user_id):
        user = db.users.find_one({'_id': ObjectId(user_id)})
        if user:
            return [db.bookings.find_one({'_id': ObjectId(b_id)}) for b_id in user.get('bookings', [])]
        return []

    @staticmethod
    def add_viewed_hotel(user_id, hotel_id):
        """Добавление просмотренного отеля с timestamp (без дубликатов, обновляет дату)"""
        new_view = {
            'hotel_id': hotel_id,
            'viewed_at': datetime.datetime.utcnow()
        }
        db.users.update_one(
            {'_id': ObjectId(user_id), 'viewed_hotels.hotel_id': {'$ne': hotel_id}},
            {'$push': {'viewed_hotels': new_view}}
        )
        db.users.update_one(
            {'_id': ObjectId(user_id), 'viewed_hotels.hotel_id': hotel_id},
            {'$set': {'viewed_hotels.$[elem].viewed_at': new_view['viewed_at']}},
            array_filters=[{'elem.hotel_id': hotel_id}]
        )

    @staticmethod
    def get_viewed_hotels(user_id):
        """Получить список просмотренных отелей с данными, сортировка по viewed_at"""
        user = db.users.find_one({'_id': ObjectId(user_id)})
        if user and user.get('viewed_hotels'):
            viewed_hotels = []
            for h in user['viewed_hotels']:
                if isinstance(h, str):
                    viewed_hotels.append({'hotel_id': h, 'viewed_at': datetime.datetime.utcnow()})
                elif isinstance(h, dict) and 'hotel_id' in h and 'viewed_at' in h:
                    viewed_hotels.append(h)
            
            viewed_hotels = sorted(viewed_hotels, key=lambda x: x['viewed_at'], reverse=True)
            hotels = [db.hotels.find_one({'_id': ObjectId(h['hotel_id'])}) for h in viewed_hotels]
            return [h for h in hotels if h]
        return []

    @staticmethod
    def clear_viewed_hotels(user_id, hotel_ids):
        """Удаление выбранных отелей из истории"""
        db.users.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$pull': {
                    'viewed_hotels': {
                        'hotel_id': {'$in': hotel_ids}
                    }
                }
            }
        )

    @staticmethod
    def set_admin_status(user_id, admin_status):
        """Установка статуса администратора"""
        db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'admin': admin_status}}
        )

    @staticmethod
    def get_admin_status(user_id):
        """Получение статуса администратора"""
        user = db.users.find_one({'_id': ObjectId(user_id)})
        return user.get('admin', False) if user else False

    @staticmethod
    def get_user_by_id(user_id):
        """Получение пользователя по ID"""
        return db.users.find_one({'_id': ObjectId(user_id)})