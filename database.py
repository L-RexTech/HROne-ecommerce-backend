import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
client = MongoClient(MONGODB_URL)
database = client.ecommerce

# Collections
products_collection = database.products
orders_collection = database.orders
