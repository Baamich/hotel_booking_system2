# config.py
from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/hotel_db')
    SECRET_KEY = os.getenv('SECRET_KEY', 'a18d7515f06064771b14381f569a9b77')
    EMAIL_FROM = os.getenv('EMAIL_FROM', 'test-p7kx4xwvj68g9yjr.mlsender.net')
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.mailersend.net')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', 'mssp.Dg2dUGv.pxkjn41rq20gz781.I7m3BT3')
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', 'AIzaSyAh-pWiue5sxCqbGG5ujWu59D0XqanCkUU')  