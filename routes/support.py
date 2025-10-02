from flask import Blueprint, render_template, request, session, redirect, url_for, flash
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
    
    # Получаем все чаты пользователя
    chats = db.chats.find({'user_id': user_id})
    return render_template('support/chats.html', chats=chats, lang=lang)

@support_bp.route('/chat/new', methods=['GET', 'POST'])
def new_chat():
    lang = session.get('lang', 'eng')
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        chat = {
            'user_id': user_id,
            'created_at': datetime.utcnow(),
            'messages': [
                {
                    'sender': 'system',
                    'content': gettext('support_welcome', lang),
                    'timestamp': datetime.utcnow()
                }
            ],
            'admin_id': None,
            'status': 'new'
        }
        chat_id = db.chats.insert_one(chat).inserted_id
        return redirect(url_for('support.chat', chat_id=chat_id))
    
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
    
    return render_template('support/chat.html', chat=chat, chat_id=chat_id, lang=lang)

@support_bp.route('/chat/<chat_id>/send', methods=['POST'])
def send_message(chat_id):
    user_id = session.get('user_id')
    lang = session.get('lang', 'eng')
    if not user_id:
        return redirect(url_for('auth.login'))
    
    message_content = request.form.get('message')
    if message_content:
        db.chats.update_one(
            {'_id': ObjectId(chat_id), 'user_id': user_id},
            {
                '$push': {
                    'messages': {
                        'sender': 'user',
                        'content': message_content,
                        'timestamp': datetime.utcnow()
                    }
                }
            }
        )
        db.chats.update_one(
            {'_id': ObjectId(chat_id), 'user_id': user_id},
            {
                '$push': {
                    'messages': {
                        'sender': 'system',
                        'content': gettext('support_wait', lang),
                        'timestamp': datetime.utcnow()
                    }
                },
                '$set': {'status': 'in_progress'}
            }
        )
        from app import socketio
        socketio.emit('new_message', {'chat_id': chat_id}, room=chat_id)
    
    return redirect(url_for('support.chat', chat_id=chat_id))

@support_bp.route('/admin_panel')
def admin_panel():
    lang = session.get('lang', 'eng')
    user_id = session.get('user_id')
    if not user_id or not User.get_admin_status(user_id):
        flash(gettext('flash_error_prefix', lang) + 'Доступ только для администраторов!')
        return redirect(url_for('auth.profile'))
    
    new_chats = list(db.chats.find({'admin_id': None, 'status': 'new'}))
    return render_template('admin_panel.html', new_chats=new_chats, lang=lang)

@support_bp.route('/admin/take_chat/<chat_id>', methods=['POST'])
def take_chat(chat_id):
    lang = session.get('lang', 'eng')
    user_id = session.get('user_id')
    if not user_id or not User.get_admin_status(user_id):
        flash(gettext('flash_error_prefix', lang) + 'Доступ только для администраторов!')
        return redirect(url_for('support.admin_panel'))
    
    admin = User.get_user_by_id(user_id)  # Получаем пользователя
    if admin:
        admin_name = admin['name']
        chat = db.chats.find_one_and_update(
            {'_id': ObjectId(chat_id), 'admin_id': None},
            {
                '$set': {
                    'admin_id': user_id,
                    'status': 'in_progress',
                    'admin_name': admin_name
                }
            },
            return_document=True
        )
        if chat:
            flash(gettext('flash_success', lang) + 'Чат успешно взят!')
            return redirect(url_for('support.chat', chat_id=chat_id))
        else:
            flash(gettext('flash_error_prefix', lang) + 'Чат уже занят или не существует!')
            return redirect(url_for('support.admin_panel'))
    else:
        flash(gettext('flash_error_prefix', lang) + 'Ошибка при получении данных администратора!')
        return redirect(url_for('support.admin_panel'))

@support_bp.route('/admin/history')
def admin_history():
    lang = session.get('lang', 'eng')
    user_id = session.get('user_id')
    if not user_id or not User.get_admin_status(user_id):
        flash(gettext('flash_error_prefix', lang) + 'Доступ только для администраторов!')
        return redirect(url_for('auth.profile'))
    
    history = list(db.chats.find({'admin_id': user_id}).sort('updated_at', -1))
    return render_template('admin_history.html', history=history, lang=lang)