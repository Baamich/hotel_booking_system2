from flask import Blueprint, render_template, request, session, redirect, url_for, flash
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
                'status': 'new'
            }
            chat_id = db.chats.insert_one(chat).inserted_id
            return redirect(url_for('support.chat', chat_id=chat_id))
        else:
            flash(gettext('flash_error_prefix', lang) + 'Введите сообщение!')
    
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