"""
Health check endpoints for monitoring and observability.
"""
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.core.logging import get_logger
from app.db.postgres import engine
from app.db import redis as redis_module
from app.db import mongodb as mongodb_module
from app.schemas.common import HealthResponse

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns service health status and dependency checks for enabled databases only.

    Returns:
        HealthResponse: Health status and checks
    """
    checks = {
        "timestamp": datetime.utcnow().isoformat(),
        "configuration": {
            "enabled_databases": settings.enabled_databases,
            "postgres_enabled": settings.ENABLE_POSTGRES,
            "mongodb_enabled": settings.ENABLE_MONGODB,
            "redis_enabled": settings.ENABLE_REDIS,
        }
    }
    
    # Check only enabled databases
    if settings.ENABLE_POSTGRES:
        checks["postgres"] = await check_postgres()
    
    if settings.ENABLE_MONGODB:
        checks["mongodb"] = await check_mongodb()
    
    if settings.ENABLE_REDIS:
        checks["redis"] = await check_redis()

    # Check if all enabled databases are healthy
    enabled_db_checks = [
        checks.get("postgres", {"status": "disabled"}),
        checks.get("mongodb", {"status": "disabled"}),
        checks.get("redis", {"status": "disabled"})
    ]
    
    all_healthy = all(
        check["status"] in ["healthy", "disabled"] 
        for check in enabled_db_checks
    )

    return HealthResponse(
        status="healthy" if all_healthy else "unhealthy",
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        checks=checks,
    )


@router.get("/ready", tags=["Health"])
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint.

    Returns whether the service is ready to accept traffic.
    Service is ready if all enabled databases are healthy.

    Returns:
        Dict with readiness status
    """
    ready = True
    
    # Check only enabled databases
    if settings.ENABLE_POSTGRES:
        postgres_status = await check_postgres()
        ready = ready and postgres_status["status"] == "healthy"
    
    if settings.ENABLE_MONGODB:
        mongodb_status = await check_mongodb()
        ready = ready and mongodb_status["status"] == "healthy"
    
    if settings.ENABLE_REDIS:
        redis_status = await check_redis()
        ready = ready and redis_status["status"] == "healthy"

    return {
        "status": "ready" if ready else "not_ready",
        "enabled_databases": settings.enabled_databases,
        "timestamp": datetime.utcnow().isoformat(),
    }


async def check_postgres() -> Dict[str, str]:
    """
    Check PostgreSQL connectivity.

    Returns:
        Dict with PostgreSQL health status
    """
    if not settings.ENABLE_POSTGRES:
        return {"status": "disabled", "message": "PostgreSQL is not enabled"}
    
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "healthy", "message": "PostgreSQL connection successful"}
    except Exception as e:
        logger.error("PostgreSQL health check failed", error=str(e))
        return {"status": "unhealthy", "message": str(e)}


async def check_mongodb() -> Dict[str, str]:
    """
    Check MongoDB connectivity.

    Returns:
        Dict with MongoDB health status
    """
    if not settings.ENABLE_MONGODB:
        return {"status": "disabled", "message": "MongoDB is not enabled"}
    
    try:
        if mongodb_module.mongo_client:
            await mongodb_module.mongo_client.admin.command("ping")
            return {"status": "healthy", "message": "MongoDB connection successful"}
        return {"status": "unhealthy", "message": "MongoDB client not initialized"}
    except Exception as e:
        logger.error("MongoDB health check failed", error=str(e))
        return {"status": "unhealthy", "message": str(e)}


async def check_redis() -> Dict[str, str]:
    """
    Check Redis connectivity.

    Returns:
        Dict with Redis health status
    """
    if not settings.ENABLE_REDIS:
        return {"status": "disabled", "message": "Redis is not enabled"}
    
    try:
        if redis_module.redis_client and await redis_module.redis_client.ping():
            return {"status": "healthy", "message": "Redis connection successful"}
        return {"status": "unhealthy", "message": "Redis client not initialized"}
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        return {"status": "unhealthy", "message": str(e)}
