from flask import Flask, session, render_template, redirect, url_for, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from config import Config
from dotenv import load_dotenv
from translations import gettext
from currencies import CURRENCIES, get_symbol
from models.user import User
import os

load_dotenv()  # Загружаем .env (если есть)

app = Flask(__name__)
app.config.from_object(Config)

# MongoDB из переменной окружения (для Docker)
if os.getenv("MONGO_URI"):
    app.config["MONGO_URI"] = os.getenv("MONGO_URI")

CORS(app, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*")

# Jinja globals
app.jinja_env.globals['gettext'] = gettext
app.jinja_env.globals['FLAGS'] = {'rus': 'RU', 'eng': 'US', 'rom': 'RO'}
app.jinja_env.globals['get_symbol'] = get_symbol
app.jinja_env.globals['User'] = User

# Импорт роутов (после инициализации app)
from routes.auth import auth_bp
from routes.search import search_bp
from routes.booking import booking_bp
from routes.support import support_bp, emit_socket_event
from routes.moderator import moderator_bp
from routes.socketio_events import register_socketio_events

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(search_bp, url_prefix='/search')
app.register_blueprint(booking_bp, url_prefix='/booking')
app.register_blueprint(support_bp, url_prefix='/support')
app.register_blueprint(moderator_bp, url_prefix='/moderator')

def emit_socket_event(event_name, data, broadcast=True, namespace='/'):
    socketio.emit(event_name, data, broadcast=broadcast, namespace=namespace)

register_socketio_events(socketio)

@app.route('/')
def index():
    lang = session.get('lang', 'eng')
    return redirect(url_for('search.search_hotels'))

@app.route('/health')
def health():
    return jsonify({"status": "ok", "service": "main-app"}), 200

@app.route('/ai/session')
def ai_session():
    return {
        'lang': session.get('lang', 'eng'),
        'currency': session.get('currency', 'usd')
    }

if __name__ == '__main__':
    socketio.run(app, debug=False, host='0.0.0.0', port=5000)