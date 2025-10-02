from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from flask_socketio import emit, join_room
from pymongo import MongoClient
from bson.objectid import ObjectId
from translations import gettext
import os
from datetime import datetime
from models.user import User

support_bp = Blueprint('support', __name__)

# Подключение к MongoDB
mongo = MongoClient(os.getenv('MONGO_URI'))
db = mongo.get_database()

@support_bp.route('/chats')
def chats():
    lang = session.get('lang', 'eng')
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))
    
    # Получаем все чаты пользователя, с форматированной датой
    chats = []
    for chat in db.chats.find({'user_id': user_id}).sort('updated_at', -1):
        chat['formatted_date'] = chat.get('updated_at', chat['created_at']).strftime('%Y-%m-%d %H:%M')
        chats.append(chat)
    
    return render_template('support/chats.html', chats=chats, lang=lang)

@support_bp.route('/chat/new', methods=['GET', 'POST'])
def new_chat():
    lang = session.get('lang', 'eng')
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        message_content = request.form.get('message')
        if message_content:
            user_name = session.get('user_name', 'Пользователь')
            # Создаём чат с первым сообщением + системным
            now = datetime.utcnow()
            chat = {
                'user_id': user_id,
                'user_name': user_name,
                'created_at': now,
                'updated_at': now,
                'messages': [
                    {
                        'sender': 'user',
                        'content': message_content,
                        'timestamp': now
                    },
                    {
                        'sender': 'system',
                        'content': gettext('support_wait', lang),
                        'timestamp': now
                    }
                ],
                'admin_id': None,
                'status': 'new'  # new после сообщения
            }
            chat_id = db.chats.insert_one(chat).inserted_id
            return redirect(url_for('support.chat', chat_id=chat_id))
        else:
            flash(gettext('flash_error_prefix', lang) + 'Введите сообщение!')
    
    # GET: Форма для первого сообщения
    return render_template('support/new_chat.html', lang=lang)

@support_bp.route('/chat/<chat_id>')
def chat(chat_id):
    lang = session.get('lang', 'eng')
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))
    
    chat = db.chats.find_one({'_id': ObjectId(chat_id), 'user_id': user_id})
    if not chat:
        return redirect(url_for('support.chats'))
    
    is_admin = User.get_admin_status(user_id)
    chat['formatted_date'] = chat.get('updated_at', chat['created_at']).strftime('%Y-%m-%d %H:%M')
    return render_template('support/chat.html', chat=chat, chat_id=chat_id, lang=lang, is_admin=is_admin)

@support_bp.route('/chat/<chat_id>/send', methods=['POST'])
def send_message(chat_id):
    user_id = session.get('user_id')
    lang = session.get('lang', 'eng')
    if not user_id:
        return redirect(url_for('auth.login'))
    
    message_content = request.form.get('message')
    if message_content:
        now = datetime.utcnow()
        db.chats.update_one(
            {'_id': ObjectId(chat_id), 'user_id': user_id},
            {
                '$push': {
                    'messages': {
                        'sender': 'user',
                        'content': message_content,
                        'timestamp': now
                    }
                },
                '$set': {'updated_at': now}
            }
        )
        from app import socketio
        socketio.emit('new_message', {'chat_id': chat_id}, room=chat_id)
    
    return redirect(url_for('support.chat', chat_id=chat_id))

