# load_hotels_from_google.py
import requests
import base64
from io import BytesIO
from PIL import Image
import time
import os
from dotenv import load_dotenv
from models import db
from models.hotel import Hotel

load_dotenv()

# === КЛЮЧ ===
API_KEY = os.getenv("GOOGLE_PLACES_SERVER_KEY")
if not API_KEY:
    print("ОШИБКА: GOOGLE_PLACES_SERVER_KEY не найден в .env!")
    exit()

# === ГЛОБАЛЬНЫЕ ПОИСКОВЫЕ ЗАПРОСЫ ===
SEARCH_QUERIES = [
    "отели в Кишинёв Молдова",
    "hotels in Bucharest Romania",
    "hotels in Cluj-Napoca Romania",
    "hotels in Constanța Romania",
    "hotels in Iași Romania",
    "hotels in Brașov Romania",
    "hotels in Timișoara Romania",
    "hotels in Sofia Bulgaria",
    "hotels in Belgrade Serbia",
    "hotels in Budapest Hungary",
    "hotels in Prague Czech Republic",
    "hotels in Vienna Austria",
    "hotels in Warsaw Poland",
    "hotels in Kyiv Ukraine",
    "hotels in Lviv Ukraine",
    "hotels in Paris France",
    "hotels in Berlin Germany",
    "hotels in Rome Italy",
    "hotels in Barcelona Spain",
    "hotels in London UK",
    "hotels in Amsterdam Netherlands",
    "hotels in Istanbul Turkey",
    "hotels in Athens Greece",
    "hotels in Dubai UAE",
    "hotels in Bangkok Thailand",
    "hotels in Tokyo Japan",
    "hotels in New York USA",
    "hotels in Miami USA"
]

MAX_HOTELS_PER_QUERY = 1000
MAX_REVIEWS_PER_HOTEL = 1000
REQUEST_DELAY = 2.3

# === ВАЛЮТЫ ===
COUNTRY_TO_CURRENCY = {
    'Moldova': 'MDL', 'Romania': 'RON', 'Bulgaria': 'BGN', 'Serbia': 'RSD',
    'Hungary': 'HUF', 'Czech Republic': 'CZK', 'Austria': 'EUR', 'Poland': 'PLN',
    'Ukraine': 'UAH', 'France': 'EUR', 'Germany': 'EUR', 'Italy': 'EUR',
    'Spain': 'EUR', 'UK': 'GBP', 'Netherlands': 'EUR', 'Turkey': 'TRY',
    'Greece': 'EUR', 'UAE': 'AED', 'Thailand': 'THB', 'Japan': 'JPY', 'USA': 'USD'
}

def get_photo_base64(photo_name, max_width=400):
    url = f"https://places.googleapis.com/v1/{photo_name}/media"
    params = {'maxWidthPx': max_width, 'key': API_KEY}
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=80)
            return base64.b64encode(buffered.getvalue()).decode('utf-8')
    except Exception as e:
        print(f"Фото ошибка: {e}")
    return None

