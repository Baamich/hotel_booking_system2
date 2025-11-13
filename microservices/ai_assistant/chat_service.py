from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import re
import os
import sys
from dotenv import load_dotenv

# === ДОБАВЛЯЕМ КОРЕНЬ ПРОЕКТА В ПУТЬ ===
current_dir = os.path.dirname(os.path.abspath(__file__))  # ai_assistant/
microservices_dir = os.path.dirname(current_dir)           # microservices/
project_root = os.path.dirname(microservices_dir)          # hotel_booking_system/
if project_root not in sys.path:
    sys.path.insert(0, project_root)
print(f"[AI] Добавлен путь: {project_root}")

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

# === ВАЛЮТЫ — ИМПОРТ ИЗ КОРНЯ ===
try:
    from currencies import CURRENCIES, convert_price, get_symbol
    print("[AI] Валюты загружены из currencies.py")
except Exception as e:
    print(f"[AI ERROR] Не удалось загрузить currencies.py: {e}")
    CURRENCIES = {
        'usd': {'symbol': '$', 'rate': 1},
        'eur': {'symbol': '€', 'rate': 0.85},
        'mdl': {'symbol': 'L', 'rate': 16.45},
        'ron': {'symbol': 'lei', 'rate': 4.27},
        'uah': {'symbol': '₴', 'rate': 41.19},
        'rub': {'symbol': '₽', 'rate': 83.24}
    }
    def convert_price(price, from_cur, to_cur):
        from_cur = from_cur.lower()
        to_cur = to_cur.lower()
        if from_cur not in CURRENCIES or to_cur not in CURRENCIES:
            return price
        rate_from = CURRENCIES[from_cur]['rate']
        rate_to = CURRENCIES[to_cur]['rate']
        return round((price / rate_from) * rate_to, 2)
    def get_symbol(cur):
        return CURRENCIES.get(cur.lower(), CURRENCIES['usd'])['symbol']

# === ИМПОРТ ПЕРЕВОДОВ ===
try:
    from translations import gettext, FLAGS
    print("[AI] Переводы загружены из translations.py")
except Exception as e:
    print(f"[AI ERROR] Не удалось загрузить translations.py: {e}")
    FLAGS = {'rus': 'RU', 'eng': 'US', 'rom': 'RO'}
    def gettext(key, lang='eng'):
        return key

# === ВСЕ ВАРИАНТЫ ВАЛЮТ: падежи + сокращения + символы ===
CURRENCY_FORMS = {
    # USD
    'доллар': 'usd', 'доллара': 'usd', 'долларов': 'usd',
    'долар': 'usd', 'доларов': 'usd',
    'usd': 'usd', '$': 'usd',
    # EUR
    'евро': 'eur', 'eur': 'eur', '€': 'eur',
    # MDL
    'лей': 'mdl', 'лея': 'mdl', 'леев': 'mdl',
    'молдавский лей': 'mdl', 'молдавских лей': 'mdl',
    'mdl': 'mdl', 'l': 'mdl',
    # RON
    'рон': 'ron', 'рона': 'ron', 'ронов': 'ron',
    'румынский лей': 'ron', 'румынских лей': 'ron',
    'ron': 'ron', 'lei': 'ron',
    # UAH
    'гривна': 'uah', 'гривны': 'uah', 'гривен': 'uah',
    'грн': 'uah', '₴': 'uah',
    # RUB
    'рубль': 'rub', 'рубля': 'rub', 'рублей': 'rub',
    'руб': 'rub', '₽': 'rub'
}

# === ДИНАМИЧЕСКИЕ ГОРОДА ИЗ БД ===
def get_cities_from_db():
    if not DB_CONNECTED:
        return []
    try:
        cities = hotels_collection.distinct("city")
        return [c for c in cities if c]
    except:
        return []

CITIES_DB = get_cities_from_db()
print(f"[AI] Города из БД: {CITIES_DB}")

