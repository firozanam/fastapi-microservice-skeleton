"""
Security module for authentication and authorization.
Handles JWT tokens, password hashing, and OTP generation.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

import bcrypt
from jose import JWTError, jwt
from passlib.context import CryptContext
from pyotp import TOTP

from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        subject: Token subject (usually user ID)
        expires_delta: Optional expiration time delta
        additional_claims: Additional claims to include in token

    Returns:
        Encoded JWT token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access",
        "iat": datetime.utcnow(),
    }

    if additional_claims:
        to_encode.update(additional_claims)

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT refresh token.

    Args:
        subject: Token subject (usually user ID)
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT refresh token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
        "iat": datetime.utcnow(),
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError as e:
        raise JWTError(f"Invalid token: {str(e)}")


def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    """
    Verify a JWT token and check its type.

    Args:
        token: JWT token string
        token_type: Expected token type (access/refresh)

    Returns:
        Decoded token payload

    Raises:
        JWTError: If token is invalid, expired, or wrong type
    """
    payload = decode_token(token)

    if payload.get("type") != token_type:
        raise JWTError(f"Invalid token type: expected {token_type}")

    return payload


def generate_otp(secret: str) -> str:
    """
    Generate a one-time password (OTP).

    Args:
        secret: Secret key used to generate OTP

    Returns:
        OTP string
    """
    totp = TOTP(
        s=secret,
        digits=settings.SECURITY_OTP_LENGTH,
        interval=settings.SECURITY_OTP_EXPIRE_MINUTES * 60,
    )
    return totp.now()


def verify_otp(otp: str, secret: str) -> bool:
    """
    Verify a one-time password (OTP).

    Args:
        otp: OTP to verify
        secret: Secret key used to generate OTP

    Returns:
        True if OTP is valid, False otherwise
    """
    totp = TOTP(
        s=secret,
        digits=settings.SECURITY_OTP_LENGTH,
        interval=settings.SECURITY_OTP_EXPIRE_MINUTES * 60,
    )
    return totp.verify(otp, valid_window=1)


def hash_token(token: str) -> str:
    """
    Hash a token for secure storage.

    Args:
        token: Token string to hash

    Returns:
        Hashed token
    """
    salt = bcrypt.gensalt(rounds=settings.SECURITY_BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(token.encode(), salt)
    return hashed.decode()


def verify_hashed_token(token: str, hashed_token: str) -> bool:
    """
    Verify a token against its hash.

    Args:
        token: Token string to verify
        hashed_token: Hashed token to compare against

    Returns:
        True if token matches hash, False otherwise
    """
    return bcrypt.checkpw(token.encode(), hashed_token.encode())
