"""Database module for PostgreSQL, Redis, and MongoDB connections."""
from app.db.mongodb import MongoRepository, close_mongo, get_mongo, init_mongo
from app.db.postgres import (
    AsyncSession,
    Base,
    close_db,
    get_db,
    init_db,
)
from app.db.redis import (
    CacheService,
    Redis,
    close_redis,
    get_cache_service,
    get_redis,
    init_redis,
)

__all__ = [
    # PostgreSQL
    "AsyncSession",
    "Base",
    "get_db",
    "init_db",
    "close_db",
    # Redis
    "Redis",
    "CacheService",
    "get_redis",
    "get_cache_service",
    "init_redis",
    "close_redis",
    # MongoDB
    "MongoRepository",
    "get_mongo",
    "init_mongo",
    "close_mongo",
]
