"""Pydantic schemas for request/response validation."""
from app.schemas.common import (
    ErrorDetail,
    ErrorResponse,
    FieldError,
    HealthResponse,
    MessageResponse,
    PaginatedResponse,
    PaginationMeta,
    SuccessResponse,
    ValidationErrorDetail,
    ValidationErrorResponse,
)
from app.schemas.user import (
    ForgotPassword,
    ResetPassword,
    TokenRefresh,
    TokenResponse,
    UserBase,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    VerifyOTP,
)

__all__ = [
    # Common
    "SuccessResponse",
    "PaginatedResponse",
    "PaginationMeta",
    "ErrorResponse",
    "ErrorDetail",
    "ValidationErrorResponse",
    "ValidationErrorDetail",
    "FieldError",
    "HealthResponse",
    "MessageResponse",
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserLogin",
    "TokenResponse",
    "TokenRefresh",
    "ForgotPassword",
    "ResetPassword",
    "VerifyOTP",
]
