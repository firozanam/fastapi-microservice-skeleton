"""
Error handling middleware and exception handlers.
"""
import traceback

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from jose import JWTError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.common import (
    ErrorDetail,
    ErrorResponse,
    FieldError,
    ValidationErrorDetail,
    ValidationErrorResponse,
)

logger = get_logger(__name__)


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        code: str = "app_error",
        details: dict = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ):
        self.message = message
        self.code = code
        self.details = details
        self.status_code = status_code
        super().__init__(message)


class NotFoundException(AppException):
    """Resource not found exception."""

    def __init__(self, message: str = "Resource not found", details: dict = None):
        super().__init__(
            message=message,
            code="not_found",
            details=details,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class BadRequestException(AppException):
    """Bad request exception."""

    def __init__(self, message: str = "Bad request", details: dict = None):
        super().__init__(
            message=message,
            code="bad_request",
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class UnauthorizedException(AppException):
    """Unauthorized exception."""

    def __init__(self, message: str = "Unauthorized", details: dict = None):
        super().__init__(
            message=message,
            code="unauthorized",
            details=details,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class ForbiddenException(AppException):
    """Forbidden exception."""

    def __init__(self, message: str = "Forbidden", details: dict = None):
        super().__init__(
            message=message,
            code="forbidden",
            details=details,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class ConflictException(AppException):
    """Conflict exception."""

    def __init__(self, message: str = "Resource conflict", details: dict = None):
        super().__init__(
            message=message,
            code="conflict",
            details=details,
            status_code=status.HTTP_409_CONFLICT,
        )


class ValidationException(AppException):
    """Validation exception."""

    def __init__(self, message: str = "Validation failed", details: dict = None):
        super().__init__(
            message=message,
            code="validation_error",
            details=details,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class RateLimitException(AppException):
    """Rate limit exception."""

    def __init__(self, message: str = "Rate limit exceeded", details: dict = None):
        super().__init__(
            message=message,
            code="rate_limit_exceeded",
            details=details,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Setup exception handlers for the FastAPI application.

    Args:
        app: FastAPI application instance
    """

    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request, exc: AppException
    ) -> JSONResponse:
        """Handle application exceptions."""
        logger.error(
            "Application exception",
            code=exc.code,
            message=exc.message,
            path=request.url.path,
            status_code=exc.status_code,
        )

        error_detail = ErrorDetail(
            code=exc.code,
            message=exc.message,
            details=exc.details,
            stack_trace=traceback.format_exc() if settings.DEBUG else None,
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(error=error_detail).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """Handle Pydantic validation errors."""
        logger.warning(
            "Validation error",
            errors=exc.errors(),
            path=request.url.path,
        )

        field_errors = [
            FieldError(
                field=error["loc"][-1] if error["loc"] else "body",
                message=error["msg"],
                type=error["type"],
            )
            for error in exc.errors()
        ]

        validation_detail = ValidationErrorDetail(errors=field_errors)

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ValidationErrorResponse(error=validation_detail).model_dump(),
        )

    @app.exception_handler(JWTError)
    async def jwt_exception_handler(request: Request, exc: JWTError) -> JSONResponse:
        """Handle JWT errors."""
        logger.warning(
            "JWT error",
            error=str(exc),
            path=request.url.path,
        )

        error_detail = ErrorDetail(
            code="invalid_token",
            message="Invalid or expired token",
        )

        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=ErrorResponse(error=error_detail).model_dump(),
        )

    @app.exception_handler(IntegrityError)
    async def integrity_exception_handler(
        request: Request,
        exc: IntegrityError,
    ) -> JSONResponse:
        """Handle database integrity errors."""
        logger.error(
            "Database integrity error",
            error=str(exc),
            path=request.url.path,
        )

        error_detail = ErrorDetail(
            code="integrity_error",
            message="Database integrity constraint violated",
        )

        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorResponse(error=error_detail).model_dump(),
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(
        request: Request,
        exc: SQLAlchemyError,
    ) -> JSONResponse:
        """Handle SQLAlchemy errors."""
        logger.error(
            "Database error",
            error=str(exc),
            path=request.url.path,
        )

        error_detail = ErrorDetail(
            code="database_error",
            message="Database operation failed",
            stack_trace=traceback.format_exc() if settings.DEBUG else None,
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(error=error_detail).model_dump(),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle all other exceptions."""
        logger.error(
            "Unhandled exception",
            error=str(exc),
            path=request.url.path,
            stack_trace=traceback.format_exc(),
        )

        error_detail = ErrorDetail(
            code="internal_error",
            message="An internal server error occurred",
            stack_trace=traceback.format_exc() if settings.DEBUG else None,
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(error=error_detail).model_dump(),
        )
