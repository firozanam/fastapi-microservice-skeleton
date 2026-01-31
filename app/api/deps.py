"""
Common dependencies for API endpoints.
"""
from typing import Optional

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import verify_token
from app.db.postgres import get_db
from app.db.redis import CacheService, get_cache_service
from app.models.user import User
from app.middleware.error_handler import UnauthorizedException

# Security scheme for JWT
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP authorization credentials
        db: Database session

    Returns:
        Current authenticated user

    Raises:
        UnauthorizedException: If token is invalid or user not found
    """
    try:
        # Verify and decode token
        payload = verify_token(credentials.credentials, token_type="access")
        user_id: str = payload.get("sub")

        if user_id is None:
            raise UnauthorizedException("Invalid token: missing subject")

    except JWTError as e:
        raise UnauthorizedException(f"Invalid token: {str(e)}")

    # Query user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise UnauthorizedException("User not found")

    if user.status != "active":
        raise UnauthorizedException("User account is not active")

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise None.

    Args:
        credentials: Optional HTTP authorization credentials
        db: Database session

    Returns:
        Current user if authenticated, None otherwise
    """
    if credentials is None:
        return None

    try:
        payload = verify_token(credentials.credentials, token_type="access")
        user_id: str = payload.get("sub")

        if user_id is None:
            return None

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user is None or user.status != "active":
            return None

        return user

    except JWTError:
        return None


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Require user to have admin role.

    Args:
        current_user: Current authenticated user

    Returns:
        Current user if admin

    Raises:
        UnauthorizedException: If user is not admin
    """
    # TODO: Implement role-based access control
    # For now, we'll use a simple check
    if not getattr(current_user, "is_admin", False):
        raise UnauthorizedException("Admin access required")

    return current_user


def get_cache(
    cache_service: CacheService = Depends(get_cache_service),
) -> CacheService:
    """
    Get cache service dependency.

    Args:
        cache_service: Cache service instance

    Returns:
        Cache service
    """
    return cache_service


def get_request_id(
    x_request_id: Optional[str] = Header(None),
) -> Optional[str]:
    """
    Get request ID from header.

    Args:
        x_request_id: X-Request-ID header value

    Returns:
        Request ID or None
    """
    return x_request_id
