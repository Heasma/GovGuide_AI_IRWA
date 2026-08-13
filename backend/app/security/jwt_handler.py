"""
GovGuide AI — JWT Handler
Encodes and decodes JWT access and refresh tokens.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt

from app.config import get_settings

settings = get_settings()


def create_access_token(subject: str, role: str, extra: dict = None) -> str:
    """
    Create a short-lived JWT access token.

    Args:
        subject: User ID (UUID as string)
        role: User role (public | citizen | admin)
        extra: Optional additional claims
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": subject,
        "role": role,
        "type": "access",
        "iat": now,
        "exp": expire,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    """
    Create a long-lived JWT refresh token.
    Refresh tokens carry minimal claims intentionally.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": subject,
        "type": "refresh",
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    Returns:
        Decoded payload dict.

    Raises:
        JWTError: If the token is invalid, expired, or tampered.
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


def get_token_subject(token: str) -> Optional[str]:
    """
    Safely extract the subject (user ID) from a token.
    Returns None if the token is invalid.
    """
    try:
        payload = decode_token(token)
        return payload.get("sub")
    except JWTError:
        return None
