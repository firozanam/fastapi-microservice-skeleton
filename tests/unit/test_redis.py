"""
Unit tests for Redis cache module.
Tests Redis initialization, connection, and CacheService operations.

Note: All tests in this file require Redis to be enabled (ENABLE_REDIS=true).
Tests will be automatically skipped if Redis is disabled.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from redis.asyncio import Redis as AsyncRedis

from app.db.redis import (
    CacheService,
    close_redis,
    get_cache_service,
    get_redis,
    init_redis,
    redis_client,
)


# Mark all tests in this module as requiring Redis
pytestmark = pytest.mark.redis


@pytest.mark.unit
class TestInitRedis:
    """Test Redis initialization."""

    @pytest.mark.asyncio
    async def test_init_redis_success(self):
        """Test successful Redis initialization."""
        from app.db import redis as redis_module
        
        with patch("app.db.redis.redis") as mock_redis:
            mock_redis_client = AsyncMock(spec=AsyncRedis)
            mock_redis.from_url.return_value = mock_redis_client
            mock_redis_client.ping = AsyncMock(return_value=True)

            await init_redis()

            mock_redis.from_url.assert_called_once()
            mock_redis_client.ping.assert_called_once()
            assert redis_module.redis_client == mock_redis_client

    @pytest.mark.asyncio
    async def test_init_redis_connection_error(self):
        """Test Redis initialization with connection error."""
        from app.db import redis as redis_module
        
        with patch("app.db.redis.redis") as mock_redis:
            from app.core.logging import get_logger

            mock_redis_client = AsyncMock(spec=AsyncRedis)
            mock_redis.from_url.return_value = mock_redis_client
            mock_redis_client.ping = AsyncMock(side_effect=Exception("Connection failed"))

            with pytest.raises(Exception, match="Connection failed"):
                await init_redis()

            assert redis_module.redis_client is None

    @pytest.mark.asyncio
    async def test_init_redis_sets_global_client(self):
        """Test that init_redis sets global redis_client."""
        from app.db import redis as redis_module

        with patch("app.db.redis.redis") as mock_redis:
            mock_redis_client = AsyncMock(spec=AsyncRedis)
            mock_redis.from_url.return_value = mock_redis_client
            mock_redis_client.ping = AsyncMock(return_value=True)

            await init_redis()

            assert redis_module.redis_client is not None
            assert redis_module.redis_client == mock_redis_client


@pytest.mark.unit
class TestCloseRedis:
    """Test Redis connection closing."""

    @pytest.mark.asyncio
    async def test_close_redis_success(self):
        """Test successful Redis connection closing."""
        from app.db import redis as redis_module
        
        mock_redis_client = AsyncMock(spec=AsyncRedis)
        mock_redis_client.close = AsyncMock()
        
        # Set the global redis_client
        with patch.object(redis_module, 'redis_client', mock_redis_client):
            await close_redis()
            mock_redis_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_redis_when_client_is_none(self):
        """Test closing Redis when client is None."""
        from app.db import redis as redis_module
        
        with patch.object(redis_module, 'redis_client', None):
            # Should not raise exception
            await close_redis()


@pytest.mark.unit
class TestGetRedis:
    """Test get_redis dependency function."""

    @pytest.mark.asyncio
    async def test_get_redis_returns_client(self):
        """Test that get_redis returns the global redis_client."""
        from app.db import redis as redis_module
        
        mock_redis_instance = AsyncMock(spec=AsyncRedis)
        
        with patch.object(redis_module, 'redis_client', mock_redis_instance):
            result = await get_redis()
            assert result == mock_redis_instance


@pytest.mark.unit
class TestGetCacheService:
    """Test get_cache_service dependency function."""

    @pytest.mark.asyncio
    async def test_get_cache_service_returns_cache_service(self):
        """Test that get_cache_service returns CacheService instance."""
        from app.db import redis as redis_module
        
        mock_redis_instance = AsyncMock(spec=AsyncRedis)
        
        with patch.object(redis_module, 'redis_client', mock_redis_instance):
            result = get_cache_service()
            assert isinstance(result, CacheService)
            assert result.redis == mock_redis_instance


@pytest.mark.unit
class TestCacheServiceInit:
    """Test CacheService initialization."""

    def test_cache_service_init(self):
        """Test CacheService initialization."""
        mock_redis = AsyncMock(spec=AsyncRedis)

        cache_service = CacheService(mock_redis)

        assert cache_service.redis == mock_redis


@pytest.mark.unit
class TestCacheServiceGet:
    """Test CacheService get method."""

    @pytest.mark.asyncio
    async def test_cache_service_get_success(self):
        """Test successful cache get."""
        mock_redis = AsyncMock(spec=AsyncRedis)
        mock_redis.get = AsyncMock(return_value="cached_value")
        cache_service = CacheService(mock_redis)

        result = await cache_service.get("test_key")

        assert result == "cached_value"
        mock_redis.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_cache_service_get_not_found(self):
        """Test cache get when key doesn't exist."""
        mock_redis = AsyncMock(spec=AsyncRedis)
        mock_redis.get = AsyncMock(return_value=None)
        cache_service = CacheService(mock_redis)

        result = await cache_service.get("nonexistent_key")

        assert result is None
        mock_redis.get.assert_called_once_with("nonexistent_key")

    @pytest.mark.asyncio
    async def test_cache_service_get_error(self):
        """Test cache get with error."""
        from app.core.logging import get_logger

        mock_redis = AsyncMock(spec=AsyncRedis)
        mock_redis.get = AsyncMock(side_effect=Exception("Redis error"))
        cache_service = CacheService(mock_redis)

        result = await cache_service.get("test_key")

        assert result is None


