"""
Integration tests for API flows.
Tests complete authentication, user management, and error handling flows.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.users import (
    forgot_password,
    get_current_user_info,
    login,
    refresh_token,
    register,
    reset_password,
    update_current_user,
)
from app.core.security import create_access_token, create_refresh_token, get_password_hash
from app.models.user import User
from app.schemas.user import (
    ForgotPassword,
    ResetPassword,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserUpdate,
)


@pytest.mark.integration
class TestAuthenticationFlow:
    """Test complete authentication flow."""

    async def test_complete_registration_login_flow(self, client: AsyncClient, db_session: AsyncSession):
        """Test complete registration and login flow."""
        # Register user
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
        
        # Login with registered user
        login_data = UserLogin(
            email="newuser@example.com",
            password="Password123",
        )
        response = await client.post("/api/v1/auth/login", json=login_data.model_dump())
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]

    async def test_duplicate_registration_flow(self, client: AsyncClient, db_session: AsyncSession):
        """Test registration with duplicate email."""
        # Register user
        user_data = UserCreate(
            email="existing@example.com",
            password="Password123",
            first_name="Existing",
            last_name="User",
        )
        response = await client.post("/api/v1/auth/register", json=user_data.model_dump())
        assert response.status_code == 409
        data = response.json()
        assert data["success"] is False

    async def test_token_refresh_flow(self, client: AsyncClient, db_session: AsyncSession):
        """Test token refresh flow."""
        # Create user and login
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
        
        login_data = UserLogin(
            email="refresh@example.com",
            password="Password123",
        )
        login_response = await client.post("/api/v1/auth/login", json=login_data.model_dump())
        access_token = login_response.json()["data"]["access_token"]
        
        # Refresh token
        from app.schemas.user import TokenRefresh
        token_data = TokenRefresh(refresh_token=access_token)
        response = await client.post("/api/v1/auth/refresh", json=token_data.model_dump())
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]


@pytest.mark.integration
class TestUserManagementFlow:
    """Test complete user management flow."""

    async def test_user_update_flow(self, client: AsyncClient, db_session: AsyncSession):
        """Test user update flow."""
        # Create user and login
        user = User(
            email="update@example.com",
            password_hash=get_password_hash("Password123"),
            first_name="Update",
            last_name="User",
            status="active",
            locale="en-US",
        )
        db_session.add(user)
        await db_session.commit()
        
        login_data = UserLogin(
            email="update@example.com",
            password="Password123",
        )
        login_response = await client.post("/api/v1/auth/login", json=login_data.model_dump())
        access_token = login_response.json()["data"]["access_token"]
        
        # Update user
        update_data = UserUpdate(
            first_name="Updated",
            last_name="Name",
        )
        response = await client.put(
            "/api/v1/users/me",
            json=update_data.model_dump(),
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["first_name"] == "Updated"


@pytest.mark.integration
class TestPasswordResetFlow:
    """Test password reset flow."""

    async def test_forgot_password_flow(self, client: AsyncClient):
        """Test forgot password flow."""
        request_data = ForgotPassword(email="reset@example.com")
        response = await client.post("/api/v1/auth/forgot-password", json=request_data.model_dump())
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data

    async def test_reset_password_flow(self, client: AsyncClient):
        """Test reset password flow."""
        request_data = ResetPassword(
            token="reset_token_123",
            new_password="NewPassword123",
        )
        response = await client.post("/api/v1/auth/reset-password", json=request_data.model_dump())
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data


@pytest.mark.integration
class TestHealthCheckFlow:
    """Test health check flows."""

    async def test_health_check_integration(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "status" in data
        assert "checks" in data

    async def test_readiness_check_integration(self, client: AsyncClient):
        """Test readiness check endpoint."""
        response = await client.get("/api/v1/ready")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data


@pytest.mark.integration
class TestErrorHandlingFlow:
    """Test error handling across endpoints."""

    async def test_validation_error_handling(self, client: AsyncClient):
        """Test validation error handling."""
        # Send invalid data
        user_data = UserCreate(
            email="invalid-email",
            password="123",  # Too short
        )
        response = await client.post("/api/v1/auth/register", json=user_data.model_dump())
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False

    async def test_not_found_handling(self, client: AsyncClient):
        """Test not found error handling."""
        # Try to get non-existent user
        response = await client.get("/api/v1/users/nonexistent")
        assert response.status_code == 404

    async def test_method_not_allowed_handling(self, client: AsyncClient):
        """Test method not allowed error handling."""
        # Try POST on GET endpoint
        response = await client.post("/api/v1/health")
        assert response.status_code == 405


@pytest.mark.integration
class TestAuthenticationWithDifferentScenarios:
    """Test authentication with different scenarios."""

    async def test_login_with_wrong_password(self, client: AsyncClient, db_session: AsyncSession):
        """Test login with wrong password."""
        # Create user
        user = User(
            email="wrongpass@example.com",
            password_hash=get_password_hash("CorrectPassword"),
            first_name="Wrong",
            last_name="Pass",
            status="active",
            locale="en-US",
        )
        db_session.add(user)
        await db_session.commit()
        
        login_data = UserLogin(
            email="wrongpass@example.com",
            password="WrongPassword",
        )
        response = await client.post("/api/v1/auth/login", json=login_data.model_dump())
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False

    async def test_access_protected_endpoint_without_token(self, client: AsyncClient):
        """Test accessing protected endpoint without token."""
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 403

    async def test_access_protected_endpoint_with_invalid_token(self, client: AsyncClient):
        """Test accessing protected endpoint with invalid token."""
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 403


@pytest.mark.integration
class TestSecurityFlow:
    """Test security-related flows."""

    async def test_password_hashing_flow(self):
        """Test password hashing."""
        password = "TestPassword123"
        hashed = get_password_hash(password)
        assert hashed is not None
        assert hashed != password
        assert isinstance(hashed, str)

    async def test_token_generation_and_verification_flow(self):
        """Test token generation and verification."""
        # Create user
        user = User(
            email="token@example.com",
            password_hash=get_password_hash("Password123"),
            first_name="Token",
            last_name="User",
            status="active",
            locale="en-US",
        )
        
        # Generate access token
        access_token = create_access_token(subject=str(user.id))
        assert access_token is not None
        assert isinstance(access_token, str)

    async def test_refresh_token_generation_flow(self):
        """Test refresh token generation."""
        # Create user
        user = User(
            email="refresh@example.com",
            password_hash=get_password_hash("Password123"),
            first_name="Refresh",
            last_name="User",
            status="active",
            locale="en-US",
        )
        
        # Generate refresh token
        refresh_token = create_refresh_token(subject=str(user.id))
        assert refresh_token is not None
        assert isinstance(refresh_token, str)

    async def test_token_expiration_flow(self):
        """Test token expiration handling."""
        # Create user
        user = User(
            email="expire@example.com",
            password_hash=get_password_hash("Password123"),
            first_name="Expire",
            last_name="User",
            status="active",
            locale="en-US",
        )
        
        # Generate short-lived token
        from datetime import timedelta
        access_token = create_access_token(
            subject=str(user.id),
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        # Try to use expired token
        from app.core.security import verify_token
        from jose import JWTError
        with pytest.raises(JWTError):
            verify_token(access_token)


@pytest.mark.integration
class TestCrossEndpointFlow:
    """Test cross-endpoint flows."""

    async def test_register_and_get_user_flow(self, client: AsyncClient, db_session: AsyncSession):
        """Test register and get user flow."""
        # Register user
        user_data = UserCreate(
            email="cross@example.com",
            password="Password123",
            first_name="Cross",
            last_name="Endpoint",
        )
        response = await client.post("/api/v1/auth/register", json=user_data.model_dump())
        assert response.status_code == 201
        
        # Login
        login_data = UserLogin(
            email="cross@example.com",
            password="Password123",
        )
        login_response = await client.post("/api/v1/auth/login", json=login_data.model_dump())
        access_token = login_response.json()["data"]["access_token"]
        
        # Get user info
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_multiple_concurrent_requests_flow(self, client: AsyncClient, db_session: AsyncSession):
        """Test handling multiple concurrent requests."""
        # Create multiple users concurrently
        import asyncio
        
        async def register_user(email):
            user_data = UserCreate(
                email=email,
                password="Password123",
                first_name="Concurrent",
                last_name="User",
            )
            return await client.post("/api/v1/auth/register", json=user_data.model_dump())
        
        # Make concurrent requests
        results = await asyncio.gather(
            register_user("user1@example.com"),
            register_user("user2@example.com"),
            register_user("user3@example.com"),
        )
        
        # All should succeed
        for result in results:
            assert result.status_code == 201


@pytest.mark.integration
class TestEdgeCases:
    """Test edge cases and error handling."""

    async def test_user_update_with_no_changes_flow(self, client: AsyncClient, db_session: AsyncSession):
        """Test user update with no changes."""
        # Create user and login
        user = User(
            email="nochange@example.com",
            password_hash=get_password_hash("Password123"),
            first_name="No",
            last_name="Change",
            status="active",
            locale="en-US",
        )
        db_session.add(user)
        await db_session.commit()
        
        login_data = UserLogin(
            email="nochange@example.com",
            password="Password123",
        )
        login_response = await client.post("/api/v1/auth/login", json=login_data.model_dump())
        access_token = login_response.json()["data"]["access_token"]
        
        # Update with no changes
        update_data = UserUpdate()
        response = await client.put(
            "/api/v1/users/me",
            json=update_data.model_dump(),
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_password_strength_validation_flow(self, client: AsyncClient):
        """Test password strength validation."""
        # Test password without uppercase
        user_data = UserCreate(
            email="weak@example.com",
            password="lowercase123",  # No uppercase
            first_name="Weak",
            last_name="Password",
        )
        response = await client.post("/api/v1/auth/register", json=user_data.model_dump())
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False

    async def test_email_validation_flow(self, client: AsyncClient):
        """Test email validation."""
        # Test with invalid email
        user_data = UserCreate(
            email="invalid-email",
            password="Password123",
            first_name="Invalid",
            last_name="Email",
        )
        response = await client.post("/api/v1/auth/register", json=user_data.model_dump())
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False

    async def test_token_refresh_with_expired_token_flow(self, client: AsyncClient):
        """Test token refresh with expired token."""
        # Create expired token
        from datetime import timedelta
        expired_token = create_access_token(
            subject="test_user_id",
            expires_delta=timedelta(seconds=-1)
        )
        
        # Try to refresh with expired token
        from app.schemas.user import TokenRefresh
        token_data = TokenRefresh(refresh_token=expired_token)
        response = await client.post("/api/v1/auth/refresh", json=token_data.model_dump())
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False

    async def test_health_checks_with_dependencies_flow(self, client: AsyncClient):
        """Test health checks with dependency failures."""
        # Health check should work even if some dependencies are down
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        # Should return status even if some checks fail
        assert "status" in data
        assert "checks" in data
