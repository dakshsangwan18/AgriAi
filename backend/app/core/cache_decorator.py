from functools import wraps
from typing import Optional, Callable, Any
import hashlib
from app.core.cache import cache_manager
from app.core.logging_config import logger


def cached(
    ttl: int = 300,  # 5 minutes default
    key_prefix: str = "",
    key_builder: Optional[Callable] = None,
    namespace: str = "decorator"
):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                built_key = str(key_builder(*args, **kwargs))
                cache_key = f"{key_prefix}:{built_key}" if key_prefix else built_key
            else:
                # Default: hash function name + serialized args/kwargs
                args_str = str(args) + str(sorted(kwargs.items()))
                key_hash = hashlib.md5(args_str.encode()).hexdigest()[:16]
                base_key = f"{func.__name__}:{key_hash}"
                cache_key = f"{key_prefix}:{base_key}" if key_prefix else base_key

            cache_namespace = namespace
            
            try:
                # Try to get from cache
                cached_value = cache_manager.get(cache_namespace, cache_key)
                
                if cached_value is not None:
                    logger.debug(
                        f"Cache HIT: {cache_key}",
                        extra={
                            "function": func.__name__,
                            "cache_key": cache_key
                        }
                    )
                    return cached_value
                
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
                cache_manager.set(cache_namespace, cache_key, result, ttl=ttl)
                
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


async def invalidate_cache_pattern(namespace: str, pattern: str = "*"):
    try:
        deleted = cache_manager.invalidate_pattern(namespace, pattern)
        logger.info(
            f"Cache invalidated: {namespace}:{pattern}",
            extra={"keys_deleted": deleted, "namespace": namespace}
        )
        return deleted
    except Exception as e:
        logger.error(
            f"Cache invalidation failed: {str(e)}",
            extra={"pattern": pattern}
        )
        return 0
