"""
GovGuide AI — Authentication Service
"""

import uuid
import structlog
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.repositories.user_repository import UserRepository
from app.security.password_hasher import hash_password, verify_password
from app.security.jwt_handler import create_access_token, create_refresh_token, decode_token
from app.security.audit_logger import log_login
from app.services.exceptions import (
    DuplicateUserError,
    InvalidCredentialsError,
    InactiveUserError,
    InvalidTokenError,
    UserNotFoundError,
)

logger = structlog.get_logger(__name__)
settings = get_settings()


class AuthService:
    """Coordinates authentication and user workflow logic."""

    @staticmethod
    async def register(db: AsyncSession, email: str, password: str) -> dict:
        """
        Coordinates user registration:
        - Checks for duplicate emails.
        - Hashes password.
        - Persists user via UserRepository.
        """
        existing = await UserRepository.get_by_email(db, email)
        if existing:
            raise DuplicateUserError("An account with this email already exists.")

        hashed_password = hash_password(password)
        user = await UserRepository.create(db, email=email, password_hash=hashed_password, role="public")
        logger.info("user_registered", user_id=str(user.id))
        return {"message": "Account created successfully.", "user_id": str(user.id)}

    @staticmethod
    async def login(db: AsyncSession, email: str, password: str, ip_address: str = "unknown") -> dict:
        """
        Coordinates user login:
        - Verifies user credentials.
        - Generates JWT access/refresh tokens.
        - Logs audit events.
        """
        user = await UserRepository.get_by_email(db, email)

        if not user or not verify_password(password, user.password_hash):
            log_login(user_id=str(user.id) if user else "unknown", ip=ip_address, success=False)
            raise InvalidCredentialsError("Invalid email or password.")

        if not user.is_active:
            raise InactiveUserError("Account is deactivated.")

        access_token = create_access_token(subject=str(user.id), role=user.role)
        refresh_token = create_refresh_token(subject=str(user.id))

        log_login(user_id=str(user.id), ip=ip_address, success=True)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    @staticmethod
    async def refresh_token(db: AsyncSession, refresh_token: str) -> dict:
        """
        Refreshes access and refresh tokens.
        """
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise InvalidTokenError("Invalid token type.")
            user_id = payload.get("sub")
        except JWTError:
            raise InvalidTokenError("Invalid or expired refresh token.")

        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            raise InvalidTokenError("Invalid token subject UUID.")

        user = await UserRepository.get_by_id(db, user_uuid)
        if not user or not user.is_active:
            raise InvalidTokenError("User not found or inactive.")

        new_access_token = create_access_token(subject=str(user.id), role=user.role)
        new_refresh_token = create_refresh_token(subject=str(user.id))

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    @staticmethod
    async def get_profile(db: AsyncSession, user_id: str) -> dict:
        """
        Retrieves user profile information.
        """
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            raise UserNotFoundError("User not found.")

        user = await UserRepository.get_by_id(db, user_uuid)
        if not user:
            raise UserNotFoundError("User not found.")

        return {
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role,
            "created_at": user.created_at,
        }

    @staticmethod
    async def list_users(db: AsyncSession, skip: int = 0, limit: int = 50) -> list:
        """
        Lists all users (for admin panel).
        """
        users = await UserRepository.list_all(db, skip=skip, limit=limit)
        return [
            {
                "user_id": str(u.id),
                "email": u.email,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at,
            }
            for u in users
        ]
