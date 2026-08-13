"""
GovGuide AI — Role-Based Access Control (RBAC)
Defines roles and permission checks used as FastAPI dependencies.
"""

from enum import Enum
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.security.jwt_handler import decode_token
from jose import JWTError

bearer_scheme = HTTPBearer(auto_error=False)


class Role(str, Enum):
    """Application roles in ascending order of privilege."""
    PUBLIC = "public"
    CITIZEN = "citizen"
    ADMIN = "admin"


# Privilege levels for comparison
_ROLE_LEVEL = {
    Role.PUBLIC: 0,
    Role.CITIZEN: 1,
    Role.ADMIN: 2,
}


def _get_current_token_payload(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """
    Internal dependency: extracts and validates JWT from Authorization header.
    Raises 401 if token is missing or invalid.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type.",
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(payload: dict = Depends(_get_current_token_payload)) -> dict:
    """
    FastAPI dependency: returns the current authenticated user's claims.
    Use this for any endpoint that requires authentication.
    """
    return {
        "user_id": payload.get("sub"),
        "role": payload.get("role", Role.PUBLIC),
    }


def require_role(minimum_role: Role):
    """
    Factory that returns a FastAPI dependency enforcing a minimum role.

    Usage:
        @router.get("/admin/users")
        async def list_users(user=Depends(require_role(Role.ADMIN))):
            ...
    """
    def dependency(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role", Role.PUBLIC)
        if _ROLE_LEVEL.get(user_role, 0) < _ROLE_LEVEL[minimum_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {minimum_role.value}.",
            )
        return current_user

    return dependency


# Convenience shortcuts
require_citizen = require_role(Role.CITIZEN)
require_admin = require_role(Role.ADMIN)
