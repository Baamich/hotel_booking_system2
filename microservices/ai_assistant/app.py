from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
from dotenv import load_dotenv
load_dotenv()

# === ПУТЬ К КОРНЮ ===
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from chat_service import process_message
from translations import gettext

app = Flask(__name__)
CORS(app)

@app.route('/health')
def health():
    return jsonify({"status": "ok", "service": "ai-assistant"}), 200

@app.route('/chat', methods=['OPTIONS', 'POST'])
def chat():
    if request.method == 'OPTIONS':
        return '', 200

    data = request.get_json() or {}
    user_message = data.get('message', '').strip()
    lang = data.get('lang', 'eng')

    if user_message == 'ping':
        return jsonify({'reply': 'pong'}), 200

    if not user_message:
        return jsonify({'reply': gettext('type_message', lang)}), 200

    try:
        reply = process_message(user_message, lang)
        return jsonify({'reply': reply}), 200
    except Exception as e:
        print(f"[AI ERROR] {e}")
        return jsonify({'reply': gettext('flash_error', lang)}), 500

if __name__ == '__main__':
    print("ИИ-помощник запущен: http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=False)