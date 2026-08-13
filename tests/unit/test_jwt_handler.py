"""Unit tests — JWT handler"""

import pytest
import time
from jose import JWTError

# Patch settings before importing jwt_handler
import os
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/x")
os.environ.setdefault("DATABASE_SYNC_URL", "postgresql://x:x@localhost/x")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-unit-tests-only")

from app.security.jwt_handler import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_token_subject,
)


def test_create_access_token_returns_string():
    token = create_access_token(subject="user-123", role="citizen")
    assert isinstance(token, str)
    assert len(token) > 0


def test_access_token_contains_correct_claims():
    token = create_access_token(subject="user-abc", role="admin")
    payload = decode_token(token)
    assert payload["sub"] == "user-abc"
    assert payload["role"] == "admin"
    assert payload["type"] == "access"


def test_refresh_token_type():
    token = create_refresh_token(subject="user-123")
    payload = decode_token(token)
    assert payload["type"] == "refresh"
    assert payload["sub"] == "user-123"


def test_invalid_token_raises():
    with pytest.raises(JWTError):
        decode_token("this.is.not.a.valid.token")


def test_get_token_subject_returns_none_for_invalid():
    result = get_token_subject("invalid-token")
    assert result is None


def test_get_token_subject_returns_user_id():
    token = create_access_token(subject="user-xyz", role="public")
    result = get_token_subject(token)
    assert result == "user-xyz"
