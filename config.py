import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a18d7515f06064771b14381f569a9b77'  
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/hotel_db'