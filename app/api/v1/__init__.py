"""API v1 router."""
from fastapi import APIRouter

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.users import router as users_router

api_router = APIRouter()

# Include sub-routers
api_router.include_router(health_router)
# Include users router with /users prefix for user management endpoints
api_router.include_router(users_router, prefix="/users", tags=["Users"])
# Include auth routes without /users prefix for direct access
api_router.include_router(users_router, tags=["Authentication"])
