from motor.motor_asyncio import AsyncIOMotorClient
from datetime import timezone
from src.utils import load_config

cfg = load_config()

MONGO_URL = cfg["MongoDB"]["MONGO_URL"]
DB_NAME = cfg["MongoDB"]["DB_NAME"]
USER_COLLECTION = cfg["MongoDB"]["USER_COLLECTION"]
CHAT_HISTORY_COLLECTION = cfg["MongoDB"]["CHAT_HISTORY_COLLECTION"]

client = AsyncIOMotorClient(MONGO_URL, tz_aware=True, tzinfo=timezone.utc)
db = client[DB_NAME]

users_collection = db[USER_COLLECTION]
conversations_collection = db[CHAT_HISTORY_COLLECTION]


