import aioredis
from functools import wraps
from fastapi import Request

REDIS_URL = "redis://redis:6379"

async def get_redis():
    return await aioredis.from_url(REDIS_URL, decode_responses=True)

def cache(ttl: int = 60):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Stub: add caching logic here
            return await func(*args, **kwargs)
        return wrapper
    return decorator 