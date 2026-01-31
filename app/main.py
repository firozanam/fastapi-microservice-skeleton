"""
Main FastAPI application entry point.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.db import close_db, close_mongo, close_redis, init_db, init_mongo, init_redis
from app.middleware import LoggingMiddleware, setup_exception_handlers

# Configure logging
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan.

    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info(
        "Starting application", 
        app_name=settings.APP_NAME, 
        version=settings.APP_VERSION,
        environment=settings.APP_ENV
    )
    
    # Log enabled databases
    enabled_dbs = settings.enabled_databases
    logger.info(
        "Database configuration", 
        enabled_databases=enabled_dbs,
        postgres=settings.ENABLE_POSTGRES,
        mongodb=settings.ENABLE_MONGODB,
        redis=settings.ENABLE_REDIS
    )

    # Initialize database connections conditionally
    if settings.ENABLE_REDIS:
        try:
            await init_redis()
        except Exception as e:
            logger.error("Failed to initialize Redis - service may have limited functionality", error=str(e))
    else:
        logger.info("Redis initialization skipped (disabled)")
    
    if settings.ENABLE_MONGODB:
        try:
            await init_mongo()
        except Exception as e:
            logger.error("Failed to initialize MongoDB - service may have limited functionality", error=str(e))
    else:
        logger.info("MongoDB initialization skipped (disabled)")
    
    if settings.ENABLE_POSTGRES:
        try:
            await init_db()
        except Exception as e:
            logger.error("Failed to initialize PostgreSQL - service may have limited functionality", error=str(e))
    else:
        logger.info("PostgreSQL initialization skipped (disabled)")

    logger.info("Application started successfully", enabled_databases=enabled_dbs)

    yield

    # Shutdown
    logger.info("Shutting down application")

    # Close database connections conditionally
    if settings.ENABLE_REDIS:
        try:
            await close_redis()
        except Exception as e:
            logger.error("Error closing Redis connection", error=str(e))
    
    if settings.ENABLE_MONGODB:
        try:
            await close_mongo()
        except Exception as e:
            logger.error("Error closing MongoDB connection", error=str(e))
    
    if settings.ENABLE_POSTGRES:
        try:
            await close_db()
        except Exception as e:
            logger.error("Error closing PostgreSQL connection", error=str(e))

    logger.info("Application shutdown complete")


def create_application() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI application
    """
    # Create FastAPI app
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Production-ready FastAPI microservice skeleton with modular database configuration",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # Setup exception handlers
    setup_exception_handlers(app)

    # Setup CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )

    # Setup logging middleware
    app.add_middleware(LoggingMiddleware)

    # Include API router
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
            "status": "running",
        }

    return app


# Create application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower(),
    )
