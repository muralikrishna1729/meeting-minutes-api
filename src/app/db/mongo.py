import motor.motor_asyncio as moto
from src.app.config import settings

mongo_client = moto.AsyncIOMotorClient(settings.MONGODB_URL)
db = mongo_client[settings.MONGODB_DB]
