from flask_socketio import join_room, emit
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from datetime import datetime
from flask import session
from models.user import User

# Подключение к MongoDB
mongo = MongoClient(os.getenv('MONGO_URI'))
db = mongo.get_database()

def register_socketio_events(socketio):
    @socketio.on('connect')
    def handle_connect():
        user_id = session.get('user_id')
        if not user_id:
            return False  
        return True

    @socketio.on('join')
    def handle_join(data):
        chat_id = data.get('chat_id')
        if not chat_id:
            return
        try:
            chat = db.chats.find_one({'_id': ObjectId(chat_id)})
            if not chat:
                return
            user_id = session.get('user_id')
            if user_id == chat.get('user_id') or (User.get_admin_status(user_id) and chat.get('admin_id') == user_id):
                join_room(chat_id)
                emit('joined', {'message': 'Connected to chat'}, room=chat_id)
                # Отправляем текущее имя админа при подключении
                emit('update_admin_name', {'admin_name': chat.get('admin_name', '')}, room=chat_id)
        except Exception as e:
            print(f"Join error for chat_id {chat_id}: {e}")

    @socketio.on('send_message')
    def handle_send_message(data):
        chat_id = data.get('chat_id')
        message_content = data.get('message')
        if not chat_id or not message_content:
            return
        
        try:
            chat = db.chats.find_one({'_id': ObjectId(chat_id)})
            if not chat:
                return
            user_id = session.get('user_id')
            now = datetime.utcnow()
            sender = 'user' if user_id == chat.get('user_id') else 'support' if User.get_admin_status(user_id) else None
            if not sender:
                return
            
            db.chats.update_one(
                {'_id': ObjectId(chat_id)},
                {
                    '$push': {
                        'messages': {
                            'sender': sender,
                            'content': message_content,
                            'timestamp': now
                        }
                    },
                    '$set': {'updated_at': now}
                }
            )
            
            # Отправляем сообщение всем в комнате
            emit('new_message', {
                'sender': sender,
                'content': message_content,
                'timestamp': now.isoformat(),
                'time_str': now.strftime('%H:%M')
            }, room=chat_id)
        except Exception as e:
            print(f"Send message error for chat_id {chat_id}: {e}")

    @socketio.on('disconnect')
    def handle_disconnect():
        print('Client disconnected')

    @socketio.on('join_admin_panel')
    def handle_join_admin_panel():
        user_id = session.get('user_id')
        if not user_id or not User.get_admin_status(user_id):
            return False
        # Отправляем текущие новые чаты при подключении
        new_chats = list(db.chats.find({'admin_id': None, 'status': 'new'}).sort('created_at', -1))
        for chat in new_chats:
            emit('new_chat', {
                '_id': str(chat['_id']),
                'user_name': chat['user_name'],
                'created_at': chat['created_at']
            }, broadcast=True)

    # Обновление имени админа при взятии чата
    @socketio.on('take_chat')
    def handle_take_chat(data):
        chat_id = data.get('chat_id')
        user_id = session.get('user_id')
        if not chat_id or not user_id or not User.get_admin_status(user_id):
            return
        try:
            admin = User.get_user_by_id(user_id)
            if admin:
                admin_name = admin['name']
                chat = db.chats.find_one_and_update(
                    {'_id': ObjectId(chat_id), 'admin_id': None},
                    {
                        '$set': {
                            'admin_id': user_id,
                            'status': 'in_progress',
                            'admin_name': admin_name,
                            'updated_at': datetime.utcnow()
                        }
                    },
                    return_document=True
                )
                if chat:
                    emit('update_admin_name', {'admin_name': admin_name}, room=chat_id)
                    emit('chat_taken', {'chat_id': str(chat_id)}, broadcast=True)
        except Exception as e:
            print(f"Take chat error for chat_id {chat_id}: {e}")