def get_place_details(place_id):
    url = f"https://places.googleapis.com/v1/places/{place_id}"
    headers = {
        'X-Goog-Api-Key': API_KEY,
        'X-Goog-FieldMask': 'reviews,photos,priceLevel'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Детали ошибка {place_id}: {response.status_code}")
    except Exception as e:
        print(f"Детали исключение: {e}")
    return {}

def search_hotels(query):
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': API_KEY,
        'X-Goog-FieldMask': (
            'places.displayName,places.formattedAddress,places.location,'
            'places.priceLevel,places.rating,places.photos,places.id,'
            'places.addressComponents'
        )
    }
    data = {
        "textQuery": query,
        "maxResultCount": MAX_HOTELS_PER_QUERY,
        "rankPreference": "RELEVANCE"
    }
    try:
        response = requests.post(url, json=data, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Поиск ошибка '{query}': {response.status_code}")
            return []
        return response.json().get('places', [])
    except Exception as e:
        print(f"Поиск исключение: {e}")
        return []

def extract_city_country(address_components):
    city = country = None
    for comp in address_components:
        types = comp.get('types', [])
        if 'locality' in types or 'administrative_area_level_2' in types:
            city = comp.get('longText')
        if 'country' in types:
            country = comp.get('longText')
    return city or "Unknown City", country or "Unknown"

def price_level_to_usd(level):
    mapping = {
        'PRICE_LEVEL_INEXPENSIVE': 40,
        'PRICE_LEVEL_MODERATE': 80,
        'PRICE_LEVEL_EXPENSIVE': 150,
        'PRICE_LEVEL_VERY_EXPENSIVE': 300
    }
    return mapping.get(level)  # None если нет

def rating_to_price(rating):
    """Жёсткая оценка по рейтингу — без 80$"""
    if rating >= 4.8: return 180
    if rating >= 4.5: return 140
    if rating >= 4.0: return 100
    if rating >= 3.5: return 65
    if rating >= 3.0: return 50
    return 35  # 1-2 звезды

def rating_to_stars(rating):
    if rating >= 4.5: return 5
    if rating >= 4.0: return 4
    if rating >= 3.5: return 3
    if rating >= 3.0: return 2
    return 1

def save_hotel_from_place(place):
    name = place.get('displayName', {}).get('text', 'Unknown Hotel')
    address = place.get('formattedAddress', '')
    location = place.get('location', {})
    lat = location.get('latitude')
    lng = location.get('longitude')
    components = place.get('addressComponents', [])
    city, country = extract_city_country(components)
    if city == "Unknown City":
        city = address.split(',')[0].strip()

    currency = COUNTRY_TO_CURRENCY.get(country, 'USD')
    rating = place.get('rating', 3.0)
    category = rating_to_stars(rating)

    # === ЦЕНА: 1. поиск → 2. детали → 3. по рейтингу ===
    price_level = place.get('priceLevel')
    price_source = "search"
    if not price_level:
        place_id = place.get('id')
        if place_id:
            details = get_place_details(place_id)
            price_level = details.get('priceLevel')
            price_source = "details"
            time.sleep(1)

    price_usd = price_level_to_usd(price_level)
    if price_usd is None:
        price_usd = rating_to_price(rating)
        price_source = "rating"

    price_usd = round(price_usd, 2)

    # === ФОТО ===
    photos_data = place.get('photos', [])[:3]
    photos_base64 = []
    for photo in photos_data:
        photo_name = photo.get('name')
        if photo_name:
            b64 = get_photo_base64(photo_name)
            if b64:
                photos_base64.append(b64)
            time.sleep(0.5)

    # === ОТЗЫВЫ ===
    place_id = place.get('id')
    reviews = []
    if place_id:
        details = get_place_details(place_id)
        google_reviews = details.get('reviews', [])[:MAX_REVIEWS_PER_HOTEL]
        for rev in google_reviews:
            author = rev.get('authorAttribution', {}).get('displayName', 'Google User')
            text = rev.get('text', {}).get('text', 'Отличное место!')[:500]
            rating_rev = rev.get('rating', 5)
            rev_photos = []
            if 'photos' in rev:
                for p in rev.get('photos', [])[:1]:
                    photo_name = p.get('name')
                    if photo_name:
                        b64 = get_photo_base64(photo_name, max_width=300)
                        if b64:
                            rev_photos.append(b64)
                        time.sleep(0.5)
            reviews.append({
                'user': author,
                'text': text,
                'rating': rating_rev,
                'photos': rev_photos,
                'source': 'google'
            })
        time.sleep(1)

    if not reviews:
        reviews = [{
            'user': 'Google User',
            'text': f'Рейтинг: {rating:.1f}/5',
            'rating': round(rating, 1),
            'photos': [],
            'source': 'google'
        }]

    rooms = {'standard': {'available': 10}}

    hotel_data = {
        'name': name,
        'city': city,
        'price_usd': price_usd,
        'category': category,
        'description': f"Отель в {city}, {country}. Рейтинг: {rating}/5.",
        'photos': photos_base64,
        'reviews': reviews,
        'rooms': rooms,
        'currency': currency,
        'location_address': address,
        'latitude': lat,
        'longitude': lng
    }

    existing = db.hotels.find_one({'name': name, 'city': city})
    if existing:
        return False

    try:
        Hotel.create_hotel(hotel_data)
        print(f"Добавлен: {name} | {city}, {country} | {category}★ | ${price_usd} | "
              f"Отзывов: {len(reviews)} | Цена: {price_level or 'по рейтингу'} ({price_source})")
        return True
    except Exception as e:
        print(f"Ошибка: {e}")
        return False

# === ЗАПУСК ===
if __name__ == "__main__":
    print("ГЛОБАЛЬНАЯ загрузка отелей с ТОЧНОЙ ЦЕНОЙ (БЕЗ 80$!)...")
    print(f"Ключ: {API_KEY[:10]}...{API_KEY[-4:]}")

    total = 0
    for query in SEARCH_QUERIES:
        print(f"\nПоиск: {query}")
        places = search_hotels(query)
        if not places:
            print("→ Ничего")
            continue
        for place in places:
            if save_hotel_from_place(place):
                total += 1
            time.sleep(REQUEST_DELAY)
        time.sleep(1.5)

    print(f"\nГОТОВО! Добавлено {total} отелей.")
    print("→ Цена: INEXPENSIVE=40$, MODERATE=80$, EXPENSIVE=150$, VERY_EXPENSIVE=300$")
    print("→ Нет priceLevel → по рейтингу: 5★=140-180$, 1★=35$")