import redis.asyncio as aioredis
from app.config import settings

redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True) 

async def get_cache(key: str):
    return await redis_client.get(key)

async def set_cache(key: str, value: str, expire: int = 3600):
    await redis_client.set(key, value, ex=expire)

async def delete_cache(key: str):
    await redis_client.delete(key)

