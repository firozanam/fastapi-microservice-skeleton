"""
User management endpoints.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.db.postgres import get_db
from app.middleware.error_handler import (
    BadRequestException,
    ConflictException,
)
from app.models.user import User
from app.schemas.common import MessageResponse, SuccessResponse
from app.schemas.user import (
    ForgotPassword,
    ResetPassword,
    TokenRefresh,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/auth/register",
    response_model=SuccessResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    tags=["Authentication"],
)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[UserResponse]:
    """
    Register a new user.

    Args:
        user_in: User registration data
        db: Database session

    Returns:
        SuccessResponse with created user
    """
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none():
        raise ConflictException("Email already registered")

    # Create user
    user = User(
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        phone=user_in.phone,
        country_code=user_in.country_code,
        locale=user_in.locale,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info("User registered", user_id=str(user.id), email=user.email)

    return SuccessResponse(
        message="User registered successfully",
        data=UserResponse.model_validate(user),
    )


@router.post(
    "/auth/login",
    response_model=SuccessResponse[TokenResponse],
    tags=["Authentication"],
)
async def login(
    user_in: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[TokenResponse]:
    """
    Authenticate user and return tokens.

    Args:
        user_in: User login credentials
        db: Database session

    Returns:
        SuccessResponse with access and refresh tokens
    """
    # Find user by email
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalar_one_or_none()

    if not user:
        raise BadRequestException("Invalid email or password")

    # Verify password
    if not verify_password(user_in.password, user.password_hash):
        raise BadRequestException("Invalid email or password")

    # Check user status
    if user.status != "active":
        raise BadRequestException("User account is not active")

    # Generate tokens
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))

    logger.info("User logged in", user_id=str(user.id), email=user.email)

    return SuccessResponse(
        message="Login successful",
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        ),
    )


@router.post(
    "/auth/refresh",
    response_model=SuccessResponse[TokenResponse],
    tags=["Authentication"],
)
async def refresh_token(
    token_in: TokenRefresh,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[TokenResponse]:
    """
    Refresh access token using refresh token.

    Args:
        token_in: Refresh token
        db: Database session

    Returns:
        SuccessResponse with new access and refresh tokens
    """
    # Verify refresh token
    from app.core.security import decode_token

    payload = decode_token(token_in.refresh_token)
    user_id: str = payload.get("sub")

    if not user_id:
        raise BadRequestException("Invalid refresh token")

    # Find user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or user.status != "active":
        raise BadRequestException("Invalid refresh token")

    # Generate new tokens
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))

    logger.info("Token refreshed", user_id=str(user.id))

    return SuccessResponse(
        message="Token refreshed successfully",
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        ),
    )


@router.get(
    "/users/me",
    response_model=SuccessResponse[UserResponse],
    tags=["Users"],
)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[UserResponse]:
    """
    Get current user information.

    Args:
        current_user: Current authenticated user

    Returns:
        SuccessResponse with user data
    """
    return SuccessResponse(
        message="User information retrieved successfully",
        data=UserResponse.model_validate(current_user),
    )


@router.put(
    "/users/me",
    response_model=SuccessResponse[UserResponse],
    tags=["Users"],
)
async def update_current_user(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[UserResponse]:
    """
    Update current user information.

    Args:
        user_in: User update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        SuccessResponse with updated user data
    """
    # Update user fields
    if user_in.first_name is not None:
        current_user.first_name = user_in.first_name
    if user_in.last_name is not None:
        current_user.last_name = user_in.last_name
    if user_in.phone is not None:
        current_user.phone = user_in.phone
    if user_in.country_code is not None:
        current_user.country_code = user_in.country_code
    if user_in.locale is not None:
        current_user.locale = user_in.locale

    await db.commit()
    await db.refresh(current_user)

    logger.info("User updated", user_id=str(current_user.id))

    return SuccessResponse(
        message="User updated successfully",
        data=UserResponse.model_validate(current_user),
    )


@router.post(
    "/auth/forgot-password",
    response_model=MessageResponse,
    tags=["Authentication"],
)
async def forgot_password(
    request: ForgotPassword,
) -> MessageResponse:
    """
    Initiate password reset.

    Args:
        request: Forgot password request

    Returns:
        MessageResponse
    """
    # TODO: Implement password reset email sending
    # For now, just log the request
    logger.info("Password reset requested", email=request.email)

    return MessageResponse(
        message="If the email exists, a password reset link has been sent"
    )


@router.post(
    "/auth/reset-password",
    response_model=MessageResponse,
    tags=["Authentication"],
)
async def reset_password(
    request: ResetPassword,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """
    Complete password reset.

    Args:
        request: Reset password request
        db: Database session

    Returns:
        MessageResponse
    """
    # TODO: Implement password reset token verification
    # For now, just log the request
    logger.info("Password reset attempted", token=request.token[:10] + "...")

    return MessageResponse(message="Password reset successful")
