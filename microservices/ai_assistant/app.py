from flask import Flask, request, jsonify
from flask_cors import CORS  # <--- НОВОЕ
import sys
import os
from dotenv import load_dotenv
load_dotenv()

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from chat_service import process_message

app = Flask(__name__)
CORS(app)  # <--- ВКЛЮЧАЕМ CORS ДЛЯ ВСЕХ

def bot_gettext(key, lang='eng'):
    try:
        from translations import TRANSLATIONS
        return TRANSLATIONS.get(lang, TRANSLATIONS['eng']).get(key, key)
    except:
        return key

@app.route('/chat', methods=['OPTIONS', 'POST'])
def chat():
    # === ОБРАБОТКА OPTIONS (CORS preflight) ===
    if request.method == 'OPTIONS':
        return '', 200

    data = request.get_json() or {}
    user_message = data.get('message', '').strip()
    lang = data.get('lang', 'eng')

    # === PING ===
    if user_message == 'ping':
        return jsonify({'reply': 'pong'}), 200

    if not user_message:
        return jsonify({'reply': 'Напишите сообщение...'}), 200

    try:
        reply = process_message(user_message, lang, bot_gettext)
        return jsonify({'reply': reply}), 200
    except Exception as e:
        print(f"[AI ERROR] {e}")
        return jsonify({'reply': 'Ошибка. Попробуйте позже.'}), 500

if __name__ == '__main__':
    print("ИИ-помощник запущен: http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=False)