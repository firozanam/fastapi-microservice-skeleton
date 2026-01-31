"""
Unit tests for error handler middleware.
Tests all custom exceptions and exception handlers.
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from jose import JWTError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.middleware.error_handler import (
    AppException,
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    RateLimitException,
    setup_exception_handlers,
    UnauthorizedException,
    ValidationException,
)
from app.schemas.common import (
    ErrorResponse,
    FieldError,
    ValidationErrorDetail,
)


@pytest.mark.unit
class TestAppException:
    """Test AppException class."""

    def test_app_exception_init_defaults(self):
        """Test AppException initialization with defaults."""
        exc = AppException("Test error")

        assert exc.message == "Test error"
        assert exc.code == "app_error"
        assert exc.details is None
        assert exc.status_code == 500

    def test_app_exception_init_with_details(self):
        """Test AppException initialization with details."""
        details = {"field": "email", "error": "Invalid"}
        exc = AppException("Test error", details=details, status_code=400)

        assert exc.message == "Test error"
        assert exc.code == "app_error"
        assert exc.details == details
        assert exc.status_code == 400


@pytest.mark.unit
class TestNotFoundException:
    """Test NotFoundException class."""

    def test_not_found_exception_defaults(self):
        """Test NotFoundException with defaults."""
        exc = NotFoundException()

        assert exc.message == "Resource not found"
        assert exc.code == "not_found"
        assert exc.status_code == 404

    def test_not_found_exception_custom_message(self):
        """Test NotFoundException with custom message."""
        exc = NotFoundException("User not found")

        assert exc.message == "User not found"
        assert exc.code == "not_found"
        assert exc.status_code == 404

    def test_not_found_exception_with_details(self):
        """Test NotFoundException with details."""
        details = {"resource": "User", "id": "123"}
        exc = NotFoundException("User not found", details=details)

        assert exc.message == "User not found"
        assert exc.details == details


@pytest.mark.unit
class TestBadRequestException:
    """Test BadRequestException class."""

    def test_bad_request_exception_defaults(self):
        """Test BadRequestException with defaults."""
        exc = BadRequestException()

        assert exc.message == "Bad request"
        assert exc.code == "bad_request"
        assert exc.status_code == 400

    def test_bad_request_exception_custom_message(self):
        """Test BadRequestException with custom message."""
        exc = BadRequestException("Invalid input")

        assert exc.message == "Invalid input"


@pytest.mark.unit
class TestUnauthorizedException:
    """Test UnauthorizedException class."""

    def test_unauthorized_exception_defaults(self):
        """Test UnauthorizedException with defaults."""
        exc = UnauthorizedException()

        assert exc.message == "Unauthorized"
        assert exc.code == "unauthorized"
        assert exc.status_code == 401

    def test_unauthorized_exception_custom_message(self):
        """Test UnauthorizedException with custom message."""
        exc = UnauthorizedException("Token expired")

        assert exc.message == "Token expired"


@pytest.mark.unit
class TestForbiddenException:
    """Test ForbiddenException class."""

    def test_forbidden_exception_defaults(self):
        """Test ForbiddenException with defaults."""
        exc = ForbiddenException()

        assert exc.message == "Forbidden"
        assert exc.code == "forbidden"
        assert exc.status_code == 403


@pytest.mark.unit
class TestConflictException:
    """Test ConflictException class."""

    def test_conflict_exception_defaults(self):
        """Test ConflictException with defaults."""
        exc = ConflictException()

        assert exc.message == "Resource conflict"
        assert exc.code == "conflict"
        assert exc.status_code == 409

    def test_conflict_exception_custom_message(self):
        """Test ConflictException with custom message."""
        exc = ConflictException("Email already exists")

        assert exc.message == "Email already exists"


@pytest.mark.unit
class TestValidationException:
    """Test ValidationException class."""

    def test_validation_exception_defaults(self):
        """Test ValidationException with defaults."""
        exc = ValidationException()

        assert exc.message == "Validation failed"
        assert exc.code == "validation_error"
        assert exc.status_code == 422


@pytest.mark.unit
class TestRateLimitException:
    """Test RateLimitException class."""

    def test_rate_limit_exception_defaults(self):
        """Test RateLimitException with defaults."""
        exc = RateLimitException()

        assert exc.message == "Rate limit exceeded"
        assert exc.code == "rate_limit_exceeded"
        assert exc.status_code == 429


@pytest.mark.unit
class TestSetupExceptionHandlers:
    """Test setup_exception_handlers function."""

    def test_setup_exception_handlers_registers_handlers(self):
        """Test that setup_exception_handlers registers all handlers."""
        app = MagicMock()

        setup_exception_handlers(app)

        assert app.exception_handler.call_count >= 6


@pytest.mark.unit
class TestAppExceptionHandler:
    """Test AppException handler."""

    @pytest.mark.asyncio
    async def test_app_exception_handler_debug_mode(self):
        """Test AppException handler in debug mode."""
        app = MagicMock()
        request = MagicMock(spec=Request)
        request.url.path = "/api/test"
        exc = AppException("Test error", details={"key": "value"})

        with patch("app.middleware.error_handler.settings") as mock_settings, \
             patch("app.middleware.error_handler.traceback") as mock_traceback, \
             patch("app.middleware.error_handler.JSONResponse") as mock_response, \
             patch("app.middleware.error_handler.get_logger") as mock_get_logger:
            mock_settings.DEBUG = True
            mock_traceback.format_exc.return_value = "Stack trace here"
            mock_logger_instance = MagicMock()
            mock_get_logger.return_value = mock_logger_instance
            mock_response_instance = MagicMock()
            mock_response.return_value = mock_response_instance

            handler = setup_exception_handlers(app)
            result = await handler(app.exception_handler.call_args[0][0], request, exc)

            mock_logger_instance.error.assert_called_once()
            call_args = mock_logger_instance.error.call_args
            assert "code" in call_args[1]
            assert "message" in call_args[1]
            assert "path" in call_args[1]
            assert "status_code" in call_args[1]
            assert "stack_trace" in call_args[1]
            assert call_args[1]["stack_trace"] == "Stack trace here"

    @pytest.mark.asyncio
    async def test_app_exception_handler_production_mode(self):
        """Test AppException handler in production mode."""
        app = MagicMock()
        request = MagicMock(spec=Request)
        request.url.path = "/api/test"
        exc = AppException("Test error")

        with patch("app.middleware.error_handler.settings") as mock_settings, \
             patch("app.middleware.error_handler.traceback") as mock_traceback, \
             patch("app.middleware.error_handler.JSONResponse") as mock_response, \
             patch("app.middleware.error_handler.get_logger") as mock_get_logger:
            mock_settings.DEBUG = False
            mock_logger_instance = MagicMock()
            mock_get_logger.return_value = mock_logger_instance
            mock_response_instance = MagicMock()
            mock_response.return_value = mock_response_instance

            handler = setup_exception_handlers(app)
            result = await handler(app.exception_handler.call_args[0][0], request, exc)

            mock_logger_instance.error.assert_called_once()
            call_args = mock_logger_instance.error.call_args
            assert "stack_trace" in call_args[1]
            assert call_args[1]["stack_trace"] is None


@pytest.mark.unit
class TestValidationExceptionHandler:
    """Test validation exception handler."""

    @pytest.mark.asyncio
    async def test_validation_exception_handler(self):
        """Test validation error handler."""
        app = MagicMock()
        request = MagicMock(spec=Request)
        request.url.path = "/api/test"
        exc = MagicMock(spec=RequestValidationError)
        exc.errors.return_value = [
            {"loc": ["body", "email"], "msg": "Invalid email", "type": "value_error"}
        ]

        with patch("app.middleware.error_handler.JSONResponse") as mock_response, \
             patch("app.middleware.error_handler.get_logger") as mock_get_logger, \
             patch("app.middleware.error_handler.ValidationErrorDetail") as mock_validation_detail, \
             patch("app.middleware.error_handler.FieldError") as mock_field_error, \
             patch("app.middleware.error_handler.ValidationErrorResponse") as mock_validation_response, \
             patch("app.middleware.error_handler.ErrorResponse") as mock_error_response:
            mock_logger_instance = MagicMock()
            mock_get_logger.return_value = mock_logger_instance
            mock_validation_detail_instance = MagicMock()
            mock_field_error_instance = MagicMock()
            mock_validation_response_instance = MagicMock()
            mock_error_response_instance = MagicMock()
            mock_response_instance = MagicMock()
            mock_response.return_value = mock_response_instance

            mock_validation_detail.return_value = mock_validation_detail_instance
            mock_field_error.return_value = mock_field_error_instance
            mock_validation_response.return_value = mock_validation_response_instance
            mock_error_response.return_value = mock_error_response_instance

            handler = setup_exception_handlers(app)
            result = await handler(app.exception_handler.call_args[1][0], request, exc)

            mock_logger_instance.warning.assert_called_once()
            mock_field_error.assert_called_once_with("body", "Invalid email", "value_error")
            mock_response_instance.assert_called_once_with(422, mock_validation_response_instance.model_dump())


@pytest.mark.unit
class TestJwtExceptionHandler:
    """Test JWT exception handler."""

    @pytest.mark.asyncio
    async def test_jwt_exception_handler(self):
        """Test JWT error handler."""
        app = MagicMock()
        request = MagicMock(spec=Request)
        request.url.path = "/api/test"
        exc = JWTError("Invalid token")

        with patch("app.middleware.error_handler.JSONResponse") as mock_response, \
             patch("app.middleware.error_handler.get_logger") as mock_get_logger, \
             patch("app.middleware.error_handler.ErrorResponse") as mock_error_response, \
             patch("app.middleware.error_handler.ErrorDetail") as mock_error_detail:
            mock_logger_instance = MagicMock()
            mock_get_logger.return_value = mock_logger_instance
            mock_error_detail_instance = MagicMock()
            mock_error_response_instance = MagicMock()
            mock_response_instance = MagicMock()
            mock_response.return_value = mock_response_instance

            mock_error_response.return_value = mock_error_response_instance
            mock_error_detail.return_value = mock_error_detail_instance

            handler = setup_exception_handlers(app)
            result = await handler(app.exception_handler.call_args[2][0], request, exc)

            mock_logger_instance.warning.assert_called_once()
            mock_error_detail.assert_called_once_with("invalid_token", "Invalid or expired token")
            mock_response_instance.assert_called_once_with(401, mock_error_response_instance.model_dump())


@pytest.mark.unit
class TestIntegrityExceptionHandler:
    """Test integrity exception handler."""

    @pytest.mark.asyncio
    async def test_integrity_exception_handler(self):
        """Test integrity exception handler."""
        from app.middleware.error_handler import setup_exception_handlers
        from sqlalchemy.exc import IntegrityError
        from fastapi import FastAPI, Request
        
        app = FastAPI()
        setup_exception_handlers(app)
        
        # Create a mock request
        request = MagicMock(spec=Request)
        request.url.path = "/api/test"
        
        # Create IntegrityError with proper SQLAlchemy structure
        exc = IntegrityError(
            statement="INSERT INTO users",
            params={},
            orig=Exception("Duplicate key")
        )
        
        # Find and call the integrity handler
        for handler_info in app.exception_handlers.items():
            if handler_info[0] == IntegrityError:
                handler = handler_info[1]
                result = await handler(request, exc)
                
                assert result.status_code == 409
                assert "integrity_error" in result.body.decode()
                break
        else:
            pytest.fail("IntegrityError handler not found")


@pytest.mark.unit
class TestSqlalchemyExceptionHandler:
    """Test SQLAlchemy exception handler."""

    @pytest.mark.asyncio
    async def test_sqlalchemy_exception_handler_debug_mode(self):
        """Test SQLAlchemy exception handler in debug mode."""
        app = MagicMock()
        request = MagicMock(spec=Request)
        request.url.path = "/api/test"
        exc = SQLAlchemyError("Query failed")

        with patch("app.middleware.error_handler.settings") as mock_settings, \
             patch("app.middleware.error_handler.traceback") as mock_traceback, \
             patch("app.middleware.error_handler.JSONResponse") as mock_response, \
             patch("app.middleware.error_handler.get_logger") as mock_get_logger, \
             patch("app.middleware.error_handler.ErrorResponse") as mock_error_response, \
             patch("app.middleware.error_handler.ErrorDetail") as mock_error_detail:
            mock_settings.DEBUG = True
            mock_traceback.format_exc.return_value = "Stack trace here"
            mock_logger_instance = MagicMock()
            mock_get_logger.return_value = mock_logger_instance
            mock_error_detail_instance = MagicMock()
            mock_error_response_instance = MagicMock()
            mock_response_instance = MagicMock()
            mock_response.return_value = mock_response_instance

            mock_error_response.return_value = mock_error_response_instance
            mock_error_detail.return_value = mock_error_detail_instance

            handler = setup_exception_handlers(app)
            result = await handler(app.exception_handler.call_args[4][0], request, exc)

            mock_logger_instance.error.assert_called_once()
            call_args = mock_logger_instance.error.call_args
            assert "stack_trace" in call_args[1]
            assert call_args[1]["stack_trace"] == "Stack trace here"

    @pytest.mark.asyncio
    async def test_sqlalchemy_exception_handler_production_mode(self):
        """Test SQLAlchemy exception handler in production mode."""
        app = MagicMock()
        request = MagicMock(spec=Request)
        request.url.path = "/api/test"
        exc = SQLAlchemyError("Query failed")

        with patch("app.middleware.error_handler.settings") as mock_settings, \
             patch("app.middleware.error_handler.traceback") as mock_traceback, \
             patch("app.middleware.error_handler.JSONResponse") as mock_response, \
             patch("app.middleware.error_handler.get_logger") as mock_get_logger, \
             patch("app.middleware.error_handler.ErrorResponse") as mock_error_response, \
             patch("app.middleware.error_handler.ErrorDetail") as mock_error_detail:
            mock_settings.DEBUG = False
            mock_logger_instance = MagicMock()
            mock_get_logger.return_value = mock_logger_instance
            mock_error_detail_instance = MagicMock()
            mock_error_response_instance = MagicMock()
            mock_response_instance = MagicMock()
            mock_response.return_value = mock_response_instance

            mock_error_response.return_value = mock_error_response_instance
            mock_error_detail.return_value = mock_error_detail_instance

            handler = setup_exception_handlers(app)
            result = await handler(app.exception_handler.call_args[4][0], request, exc)

            mock_logger_instance.error.assert_called_once()
            call_args = mock_logger_instance.error.call_args
            assert "stack_trace" in call_args[1]
            assert call_args[1]["stack_trace"] is None


@pytest.mark.unit
class TestGeneralExceptionHandler:
    """Test general exception handler."""

    @pytest.mark.asyncio
    async def test_general_exception_handler_debug_mode(self):
        """Test general exception handler in debug mode."""
        from app.middleware.error_handler import setup_exception_handlers
        from fastapi import FastAPI, Request
        
        app = FastAPI()
        setup_exception_handlers(app)
        
        # Create a mock request
        request = MagicMock(spec=Request)
        request.url.path = "/api/test"
        
        # Create a general exception
        exc = Exception("Unexpected error")
        
        # Find and call the general exception handler
        with patch("app.middleware.error_handler.settings") as mock_settings:
            mock_settings.DEBUG = True
            
            for handler_info in app.exception_handlers.items():
                if handler_info[0] == Exception:
                    handler = handler_info[1]
                    result = await handler(request, exc)
                    
                    assert result.status_code == 500
                    assert "internal_error" in result.body.decode()
                    break
            else:
                pytest.fail("Exception handler not found")

    @pytest.mark.asyncio
    async def test_general_exception_handler_production_mode(self):
        """Test general exception handler in production mode."""
        from app.middleware.error_handler import setup_exception_handlers
        from fastapi import FastAPI, Request
        
        app = FastAPI()
        setup_exception_handlers(app)
        
        # Create a mock request
        request = MagicMock(spec=Request)
        request.url.path = "/api/test"
        
        # Create a general exception
        exc = Exception("Unexpected error")
        
        # Find and call the general exception handler
        with patch("app.middleware.error_handler.settings") as mock_settings:
            mock_settings.DEBUG = False
            
            for handler_info in app.exception_handlers.items():
                if handler_info[0] == Exception:
                    handler = handler_info[1]
                    result = await handler(request, exc)
                    
                    assert result.status_code == 500
                    assert "internal_error" in result.body.decode()
                    break
            else:
                pytest.fail("Exception handler not found")


@pytest.mark.unit
class TestSchemas:
    """Test error response schemas."""

    def test_error_response_schema(self):
        """Test ErrorResponse schema."""
        from app.schemas.common import ErrorDetail

        error_detail = ErrorDetail(code="test_code", message="Test message")
        response = ErrorResponse(error=error_detail)

        assert response.success is False
        assert response.error.code == "test_code"
        assert response.error.message == "Test message"

    def test_validation_error_response_schema(self):
        """Test ValidationErrorResponse schema."""
        from app.schemas.common import FieldError

        field_errors = [
            FieldError(field="email", message="Invalid email", type="value_error")
        ]
        validation_detail = ValidationErrorDetail(errors=field_errors)
        response = ValidationErrorResponse(error=validation_detail)

        assert response.success is False
        assert response.error.code == "validation_error"
        assert response.error.errors == field_errors

    def test_field_error_schema(self):
        """Test FieldError schema."""
        field_error = FieldError(field="email", message="Invalid email", type="value_error")

        assert field_error.field == "email"
        assert field_error.message == "Invalid email"
        assert field_error.type == "value_error"