# JSON endpoint для polling сообщений (для пользователей)
@support_bp.route('/chat/<chat_id>/messages')
def get_chat_messages(chat_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Валидация chat_id
    if len(chat_id) != 24 or not all(c in '0123456789abcdefABCDEF' for c in chat_id):
        print(f"Invalid chat_id: {chat_id}")  # Лог для отладки
        return jsonify({'error': 'Invalid chat ID format'}), 400
    
    try:
        chat = db.chats.find_one({'_id': ObjectId(chat_id), 'user_id': user_id})
    except Exception as e:
        print(f"ObjectId error for {chat_id}: {e}")
        return jsonify({'error': 'Invalid chat ID'}), 400
    
    if not chat:
        return jsonify({'error': 'Chat not found'}), 404
    
    messages = []
    for msg in chat.get('messages', []):
        messages.append({
            'sender': msg['sender'],
            'content': msg['content'],
            'timestamp': msg['timestamp'].isoformat(),
            'time_str': msg['timestamp'].strftime('%H:%M')
        })
    
    return jsonify({'messages': messages})

@support_bp.route('/admin/chat/<chat_id>')
def admin_chat(chat_id):
    lang = session.get('lang', 'eng')
    user_id = session.get('user_id')
    if not user_id or not User.get_admin_status(user_id):
        flash(gettext('flash_error_prefix', lang) + 'Доступ только для администраторов!')
        return redirect(url_for('auth.profile'))
    
    chat = db.chats.find_one({'_id': ObjectId(chat_id), 'admin_id': user_id})
    if not chat:
        flash(gettext('flash_error_prefix', lang) + 'Чат недоступен!')
        return redirect(url_for('support.admin_panel'))
    
    is_admin = True
    chat['formatted_date'] = chat.get('updated_at', chat['created_at']).strftime('%Y-%m-%d %H:%M')
    return render_template('support/chat.html', chat=chat, chat_id=chat_id, lang=lang, is_admin=is_admin)

@support_bp.route('/admin/chat/<chat_id>/send', methods=['POST'])
def admin_send_message(chat_id):
    user_id = session.get('user_id')
    lang = session.get('lang', 'eng')
    if not user_id or not User.get_admin_status(user_id):
        flash(gettext('flash_error_prefix', lang) + 'Доступ только для администраторов!')
        return redirect(url_for('support.admin_panel'))
    
    message_content = request.form.get('message')
    if message_content:
        now = datetime.utcnow()
        db.chats.update_one(
            {'_id': ObjectId(chat_id), 'admin_id': user_id},
            {
                '$push': {
                    'messages': {
                        'sender': 'support',  # 'support' вместо 'admin_Имя'
                        'content': message_content,
                        'timestamp': now
                    }
                },
                '$set': {'updated_at': now, 'status': 'in_progress'}
            }
        )
        from app import socketio
        socketio.emit('new_message', {'chat_id': chat_id}, room=chat_id)
    
    return redirect(url_for('support.admin_chat', chat_id=chat_id))

# JSON endpoint для polling сообщений (для админов)
def get_admin_chat_messages(chat_id):
    user_id = session.get('user_id')
    if not user_id or not User.get_admin_status(user_id):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        chat = db.chats.find_one({'_id': ObjectId(chat_id), 'admin_id': user_id})
    except Exception as e:
        print(f"ObjectId error: {e}")
        return jsonify({'error': 'Invalid chat ID'}), 400
    
    if not chat:
        return jsonify({'error': 'Chat not found'}), 404
    
    messages = []
    for msg in chat.get('messages', []):
        messages.append({
            'sender': msg['sender'],
            'content': msg['content'],
            'timestamp': msg['timestamp'].isoformat(),
            'time_str': msg['timestamp'].strftime('%H:%M')
        })
    
    return jsonify({'messages': messages})

# Новый маршрут: Освободить чат
@support_bp.route('/admin/release_chat/<chat_id>', methods=['POST'])
def release_chat(chat_id):
    lang = session.get('lang', 'eng')
    user_id = session.get('user_id')
    if not user_id or not User.get_admin_status(user_id):
        flash(gettext('flash_error_prefix', lang) + 'Доступ только для администраторов!')
        return redirect(url_for('support.admin_panel'))
    
    chat = db.chats.find_one_and_update(
        {'_id': ObjectId(chat_id), 'admin_id': user_id},
        {
            '$set': {
                'admin_id': None,
                'status': 'new',
                'updated_at': datetime.utcnow()
            }
        },
        return_document=True
    )
    if chat:
        flash(gettext('flash_success', lang) + 'Чат освобождён и возвращён в очередь!')
        return redirect(url_for('support.admin_panel'))
    else:
        flash(gettext('flash_error_prefix', lang) + 'Чат не найден или не назначен вам!')
        return redirect(url_for('support.admin_panel'))

@support_bp.route('/admin_panel')
def admin_panel():
    lang = session.get('lang', 'eng')
    user_id = session.get('user_id')
    if not user_id or not User.get_admin_status(user_id):
        flash(gettext('flash_error_prefix', lang) + 'Доступ только для администраторов!')
        return redirect(url_for('auth.profile'))
    
    new_chats = list(db.chats.find({'admin_id': None, 'status': 'new'}).sort('created_at', -1))
    return render_template('admin_panel.html', new_chats=new_chats, lang=lang)

@support_bp.route('/admin/take_chat/<chat_id>', methods=['POST'])
def take_chat(chat_id):
    lang = session.get('lang', 'eng')
    user_id = session.get('user_id')
    if not user_id or not User.get_admin_status(user_id):
        flash(gettext('flash_error_prefix', lang) + 'Доступ только для администраторов!')
        return redirect(url_for('support.admin_panel'))
    
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
            flash(gettext('flash_success', lang) + 'Чат успешно взят!')
            return redirect(url_for('support.admin_chat', chat_id=chat_id))
        else:
            flash(gettext('flash_error_prefix', lang) + 'Чат уже занят!')
            return redirect(url_for('support.admin_panel'))
    else:
        flash(gettext('flash_error_prefix', lang) + 'Ошибка данных!')
        return redirect(url_for('support.admin_panel'))

@support_bp.route('/admin/history')
def admin_history():
    lang = session.get('lang', 'eng')
    user_id = session.get('user_id')
    if not user_id or not User.get_admin_status(user_id):
        flash(gettext('flash_error_prefix', lang) + 'Доступ только для администраторов!')
        return redirect(url_for('auth.profile'))
    
    # Форматируем даты
    history = []
    for chat in db.chats.find({'admin_id': user_id}).sort('updated_at', -1):
        chat['formatted_date'] = chat.get('updated_at', chat['created_at']).strftime('%Y-%m-%d %H:%M')
        history.append(chat)
    
    return render_template('admin_history.html', history=history, lang=lang)