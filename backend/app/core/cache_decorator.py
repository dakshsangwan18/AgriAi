from functools import wraps
from typing import Optional, Callable, Any
import json
import hashlib
from app.core.cache import cache_manager
from app.core.logging_config import logger


def cached(
    ttl: int = 300,  # 5 minutes default
    key_prefix: str = "",
    key_builder: Optional[Callable] = None
):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Default: hash function name + serialized args/kwargs
                args_str = str(args) + str(sorted(kwargs.items()))
                key_hash = hashlib.md5(args_str.encode()).hexdigest()[:16]
                cache_key = f"{key_prefix}:{func.__name__}:{key_hash}"
            
            try:
                # Try to get from cache
                cached_value = await cache_manager.get(cache_key)
                
                if cached_value is not None:
                    logger.debug(
                        f"Cache HIT: {cache_key}",
                        extra={
                            "function": func.__name__,
                            "cache_key": cache_key
                        }
                    )
                    return json.loads(cached_value)
                
                logger.debug(
                    f"Cache MISS: {cache_key}",
                    extra={
                        "function": func.__name__,
                        "cache_key": cache_key
                    }
                )
                
            except Exception as e:
                # If cache fails, just log and continue
                logger.warning(
                    f"Cache GET failed: {str(e)}",
                    extra={"cache_key": cache_key}
                )
            
            # Execute the actual function
            result = await func(*args, **kwargs)
            
            # Store in cache
            try:
                serialized = json.dumps(result, default=str)
                await cache_manager.set(cache_key, serialized, ttl=ttl)
                
                logger.debug(
                    f"Cache SET: {cache_key}",
                    extra={
                        "function": func.__name__,
                        "ttl": ttl
                    }
                )
            except Exception as e:
                # Log but don't fail if caching fails
                logger.warning(
                    f"Cache SET failed: {str(e)}",
                    extra={"cache_key": cache_key}
                )
            
            return result
        
        return wrapper
    return decorator


async def invalidate_cache_pattern(pattern: str):
    try:
        deleted = await cache_manager.delete_pattern(pattern)
        logger.info(
            f"Cache invalidated: {pattern}",
            extra={"keys_deleted": deleted}
        )
        return deleted
    except Exception as e:
        logger.error(
            f"Cache invalidation failed: {str(e)}",
            extra={"pattern": pattern}
        )
        return 0
