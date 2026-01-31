"""
Unit tests for main application module.
Tests application creation, lifespan management, root endpoint, and main block.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app, create_application, lifespan


@pytest.mark.unit
class TestCreateApplication:
    """Test create_application function."""

    def test_create_application_returns_fastapi_app(self):
        """Test that create_application returns FastAPI app."""
        result = create_application()

        assert result is not None
        assert hasattr(result, "add_middleware")
        assert hasattr(result, "include_router")
        assert hasattr(result, "get")

    def test_create_application_sets_title(self):
        """Test that create_application sets app title."""
        with patch("app.main.settings") as mock_settings:
            mock_settings.APP_NAME = "test-service"
            mock_settings.APP_VERSION = "1.0.0"
            mock_settings.DEBUG = True

            app = create_application()

            assert app.title == "test-service"

    def test_create_application_sets_version(self):
        """Test that create_application sets app version."""
        with patch("app.main.settings") as mock_settings:
            mock_settings.APP_VERSION = "2.0.0"

            app = create_application()

            assert app.version == "2.0.0"

    def test_create_application_sets_description(self):
        """Test that create_application sets app description."""
        app = create_application()

        assert "Production-ready FastAPI microservice" in app.description

    def test_create_application_sets_lifespan(self):
        """Test that create_application sets lifespan."""
        app = create_application()

        assert app.router.lifespan_context is not None

    def test_create_application_sets_cors_middleware(self):
        """Test that create_application adds CORS middleware."""
        with patch("app.main.settings") as mock_settings:
            mock_settings.CORS_ORIGINS = ["http://localhost:3000"]
            mock_settings.CORS_ALLOW_CREDENTIALS = True
            mock_settings.CORS_ALLOW_METHODS = ["*"]
            mock_settings.CORS_ALLOW_HEADERS = ["*"]

            app = create_application()

            assert len(app.user_middleware) > 0

    def test_create_application_sets_logging_middleware(self):
        """Test that create_application adds logging middleware."""
        app = create_application()

        assert len(app.user_middleware) > 0

    def test_create_application_includes_router(self):
        """Test that create_application includes API router."""
        with patch("app.main.api_router") as mock_router:
            app = create_application()

            assert len(app.routes) > 0

    def test_create_application_sets_debug_docs(self):
        """Test that create_application sets docs in debug mode."""
        with patch("app.main.settings") as mock_settings:
            mock_settings.DEBUG = True

            app = create_application()

            assert app.docs_url is not None
            assert app.redoc_url is not None
            assert app.openapi_url is not None

    def test_create_application_hides_docs_in_production(self):
        """Test that create_application hides docs in production mode."""
        with patch("app.main.settings") as mock_settings:
            mock_settings.DEBUG = False

            app = create_application()

            assert app.docs_url is None
            assert app.redoc_url is None
            assert app.openapi_url is None


@pytest.mark.unit
class TestLifespan:
    """Test lifespan context manager."""

    @pytest.mark.asyncio
    async def test_lifespan_startup(self):
        """Test lifespan startup."""
        with patch("app.main.logger") as mock_logger, \
             patch("app.main.init_redis") as mock_init_redis, \
             patch("app.main.init_mongo") as mock_init_mongo, \
             patch("app.main.init_db") as mock_init_db:

            mock_app = MagicMock()

            async with lifespan(mock_app) as _:
                pass

            mock_logger.info.assert_called()
            call_args = mock_logger.info.call_args
            assert "Starting application" in call_args[1]
            mock_init_redis.assert_called_once()
            mock_init_mongo.assert_called_once()
            mock_init_db.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_shutdown(self):
        """Test lifespan shutdown."""
        with patch("app.main.logger") as mock_logger, \
             patch("app.main.close_redis") as mock_close_redis, \
             patch("app.main.close_mongo") as mock_close_mongo, \
             patch("app.main.close_db") as mock_close_db:

            mock_app = MagicMock()

            async with lifespan(mock_app) as _:
                pass

            mock_logger.info.assert_called()
            call_args = mock_logger.info.call_args
            assert "Shutting down application" in call_args[1]
            mock_close_redis.assert_called_once()
            mock_close_mongo.assert_called_once()
            mock_close_db.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_logs_success(self):
        """Test lifespan logs success messages."""
        with patch("app.main.logger") as mock_logger, \
             patch("app.main.init_redis") as mock_init_redis, \
             patch("app.main.init_mongo") as mock_init_mongo, \
             patch("app.main.init_db") as mock_init_db:

            mock_init_redis.return_value = None
            mock_init_mongo.return_value = None
            mock_init_db.return_value = None

            mock_app = MagicMock()

            async with lifespan(mock_app) as _:
                pass

            assert mock_logger.info.call_count == 2
            call_args_list = [call.args for call in mock_logger.info.call_args_list]
            assert any("Application started successfully" in str(args) for args in call_args_list)


@pytest.mark.unit
class TestRootEndpoint:
    """Test root endpoint."""

    @pytest.mark.asyncio
    async def test_root_endpoint(self):
        """Test root endpoint returns correct response."""
        from httpx import AsyncClient
        
        # Use the actual app instance which already has proper settings
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/")
            
            assert response.status_code == 200
            data = response.json()
            assert "name" in data
            assert "version" in data
            assert "environment" in data
            assert data["status"] == "running"


@pytest.mark.unit
class TestMainBlock:
    """Test main block execution."""

    def test_main_block_calls_uvicorn_in_production(self):
        """Test that main block calls uvicorn in production mode."""
        with patch("app.main.settings") as mock_settings, \
             patch("app.main.uvicorn") as mock_uvicorn, \
             patch("app.main.__name__", "__main__"):

            mock_settings.DEBUG = False
            mock_settings.HOST = "0.0.0.0"
            mock_settings.PORT = 8000
            mock_settings.WORKERS = 4
            mock_settings.LOG_LEVEL = "INFO"

            exec("from app.main import *")

            mock_uvicorn.run.assert_called_once()
            call_kwargs = mock_uvicorn.run.call_args[1]
            assert call_kwargs["host"] == "0.0.0.0"
            assert call_kwargs["port"] == 8000
            assert call_kwargs["workers"] == 4
            assert call_kwargs["log_level"] == "info"

    def test_main_block_calls_uvicorn_in_development(self):
        """Test that main block calls uvicorn in development mode."""
        with patch("app.main.settings") as mock_settings, \
             patch("app.main.uvicorn") as mock_uvicorn, \
             patch("app.main.__name__", "__main__"):

            mock_settings.DEBUG = True
            mock_settings.HOST = "0.0.0.0"
            mock_settings.PORT = 8000
            mock_settings.LOG_LEVEL = "INFO"

            exec("from app.main import *")

            mock_uvicorn.run.assert_called_once()
            call_kwargs = mock_uvicorn.run.call_args[1]
            assert call_kwargs["host"] == "0.0.0.0"
            assert call_kwargs["port"] == 8000
            assert call_kwargs["reload"] is True
            assert call_kwargs["workers"] == 1
            assert call_kwargs["log_level"] == "info"


@pytest.mark.unit
class TestAppInstance:
    """Test app instance."""

    def test_app_instance_exists(self):
        """Test that app instance is created."""
        assert app is not None
        assert hasattr(app, "routes")
        assert hasattr(app, "include_router")
