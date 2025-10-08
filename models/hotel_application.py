from models import db
from bson import ObjectId
import datetime

class HotelApplication:
    @staticmethod
    def create_application(user_id, data):
        """Создание заявки на добавление отеля"""
        application = {
            'user_id': ObjectId(user_id),
            'hotel_data': data,
            'status': 'pending',  # pending, approved, rejected
            'rejection_reason': None,
            'created_at': datetime.datetime.utcnow(),
            'updated_at': datetime.datetime.utcnow()
        }
        result = db.hotel_applications.insert_one(application)
        return str(result.inserted_id)

    @staticmethod
    def get_pending_applications():
        """Получение всех заявок со статусом pending"""
        applications = list(db.hotel_applications.find({'status': 'pending'}))
        return [{
            '_id': str(app['_id']),
            'user_id': str(app['user_id']),
            'hotel_data': app.get('hotel_data', {}),
            'status': app.get('status', 'pending'),
            'rejection_reason': app.get('rejection_reason', None),
            'created_at': app.get('created_at', None),
            'updated_at': app.get('updated_at', None)
        } for app in applications]

    @staticmethod
    def get_application_by_id(application_id):
        """Получение заявки по ID"""
        app = db.hotel_applications.find_one({'_id': ObjectId(application_id)})
        if app:
            return {
                '_id': str(app['_id']),
                'user_id': str(app['user_id']),
                'hotel_data': app.get('hotel_data', {}),
                'status': app.get('status', 'pending'),
                'rejection_reason': app.get('rejection_reason', None),
                'created_at': app.get('created_at', None),
                'updated_at': app.get('updated_at', None)
            }
        return None

    @staticmethod
    def get_user_applications(user_id):
        """Получение всех заявок пользователя"""
        applications = list(db.hotel_applications.find({'user_id': ObjectId(user_id)}))
        return [{
            '_id': str(app['_id']),
            'user_id': str(app['user_id']),
            'hotel_data': app.get('hotel_data', {}),
            'status': app.get('status', 'pending'),
            'rejection_reason': app.get('rejection_reason', None),
            'created_at': app.get('created_at', None),
            'updated_at': app.get('updated_at', None)
        } for app in applications]

    @staticmethod
    def update_application_status(application_id, status, rejection_reason=None):
        """Обновление статуса заявки"""
        update_data = {
            'status': status,
            'updated_at': datetime.datetime.utcnow()
        }
        if rejection_reason:
            update_data['rejection_reason'] = rejection_reason
        db.hotel_applications.update_one(
            {'_id': ObjectId(application_id)},
            {'$set': update_data}
        )