from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
from dotenv import load_dotenv
load_dotenv()

# === ДОБАВЛЯЕМ КОРЕНЬ ПРОЕКТА ===
current_dir = os.path.dirname(os.path.abspath(__file__))
microservices_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(microservices_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
print(f"[APP] Путь к корню: {project_root}")

# === ИМПОРТИРУЕМ process_message И gettext ===
from chat_service import process_message
from translations import gettext  # <-- ГЛОБАЛЬНЫЙ gettext

app = Flask(__name__)
CORS(app)

@app.route('/chat', methods=['OPTIONS', 'POST'])
def chat():
    # === CORS preflight ===
    if request.method == 'OPTIONS':
        return '', 200

    data = request.get_json() or {}
    user_message = data.get('message', '').strip()
    lang = data.get('lang', 'eng')

    # === PING ===
    if user_message == 'ping':
        return jsonify({'reply': 'pong'}), 200

    if not user_message:
        return jsonify({'reply': gettext('type_message', lang)}), 200

    try:
        # ПЕРЕДАЁМ ТОЛЬКО message и lang
        reply = process_message(user_message, lang)
        return jsonify({'reply': reply}), 200
    except Exception as e:
        print(f"[AI ERROR] {e}")
        return jsonify({'reply': gettext('flash_error', lang)}), 500

if __name__ == '__main__':
    print("ИИ-помощник запущен: http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=False)