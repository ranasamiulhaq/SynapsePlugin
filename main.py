from fastapi import FastAPI
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
from bson import ObjectId
from Routes.pluginRouter import router as pluginRouter
app = FastAPI()
app.include_router(pluginRouter,prefix='/plugin')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

