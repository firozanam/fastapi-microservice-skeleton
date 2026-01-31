"""
Unit tests for PostgreSQL database module.
Tests database initialization, session management, and connection handling.

Note: All tests in this file require PostgreSQL to be enabled (ENABLE_POSTGRES=true).
Tests will be automatically skipped if PostgreSQL is disabled.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import (
    AsyncSessionLocal,
    Base,
    close_db,
    engine,
    get_db,
    init_db,
)


# Mark all tests in this module as requiring PostgreSQL
pytestmark = pytest.mark.postgres


@pytest.mark.unit
class TestGetDb:
    """Test get_db dependency function."""

    @pytest.mark.asyncio
    async def test_get_db_yields_session(self):
        """Test that get_db yields a database session."""
        with patch("app.db.postgres.AsyncSessionLocal") as mock_session_local:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
            mock_context_manager.__aexit__ = AsyncMock()
            mock_session_local.return_value = mock_context_manager

            async for session in get_db():
                assert session == mock_session

            mock_session_local.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_db_commits_on_success(self):
        """Test that get_db commits on success."""
        with patch("app.db.postgres.AsyncSessionLocal") as mock_session_local:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_session.commit = AsyncMock()
            mock_session.close = AsyncMock()
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
            mock_context_manager.__aexit__ = AsyncMock()
            mock_session_local.return_value = mock_context_manager

            async for _ in get_db():
                pass

            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_db_rollbacks_on_exception(self):
        """Test that get_db rolls back on exception."""
        from app.core.logging import get_logger

        with patch("app.db.postgres.AsyncSessionLocal") as mock_session_local:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_session.rollback = AsyncMock()
            mock_session.close = AsyncMock()
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
            mock_context_manager.__aexit__ = AsyncMock()
            mock_session_local.return_value = mock_context_manager

            # Create generator and consume it with exception
            gen = get_db()
            try:
                session = await gen.__anext__()
                raise Exception("Database error")
            except Exception:
                # Clean up the generator
                try:
                    await gen.athrow(Exception, Exception("Database error"))
                except (StopAsyncIteration, Exception):
                    pass

            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()


@pytest.mark.unit
class TestInitDb:
    """Test database initialization."""

    @pytest.mark.asyncio
    async def test_init_db_in_development_with_debug(self):
        """Test init_db in development mode with debug enabled."""
        with patch("app.db.postgres.settings") as mock_settings, \
             patch("app.db.postgres.Base") as mock_base, \
             patch("app.db.postgres.engine") as mock_engine:

            mock_settings.APP_ENV = "development"
            mock_settings.DEBUG = True
            mock_base.metadata = MagicMock()
            mock_base.metadata.create_all = MagicMock()
            mock_connection = AsyncMock()
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_connection)
            mock_context_manager.__aexit__ = AsyncMock()
            mock_engine.begin.return_value = mock_context_manager
            
            # run_sync should call the passed function
            async def mock_run_sync(func):
                func(mock_connection)
            mock_connection.run_sync = AsyncMock(side_effect=mock_run_sync)

            await init_db()

            mock_engine.begin.assert_called_once()
            mock_connection.run_sync.assert_called_once()
            mock_base.metadata.create_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_init_db_in_production(self):
        """Test init_db in production mode (should not create tables)."""
        with patch("app.db.postgres.settings") as mock_settings, \
             patch("app.db.postgres.Base") as mock_base, \
             patch("app.db.postgres.engine") as mock_engine:

            mock_settings.APP_ENV = "production"
            mock_base.metadata = MagicMock()

            await init_db()

            # Should not create tables in production
            mock_base.metadata.create_all.assert_not_called()

    @pytest.mark.asyncio
    async def test_init_db_with_debug_false(self):
        """Test init_db with debug disabled (should not create tables)."""
        with patch("app.db.postgres.settings") as mock_settings, \
             patch("app.db.postgres.Base") as mock_base, \
             patch("app.db.postgres.engine") as mock_engine:

            mock_settings.DEBUG = False
            mock_base.metadata = MagicMock()

            await init_db()

            # Should not create tables when debug is False
            mock_base.metadata.create_all.assert_not_called()

    @pytest.mark.asyncio
    async def test_init_db_with_exception(self):
        """Test init_db handles exceptions gracefully."""
        from app.core.logging import get_logger

        with patch("app.db.postgres.settings") as mock_settings, \
             patch("app.db.postgres.engine") as mock_engine:

            mock_settings.APP_ENV = "development"
            mock_settings.DEBUG = True
            mock_engine.begin = MagicMock(side_effect=Exception("Connection failed"))

            # Should not raise exception
            await init_db()


@pytest.mark.unit
class TestCloseDb:
    """Test database connection closing."""

    @pytest.mark.asyncio
    async def test_close_db_disposes_engine(self):
        """Test that close_db disposes the engine."""
        with patch("app.db.postgres.engine") as mock_engine:
            mock_engine.dispose = AsyncMock()

            await close_db()

            mock_engine.dispose.assert_called_once()


@pytest.mark.unit
class TestEngineConfiguration:
    """Test engine configuration."""

    def test_engine_is_configured(self):
        """Test that engine is properly configured."""
        assert engine is not None

    def test_async_session_local_is_configured(self):
        """Test that AsyncSessionLocal is properly configured."""
        assert AsyncSessionLocal is not None

    def test_base_is_configured(self):
        """Test that Base is properly configured."""
        assert Base is not None
