"""
Unit tests for API dependencies module.
Tests get_current_user, get_current_user_optional, require_admin, get_cache, get_request_id.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_cache,
    get_current_user,
    get_current_user_optional,
    get_request_id,
    require_admin,
    security,
)
from app.middleware.error_handler import UnauthorizedException
from app.models.user import User


@pytest.mark.unit
class TestSecurityScheme:
    """Test security scheme."""

    def test_security_scheme_exists(self):
        """Test that security scheme is HTTPBearer."""
        from fastapi.security import HTTPBearer
        assert isinstance(security, HTTPBearer)


@pytest.mark.unit
class TestGetCurrentUser:
    """Test get_current_user dependency."""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self):
        """Test successful user retrieval."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = "test-user-id"
        mock_user.status = "active"

        with patch("app.api.deps.verify_token") as mock_verify:
            mock_verify.return_value = {"sub": "test-user-id"}
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_db.execute = AsyncMock(return_value=mock_result)

            result = await get_current_user(
                credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token"),
                db=mock_db
            )

            assert result == mock_user
            mock_verify.assert_called_once_with("valid_token", token_type="access")

    @pytest.mark.asyncio
    async def test_get_current_user_missing_subject(self):
        """Test get_current_user with missing subject."""
        mock_db = AsyncMock(spec=AsyncSession)

        with patch("app.api.deps.verify_token") as mock_verify:
            mock_verify.return_value = {}

            with pytest.raises(UnauthorizedException, match="Invalid token: missing subject"):
                await get_current_user(
                    credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials="token"),
                    db=mock_db
                )

    @pytest.mark.asyncio
    async def test_get_current_user_jwt_error(self):
        """Test get_current_user with JWT error."""
        mock_db = AsyncMock(spec=AsyncSession)

        with patch("app.api.deps.verify_token") as mock_verify:
            mock_verify.side_effect = JWTError("Invalid token")

            with pytest.raises(UnauthorizedException, match="Invalid token"):
                await get_current_user(
                    credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid_token"),
                    db=mock_db
                )

    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self):
        """Test get_current_user when user not found."""
        mock_db = AsyncMock(spec=AsyncSession)

        with patch("app.api.deps.verify_token") as mock_verify:
            mock_verify.return_value = {"sub": "test-user-id"}
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute = AsyncMock(return_value=mock_result)

            with pytest.raises(UnauthorizedException, match="User not found"):
                await get_current_user(
                    credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token"),
                    db=mock_db
                )

    @pytest.mark.asyncio
    async def test_get_current_user_inactive_user(self):
        """Test get_current_user when user is inactive."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = "test-user-id"
        mock_user.status = "inactive"

        with patch("app.api.deps.verify_token") as mock_verify:
            mock_verify.return_value = {"sub": "test-user-id"}
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_db.execute = AsyncMock(return_value=mock_result)

            with pytest.raises(UnauthorizedException, match="User account is not active"):
                await get_current_user(
                    credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token"),
                    db=mock_db
                )


@pytest.mark.unit
class TestGetCurrentUserOptional:
    """Test get_current_user_optional dependency."""

    @pytest.mark.asyncio
    async def test_get_current_user_optional_with_valid_token(self):
        """Test get_current_user_optional with valid token."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = "test-user-id"
        mock_user.status = "active"

        with patch("app.api.deps.verify_token") as mock_verify:
            mock_verify.return_value = {"sub": "test-user-id"}
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_db.execute = AsyncMock(return_value=mock_result)

            result = await get_current_user_optional(
                credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token"),
                db=mock_db
            )

            assert result == mock_user

    @pytest.mark.asyncio
    async def test_get_current_user_optional_without_credentials(self):
        """Test get_current_user_optional without credentials."""
        mock_db = AsyncMock(spec=AsyncSession)

        result = await get_current_user_optional(
            credentials=None,
            db=mock_db
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_get_current_user_optional_missing_subject(self):
        """Test get_current_user_optional with missing subject."""
        mock_db = AsyncMock(spec=AsyncSession)

        with patch("app.api.deps.verify_token") as mock_verify:
            mock_verify.return_value = {}

            result = await get_current_user_optional(
                credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials="token"),
                db=mock_db
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_get_current_user_optional_jwt_error(self):
        """Test get_current_user_optional with JWT error."""
        mock_db = AsyncMock(spec=AsyncSession)

        with patch("app.api.deps.verify_token") as mock_verify:
            mock_verify.side_effect = JWTError("Invalid token")

            result = await get_current_user_optional(
                credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid_token"),
                db=mock_db
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_get_current_user_optional_user_not_found(self):
        """Test get_current_user_optional when user not found."""
        mock_db = AsyncMock(spec=AsyncSession)

        with patch("app.api.deps.verify_token") as mock_verify:
            mock_verify.return_value = {"sub": "test-user-id"}
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute = AsyncMock(return_value=mock_result)

            result = await get_current_user_optional(
                credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token"),
                db=mock_db
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_get_current_user_optional_inactive_user(self):
        """Test get_current_user_optional when user is inactive."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = MagicMock(spec=User)
        mock_user.id = "test-user-id"
        mock_user.status = "inactive"

        with patch("app.api.deps.verify_token") as mock_verify:
            mock_verify.return_value = {"sub": "test-user-id"}
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_db.execute = AsyncMock(return_value=mock_result)

            result = await get_current_user_optional(
                credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token"),
                db=mock_db
            )

            assert result is None


@pytest.mark.unit
class TestRequireAdmin:
    """Test require_admin dependency."""

    @pytest.mark.asyncio
    async def test_require_admin_with_admin_user(self):
        """Test require_admin with admin user."""
        mock_user = MagicMock(spec=User)
        mock_user.is_admin = True

        result = await require_admin(current_user=mock_user)

        assert result == mock_user

    @pytest.mark.asyncio
    async def test_require_admin_with_non_admin_user(self):
        """Test require_admin with non-admin user."""
        mock_user = MagicMock(spec=User)
        mock_user.is_admin = False

        with pytest.raises(UnauthorizedException, match="Admin access required"):
            await require_admin(current_user=mock_user)

    @pytest.mark.asyncio
    async def test_require_admin_without_is_admin_attribute(self):
        """Test require_admin when user doesn't have is_admin attribute."""
        mock_user = MagicMock(spec=User)
        delattr(mock_user, "is_admin")

        with pytest.raises(UnauthorizedException, match="Admin access required"):
            await require_admin(current_user=mock_user)


@pytest.mark.unit
class TestGetCache:
    """Test get_cache dependency."""

    def test_get_cache_returns_cache_service(self):
        """Test that get_cache returns CacheService."""
        mock_cache_service = MagicMock()

        result = get_cache(cache_service=mock_cache_service)

        assert result == mock_cache_service


@pytest.mark.unit
class TestGetRequestId:
    """Test get_request_id dependency."""

    def test_get_request_id_with_header(self):
        """Test get_request_id with X-Request-ID header."""
        result = get_request_id(x_request_id="test-request-id")

        assert result == "test-request-id"

    def test_get_request_id_without_header(self):
        """Test get_request_id without X-Request-ID header."""
        result = get_request_id(x_request_id=None)

        assert result is None
