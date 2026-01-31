"""
Unit tests for schemas module.
Tests all common and user schemas.
"""
import pytest
from datetime import datetime
from uuid import UUID, uuid4

from app.schemas.common import (
    ErrorResponse,
    FieldError,
    HealthResponse,
    MessageResponse,
    PaginationMeta,
    PaginatedResponse,
    SuccessResponse,
    ValidationErrorDetail,
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


@pytest.mark.unit
class TestPaginationMeta:
    """Test PaginationMeta schema."""

    def test_pagination_meta_success(self):
        """Test PaginationMeta with valid data."""
        meta = PaginationMeta(
            page=1,
            page_size=20,
            total_items=100,
            total_pages=5,
            has_next=True,
            has_previous=False
        )

        assert meta.page == 1
        assert meta.page_size == 20
        assert meta.total_items == 100
        assert meta.total_pages == 5
        assert meta.has_next is True
        assert meta.has_previous is False


@pytest.mark.unit
class TestSuccessResponse:
    """Test SuccessResponse schema."""

    def test_success_response_with_data(self):
        """Test SuccessResponse with data."""
        response = SuccessResponse(
            message="Success",
            data={"key": "value"}
        )

        assert response.success is True
        assert response.message == "Success"
        assert response.data == {"key": "value"}

    def test_success_response_without_data(self):
        """Test SuccessResponse without data."""
        response = SuccessResponse(message="Success")

        assert response.success is True
        assert response.message == "Success"
        assert response.data is None


@pytest.mark.unit
class TestPaginatedResponse:
    """Test PaginatedResponse schema."""

    def test_paginated_response_success(self):
        """Test PaginatedResponse with valid data."""
        meta = PaginationMeta(
            page=1,
            page_size=20,
            total_items=100,
            total_pages=5,
            has_next=True,
            has_previous=False
        )
        response = PaginatedResponse(
            message="Success",
            data=[{"id": 1}, {"id": 2}],
            pagination=meta
        )

        assert response.success is True
        assert response.message == "Success"
        assert len(response.data) == 2
        assert response.pagination == meta


@pytest.mark.unit
class TestErrorResponse:
    """Test ErrorResponse schema."""

    def test_error_response_success(self):
        """Test ErrorResponse with valid error."""
        from app.schemas.common import ErrorDetail

        error = ErrorDetail(code="test_code", message="Test error")
        response = ErrorResponse(error=error)

        assert response.success is False
        assert response.error.code == "test_code"
        assert response.error.message == "Test error"


@pytest.mark.unit
class TestValidationErrorDetail:
    """Test ValidationErrorDetail schema."""

    def test_validation_error_detail_success(self):
        """Test ValidationErrorDetail with valid errors."""
        from app.schemas.common import FieldError

        field_errors = [
            FieldError(field="email", message="Invalid email", type="value_error"),
            FieldError(field="password", message="Too short", type="string_too_short")
        ]
        detail = ValidationErrorDetail(errors=field_errors)

        assert detail.code == "validation_error"
        assert detail.message == "Validation failed"
        assert len(detail.errors) == 2
        assert detail.errors[0].field == "email"
        assert detail.errors[1].field == "password"


@pytest.mark.unit
class TestFieldError:
    """Test FieldError schema."""

    def test_field_error_success(self):
        """Test FieldError with valid data."""
        error = FieldError(field="email", message="Invalid", type="value_error")

        assert error.field == "email"
        assert error.message == "Invalid"
        assert error.type == "value_error"


@pytest.mark.unit
class TestHealthResponse:
    """Test HealthResponse schema."""

    def test_health_response_success(self):
        """Test HealthResponse with valid data."""
        response = HealthResponse(
            status="healthy",
            version="1.0.0",
            environment="production",
            checks={"database": {"status": "healthy"}, "redis": {"status": "healthy"}}
        )

        assert response.status == "healthy"
        assert response.version == "1.0.0"
        assert response.environment == "production"
        assert "database" in response.checks
        assert "redis" in response.checks


@pytest.mark.unit
class TestMessageResponse:
    """Test MessageResponse schema."""

    def test_message_response_success(self):
        """Test MessageResponse with valid message."""
        response = MessageResponse(message="Operation successful")

        assert response.success is True
        assert response.message == "Operation successful"


@pytest.mark.unit
class TestUserBase:
    """Test UserBase schema."""

    def test_user_base_success(self):
        """Test UserBase with valid data."""
        user = UserBase(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            phone="+1234567890",
            country_code="US",
            locale="en-US"
        )

        assert user.email == "test@example.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.phone == "+1234567890"
        assert user.country_code == "US"
        assert user.locale == "en-US"


@pytest.mark.unit
class TestUserCreate:
    """Test UserCreate schema."""

    def test_user_create_success(self):
        """Test UserCreate with valid data."""
        user = UserCreate(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            password="Password123"
        )

        assert user.email == "test@example.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.password == "Password123"

    def test_user_create_password_too_short(self):
        """Test UserCreate with password too short."""
        with pytest.raises(ValueError, match="String should have at least 8 characters"):
            UserCreate(
                email="test@example.com",
                first_name="John",
                last_name="Doe",
                password="short"
            )

    def test_user_create_password_no_uppercase(self):
        """Test UserCreate with password without uppercase."""
        with pytest.raises(ValueError, match="Password must contain at least one uppercase letter"):
            UserCreate(
                email="test@example.com",
                first_name="John",
                last_name="Doe",
                password="lowercase123"
            )

    def test_user_create_password_no_lowercase(self):
        """Test UserCreate with password without lowercase."""
        with pytest.raises(ValueError, match="Password must contain at least one lowercase letter"):
            UserCreate(
                email="test@example.com",
                first_name="John",
                last_name="Doe",
                password="UPPERCASE123"
            )

    def test_user_create_password_no_digit(self):
        """Test UserCreate with password without digit."""
        with pytest.raises(ValueError, match="Password must contain at least one digit"):
            UserCreate(
                email="test@example.com",
                first_name="John",
                last_name="Doe",
                password="NoDigits"
            )


@pytest.mark.unit
class TestUserUpdate:
    """Test UserUpdate schema."""

    def test_user_update_all_fields(self):
        """Test UserUpdate with all fields."""
        user = UserUpdate(
            first_name="Updated",
            last_name="Name",
            phone="+9876543210",
            country_code="CA",
            locale="fr-CA"
        )

        assert user.first_name == "Updated"
        assert user.last_name == "Name"
        assert user.phone == "+9876543210"
        assert user.country_code == "CA"
        assert user.locale == "fr-CA"

    def test_user_update_partial_fields(self):
        """Test UserUpdate with partial fields."""
        user = UserUpdate(first_name="Updated")

        assert user.first_name == "Updated"
        assert user.last_name is None
        assert user.phone is None
        assert user.country_code is None
        assert user.locale is None

    def test_user_update_no_fields(self):
        """Test UserUpdate with no fields."""
        user = UserUpdate()

        assert user.first_name is None
        assert user.last_name is None
        assert user.phone is None
        assert user.country_code is None
        assert user.locale is None

    def test_user_update_first_name_too_short(self):
        """Test UserUpdate with first_name too short."""
        with pytest.raises(ValueError, match="String should have at least 1 character"):
            UserUpdate(first_name="")

    def test_user_update_first_name_too_long(self):
        """Test UserUpdate with first_name too long."""
        with pytest.raises(ValueError, match="String should have at most 100 characters"):
            UserUpdate(first_name="A" * 101)

    def test_user_update_last_name_too_short(self):
        """Test UserUpdate with last_name too short."""
        with pytest.raises(ValueError, match="String should have at least 1 character"):
            UserUpdate(last_name="")

    def test_user_update_last_name_too_long(self):
        """Test UserUpdate with last_name too long."""
        with pytest.raises(ValueError, match="String should have at most 100 characters"):
            UserUpdate(last_name="A" * 101)

    def test_user_update_country_code_invalid_length(self):
        """Test UserUpdate with invalid country_code length."""
        with pytest.raises(ValueError, match="String should have at most 2 characters"):
            UserUpdate(country_code="USA")

    def test_user_update_country_code_too_short(self):
        """Test UserUpdate with country_code too short."""
        with pytest.raises(ValueError, match="String should have at least 2 characters"):
            UserUpdate(country_code="U")


@pytest.mark.unit
class TestUserResponse:
    """Test UserResponse schema."""

    def test_user_response_success(self):
        """Test UserResponse with valid data."""
        user_id = uuid4()
        response = UserResponse(
            id=user_id,
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            phone="+1234567890",
            country_code="US",
            locale="en-US",
            status="active",
            email_verified=True,
            phone_verified=False,
            two_factor_enabled=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        assert response.id == user_id
        assert response.email == "test@example.com"
        assert response.status == "active"
        assert response.email_verified is True
        assert response.phone_verified is False
        assert response.two_factor_enabled is False
        assert isinstance(response.created_at, datetime)
        assert isinstance(response.updated_at, datetime)


@pytest.mark.unit
class TestUserLogin:
    """Test UserLogin schema."""

    def test_user_login_success(self):
        """Test UserLogin with valid data."""
        login = UserLogin(
            email="test@example.com",
            password="password123"
        )

        assert login.email == "test@example.com"
        assert login.password == "password123"


@pytest.mark.unit
class TestTokenResponse:
    """Test TokenResponse schema."""

    def test_token_response_success(self):
        """Test TokenResponse with valid data."""
        response = TokenResponse(
            access_token="access_token_123",
            refresh_token="refresh_token_456",
            token_type="bearer",
            expires_in=3600
        )

        assert response.access_token == "access_token_123"
        assert response.refresh_token == "refresh_token_456"
        assert response.token_type == "bearer"
        assert response.expires_in == 3600


@pytest.mark.unit
class TestTokenRefresh:
    """Test TokenRefresh schema."""

    def test_token_refresh_success(self):
        """Test TokenRefresh with valid data."""
        refresh = TokenRefresh(refresh_token="refresh_token_123")

        assert refresh.refresh_token == "refresh_token_123"


@pytest.mark.unit
class TestForgotPassword:
    """Test ForgotPassword schema."""

    def test_forgot_password_success(self):
        """Test ForgotPassword with valid data."""
        request = ForgotPassword(email="test@example.com")

        assert request.email == "test@example.com"


@pytest.mark.unit
class TestResetPassword:
    """Test ResetPassword schema."""

    def test_reset_password_success(self):
        """Test ResetPassword with valid data."""
        request = ResetPassword(
            token="reset_token_123",
            new_password="NewPassword123"
        )

        assert request.token == "reset_token_123"
        assert request.new_password == "NewPassword123"

    def test_reset_password_too_short(self):
        """Test ResetPassword with password too short."""
        with pytest.raises(ValueError, match="String should have at least 8 characters"):
            ResetPassword(token="token", new_password="short")

    def test_reset_password_no_uppercase(self):
        """Test ResetPassword with password without uppercase."""
        with pytest.raises(ValueError, match="Password must contain at least one uppercase letter"):
            ResetPassword(token="token", new_password="lowercase123")

    def test_reset_password_no_lowercase(self):
        """Test ResetPassword with password without lowercase."""
        with pytest.raises(ValueError, match="Password must contain at least one lowercase letter"):
            ResetPassword(token="token", new_password="UPPERCASE123")

    def test_reset_password_no_digit(self):
        """Test ResetPassword with password without digit."""
        with pytest.raises(ValueError, match="Password must contain at least one digit"):
            ResetPassword(token="token", new_password="NoDigits")


@pytest.mark.unit
class TestVerifyOTP:
    """Test VerifyOTP schema."""

    def test_verify_otp_success(self):
        """Test VerifyOTP with valid data."""
        verify = VerifyOTP(
            email="test@example.com",
            otp="123456"
        )

        assert verify.email == "test@example.com"
        assert verify.otp == "123456"

    def test_verify_otp_too_short(self):
        """Test VerifyOTP with OTP too short."""
        with pytest.raises(ValueError, match="String should have at least 6 characters"):
            VerifyOTP(email="test@example.com", otp="123")

    def test_verify_otp_too_long(self):
        """Test VerifyOTP with OTP too long."""
        with pytest.raises(ValueError, match="String should have at most 6 characters"):
            VerifyOTP(email="test@example.com", otp="1234567")
