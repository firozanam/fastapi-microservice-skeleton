"""
Unit tests for user management endpoints.
Tests register, login, refresh, get_user, update_user, forgot/reset password endpoints.

Note: All tests in this file require PostgreSQL to be enabled (ENABLE_POSTGRES=true).
Tests will be automatically skipped if PostgreSQL is disabled.
"""
import pytest
from datetime import timedelta
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.api.v1.endpoints.users import (
    forgot_password,
    get_current_user_info,
    login,
    register,
    refresh_token,
    reset_password,
    update_current_user,
)
from app.core.security import create_access_token, create_refresh_token, get_password_hash
from app.middleware.error_handler import BadRequestException, ConflictException, UnauthorizedException
from app.models.user import User
from app.schemas.common import SuccessResponse
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


# Mark all tests in this module as requiring PostgreSQL
pytestmark = pytest.mark.postgres


@pytest.mark.unit
class TestRegister:
    """Test register endpoint."""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient, db_session: AsyncSession):
        """Test successful user registration."""
        user_data = UserCreate(
            email="newuser@example.com",
            password="Password123",
            first_name="New",
            last_name="User",
        )

        response = await client.post("/api/v1/auth/register", json=user_data.model_dump())

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["email"] == "newuser@example.com"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, db_session: AsyncSession):
        """Test registration with duplicate email."""
        # Create existing user
        existing_user = User(
            email="existing@example.com",
            password_hash=get_password_hash("Password123"),
            first_name="Existing",
            last_name="User",
            status="active",
            locale="en-US",
        )
        db_session.add(existing_user)
        await db_session.commit()

        user_data = UserCreate(
            email="existing@example.com",
            password="Password123",
            first_name="New",
            last_name="User",
        )

        response = await client.post("/api/v1/auth/register", json=user_data.model_dump())

        assert response.status_code == 409
        data = response.json()
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_register_minimal_data(self, client: AsyncClient, db_session: AsyncSession):
        """Test registration with minimal required data."""
        user_data = UserCreate(
            email="minimal@example.com",
            password="Password123",
            first_name="Test",
            last_name="User",
        )

        response = await client.post("/api/v1/auth/register", json=user_data.model_dump())

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_register_all_fields(self, client: AsyncClient, db_session: AsyncSession):
        """Test registration with all fields."""
        user_data = UserCreate(
            email="allfields@example.com",
            password="Password123",
            first_name="All",
            last_name="Fields",
            phone="+1234567890",
            country_code="US",
            locale="en-US",
        )

        response = await client.post("/api/v1/auth/register", json=user_data.model_dump())

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["phone"] == "+1234567890"
        assert data["data"]["country_code"] == "US"


@pytest.mark.unit
class TestLogin:
    """Test login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, db_session: AsyncSession):
        """Test successful login."""
        # Create user
        user = User(
            email="login@example.com",
            password_hash=get_password_hash("Password123"),
            first_name="Login",
            last_name="User",
            status="active",
            locale="en-US",
        )
        db_session.add(user)
        await db_session.commit()

        login_data = UserLogin(
            email="login@example.com",
            password="Password123",
        )

        response = await client.post("/api/v1/auth/login", json=login_data.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]

    @pytest.mark.asyncio
    async def test_login_invalid_email(self, client: AsyncClient, db_session: AsyncSession):
        """Test login with invalid email."""
        login_data = UserLogin(
            email="wrong@example.com",
            password="Password123",
        )

        response = await client.post("/api/v1/auth/login", json=login_data.model_dump())

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, client: AsyncClient, db_session: AsyncSession):
        """Test login with invalid password."""
        # Create user
        user = User(
            email="login@example.com",
            password_hash=get_password_hash("Password123"),
            first_name="Login",
            last_name="User",
            status="active",
            locale="en-US",
        )
        db_session.add(user)
        await db_session.commit()

        login_data = UserLogin(
            email="login@example.com",
            password="WrongPassword",
        )

        response = await client.post("/api/v1/auth/login", json=login_data.model_dump())

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, client: AsyncClient, db_session: AsyncSession):
        """Test login with inactive user."""
        # Create inactive user
        user = User(
            email="inactive@example.com",
            password_hash=get_password_hash("Password123"),
            first_name="Inactive",
            last_name="User",
            status="inactive",
            locale="en-US",
        )
        db_session.add(user)
        await db_session.commit()

        login_data = UserLogin(
            email="inactive@example.com",
            password="Password123",
        )

        response = await client.post("/api/v1/auth/login", json=login_data.model_dump())

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False


@pytest.mark.unit
class TestRefreshToken:
    """Test refresh token endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client: AsyncClient, db_session: AsyncSession):
        """Test successful token refresh."""
        # Create user
        user = User(
            email="refresh@example.com",
            password_hash=get_password_hash("Password123"),
            first_name="Refresh",
            last_name="User",
            status="active",
            locale="en-US",
        )
        db_session.add(user)
        await db_session.commit()

        # Create access token
        access_token = create_access_token(subject=str(user.id))

        refresh_data = TokenRefresh(refresh_token=access_token)

        response = await client.post("/api/v1/auth/refresh", json=refresh_data.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client: AsyncClient, db_session: AsyncSession):
        """Test refresh with invalid token."""
        refresh_data = TokenRefresh(refresh_token="invalid_token")

        response = await client.post("/api/v1/auth/refresh", json=refresh_data.model_dump())

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_refresh_token_expired(self, client: AsyncClient, db_session: AsyncSession):
        """Test refresh with expired token."""
        # Create expired token
        expired_token = create_access_token(
            subject="user123",
            expires_delta=timedelta(seconds=-1)
        )

        refresh_data = TokenRefresh(refresh_token=expired_token)

        response = await client.post("/api/v1/auth/refresh", json=refresh_data.model_dump())

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False


