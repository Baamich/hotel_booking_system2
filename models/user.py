from models import db
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
import datetime

class User:
    @staticmethod
    def create_user(email, password, name):
        """Регистрация: хэшируем пароль"""
        hashed_pw = generate_password_hash(password)
        data = {
            'email': email,
            'password': hashed_pw,
            'name': name,
            'bookings': [],  
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