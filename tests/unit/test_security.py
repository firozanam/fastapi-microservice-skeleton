"""
Unit tests for security module.
Tests password hashing, JWT token generation/verification, OTP, and token hashing.
"""
import pytest
from datetime import timedelta
from jose import JWTError
from unittest.mock import patch, MagicMock

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_otp,
    get_password_hash,
    hash_token,
    verify_hashed_token,
    verify_otp,
    verify_password,
    verify_token,
)


@pytest.mark.unit
class TestVerifyPassword:
    """Test password verification."""

    def test_verify_password_success(self):
        """Test successful password verification."""
        hashed = get_password_hash("TestPassword123")
        result = verify_password("TestPassword123", hashed)

        assert result is True

    def test_verify_password_wrong_password(self):
        """Test password verification with wrong password."""
        hashed = get_password_hash("TestPassword123")
        result = verify_password("WrongPassword", hashed)

        assert result is False


@pytest.mark.unit
class TestGetPasswordHash:
    """Test password hashing."""

    def test_get_password_hash(self):
        """Test password hashing."""
        hashed = get_password_hash("TestPassword123")

        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed != "TestPassword123"
        assert len(hashed) > 50

    def test_get_password_hash_different_passwords(self):
        """Test that different passwords produce different hashes."""
        hash1 = get_password_hash("Password1")
        hash2 = get_password_hash("Password2")

        assert hash1 != hash2


@pytest.mark.unit
class TestCreateAccessToken:
    """Test access token creation."""

    def test_create_access_token_default_expiry(self):
        """Test access token creation with default expiry."""
        from app.core.config import settings

        token = create_access_token(subject="user123")

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50

    def test_create_access_token_custom_expiry(self):
        """Test access token creation with custom expiry."""
        delta = timedelta(minutes=30)
        token = create_access_token(subject="user123", expires_delta=delta)

        assert token is not None
        assert isinstance(token, str)

    def test_create_access_token_with_additional_claims(self):
        """Test access token creation with additional claims."""
        additional_claims = {"role": "admin", "permissions": ["read", "write"]}
        token = create_access_token(subject="user123", additional_claims=additional_claims)

        assert token is not None
        assert isinstance(token, str)


@pytest.mark.unit
class TestCreateRefreshToken:
    """Test refresh token creation."""

    def test_create_refresh_token_default_expiry(self):
        """Test refresh token creation with default expiry."""
        token = create_refresh_token(subject="user123")

        assert token is not None
        assert isinstance(token, str)

    def test_create_refresh_token_custom_expiry(self):
        """Test refresh token creation with custom expiry."""
        delta = timedelta(days=3)
        token = create_refresh_token(subject="user123", expires_delta=delta)

        assert token is not None
        assert isinstance(token, str)


@pytest.mark.unit
class TestDecodeToken:
    """Test token decoding."""

    def test_decode_token_success(self):
        """Test successful token decoding."""
        token = create_access_token(subject="user123")
        payload = decode_token(token)

        assert payload is not None
        assert "sub" in payload
        assert "exp" in payload
        assert "type" in payload
        assert payload["sub"] == "user123"
        assert payload["type"] == "access"

    def test_decode_token_invalid(self):
        """Test decoding invalid token."""
        with pytest.raises(JWTError, match="Invalid token"):
            decode_token("invalid_token_string")


@pytest.mark.unit
class TestVerifyToken:
    """Test token verification."""

    def test_verify_token_success(self):
        """Test successful token verification."""
        token = create_access_token(subject="user123")
        payload = verify_token(token, token_type="access")

        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["type"] == "access"

    def test_verify_token_wrong_type(self):
        """Test token verification with wrong type."""
        token = create_access_token(subject="user123")

        with pytest.raises(JWTError, match="Invalid token type"):
            verify_token(token, token_type="refresh")

    def test_verify_token_invalid(self):
        """Test verifying invalid token."""
        with pytest.raises(JWTError, match="Invalid token"):
            verify_token("invalid_token", token_type="access")


@pytest.mark.unit
class TestGenerateOtp:
    """Test OTP generation."""

    def test_generate_otp(self):
        """Test OTP generation."""
        secret = "JBSWY3DPEHPK3PXP"  # Base32 encoded secret
        otp = generate_otp(secret)

        assert otp is not None
        assert isinstance(otp, str)
        assert len(otp) == 6
        assert otp.isdigit()

@pytest.mark.unit
class TestVerifyOtp:
    """Test OTP verification."""

    def test_verify_otp_success(self):
        """Test successful OTP verification."""
        secret = "JBSWY3DPEHPK3PXP"  # Base32 encoded secret
        otp = generate_otp(secret)

        with patch("app.core.security.TOTP") as mock_totp:
            mock_totp_instance = MagicMock()
            mock_totp.return_value = mock_totp_instance
            mock_totp_instance.verify.return_value = True

            result = verify_otp(otp, secret)

            assert result is True
            mock_totp_instance.verify.assert_called_once_with(otp, valid_window=1)

    def test_verify_otp_failure(self):
        """Test failed OTP verification."""
        secret = "test_secret_key"
        otp = "123456"

        with patch("app.core.security.TOTP") as mock_totp:
            mock_totp_instance = MagicMock()
            mock_totp.return_value = mock_totp_instance
            mock_totp_instance.verify.return_value = False

            result = verify_otp(otp, secret)

            assert result is False


@pytest.mark.unit
class TestHashToken:
    """Test token hashing."""

    def test_hash_token(self):
        """Test token hashing."""
        token = "test_token_12345"
        hashed = hash_token(token)

        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed != token
        assert len(hashed) > 50

    def test_hash_token_different_tokens(self):
        """Test that different tokens produce different hashes."""
        hash1 = hash_token("token1")
        hash2 = hash_token("token2")

        assert hash1 != hash2


@pytest.mark.unit
class TestVerifyHashedToken:
    """Test hashed token verification."""

    def test_verify_hashed_token_success(self):
        """Test successful hashed token verification."""
        token = "test_token_12345"
        hashed = hash_token(token)

        result = verify_hashed_token(token, hashed)

        assert result is True

    def test_verify_hashed_token_failure(self):
        """Test failed hashed token verification."""
        token = "test_token_12345"
        wrong_hash = hash_token("wrong_token")

        result = verify_hashed_token(token, wrong_hash)

        assert result is False
