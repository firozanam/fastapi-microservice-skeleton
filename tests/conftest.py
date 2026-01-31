"""
Pytest configuration and fixtures.

This module provides test fixtures that respect the modular database configuration.
Tests can use pytest markers to skip tests when specific databases are disabled.
"""
import asyncio
import os
import sys
import tempfile
from typing import AsyncGenerator, Generator

import pytest
from httpx import AsyncClient
from sqlalchemy import String, TypeDecorator
from sqlalchemy.dialects.sqlite import TEXT
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.types import UUID

# Add project root to sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings
from app.models.base import Base
from app.main import app


# Import all models to ensure they're registered with Base
from app.models import User  # noqa: F401


# Global test engine and session factory
_test_engine = None
_test_session_factory = None
_test_db_path = None


# ============================================================================
# PYTEST MARKERS FOR DATABASE-SPECIFIC TESTS
# ============================================================================
def pytest_configure(config):
    """Register custom markers for database-specific tests."""
    config.addinivalue_line(
        "markers", "postgres: mark test as requiring PostgreSQL"
    )
    config.addinivalue_line(
        "markers", "mongodb: mark test as requiring MongoDB"
    )
    config.addinivalue_line(
        "markers", "redis: mark test as requiring Redis"
    )


def pytest_collection_modifyitems(config, items):
    """
    Automatically skip tests based on database availability.
    
    This function runs after test collection and adds skip markers to tests
    that require databases which are disabled in the configuration.
    """
    skip_postgres = pytest.mark.skip(reason="PostgreSQL is disabled (ENABLE_POSTGRES=false)")
    skip_mongodb = pytest.mark.skip(reason="MongoDB is disabled (ENABLE_MONGODB=false)")
    skip_redis = pytest.mark.skip(reason="Redis is disabled (ENABLE_REDIS=false)")
    
    for item in items:
        # Skip PostgreSQL tests if disabled
        if "postgres" in item.keywords and not settings.ENABLE_POSTGRES:
            item.add_marker(skip_postgres)
        
        # Skip MongoDB tests if disabled
        if "mongodb" in item.keywords and not settings.ENABLE_MONGODB:
            item.add_marker(skip_mongodb)
        
        # Skip Redis tests if disabled
        if "redis" in item.keywords and not settings.ENABLE_REDIS:
            item.add_marker(skip_redis)


# ============================================================================
# HELPER FIXTURES FOR DATABASE AVAILABILITY
# ============================================================================
@pytest.fixture(scope="session")
def postgres_enabled() -> bool:
    """Check if PostgreSQL is enabled."""
    return settings.ENABLE_POSTGRES


@pytest.fixture(scope="session")
def mongodb_enabled() -> bool:
    """Check if MongoDB is enabled."""
    return settings.ENABLE_MONGODB


@pytest.fixture(scope="session")
def redis_enabled() -> bool:
    """Check if Redis is enabled."""
    return settings.ENABLE_REDIS


# SQLite compatible UUID type
class SQLiteUUID(TypeDecorator):
    """Platform-independent UUID type for SQLite."""
    
    impl = String(36)
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        """Load dialect-specific implementation."""
        if dialect.name == "sqlite":
            return dialect.type_descriptor(TEXT())
        else:
            return dialect.type_descriptor(UUID())
    
    def process_bind_param(self, value, dialect):
        """Process bound parameter value."""
        if value is None:
            return None
        elif dialect.name == "sqlite":
            return str(value)
        else:
            return value
    
    def process_result_value(self, value, dialect):
        """Process result value."""
        if value is None:
            return None
        elif dialect.name == "sqlite":
            from uuid import UUID as PyUUID
            return PyUUID(value)
        else:
            return value


@pytest.fixture(scope="session", autouse=True)
def override_jwt_algorithm():
    """Override JWT algorithm to HS256 for testing (RS256 requires RSA keys)."""
    original_algorithm = settings.JWT_ALGORITHM
    # Override to use HS256 which works with simple secret keys
    object.__setattr__(settings, 'JWT_ALGORITHM', 'HS256')
    yield
    # Restore original algorithm
    object.__setattr__(settings, 'JWT_ALGORITHM', original_algorithm)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """
    Create test database engine using SQLite file.
    
    Note: This fixture is only used when PostgreSQL is enabled. If PostgreSQL
    is disabled, tests requiring database access will be skipped.
    """
    global _test_engine, _test_session_factory, _test_db_path

    # Create a temporary file for test database
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    _test_db_path = db_file.name
    db_file.close()

    test_db_url = f"sqlite+aiosqlite:///{_test_db_path}"

    _test_engine = create_async_engine(
        test_db_url,
        connect_args={"check_same_thread": False},
    )

    # Create session factory
    _test_session_factory = async_sessionmaker(
        _test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    yield _test_engine

    await _test_engine.dispose()
    _test_engine = None
    _test_session_factory = None

    # Clean up of temporary file
    try:
        os.unlink(_test_db_path)
    except:
        pass
    _test_db_path = None


@pytest.fixture
async def db_session(test_engine, postgres_enabled) -> AsyncGenerator[AsyncSession, None]:
    """
    Create database session for tests.
    
    This fixture will skip tests if PostgreSQL is disabled.
    """
    if not postgres_enabled:
        pytest.skip("PostgreSQL is disabled")
    
    async with _test_session_factory() as session:
        yield session


@pytest.fixture
async def client(test_engine, postgres_enabled) -> AsyncGenerator[AsyncClient, None]:
    """
    Create async HTTP client for testing with test database override.
    
    This fixture conditionally sets up database overrides based on which
    databases are enabled in the configuration.
    """
    from app.db.postgres import get_db
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    
    # Store original UUID type
    original_uuid_type = PG_UUID
    
    # Replace PG_UUID with SQLite-compatible UUID for testing
    # This is a workaround for SQLite not supporting PostgreSQL UUID type
    try:
        # Only set up database if PostgreSQL is enabled
        if postgres_enabled:
            # Create tables in test database using engine
            # We need to handle UUID type for SQLite
            from app.models.base import BaseModel
            
            # Temporarily replace UUID type in model
            for table in Base.metadata.tables.values():
                for column in table.columns:
                    if isinstance(column.type, PG_UUID):
                        # Store original type
                        column._original_type = column.type
                        # Replace with SQLite-compatible type
                        column.type = SQLiteUUID()
            
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            # Override database dependency to use test database
            async def override_get_db():
                async with _test_session_factory() as session:
                    yield session

            app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

        # Clean up overrides
        app.dependency_overrides.clear()
        
        # Drop tables after each test for isolation (only if PostgreSQL enabled)
        if postgres_enabled:
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
    
    finally:
        # Restore original UUID types (only if PostgreSQL enabled)
        if postgres_enabled:
            for table in Base.metadata.tables.values():
                for column in table.columns:
                    if hasattr(column, '_original_type'):
                        column.type = column._original_type
                        delattr(column, '_original_type')


@pytest.fixture
def test_user_data():
    """Provide test user data."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123",
        "first_name": "Test",
        "last_name": "User",
        "phone": "+1234567890",
        "country_code": "US",
        "locale": "en-US",
    }