def fuzzy_match_city(input_city):
    input_city = re.sub(r'[^\w]', '', input_city.lower())
    for city in CITIES_DB:
        city_clean = re.sub(r'[^\w]', '', city.lower())
        if input_city in city_clean or city_clean in input_city:
            return city
    return None

def analyze_reviews(reviews, lang='eng'):
    if not reviews:
        return {"avg_rating": 0, "summary": gettext('no_reviews', lang)}
    ratings = [r.get('rating', 0) for r in reviews if isinstance(r.get('rating'), (int, float))]
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    return {"avg_rating": avg_rating, "summary": f"{gettext('rating', lang)}: {avg_rating:.1f}/5"}

def find_hotels_advanced(min_price=None, max_price=None, min_stars=None, max_stars=None, city=None, good_reviews=False, no_reviews=False, currency='usd', lang='eng'):
    if not DB_CONNECTED:
        return []

    mongo_query = {}

    if city:
        norm_city = fuzzy_match_city(city) or city
        mongo_query['city'] = {'$regex': f'^{re.escape(norm_city)}$', '$options': 'i'}

    if min_price is not None:
        min_usd = convert_price(min_price, currency, 'usd')
        mongo_query['price_usd'] = mongo_query.get('price_usd', {})
        mongo_query['price_usd']['$gte'] = min_usd
    if max_price is not None:
        max_usd = convert_price(max_price, currency, 'usd')
        mongo_query['price_usd'] = mongo_query.get('price_usd', {})
        mongo_query['price_usd']['$lte'] = max_usd

    if min_stars is not None:
        mongo_query['category'] = mongo_query.get('category', {})
        mongo_query['category']['$gte'] = int(min_stars)
    if max_stars is not None:
        mongo_query['category'] = mongo_query.get('category', {})
        mongo_query['category']['$lte'] = int(max_stars)

    if no_reviews:
        mongo_query['reviews'] = {'$size': 0}

    print(f"[DEBUG] Запрос: {mongo_query}")

    try:
        cursor = hotels_collection.find(mongo_query).limit(5)
        hotels = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            doc['review_analysis'] = analyze_reviews(doc.get('reviews', []), lang)
            price_usd = doc['price_usd']
            display_price = convert_price(price_usd, 'usd', currency)
            doc['display_price'] = f"{display_price:.2f} {get_symbol(currency)}"
            if doc.get('category') == 5 and doc.get('reviews'):
                doc['top_reviews'] = doc['reviews'][:3]
            else:
                doc['top_reviews'] = []
            hotels.append(doc)

        if good_reviews:
            hotels = [h for h in hotels if h['review_analysis']['avg_rating'] >= 4.0]

        print(f"[DEBUG] Найдено: {len(hotels)}")
        return hotels
    except Exception as e:
        print(f"[AI ERROR] {e}")
        return []

def detect_language(message):
    """Определяет язык по содержимому"""
    message_lower = message.lower()
    rus_chars = len(re.findall(r'[а-яё]', message_lower))
    eng_chars = len(re.findall(r'[a-z]', message_lower))
    rom_chars = len(re.findall(r'[ăîșțâ]', message_lower))  # румынские буквы

    if rus_chars > eng_chars and rus_chars > 5:
        return 'rus'
    if eng_chars > rus_chars and eng_chars > 5:
        return 'eng'
    if rom_chars > 0 or 'ă' in message_lower or 'î' in message_lower:
        return 'rom'
    return None

