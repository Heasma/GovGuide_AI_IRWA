"""
GovGuide AI — Conversation Repository

Handles all database persistence operations for conversation-related models:
QuerySession, ConversationMessage, AuditLog, AgentInteractionLog.

Contains NO HTTP logic, authentication logic, or business decisions.

Methods are derived strictly from operations currently used
in the existing routers (sessions.py, admin.py).
"""

import uuid
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import (
    QuerySession,
    ConversationMessage,
    AuditLog,
    AgentInteractionLog,
)


class ConversationRepository:
    """Data access layer for conversation-related models."""

    # ── QuerySession ──────────────────────────────────────────────────────────

    @staticmethod
    async def get_sessions_by_user(
        db: AsyncSession,
        user_id: uuid.UUID,
        *,
        limit: int = 50,
    ) -> List[QuerySession]:
        """
        Return sessions belonging to a user, ordered by start time (newest first).
        Used by: sessions.list_sessions
        """
        result = await db.execute(
            select(QuerySession)
            .where(QuerySession.user_id == user_id)
            .order_by(QuerySession.started_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_session_by_id_and_user(
        db: AsyncSession,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[QuerySession]:
        """
        Return a session only if it belongs to the given user.
        Used by: sessions.get_session_messages, sessions.delete_session
        """
        result = await db.execute(
            select(QuerySession).where(
                QuerySession.id == session_id,
                QuerySession.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def delete_session(db: AsyncSession, session: QuerySession) -> None:
        """
        Delete a session instance and commit.
        Used by: sessions.delete_session
        """
        await db.delete(session)
        await db.commit()

    # ── ConversationMessage ───────────────────────────────────────────────────

    @staticmethod
    async def get_messages_by_session(
        db: AsyncSession,
        session_id: uuid.UUID,
    ) -> List[ConversationMessage]:
        """
        Return all messages in a session, ordered by creation time.
        Used by: sessions.get_session_messages
        """
        result = await db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.session_id == session_id)
            .order_by(ConversationMessage.created_at)
        )
        return list(result.scalars().all())

    # ── AuditLog ──────────────────────────────────────────────────────────────

    @staticmethod
    async def list_audit_logs(
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        event_type: Optional[str] = None,
    ) -> List[AuditLog]:
        """
        Return audit logs with optional event_type filter, ordered by creation time.
        Used by: admin.get_audit_logs
        """
        query = select(AuditLog).order_by(AuditLog.created_at.desc())
        if event_type:
            query = query.where(AuditLog.event_type == event_type)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    # ── AgentInteractionLog ───────────────────────────────────────────────────

    @staticmethod
    async def list_agent_logs(
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AgentInteractionLog]:
        """
        Return agent interaction logs ordered by creation time.
        Used by: admin.get_agent_logs
        """
        result = await db.execute(
            select(AgentInteractionLog)
            .order_by(AgentInteractionLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
