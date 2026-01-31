"""
Redis cache client for session management and caching.
"""
from typing import Optional

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Global Redis client
redis_client: Optional[Redis] = None


async def get_redis() -> Redis:
    """
    Get Redis client instance.

    Returns:
        Redis: Redis client

    Raises:
        RuntimeError: If Redis is not enabled in configuration

    Example:
        ```python
        @app.get("/cached-data")
        async def get_cached_data(redis: Redis = Depends(get_redis)):
            data = await redis.get("key")
            return data
        ```
    """
    if not settings.ENABLE_REDIS:
        raise RuntimeError(
            "Redis is not enabled. Set ENABLE_REDIS=true in your configuration "
            "to use Redis cache features."
        )
    
    if redis_client is None:
        raise RuntimeError(
            "Redis client is not initialized. Ensure init_redis() was called during startup."
        )
    
    return redis_client


async def init_redis() -> None:
    """
    Initialize Redis connection.
    
    This function checks if Redis is enabled before attempting initialization.
    If disabled, it logs an info message and returns early.
    """
    global redis_client

    if not settings.ENABLE_REDIS:
        logger.info("Redis is disabled - skipping initialization")
        return

    try:
        logger.info("Initializing Redis connection...")
        
        redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
        )

        # Test connection
        await redis_client.ping()
        logger.info("Redis connection established successfully")

    except Exception as e:
        redis_client = None
        logger.error("Failed to connect to Redis", error=str(e))
        raise


async def close_redis() -> None:
    """Close Redis connection."""
    global redis_client

    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")


class CacheService:
    """Service for caching operations."""

    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    async def get(self, key: str) -> Optional[str]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            value = await self.redis.get(key)
            return value
        except Exception as e:
            logger.error("Cache get error", key=key, error=str(e))
            return None

    async def set(
        self,
        key: str,
        value: str,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: settings.REDIS_TTL)

        Returns:
            True if successful, False otherwise
        """
        try:
            if ttl is None:
                ttl = settings.REDIS_TTL

            await self.redis.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.error("Cache set error", key=key, error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error("Cache delete error", key=key, error=str(e))
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete keys matching pattern.

        Args:
            pattern: Key pattern (e.g., "user:*")

        Returns:
            Number of keys deleted
        """
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
            return len(keys)
        except Exception as e:
            logger.error("Cache delete pattern error", pattern=pattern, error=str(e))
            return 0

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.error("Cache exists error", key=key, error=str(e))
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration time for key.

        Args:
            key: Cache key
            ttl: Time to live in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            return await self.redis.expire(key, ttl)
        except Exception as e:
            logger.error("Cache expire error", key=key, error=str(e))
            return False

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment value in cache.

        Args:
            key: Cache key
            amount: Amount to increment

        Returns:
            New value or None if error
        """
        try:
            return await self.redis.incrby(key, amount)
        except Exception as e:
            logger.error("Cache increment error", key=key, error=str(e))
            return None


def get_cache_service() -> CacheService:
    """
    Dependency for getting cache service.

    Returns:
        CacheService: Cache service instance

    Raises:
        RuntimeError: If Redis is not enabled in configuration

    Example:
        ```python
        @app.get("/data/{id}")
        async def get_data(id: str, cache: CacheService = Depends(get_cache_service)):
            cached = await cache.get(f"data:{id}")
            if cached:
                return json.loads(cached)

            data = await fetch_data_from_db(id)
            await cache.set(f"data:{id}", json.dumps(data))
            return data
        ```
    """
    if not settings.ENABLE_REDIS:
        raise RuntimeError(
            "Redis is not enabled. Set ENABLE_REDIS=true in your configuration "
            "to use Redis cache features."
        )
    
    if redis_client is None:
        raise RuntimeError(
            "Redis client is not initialized. Ensure init_redis() was called during startup."
        )
    
    return CacheService(redis_client)
