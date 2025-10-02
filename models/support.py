from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

mongo = MongoClient(os.getenv('MONGO_URI'))
db = mongo.get_database()

# Коллекции
chats = db.chats