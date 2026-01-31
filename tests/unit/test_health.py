"""
Unit tests for health check endpoints.
Tests health_check, readiness_check, check_postgres, check_mongodb, and check_redis functions.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI

from app.api.v1.endpoints.health import (
    check_postgres,
    check_mongodb,
    check_redis,
    health_check,
    readiness_check,
)
from app.schemas.common import HealthResponse


@pytest.mark.unit
class TestHealthCheck:
    """Test health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check_all_healthy(self):
        """Test health check when all services are healthy."""
        with patch("app.api.v1.endpoints.health.check_postgres") as mock_postgres, \
             patch("app.api.v1.endpoints.health.check_mongodb") as mock_mongodb, \
             patch("app.api.v1.endpoints.health.check_redis") as mock_redis, \
             patch("app.api.v1.endpoints.health.settings") as mock_settings:
            mock_settings.ENABLE_POSTGRES = True
            mock_settings.ENABLE_MONGODB = True
            mock_settings.ENABLE_REDIS = True
            mock_settings.enabled_databases = ["PostgreSQL", "MongoDB", "Redis"]
            mock_settings.APP_VERSION = "1.0.0"
            mock_settings.APP_ENV = "development"
            
            mock_postgres.return_value = {"status": "healthy", "message": "OK"}
            mock_mongodb.return_value = {"status": "healthy", "message": "OK"}
            mock_redis.return_value = {"status": "healthy", "message": "OK"}

            result = await health_check()

            assert result.status == "healthy"
            assert result.version is not None
            assert result.environment is not None
            assert result.checks is not None

    @pytest.mark.asyncio
    async def test_health_check_postgres_unhealthy(self):
        """Test health check when PostgreSQL is unhealthy."""
        with patch("app.api.v1.endpoints.health.check_postgres") as mock_postgres, \
             patch("app.api.v1.endpoints.health.check_mongodb") as mock_mongodb, \
             patch("app.api.v1.endpoints.health.check_redis") as mock_redis, \
             patch("app.api.v1.endpoints.health.settings") as mock_settings:
            mock_settings.ENABLE_POSTGRES = True
            mock_settings.ENABLE_MONGODB = True
            mock_settings.ENABLE_REDIS = True
            mock_settings.enabled_databases = ["PostgreSQL", "MongoDB", "Redis"]
            mock_settings.APP_VERSION = "1.0.0"
            mock_settings.APP_ENV = "development"
            
            mock_postgres.return_value = {"status": "unhealthy", "message": "Error"}
            mock_mongodb.return_value = {"status": "healthy", "message": "OK"}
            mock_redis.return_value = {"status": "healthy", "message": "OK"}

            result = await health_check()

            assert result.status == "unhealthy"

    @pytest.mark.asyncio
    async def test_health_check_redis_unhealthy(self):
        """Test health check when Redis is unhealthy."""
        with patch("app.api.v1.endpoints.health.check_postgres") as mock_postgres, \
             patch("app.api.v1.endpoints.health.check_mongodb") as mock_mongodb, \
             patch("app.api.v1.endpoints.health.check_redis") as mock_redis, \
             patch("app.api.v1.endpoints.health.settings") as mock_settings:
            mock_settings.ENABLE_POSTGRES = True
            mock_settings.ENABLE_MONGODB = True
            mock_settings.ENABLE_REDIS = True
            mock_settings.enabled_databases = ["PostgreSQL", "MongoDB", "Redis"]
            mock_settings.APP_VERSION = "1.0.0"
            mock_settings.APP_ENV = "development"
            
            mock_postgres.return_value = {"status": "healthy", "message": "OK"}
            mock_mongodb.return_value = {"status": "healthy", "message": "OK"}
            mock_redis.return_value = {"status": "unhealthy", "message": "Error"}

            result = await health_check()

            assert result.status == "unhealthy"

    @pytest.mark.asyncio
    async def test_health_check_postgres_only(self):
        """Test health check with only PostgreSQL enabled."""
        with patch("app.api.v1.endpoints.health.check_postgres") as mock_postgres, \
             patch("app.api.v1.endpoints.health.settings") as mock_settings:
            mock_settings.ENABLE_POSTGRES = True
            mock_settings.ENABLE_MONGODB = False
            mock_settings.ENABLE_REDIS = False
            mock_settings.enabled_databases = ["PostgreSQL"]
            mock_settings.APP_VERSION = "1.0.0"
            mock_settings.APP_ENV = "development"
            
            mock_postgres.return_value = {"status": "healthy", "message": "OK"}

            result = await health_check()

            assert result.status == "healthy"


@pytest.mark.unit
class TestReadinessCheck:
    """Test readiness check endpoint."""

    @pytest.mark.asyncio
    async def test_readiness_check_ready(self):
        """Test readiness check when all services are ready."""
        with patch("app.api.v1.endpoints.health.check_postgres") as mock_postgres, \
             patch("app.api.v1.endpoints.health.check_mongodb") as mock_mongodb, \
             patch("app.api.v1.endpoints.health.check_redis") as mock_redis, \
             patch("app.api.v1.endpoints.health.settings") as mock_settings:
            mock_settings.ENABLE_POSTGRES = True
            mock_settings.ENABLE_MONGODB = True
            mock_settings.ENABLE_REDIS = True
            mock_settings.enabled_databases = ["PostgreSQL", "MongoDB", "Redis"]
            
            mock_postgres.return_value = {"status": "healthy"}
            mock_mongodb.return_value = {"status": "healthy"}
            mock_redis.return_value = {"status": "healthy"}

            result = await readiness_check()

            assert result["status"] == "ready"
            assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_readiness_check_not_ready(self):
        """Test readiness check when services are not ready."""
        with patch("app.api.v1.endpoints.health.check_postgres") as mock_postgres, \
             patch("app.api.v1.endpoints.health.check_mongodb") as mock_mongodb, \
             patch("app.api.v1.endpoints.health.check_redis") as mock_redis, \
             patch("app.api.v1.endpoints.health.settings") as mock_settings:
            mock_settings.ENABLE_POSTGRES = True
            mock_settings.ENABLE_MONGODB = True
            mock_settings.ENABLE_REDIS = True
            mock_settings.enabled_databases = ["PostgreSQL", "MongoDB", "Redis"]
            
            mock_postgres.return_value = {"status": "unhealthy"}
            mock_mongodb.return_value = {"status": "healthy"}
            mock_redis.return_value = {"status": "healthy"}

            result = await readiness_check()

            assert result["status"] == "not_ready"


