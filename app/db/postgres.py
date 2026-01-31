"""
PostgreSQL database connection and session management.
"""
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Create async engine
engine = create_async_engine(
    settings.POSTGRES_URL,
    pool_size=settings.POSTGRES_POOL_SIZE,
    max_overflow=settings.POSTGRES_MAX_OVERFLOW,
    pool_timeout=settings.POSTGRES_POOL_TIMEOUT,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.

    Yields:
        AsyncSession: Database session

    Raises:
        RuntimeError: If PostgreSQL is not enabled in configuration

    Example:
        ```python
        @app.get("/users/{user_id}")
        async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            return user
        ```
    """
    if not settings.ENABLE_POSTGRES:
        raise RuntimeError(
            "PostgreSQL is not enabled. Set ENABLE_POSTGRES=true in your configuration "
            "to use PostgreSQL database features."
        )
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("Database session error", error=str(e))
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables (for development only).
    
    This function checks if PostgreSQL is enabled before attempting initialization.
    If disabled, it logs an info message and returns early.
    """
    if not settings.ENABLE_POSTGRES:
        logger.info("PostgreSQL is disabled - skipping initialization")
        return
    
    try:
        logger.info("Initializing PostgreSQL connection...")
        
        # Test connection
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        
        # Create tables in development
        if settings.APP_ENV == "development" and settings.DEBUG:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("PostgreSQL tables created successfully")
        else:
            logger.info("PostgreSQL connection established successfully")
            
    except Exception as e:
        logger.warning(
            "Failed to initialize PostgreSQL - continuing without it", error=str(e)
        )
        # Don't raise - allow app to start without PostgreSQL for development


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
    logger.info("Database connections closed")
