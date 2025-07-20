from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
def Model():
    print("connecting to model")
    try:
        client = MongoClient(os.getenv('USERS_MONGO_URL'))
        db = client.api_embeddings
        collection = db.products
        print("connection complete")
        return collection
    except Exception as e:
        print(f"an exception occurred while connecting to supplement database:{e}")
        return None