@pytest.mark.unit
class TestCheckPostgres:
    """Test check_postgres function."""

    @pytest.mark.asyncio
    async def test_check_postgres_disabled(self):
        """Test PostgreSQL check when disabled."""
        with patch("app.api.v1.endpoints.health.settings") as mock_settings:
            mock_settings.ENABLE_POSTGRES = False
            
            result = await check_postgres()
            
            assert result["status"] == "disabled"

    @pytest.mark.asyncio
    async def test_check_postgres_success(self):
        """Test successful PostgreSQL check."""
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()
        
        mock_engine = MagicMock()
        mock_engine.connect = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_conn), __aexit__=AsyncMock()))

        with patch("app.api.v1.endpoints.health.settings") as mock_settings, \
             patch("app.api.v1.endpoints.health.engine", mock_engine):
            mock_settings.ENABLE_POSTGRES = True

            result = await check_postgres()

            assert result["status"] == "healthy"
            assert "successful" in result["message"]

    @pytest.mark.asyncio
    async def test_check_postgres_error(self):
        """Test PostgreSQL check with error."""
        mock_engine = MagicMock()
        mock_engine.connect = MagicMock(side_effect=Exception("Connection failed"))

        with patch("app.api.v1.endpoints.health.settings") as mock_settings, \
             patch("app.api.v1.endpoints.health.engine", mock_engine):
            mock_settings.ENABLE_POSTGRES = True

            result = await check_postgres()

            assert result["status"] == "unhealthy"
            assert "Connection failed" in result["message"]


@pytest.mark.unit
class TestCheckMongoDB:
    """Test check_mongodb function."""

    @pytest.mark.asyncio
    async def test_check_mongodb_disabled(self):
        """Test MongoDB check when disabled."""
        with patch("app.api.v1.endpoints.health.settings") as mock_settings:
            mock_settings.ENABLE_MONGODB = False
            
            result = await check_mongodb()
            
            assert result["status"] == "disabled"

    @pytest.mark.asyncio
    async def test_check_mongodb_success(self):
        """Test successful MongoDB check."""
        mock_mongo = MagicMock()
        mock_mongo.admin.command = AsyncMock(return_value={"ok": 1})

        with patch("app.api.v1.endpoints.health.settings") as mock_settings, \
             patch("app.api.v1.endpoints.health.mongodb_module.mongo_client", mock_mongo):
            mock_settings.ENABLE_MONGODB = True

            result = await check_mongodb()

            assert result["status"] == "healthy"
            assert "successful" in result["message"]

    @pytest.mark.asyncio
    async def test_check_mongodb_not_initialized(self):
        """Test MongoDB check when client is not initialized."""
        with patch("app.api.v1.endpoints.health.settings") as mock_settings, \
             patch("app.api.v1.endpoints.health.mongodb_module.mongo_client", None):
            mock_settings.ENABLE_MONGODB = True

            result = await check_mongodb()

            assert result["status"] == "unhealthy"
            assert "not initialized" in result["message"]


@pytest.mark.unit
class TestCheckRedis:
    """Test check_redis function."""

    @pytest.mark.asyncio
    async def test_check_redis_disabled(self):
        """Test Redis check when disabled."""
        with patch("app.api.v1.endpoints.health.settings") as mock_settings:
            mock_settings.ENABLE_REDIS = False
            
            result = await check_redis()
            
            assert result["status"] == "disabled"

    @pytest.mark.asyncio
    async def test_check_redis_success(self):
        """Test successful Redis check."""
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)

        with patch("app.api.v1.endpoints.health.settings") as mock_settings, \
             patch("app.api.v1.endpoints.health.redis_module.redis_client", mock_redis):
            mock_settings.ENABLE_REDIS = True

            result = await check_redis()

            assert result["status"] == "healthy"
            assert "successful" in result["message"]

    @pytest.mark.asyncio
    async def test_check_redis_not_initialized(self):
        """Test Redis check when client is not initialized."""
        with patch("app.api.v1.endpoints.health.settings") as mock_settings, \
             patch("app.api.v1.endpoints.health.redis_module.redis_client", None):
            mock_settings.ENABLE_REDIS = True

            result = await check_redis()

            assert result["status"] == "unhealthy"
            assert "not initialized" in result["message"]

    @pytest.mark.asyncio
    async def test_check_redis_error(self):
        """Test Redis check with error."""
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(side_effect=Exception("Connection failed"))

        with patch("app.api.v1.endpoints.health.settings") as mock_settings, \
             patch("app.api.v1.endpoints.health.redis_module.redis_client", mock_redis):
            mock_settings.ENABLE_REDIS = True

            result = await check_redis()

            assert result["status"] == "unhealthy"
            assert "Connection failed" in result["message"]
