"""Unit tests — RBAC"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/x")
os.environ.setdefault("DATABASE_SYNC_URL", "postgresql://x:x@localhost/x")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")

import pytest
from fastapi import HTTPException
from app.security.rbac import Role, _ROLE_LEVEL


def test_role_levels_are_ordered():
    assert _ROLE_LEVEL[Role.PUBLIC] < _ROLE_LEVEL[Role.CITIZEN]
    assert _ROLE_LEVEL[Role.CITIZEN] < _ROLE_LEVEL[Role.ADMIN]


def test_role_enum_values():
    assert Role.PUBLIC == "public"
    assert Role.CITIZEN == "citizen"
    assert Role.ADMIN == "admin"


def test_public_role_has_lowest_privilege():
    assert _ROLE_LEVEL[Role.PUBLIC] == 0


def test_admin_role_has_highest_privilege():
    assert _ROLE_LEVEL[Role.ADMIN] == 2
