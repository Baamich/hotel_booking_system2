from models import db
from models.hotel import Hotel
import json

# Фейковые данные (5 отелей)
hotels_data = [
    {
        'name': 'Hotel Luxe',
        'city': 'București',
        'price_usd': 35,  # Изменено на price_usd (base USD, ~150 RON / 4.27)
        'category': 4,
        'description': 'Luxury hotel in center',
        'photos': ['photo1.jpg', 'photo2.jpg'],
        'reviews': [{'user': 'John', 'text': 'Great!', 'rating': 5, 'photos': []}],
        'rooms': {'standard': {'available': 10}, 'suite': {'available': 2}},
        'currency': 'RON'
    },
    {
        'name': 'Budget Inn',
        'city': 'Chișinău',
        'price_usd': 3,  # Изменено (~50 MDL / 16.45)
        'category': 2,
        'description': 'Affordable stay',
        'photos': ['photo3.jpg'],
        'reviews': [{'user': 'Anna', 'text': 'Ok', 'rating': 3, 'photos': []}],
        'rooms': {'standard': {'available': 5}},
        'currency': 'MDL'
    },
    {
        'name': 'Sea View Resort',
        'city': 'Constanța',
        'price_usd': 47,  # Изменено (~200 RON / 4.27)
        'category': 5,
        'description': 'Beachfront luxury',
        'photos': ['photo4.jpg', 'photo5.jpg'],
        'reviews': [{'user': 'Mike', 'text': 'Amazing view!', 'rating': 5, 'photos': []}],
        'rooms': {'deluxe': {'available': 8}},
        'currency': 'RON'
    },
    {
        'name': 'City Center Motel',
        'city': 'Iași',
        'price_usd': 19,  # Изменено (~80 RON / 4.27)
        'category': 3,
        'description': 'Central location',
        'photos': ['photo6.jpg'],
        'reviews': [{'user': 'Sara', 'text': 'Clean', 'rating': 4, 'photos': []}],
        'rooms': {'standard': {'available': 15}},
        'currency': 'RON'
    },
    {
        'name': 'Mountain Lodge',
        'city': 'Brașov',
        'price_usd': 28,  # Изменено (~120 RON / 4.27)
        'category': 4,
        'description': 'Cozy in mountains',
        'photos': ['photo7.jpg'],
        'reviews': [{'user': 'Tom', 'text': 'Peaceful', 'rating': 4, 'photos': []}],
        'rooms': {'suite': {'available': 3}},
        'currency': 'RON'
    }
]

# Вставка
for data in hotels_data:
    Hotel.create_hotel(data)

print("Тестовые отели добавлены!")