def process_message(message, lang='eng'):
    # === gettext доступен глобально ===
    message_lower = message.strip().lower()
    detected_lang = detect_language(message)

    # === ПРОВЕРКА ЯЗЫКА ===
    if detected_lang and detected_lang not in ['rus', 'eng', 'rom']:
        langs_list = ", ".join([
            f"<code>{gettext(f'lang_name_{l}', lang)}</code>" for l in ['rus', 'eng', 'rom']
        ])
        return (
            f"<strong>{gettext('lang_not_supported', lang)}</strong><br>"
            f"{gettext('lang_please_use', lang)} {langs_list}<br>"
            f"<em>{gettext('lang_change_hint', lang)}</em>"
        )

    # === ПРИНУДИТЕЛЬНО РУССКИЙ, ЕСЛИ ПИШЕТ НА РУССКОМ ===
    response_lang = lang  # ← по умолчанию — язык профиля
    if detected_lang == 'rus':
        response_lang = 'rus'

        # === СВОДКА — ПОДДЕРЖКА ВСЕХ ЯЗЫКОВ ===
    summary_triggers = {
        'rus': ['сводка', 'примеры', 'помощь', 'help', 'example'],
        'eng': ['summary', 'examples', 'help', 'example'],
        'rom': ['rezumat', 'exemple', 'ajutor', 'exemplu']
    }

    if any(trigger in message_lower for trigger in summary_triggers.get(response_lang, [])):
        examples_key = {
            'rus': [
                'example_find_30usd', 'example_find_50eur', 'example_find_1000lei',
                'example_budget_500uah', 'example_find_2000rub', 'example_cheap_20mdl',
                'example_stars_1_2', 'example_city_chisinau', 'example_good_reviews',
                'example_no_reviews', 'example_support'
            ],
            'eng': [
                'example_find_30usd', 'example_find_50eur', 'example_find_1000lei',
                'example_budget_500uah', 'example_find_2000rub', 'example_cheap_20mdl',
                'example_stars_1_2', 'example_city_chisinau', 'example_good_reviews',
                'example_no_reviews', 'example_support'
            ],
            'rom': [
                'example_find_30usd', 'example_find_50eur', 'example_find_1000lei',
                'example_budget_500uah', 'example_find_2000rub', 'example_cheap_20mdl',
                'example_stars_1_2', 'example_city_chisinau', 'example_good_reviews',
                'example_no_reviews', 'example_support'
            ]
        }[response_lang]

        example_list = "<br>".join([f"• <code>{gettext(ex, response_lang)}</code>" for ex in examples_key])
        return f"<strong>{gettext('examples_title', response_lang)}:</strong><br><br>{example_list}<br><br><em>{gettext('examples_hint', response_lang)}</em>"
    
    # === ПРИВЕТСТВИЕ ===
    if not message.strip():
        # Используем lang из профиля, а не detected_lang
        return (
            f"{gettext('greeting', lang)}<br>"
            f"{gettext('greeting_hint', lang)}"
        )

    # === ПОДДЕРЖКА ===
    if any(w in message_lower for w in ['поддержка', 'support', 'админ', 'помощь', 'связаться', 'чат', 'служба', 'suport', 'admin']):
        return (
            f"{gettext('support_contact', response_lang)}<br>"
            f"<a href='http://127.0.0.1:5000/support/chats' target='_blank'>"
            f"{gettext('support_link', response_lang)}</a>"
        )

    # === ПОИСК ОТЕЛЕЙ ===
    if any(w in message_lower for w in ['отель', 'отели', 'hotel', 'найди', 'ищу', 'покажи', 'гостиница', 'cauta', 'hoteluri']):
        min_price = max_price = min_stars = max_stars = None
        city = None
        currency = 'usd'
        good_reviews = any(w in message_lower for w in ['хорошие', 'отличные', 'высокий', 'good', 'best', 'лучшие', 'bune', 'excelente'])
        no_reviews = any(w in message_lower for w in ['без отзывов', 'без комментариев', 'без рейтинга', 'fara recenzii'])

        # === ВАЛЮТА ===
        detected_currency = None
        for form, cur in CURRENCY_FORMS.items():
            if form in message_lower or form in message:
                detected_currency = cur
                break
        if detected_currency:
            currency = detected_currency

        # === ЦЕНА + ВАЛЮТА ===
        price_pattern = r'(до|от|pana la|de la)\s+([0-9.,]+)\s*([а-яё\w$€₴₽ăîșțâ]+)?'
        price_match = re.search(price_pattern, message_lower)
        if price_match:
            amount = float(price_match.group(2).replace(',', '.'))
            word_after = (price_match.group(3) or '').strip()
            if word_after:
                for form, cur in CURRENCY_FORMS.items():
                    if form == word_after or form in word_after:
                        currency = cur
                        break
            if price_match.group(1) in ['до', 'pana la']:
                max_price = amount
            else:
                min_price = amount

        # === ГОРОД ===
        city_match = re.search(r'(в\s+|in\s+|la\s+)([А-Яа-яA-Za-zё\.\-\săîșțâ]+?)(?=\s|$|\d)', message_lower)
        if city_match:
            city = city_match.group(2).strip()

        # === ЗВЁЗДЫ ===
        stars_range = re.search(r'(\d+)-(\d+)\s*(звезд|звёзд|звездочки|stars|stele)', message_lower)
        if stars_range:
            min_stars, max_stars = int(stars_range.group(1)), int(stars_range.group(2))
        else:
            single_star = re.search(r'(\d+)\s*(звезд|звёзд|звездочки|stars|stele)', message_lower)
            if single_star:
                min_stars = max_stars = int(single_star.group(1))

        # === ПРОВЕРКА ВАЛЮТЫ ===
        if (max_price or min_price) and currency not in CURRENCIES:
            return (
                f"<strong>{gettext('currency_not_found', response_lang)}</strong><br>"
                f"{gettext('currency_available', response_lang)}<br>"
                f"<code>{gettext('examples', response_lang)}</code>"
            )

        hotels = find_hotels_advanced(
            min_price=min_price,
            max_price=max_price,
            min_stars=min_stars,
            max_stars=max_stars,
            city=city,
            good_reviews=good_reviews,
            no_reviews=no_reviews,
            currency=currency,
            lang=response_lang
        )

        if hotels:
            conv_text = ""
            price_used = max_price or min_price
            if price_used:
                usd_eq = convert_price(price_used, currency, 'usd')
                conv_text = f" ({price_used} {get_symbol(currency)} → {usd_eq:.2f} $)"

            lines = [f"<strong>{gettext('hotels_found', response_lang)} (в {get_symbol(currency)}){conv_text}:</strong><br>"]

            for i, h in enumerate(hotels):
                if i > 0:
                    lines.append("<br>")

                link = f"/search/hotel/{h['_id']}"
                price = h['display_price']
                cat = f"{h['category']} {gettext('stars', response_lang)}"
                reviews = h['review_analysis']['summary']

                lines.append(
                    f"• <strong>{h['name']}</strong> ({h['city']})<br>"
                    f"  {cat} | {price}<br>"
                    f"  {reviews}<br>"
                )

                if h.get('top_reviews'):
                    review_lines = "<br>".join([
                        f"  — {r.get('user', gettext('anonymous', response_lang))}: {r.get('text', '')} ({r.get('rating', 0)}★)"
                        for r in h['top_reviews']
                    ])
                    lines.append(f"  <em>{gettext('top_reviews', response_lang)}:</em><br>{review_lines}<br>")

                lines.append(f"  <a href='{link}' target='_blank'>{gettext('go_to_hotel', response_lang)}</a>")
            return "<br>".join(lines)
        else:
            return (
                f"<strong>{gettext('no_hotels_found', response_lang)}</strong><br>"
                f"{gettext('check_spelling', response_lang)}<br>"
                f"<code>{gettext('examples', response_lang)}</code>"
            )

    # === ПО УМОЛЧАНИЮ ===
    return f"{gettext('not_understood', response_lang)} <code>{gettext('examples', response_lang)}</code>"