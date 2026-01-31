"""
Database availability middleware for startup health checks.

This middleware provides detailed database status logging during application
startup and can be used to fail fast if required databases are unavailable.
"""
from typing import Callable, Dict, Any
import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.db.postgres import engine as postgres_engine
from app.db.mongodb import mongo_client
from app.db.redis import redis_client

logger = structlog.get_logger(__name__)


class DatabaseHealthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to check database health and log availability on startup.
    
    This middleware logs database connectivity status and can be configured
    to fail requests if required databases are unavailable. It respects the
    ENABLE_* flags and only checks databases that are enabled.
    
    Note: This runs once per request, so for production you should rely on
    the /health endpoint for continuous monitoring. This is mainly useful
    during startup to verify database connectivity.
    """
    
    def __init__(self, app, fail_on_unavailable: bool = False):
        """
        Initialize database health middleware.
        
        Args:
            app: FastAPI application instance
            fail_on_unavailable: If True, return 503 when required database is down
        """
        super().__init__(app)
        self.fail_on_unavailable = fail_on_unavailable
        self._checked = False  # Only check once during startup
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Check database health on first request (startup).
        
        Args:
            request: Incoming request
            call_next: Next middleware in chain
            
        Returns:
            Response from next middleware or 503 if database unavailable
        """
        # Only check on first request to avoid overhead
        if not self._checked:
            self._checked = True
            db_status = await self._check_all_databases()
            
            # Log database availability
            logger.info(
                "Database availability check completed",
                databases=db_status,
                enabled_databases=settings.enabled_databases
            )
            
            # Optionally fail fast if required databases unavailable
            if self.fail_on_unavailable:
                unavailable = [
                    db for db, status in db_status.items() 
                    if not status.get("available", False)
                ]
                if unavailable:
                    logger.error(
                        "Required databases unavailable - failing request",
                        unavailable_databases=unavailable
                    )
                    from fastapi.responses import JSONResponse
                    return JSONResponse(
                        status_code=503,
                        content={
                            "error": "Service Unavailable",
                            "message": "Required databases are unavailable",
                            "unavailable_databases": unavailable,
                        }
                    )
        
        response = await call_next(request)
        return response
    
    async def _check_all_databases(self) -> Dict[str, Dict[str, Any]]:
        """
        Check all enabled databases and return their status.
        
        Returns:
            Dictionary with database status information
        """
        status = {}
        
        # Check PostgreSQL if enabled
        if settings.ENABLE_POSTGRES:
            status["postgresql"] = await self._check_postgres()
        else:
            status["postgresql"] = {
                "available": False,
                "reason": "disabled",
                "enabled": False
            }
        
        # Check MongoDB if enabled
        if settings.ENABLE_MONGODB:
            status["mongodb"] = await self._check_mongodb()
        else:
            status["mongodb"] = {
                "available": False,
                "reason": "disabled",
                "enabled": False
            }
        
        # Check Redis if enabled
        if settings.ENABLE_REDIS:
            status["redis"] = await self._check_redis()
        else:
            status["redis"] = {
                "available": False,
                "reason": "disabled",
                "enabled": False
            }
        
        return status
    
    async def _check_postgres(self) -> Dict[str, Any]:
        """Check PostgreSQL availability."""
        try:
            if postgres_engine is None:
                return {
                    "available": False,
                    "reason": "not_initialized",
                    "enabled": True
                }
            
            async with postgres_engine.connect() as conn:
                await conn.execute("SELECT 1")
            
            return {
                "available": True,
                "reason": "connected",
                "enabled": True
            }
        except Exception as e:
            logger.warning(
                "PostgreSQL health check failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return {
                "available": False,
                "reason": f"connection_failed: {type(e).__name__}",
                "enabled": True,
                "error": str(e)
            }
    
    async def _check_mongodb(self) -> Dict[str, Any]:
        """Check MongoDB availability."""
        try:
            if mongo_client is None:
                return {
                    "available": False,
                    "reason": "not_initialized",
                    "enabled": True
                }
            
            # Ping MongoDB
            await mongo_client.admin.command("ping")
            
            return {
                "available": True,
                "reason": "connected",
                "enabled": True
            }
        except Exception as e:
            logger.warning(
                "MongoDB health check failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return {
                "available": False,
                "reason": f"connection_failed: {type(e).__name__}",
                "enabled": True,
                "error": str(e)
            }
    
    async def _check_redis(self) -> Dict[str, Any]:
        """Check Redis availability."""
        try:
            if redis_client is None:
                return {
                    "available": False,
                    "reason": "not_initialized",
                    "enabled": True
                }
            
            # Ping Redis
            await redis_client.ping()
            
            return {
                "available": True,
                "reason": "connected",
                "enabled": True
            }
        except Exception as e:
            logger.warning(
                "Redis health check failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return {
                "available": False,
                "reason": f"connection_failed: {type(e).__name__}",
                "enabled": True,
                "error": str(e)
            }


def log_database_availability() -> None:
    """
    Log database availability configuration at startup.
    
    This is a simpler alternative to the middleware that just logs
    the database configuration without intercepting requests.
    """
    logger.info(
        "Database configuration loaded",
        postgres_enabled=settings.ENABLE_POSTGRES,
        mongodb_enabled=settings.ENABLE_MONGODB,
        redis_enabled=settings.ENABLE_REDIS,
        enabled_databases=settings.enabled_databases
    )
