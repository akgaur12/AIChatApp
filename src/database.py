from motor.motor_asyncio import AsyncIOMotorClient
from src.utils import load_config

cfg = load_config()

MONGO_URL = cfg["MongoDB"]["MONGO_URL"]
DB_NAME = cfg["MongoDB"]["DB_NAME"]

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

users_collection = db["users"]


