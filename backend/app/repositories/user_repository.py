"""
GovGuide AI — User Repository

Handles all database persistence operations for the User model.
Contains NO HTTP logic, JWT logic, or business decisions.

Methods are derived strictly from operations currently used
in the existing routers (auth.py, admin.py).
"""

import uuid
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Data access layer for the User model."""

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """
        Retrieve a user by email address.
        Used by: auth.register (duplicate check), auth.login
        """
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        """
        Retrieve a user by UUID primary key.
        Used by: auth.refresh_token, auth.get_me
        """
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        email: str,
        password_hash: str,
        role: str = "public",
    ) -> User:
        """
        Persist a new user and return the refreshed instance.
        Used by: auth.register
        """
        user = User(email=email, password_hash=password_hash, role=role)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def list_all(
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> List[User]:
        """
        Return a paginated list of all users.
        Used by: admin.list_users
        """
        result = await db.execute(select(User).offset(skip).limit(limit))
        return list(result.scalars().all())
