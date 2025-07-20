from pymongo import MongoClient
import os 
from dotenv import load_dotenv

load_dotenv()

def Model():
    try:
        client=MongoClient(os.getenv('Users_MONGO_URL'))
        db=client.docEmbeddings
        collection=db.chunks
        return collection
    except Exception as e:
        print(f"error connecting to chunks db:{e}")
        return None