@pytest.mark.unit
class TestCacheServiceSet:
    """Test CacheService set method."""

    @pytest.mark.asyncio
    async def test_cache_service_set_success(self):
        """Test successful cache set."""
        mock_redis = AsyncMock(spec=AsyncRedis)
        mock_redis.setex = AsyncMock(return_value=True)
        cache_service = CacheService(mock_redis)

        result = await cache_service.set("test_key", "test_value")

        assert result is True
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_service_set_with_custom_ttl(self):
        """Test cache set with custom TTL."""
        mock_redis = AsyncMock(spec=AsyncRedis)
        mock_redis.setex = AsyncMock(return_value=True)
        cache_service = CacheService(mock_redis)

        result = await cache_service.set("test_key", "test_value", ttl=600)

        assert result is True
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_service_set_with_default_ttl(self):
        """Test cache set with default TTL."""
        mock_redis = AsyncMock(spec=AsyncRedis)
        mock_redis.setex = AsyncMock(return_value=True)
        cache_service = CacheService(mock_redis)

        result = await cache_service.set("test_key", "test_value")

        assert result is True

    @pytest.mark.asyncio
    async def test_cache_service_set_error(self):
        """Test cache set with error."""
        mock_redis = AsyncMock(spec=AsyncRedis)
        mock_redis.setex = AsyncMock(side_effect=Exception("Redis error"))
        cache_service = CacheService(mock_redis)

        result = await cache_service.set("test_key", "test_value")

        assert result is False


@pytest.mark.unit
class TestCacheServiceDelete:
    """Test CacheService delete method."""

    @pytest.mark.asyncio
    async def test_cache_service_delete_success(self):
        """Test successful cache delete."""
        mock_redis = AsyncMock(spec=AsyncRedis)
        mock_redis.delete = AsyncMock(return_value=1)
        cache_service = CacheService(mock_redis)

        result = await cache_service.delete("test_key")

        assert result is True
        mock_redis.delete.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_cache_service_delete_error(self):
        """Test cache delete with error."""
        mock_redis = AsyncMock(spec=AsyncRedis)
        mock_redis.delete = AsyncMock(side_effect=Exception("Redis error"))
        cache_service = CacheService(mock_redis)

        result = await cache_service.delete("test_key")

        assert result is False


