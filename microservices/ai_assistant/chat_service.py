from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import re
import os
from dotenv import load_dotenv

load_dotenv()

# === ПОДКЛЮЧЕНИЕ К MONGODB ===
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/hotel_db')
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    db = client['hotel_db']
    hotels_collection = db['hotels']
    DB_CONNECTED = True
    print("[AI] Подключено к MongoDB: hotel_db.hotels")
except Exception as e:
    DB_CONNECTED = False
    print(f"[AI ERROR] MongoDB: {e}")

# === НОРМАЛИЗАЦИЯ ГОРОДОВ + ОПЕЧАТКИ ===
CITY_ALIASES = {
    'кишинёв': 'Chișinău', 'кишинев': 'Chișinău', 'chisinau': 'Chișinău',
    'кишиневв': 'Chișinău', 'кишинёвв': 'Chișinău', 'кишиневе': 'Chișinău',
    'бухарест': 'București', 'bucuresti': 'București', 'бухаресте': 'București',
    'яссы': 'Iași', 'iasi': 'Iași', 'ясси': 'Iași',
    'брашов': 'Brașov', 'brasov': 'Brașov', 'брашове': 'Brașov',
    'констанца': 'Constanța', 'constanta': 'Constanța', 'констанце': 'Constanța'
}

def normalize_city(city):
    city = city.lower().strip()
    city = re.sub(r'[^\w\s]', '', city)  # Убираем лишние символы
    return CITY_ALIASES.get(city, city.title())

def analyze_reviews(reviews):
    if not reviews:
        return {"avg_rating": 0, "summary": "Нет отзывов"}
    ratings = [r.get('rating', 0) for r in reviews if isinstance(r.get('rating'), (int, float))]
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    return {"avg_rating": avg_rating, "summary": f"Рейтинг: {avg_rating:.1f}/5"}

def find_hotels_advanced(min_price=None, max_price=None, min_stars=None, max_stars=None, city=None, good_reviews=False):
    if not DB_CONNECTED:
        return []

    mongo_query = {}

    if city:
        norm_city = normalize_city(city)
        mongo_query['city'] = {'$regex': f'^{re.escape(norm_city)}$', '$options': 'i'}

    if min_price is not None:
        mongo_query['price_usd'] = mongo_query.get('price_usd', {})
        mongo_query['price_usd']['$gte'] = float(min_price)
    if max_price is not None:
        mongo_query['price_usd'] = mongo_query.get('price_usd', {})
        mongo_query['price_usd']['$lte'] = float(max_price)

    if min_stars is not None:
        mongo_query['category'] = mongo_query.get('category', {})
        mongo_query['category']['$gte'] = int(min_stars)
    if max_stars is not None:
        mongo_query['category'] = mongo_query.get('category', {})
        mongo_query['category']['$lte'] = int(max_stars)

    print(f"[DEBUG] Запрос: {mongo_query}")

    try:
        cursor = hotels_collection.find(mongo_query).limit(5)
        hotels = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            doc['review_analysis'] = analyze_reviews(doc.get('reviews', []))
            hotels.append(doc)

        if good_reviews:
            hotels = [h for h in hotels if h['review_analysis']['avg_rating'] >= 4.0]

        print(f"[DEBUG] Найдено: {len(hotels)}")
        return hotels
    except Exception as e:
        print(f"[AI ERROR] {e}")
        return []

def process_message(message, lang='eng', gettext=None):
    message_lower = message.strip().lower()

    # === СВОДКА ===
    if 'сводка' in message_lower or 'примеры' in message_lower or 'помощь' in message_lower:
        return (
            "<strong>Как правильно задавать запросы:</strong><br><br>"
            "1. <code>найди отели до 30$</code><br>"
            "2. <code>отели в Кишинёве до 50 долларов</code><br>"
            "3. <code>отели 2-3 звезды до 40 usd</code><br>"
            "4. <code>в Кишиневе 4 звезды</code><br>"
            "5. <code>отели с хорошими отзывами</code><br>"
            "6. <code>бюджетные отели до 20$</code><br>"
            "7. <code>в кишиневе до 30 доларов</code><br>"
            "8. <code>отели 2-5 звезд в Бухаресте</code><br>"
            "9. <code>поддержка</code> — связь с администратором<br><br>"
            "<em>Пиши как удобно — я пойму!</em>"
        )

    # === ПРИВЕТСТВИЕ (ПЕРВОЕ СООБЩЕНИЕ) ===
    if not message.strip():
        return (
            "Здравствуйте, я текстовый ИИ-помощник, чем вам помочь?<br>"
            "Введите <strong>сводка</strong>, чтобы увидеть примеры запросов."
        )

    # === ПОДДЕРЖКА ===
    if any(w in message_lower for w in ['поддержка', 'support', 'админ', 'помощь']):
        return "Войдите в профиль → <strong>Служба поддержки</strong> → <strong>Создать чат</strong>."

    # === ПОИСК ОТЕЛЕЙ ===
    if any(w in message_lower for w in ['отель', 'отели', 'hotel', 'найди', 'ищу', 'покажи']):
        min_price = max_price = min_stars = max_stars = city = None
        good_reviews = any(w in message_lower for w in ['хорошие', 'отличные', 'высокий рейтинг', 'good', 'лучшие'])

        # Город
        city_match = re.search(r'(в\s+|in\s+)([А-Яа-яA-Za-zё\-]+)', message_lower)
        if city_match:
            city = city_match.group(2)

        # Цена (до / от)
        max_price_match = re.search(r'(до|до\s+|max)\s*(\d+)(?:\s*(долларов|доллар|usd|\$|дол\.?))?', message_lower)
        if max_price_match:
            max_price = float(max_price_match.group(2))
        min_price_match = re.search(r'(от|от\s+|min)\s*(\d+)(?:\s*(долларов|доллар|usd|\$|дол\.?))?', message_lower)
        if min_price_match:
            min_price = float(min_price_match.group(2))

        # Звёзды
        stars_range = re.search(r'(\d+)-(\d+)\s*(звезд|звёзды|звездочки|stars)', message_lower)
        if stars_range:
            min_stars, max_stars = int(stars_range.group(1)), int(stars_range.group(2))
        else:
            single_star = re.search(r'(\d+)\s*(звезд|звёзды|звездочки|stars)', message_lower)
            if single_star:
                min_stars = max_stars = int(single_star.group(1))

        hotels = find_hotels_advanced(min_price, max_price, min_stars, max_stars, city, good_reviews)

        if hotels:
            lines = ["<strong>Найдено отелей:</strong>"]
            for h in hotels:
                link = f"/search/hotel/{h['_id']}"
                price = f"{h['price_usd']:.2f} USD"
                cat = f"{h['category']} звёзд"
                reviews = h['review_analysis']['summary']
                lines.append(
                    f"• <strong>{h['name']}</strong> ({h['city']})<br>"
                    f"  {cat} | {price}<br>"
                    f"  {reviews}<br>"
                    f"  <a href='{link}' target='_blank'>Перейти к отелю</a>"
                )
            lines.append("<br><em>Хотите уточнить даты или удобства?</em>")
            return "<br>".join(lines)
        else:
            return (
                "<strong>Не нашёл отелей.</strong> Попробуйте:<br>"
                "• <code>найди отели до 30$</code><br>"
                "• <code>отели в Кишинёве</code><br>"
                "• <code>введите сводка</code> для примеров"
            )

    # === ПО УМОЛЧАНИЮ ===
    return (
        "Не понял запрос.<br>"
        "Введите <strong>сводка</strong> — покажу все примеры.<br>"
        "Или попробуйте: <code>найди отели до 30$</code>"
    )