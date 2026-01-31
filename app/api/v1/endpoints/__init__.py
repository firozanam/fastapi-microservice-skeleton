"""API v1 endpoints."""
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.users import router as users_router

__all__ = ["health_router", "users_router"]
