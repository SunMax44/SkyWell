import aioredis
from functools import wraps
from fastapi import Request
import json
import hashlib
import inspect

REDIS_URL = "redis://redis:6379"

async def get_redis():
    return await aioredis.from_url(REDIS_URL, decode_responses=True)

def make_cache_key(func, args, kwargs):
    # Build a unique key from function name and arguments
    key_data = {
        'func': func.__name__,
        'args': args,
        'kwargs': kwargs
    }
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return f"cache:{hashlib.sha256(key_str.encode()).hexdigest()}"

def cache(ttl: int = 60):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find the request object if present (for FastAPI dependencies)
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            # Generate cache key
            cache_key = make_cache_key(func, args, kwargs)
            redis = await get_redis()
            cached = await redis.get(cache_key)
            if cached is not None:
                # Deserialize and return cached response
                return json.loads(cached)
            # Call the actual function, handling both async and sync
            if inspect.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            # Serialize and cache the result
            try:
                await redis.set(cache_key, json.dumps(result), ex=ttl)
            except Exception:
                pass  # Don't fail if caching fails
            return result
        return wrapper
    return decorator 