"""
Useful decorators for AHOS
"""
import time
import functools
from typing import Callable, Any, Optional
from ahos.utils.logger import logger
from ahos.infrastructure.config.settings import settings
import redis

redis_client = None
if settings.REDIS_URL:
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
    except Exception as e:
        logger.warning(f"Could not connect to Redis: {e}")

def retry(max_retries: int = None, exceptions: tuple = (Exception,)):
    max_retries = max_retries or settings.API_MAX_RETRIES
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait_time = (attempt + 1) * 2
                        logger.warning(f"Attempt {attempt+1} failed for {func.__name__}. Retrying in {wait_time}s. Error: {str(e)}")
                        time.sleep(wait_time)
            raise last_exception
        return wrapper
    return decorator

def cache(ttl: Optional[int] = None, key_func: Optional[Callable] = None):
    ttl = ttl or settings.CACHE_TTL
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            cache_key = key_func(*args, **kwargs) if key_func else f"{func.__module__}.{func.__name__}:{args}:{frozenset(kwargs.items())}"
            if redis_client:
                try:
                    cached_result = redis_client.get(cache_key)
                    if cached_result is not None:
                        logger.debug(f"Redis cache hit for {cache_key}")
                        return eval(cached_result)
                except Exception as e:
                    logger.warning(f"Cache read failed: {e}")
            result = func(*args, **kwargs)
            if redis_client:
                try:
                    redis_client.setex(cache_key, ttl, repr(result))
                except Exception as e:
                    logger.warning(f"Cache write failed: {e}")
            return result
        return wrapper
    return decorator

def timing(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        run_time = time.perf_counter() - start_time
        logger.debug(f"Function {func.__name__} executed in {run_time:.4f} seconds")
        return result
    return wrapper

def rate_limited(max_per_second: int = None):
    max_per_second = max_per_second or settings.API_RATE_LIMIT
    min_interval = 1.0 / max_per_second
    def decorator(func: Callable) -> Callable:
        last_time = [0.0]
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            elapsed = time.perf_counter() - last_time[0]
            wait_time = min_interval - elapsed
            if wait_time > 0:
                time.sleep(wait_time)
            last_time[0] = time.perf_counter()
            return func(*args, **kwargs)
        return wrapper
    return decorator
