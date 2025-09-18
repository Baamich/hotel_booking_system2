from models import db
from bson import ObjectId
import datetime

# Обновление viewed_hotels для всех пользователей
users = db.users.find()
for user in users:
    if 'viewed_hotels' in user and isinstance(user['viewed_hotels'], list):
        # Проверяем, есть ли строки (старый формат)
        if any(isinstance(h, str) for h in user['viewed_hotels']):
            new_viewed_hotels = []
            for h in user['viewed_hotels']:
                if isinstance(h, str):
                    new_viewed_hotels.append({'hotel_id': h, 'viewed_at': datetime.datetime.utcnow()})
                else:
                    new_viewed_hotels.append(h)
            db.users.update_one(
                {'_id': user['_id']},
                {'$set': {'viewed_hotels': new_viewed_hotels}}
            )
            print(f"Updated viewed_hotels for user {user['email']}")