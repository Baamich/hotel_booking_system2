from flask import Flask, session, render_template, redirect, url_for
from flask_cors import CORS
from config import Config
from dotenv import load_dotenv
from translations import gettext
from currencies import CURRENCIES, get_symbol
import os

# Загружаем .env
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)  # Для CORS, если нужно

# Добавляем gettext как глобальную функцию для Jinja2 (исправление ошибки)
app.jinja_env.globals['gettext'] = gettext

# Новые globals для флагов и символов валюты
app.jinja_env.globals['FLAGS'] = {'rus': '🇷🇺', 'eng': '🇺🇸', 'rom': '🇷🇴'}
app.jinja_env.globals['get_symbol'] = get_symbol

# Импорт роутов (после создания app, чтобы избежать циклических импортов)
from routes.auth import auth_bp
from routes.search import search_bp
from routes.booking import booking_bp

# Регистрация blueprint'ов (позже реализуем)
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(search_bp, url_prefix='/search')
app.register_blueprint(booking_bp, url_prefix='/booking')

@app.route('/')
def index():
    lang = session.get('lang', 'eng')
    return redirect(url_for('search.search_hotels'))  

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)