@pytest.mark.unit
class TestGetCurrentUserInfo:
    """Test get current user info endpoint."""

    @pytest.mark.asyncio
    async def test_get_current_user_info_success(self, client: AsyncClient, db_session: AsyncSession):
        """Test successful get current user info."""
        # Create user
        user = User(
            id=uuid4(),
            email="user@example.com",
            password_hash=get_password_hash("Password123"),
            first_name="Test",
            last_name="User",
            status="active",
            locale="en-US",
        )
        db_session.add(user)
        await db_session.commit()

        # Create token
        token = create_access_token(subject=str(user.id))

        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == "user@example.com"

    @pytest.mark.asyncio
    async def test_get_current_user_info_unauthorized(self, client: AsyncClient):
        """Test get current user info without token."""
        response = await client.get("/api/v1/users/me")

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_current_user_info_invalid_token(self, client: AsyncClient):
        """Test get current user info with invalid token."""
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401


@pytest.mark.unit
class TestUpdateCurrentUser:
    """Test update current user endpoint."""

    @pytest.mark.asyncio
    async def test_update_current_user_success(self, client: AsyncClient, db_session: AsyncSession):
        """Test successful user update."""
        # Create user
        user = User(
            id=uuid4(),
            email="update@example.com",
            password_hash=get_password_hash("Password123"),
            first_name="Original",
            last_name="Name",
            status="active",
            locale="en-US",
        )
        db_session.add(user)
        await db_session.commit()

        # Create token
        token = create_access_token(subject=str(user.id))

        update_data = UserUpdate(first_name="Updated")

        response = await client.put(
            "/api/v1/users/me",
            json=update_data.model_dump(),
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["first_name"] == "Updated"

    @pytest.mark.asyncio
    async def test_update_current_user_partial(self, client: AsyncClient, db_session: AsyncSession):
        """Test partial user update."""
        # Create user
        user = User(
            id=uuid4(),
            email="update@example.com",
            password_hash=get_password_hash("Password123"),
            first_name="Original",
            last_name="Name",
            status="active",
            locale="en-US",
        )
        db_session.add(user)
        await db_session.commit()

        # Create token
        token = create_access_token(subject=str(user.id))

        update_data = UserUpdate(last_name="Name")

        response = await client.put(
            "/api/v1/users/me",
            json=update_data.model_dump(),
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["last_name"] == "Name"
        assert data["data"]["first_name"] == "Original"

    @pytest.mark.asyncio
    async def test_update_current_user_no_changes(self, client: AsyncClient, db_session: AsyncSession):
        """Test user update with no changes."""
        # Create user
        user = User(
            id=uuid4(),
            email="update@example.com",
            password_hash=get_password_hash("Password123"),
            first_name="Original",
            last_name="Name",
            status="active",
            locale="en-US",
        )
        db_session.add(user)
        await db_session.commit()

        # Create token
        token = create_access_token(subject=str(user.id))

        update_data = UserUpdate()

        response = await client.put(
            "/api/v1/users/me",
            json=update_data.model_dump(),
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_update_current_user_unauthorized(self, client: AsyncClient):
        """Test update without authorization."""
        update_data = UserUpdate(first_name="Updated")

        response = await client.put(
            "/api/v1/users/me",
            json=update_data.model_dump()
        )

        assert response.status_code == 403


@pytest.mark.unit
class TestForgotPassword:
    """Test forgot password endpoint."""

    @pytest.mark.asyncio
    async def test_forgot_password_success(self, client: AsyncClient):
        """Test successful forgot password."""
        request_data = ForgotPassword(email="test@example.com")

        response = await client.post("/api/v1/auth/forgot-password", json=request_data.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data

    @pytest.mark.asyncio
    async def test_forgot_password_invalid_email(self, client: AsyncClient):
        """Test forgot password with invalid email."""
        # Send invalid email directly to endpoint (bypass schema validation)
        response = await client.post("/api/v1/auth/forgot-password", json={"email": "invalid-email"})

        assert response.status_code == 422


@pytest.mark.unit
class TestResetPassword:
    """Test reset password endpoint."""

    @pytest.mark.asyncio
    async def test_reset_password_success(self, client: AsyncClient):
        """Test successful reset password."""
        request_data = ResetPassword(
            token="reset_token_123",
            new_password="NewPassword123"
        )

        response = await client.post("/api/v1/auth/reset-password", json=request_data.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(self, client: AsyncClient):
        """Test reset password with invalid token."""
        request_data = ResetPassword(
            token="invalid_token",
            new_password="NewPassword123"
        )

        response = await client.post("/api/v1/auth/reset-password", json=request_data.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_reset_password_weak_password(self, client: AsyncClient):
        """Test reset password with weak password."""
        # Send weak password directly to endpoint (bypass schema validation)
        response = await client.post("/api/v1/auth/reset-password", json={
            "token": "reset_token_123",
            "new_password": "weak"
        })

        assert response.status_code == 422
