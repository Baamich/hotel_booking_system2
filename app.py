from flask import Flask, session, render_template, redirect, url_for
from flask_cors import CORS
from flask_socketio import SocketIO
from config import Config
from dotenv import load_dotenv
from translations import gettext
from currencies import CURRENCIES, get_symbol
from models.user import User  # Импорт класса User
import os

# Загружаем .env
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)  # Для CORS, если нужно
socketio = SocketIO(app, cors_allowed_origins="http://127.0.0.1:5000")  # Убрано async_mode, используем дефолт

# Добавляем gettext как глобальную функцию для Jinja2
app.jinja_env.globals['gettext'] = gettext

# Новые globals для флагов, символов валюты и класса User
app.jinja_env.globals['FLAGS'] = {'rus': '🇷🇺', 'eng': '🇺🇸', 'rom': '🇷🇴'}
app.jinja_env.globals['get_symbol'] = get_symbol
app.jinja_env.globals['User'] = User  # Регистрация класса User

# Импорт роутов
from routes.auth import auth_bp
from routes.search import search_bp
from routes.booking import booking_bp
from routes.support import support_bp, emit_socket_event
from routes.socketio_events import register_socketio_events

# Регистрация blueprint'ов
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(search_bp, url_prefix='/search')
app.register_blueprint(booking_bp, url_prefix='/booking')
app.register_blueprint(support_bp, url_prefix='/support')

# Переопределение функции эмиссии событий
def emit_socket_event(event_name, data, broadcast=True, namespace='/'):
    socketio.emit(event_name, data, broadcast=broadcast, namespace=namespace)

# Регистрация Socket.IO событий
register_socketio_events(socketio)

@app.route('/')
def index():
    lang = session.get('lang', 'eng')
    return redirect(url_for('search.search_hotels'))  

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)