@pytest.mark.unit
class TestCacheServiceDeletePattern:
    """Test CacheService delete_pattern method."""

    @pytest.mark.asyncio
    async def test_cache_service_delete_pattern_success(self):
        """Test successful cache delete pattern."""
        mock_redis = AsyncMock(spec=AsyncRedis)
        mock_redis.keys = AsyncMock(return_value=["key1", "key2", "key3"])
        mock_redis.delete = AsyncMock()
        cache_service = CacheService(mock_redis)

        result = await cache_service.delete_pattern("test:*")

        assert result == 3
        mock_redis.keys.assert_called_once_with("test:*")
        mock_redis.delete.assert_called_once_with("key1", "key2", "key3")

    @pytest.mark.asyncio
    async def test_cache_service_delete_pattern_no_keys(self):
        """Test cache delete pattern with no matching keys."""
        mock_redis = AsyncMock(spec=AsyncRedis)
        mock_redis.keys = AsyncMock(return_value=[])
        cache_service = CacheService(mock_redis)

        result = await cache_service.delete_pattern("test:*")

        assert result == 0
        mock_redis.keys.assert_called_once_with("test:*")
        mock_redis.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_service_delete_pattern_error(self):
        """Test cache delete pattern with error."""
        mock_redis = AsyncMock(spec=AsyncRedis)
        mock_redis.keys = AsyncMock(side_effect=Exception("Redis error"))
        cache_service = CacheService(mock_redis)

        result = await cache_service.delete_pattern("test:*")

        assert result == 0


@pytest.mark.unit
class TestCacheServiceExists:
    """Test CacheService exists method."""

    @pytest.mark.asyncio
    async def test_cache_service_exists_true(self):
        """Test cache exists returns True."""
        mock_redis = AsyncMock(spec=AsyncRedis)
        mock_redis.exists = AsyncMock(return_value=1)
        cache_service = CacheService(mock_redis)

        result = await cache_service.exists("test_key")

        assert result is True
        mock_redis.exists.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_cache_service_exists_false(self):
        """Test cache exists returns False."""
        mock_redis = AsyncMock(spec=AsyncRedis)
        mock_redis.exists = AsyncMock(return_value=0)
        cache_service = CacheService(mock_redis)

        result = await cache_service.exists("test_key")

        assert result is False
        mock_redis.exists.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_cache_service_exists_error(self):
        """Test cache exists with error."""
        mock_redis = AsyncMock(spec=AsyncRedis)
        mock_redis.exists = AsyncMock(side_effect=Exception("Redis error"))
        cache_service = CacheService(mock_redis)

        result = await cache_service.exists("test_key")

        assert result is False


@pytest.mark.unit
class TestCacheServiceExpire:
    """Test CacheService expire method."""

    @pytest.mark.asyncio
    async def test_cache_service_expire_success(self):
        """Test successful cache expire."""
        mock_redis = AsyncMock(spec=AsyncRedis)
        mock_redis.expire = AsyncMock(return_value=True)
        cache_service = CacheService(mock_redis)

        result = await cache_service.expire("test_key", 600)

        assert result is True
        mock_redis.expire.assert_called_once_with("test_key", 600)

    @pytest.mark.asyncio
    async def test_cache_service_expire_error(self):
        """Test cache expire with error."""
        mock_redis = AsyncMock(spec=AsyncRedis)
        mock_redis.expire = AsyncMock(side_effect=Exception("Redis error"))
        cache_service = CacheService(mock_redis)

        result = await cache_service.expire("test_key", 600)

        assert result is False


@pytest.mark.unit
class TestCacheServiceIncrement:
    """Test CacheService increment method."""

    @pytest.mark.asyncio
    async def test_cache_service_increment_success(self):
        """Test successful cache increment."""
        mock_redis = AsyncMock(spec=AsyncRedis)
        mock_redis.incrby = AsyncMock(return_value=5)
        cache_service = CacheService(mock_redis)

        result = await cache_service.increment("test_key")

        assert result == 5
        mock_redis.incrby.assert_called_once_with("test_key", 1)

    @pytest.mark.asyncio
    async def test_cache_service_increment_with_amount(self):
        """Test cache increment with custom amount."""
        mock_redis = AsyncMock(spec=AsyncRedis)
        mock_redis.incrby = AsyncMock(return_value=10)
        cache_service = CacheService(mock_redis)

        result = await cache_service.increment("test_key", 5)

        assert result == 10
        mock_redis.incrby.assert_called_once_with("test_key", 5)

    @pytest.mark.asyncio
    async def test_cache_service_increment_error(self):
        """Test cache increment with error."""
        mock_redis = AsyncMock(spec=AsyncRedis)
        mock_redis.incrby = AsyncMock(side_effect=Exception("Redis error"))
        cache_service = CacheService(mock_redis)

        result = await cache_service.increment("test_key")

        assert result is None
